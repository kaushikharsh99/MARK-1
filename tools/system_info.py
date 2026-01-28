import datetime
import psutil

def get_time():
    """Returns the current date and time."""
    now = datetime.datetime.now()
    return now.strftime("%A, %B %d, %Y at %I:%M %p")

def get_system_status():
    """Returns CPU and Memory usage."""
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        
        status = (
            f"CPU Usage: {cpu}%\n"
            f"Memory Usage: {mem.percent}% ({mem.used // (1024**2)}MB / {mem.total // (1024**2)}MB)\"n"
            f"Battery: {psutil.sensors_battery().percent if psutil.sensors_battery() else 'N/A'}%"
        )
        return status
    except Exception as e:
        return f"❌ Error getting status: {str(e)}"
