import os
import time
import json
import gc
import speech_recognition as sr
from faster_whisper import WhisperModel
import requests
import tempfile
import subprocess
import soundfile as sf
import numpy as np

from wake import wait_for_wake_word, init_wake_word_engine
from tools.registry import TOOLS, TOOL_DEFINITIONS, execute_tool_safely

# ---------------- CONFIG ----------------

SAMPLE_RATE = 16000

OLLAMA_MODEL = "qwen2.5:3b-instruct"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Dynamically inject tool definitions
# NOTE: TOOL_DEFINITIONS is imported from tools.registry at the top of the file.
AGENT_SYSTEM_PROMPT = f"""
You are Jarvis, an AI agent.

You MUST always output valid JSON.
You MUST never output plain text.
No markdown. No explanations.

You decide both:
1) What to say to the user
2) What action to take (if any)

{TOOL_DEFINITIONS}

Use this schema ONLY:

{{
  "intent": "respond | act | respond_and_act | error",
  "speech": "string or null",
  "plan": [
      {{
        "tool": "tool_name",
        "args": {{...}},
        "description": "Short description of this step"
      }}
  ] or null,
  "confidence": number between 0.0 and 1.0
}}

Rules:
- You can provide a LIST of steps in "plan" to perform multi-step tasks.
- If an action is taken, explain it briefly in "speech"
- Be concise and confident
- If no action is needed, "plan" must be null
- If unsure, use intent = "error"
- If the user input is uncertain or ambiguous, prefer asking for clarification.
- MEMORY: If the user states a preference or fact, use 'store_memory'. If you need to recall something, use 'retrieve_memory'.
"""

PIPER_EXE = "./piper_bin/piper/piper"
PIPER_MODEL = "voices/ryan-med/en_US-ryan-medium.onnx"

# ---------------- AUDIO ----------------

def listen_for_command(recognizer, source, timeout=None):
    print("🎙️ Listening for command...", end="\r")
    try:
        audio = recognizer.listen(
            source,
            timeout=timeout,
            phrase_time_limit=None
        )
        print(" " * 40, end="\r")
        return audio
    except sr.WaitTimeoutError:
        print(" " * 40, end="\r")
        raise

# ---------------- STT ----------------

def transcribe(audio_data, model):
    pcm = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16).astype(np.float32)
    pcm /= 32768.0 

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, pcm, SAMPLE_RATE)
        wav_path = f.name

    try:
        # Tuned parameters for Medium INT8
        segments, info = model.transcribe(
            wav_path,
            beam_size=7,
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=True,
            no_speech_threshold=0.6,
            log_prob_threshold=-1.0
        )

        texts = []
        logprobs = []
        no_speech_probs = []

        for seg in segments:
            texts.append(seg.text.strip())
            logprobs.append(seg.avg_logprob)
            no_speech_probs.append(seg.no_speech_prob)

        final_text = " ".join(texts).strip()
        
        # Hallucination Guard
        hallucinations = {
            "you", "thank you", "thanks",
            "subtitles by", "amara.org", "mbc"
        }
        if final_text.lower().strip(".,!?") in hallucinations:
             return None, 0.0

        # ---- CONFIDENCE GATING ----
        if not final_text or not logprobs:
            return None, 0.0

        avg_logprob = sum(logprobs) / len(logprobs)
        max_no_speech = max(no_speech_probs)

        # Normalize logprob to roughly 0-1 scale (heuristic)
        # logprob 0 = 100%, -1 = 37%, -2 = 13%
        # Simple clamp: max(0, (logprob + 1.0))
        confidence = max(0.0, min(1.0, (avg_logprob + 1.0)))

        # Reject if likely noise or very low confidence
        # -0.7 is roughly 50% confidence
        if avg_logprob < -0.7 or max_no_speech > 0.6:
            return None, confidence

        return final_text, confidence

    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)

# ---------------- LLM ----------------

def ask_llm(text, system_prompt=AGENT_SYSTEM_PROMPT, json_format=True):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": text,
        "system": system_prompt,
        "stream": False,
    }
    if json_format:
        payload["format"] = "json"
        
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["response"].strip()
    except requests.exceptions.RequestException as e:
        print(f"❌ LLM Error: {e}")
        return None

# ---------------- PIPER ----------------

def speak(text):
    if not text:
        return
    print("🗣️ Jarvis:", text)
    cmd = (
        f'echo "{text}" | {PIPER_EXE} '
        f'--model {PIPER_MODEL} --output_raw | '
        'aplay -r 22050 -f S16_LE -t raw -'
    )
    subprocess.run(cmd, shell=True, check=True)

# ---------------- PLAN REPAIR & EXECUTION ----------------

DATA_TOOLS = {
    "search_web", "read_file", "retrieve_memory", 
    "list_files", "system_status", "get_time"
}

def request_plan_repair(user_goal, plan_state):
    print(f"🔧 Attempting Plan Repair (Attempt {plan_state.get('repair_attempts', 0) + 1})")
    
    prompt = f"""
The original user request was:
"{user_goal}"

The plan failed at step {plan_state['current_step']}.

Execution history:
{json.dumps(plan_state['history'], indent=2)}

Create a NEW plan that fixes the problem.
Do not repeat steps that already succeeded (unless necessary).
Do not blindly retry the exact same failing step without changing arguments.
If repair is impossible, return a plan with null.
"""
    
    response = ask_llm(prompt)
    if response:
        try:
            return json.loads(response).get("plan")
        except:
            return None
    return None

def generate_final_response(user_text, observations):
    """
    Asks the LLM to synthesize tool outputs into a natural response.
    """
    prompt = f"""
User Request: "{user_text}"

The system performed actions and gathered the following information:
{observations}

Please provide a concise, natural response to the user based on this information.
Do not mention "I used a tool" or "The system returned". Just answer the question or confirm the status.
"""
    # Request plain text for the summary, not JSON
    response = ask_llm(prompt, system_prompt="You are Jarvis. Summarize the information helpfully.", json_format=False)
    
    if response:
        return response
    return "I found the information but couldn't summarize it."

def execute_plan_with_repair(plan, original_user_text, repair_depth=0):
    MAX_REPAIRS = 2
    
    if repair_depth > MAX_REPAIRS:
        speak("I am stuck and cannot fix the plan. Please help.")
        return

    plan_state = {
        "current_step": 0,
        "steps": plan,
        "history": [],
        "repair_attempts": repair_depth
    }
    
    observations = []

    for i, step in enumerate(plan):
        plan_state["current_step"] = i + 1
        tool_name = step.get("tool")
        args = step.get("args", {})
        description = step.get("description", tool_name)

        print(f"▶️ Step {i+1}: {description}")
        
        # Execute Safe
        result = execute_tool_safely(tool_name, args)

        plan_state["history"].append({
            "step": step,
            "result": result
        })

        # ---- FAILURE DETECTED ----
        if result.get("status") == "error":
            print(f"❌ Step Failed: {result.get('error')}")
            speak(f"I ran into an issue with {description}.")
            
            repaired_plan = request_plan_repair(original_user_text, plan_state)

            if repaired_plan:
                speak("Adapting my plan.")
                execute_plan_with_repair(repaired_plan, original_user_text, repair_depth + 1)
            else:
                speak("I couldn't figure out how to fix it.")
            
            return # Stop this execution branch
        
        # ---- DATA COLLECTION ----
        # If the tool is a data-retrieval tool, save the result
        if tool_name in DATA_TOOLS and result.get("status") == "ok":
            output = result.get("result")
            observations.append(f"Tool '{tool_name}' output: {output}")

        time.sleep(0.5)

    # After plan finishes, if we have observations, summarize them
    if observations:
        print("📝 Synthesizing answer from tool outputs...")
        final_answer = generate_final_response(original_user_text, "\n".join(observations))
        speak(final_answer)
    else:
        speak("Done.")

# ---------------- MAIN LOOP ----------------

def main():
    print("🧠 Loading models...")

    whisper_model = None
    wake_model = None

    # Load Faster-Whisper ONCE
    try:
        whisper_model = WhisperModel(
            "medium.en",
            device="cuda",
            compute_type="int8"
        )
        print("✅ Faster-Whisper (Medium) loaded on CUDA (int8)")
    except Exception:
        print("⚠️ CUDA failed, falling back to CPU")
        whisper_model = WhisperModel(
            "medium.en",
            device="cpu",
            compute_type="int8"
        )
        print("✅ Faster-Whisper (Medium) loaded on CPU (int8)")

    try:
        wake_model = init_wake_word_engine()
        print("✅ Wake word engine ready")
    except Exception as e:
        print(f"❌ Wake word init failed: {e}")
        return

    recognizer = sr.Recognizer()

    recognizer.energy_threshold = 200
    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.15
    recognizer.pause_threshold = 2.0
    recognizer.non_speaking_duration = 0.5

    INACTIVITY_LIMIT = 300 
    
    # RELAXED CONFIDENCE THRESHOLDS (Production-Grade)
    HIGH_CONFIDENCE = 0.60
    MEDIUM_CONFIDENCE = 0.40
    LOW_CONFIDENCE = 0.25

    print("🧠 Jarvis main loop started")

    try:
        while True:
            wait_for_wake_word(wake_model)

            print("🟢 Active Chat Mode Enabled")

            with sr.Microphone(sample_rate=SAMPLE_RATE) as source:
                print("🎙️ Calibrating ambient noise...")
                recognizer.adjust_for_ambient_noise(source, duration=2.0)
                print(f"✅ Energy threshold: {recognizer.energy_threshold}")

                last_activity = time.time()

                while True:
                    if time.time() - last_activity > INACTIVITY_LIMIT:
                        print("💤 Inactivity timeout")
                        speak("I am going to sleep now.")
                        break

                    try:
                        audio = listen_for_command(recognizer, source, timeout=5)
                        text, confidence = transcribe(audio, whisper_model)

                        if not text or confidence < LOW_CONFIDENCE:
                            # Too low confidence or silence (Noise)
                            if confidence > 0:
                                print(f"🔇 Ignored noise/low confidence ({confidence:.2f})...")
                            continue

                        print(f"👤 You ({confidence:.2f}): {text}")
                        last_activity = time.time()
                        
                        # --- CONFIDENCE ROUTING ---
                        
                        # 1. Medium Confidence: Confirm with user (Soft check)
                        if confidence < HIGH_CONFIDENCE:
                            print(f"⚠️ Confidence {confidence:.2f} < {HIGH_CONFIDENCE}. Soft confirmation.")
                            speak(f"Okay, {text}.") # Acknowledge but proceed cautiously or confirm
                        
                        # 2. High Confidence (or Medium Proceed): Execute
                        response_json = ask_llm(text)
                        
                        if response_json:
                            try:
                                result = json.loads(response_json)
                                
                                # 1. Speak (if any)
                                if result.get("speech"):
                                    speak(result["speech"])
                                
                                # 2. Execute Plan (if any)
                                plan = result.get("plan")
                                if plan:
                                    execute_plan_with_repair(plan, text)
                                    
                            except json.JSONDecodeError:
                                print(f"❌ Failed to parse JSON: {response_json}")
                                speak("I'm having trouble structuring my thoughts.")
                        
                        last_activity = time.time()

                    except sr.WaitTimeoutError:
                        continue
                    except Exception as e:
                        print(f"❌ Active loop error: {e}")

    except KeyboardInterrupt:
        print("\nStopping Jarvis...")
    finally:
        # ---- ROBUST CLEANUP ----
        print("🛑 Cleaning up resources...")
        if wake_model:
            wake_model.delete()
        
        if whisper_model:
            del whisper_model
        
        # Force garbage collection to free CUDA memory
        gc.collect()
        print("✅ Models unloaded and GPU memory freed")

if __name__ == "__main__":
    main()
