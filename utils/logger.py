import sys
import time
from datetime import datetime
from .spinner import Spinner

SHOW_TIME = True  # Enable timestamps for better debugging

def _format_msg(level, message, tag):
    if SHOW_TIME:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"[{ts}] [{level}] {message} {tag}"
    else:
        return f"[{level}] {message} {tag}"

def log_info(message, tag="[INFO]"):
    print(_format_msg("INFO", message, tag))

def log_success(message, tag="[OK]"):
    print(_format_msg("SUCCESS", message, tag))

def log_warn(message, tag="[WARN]"):
    print(_format_msg("WARN", message, tag))

def log_error(message, tag="[ERR]"):
    print(_format_msg("ERROR", message, tag))

def spinner_task(task_message, duration=5):
    """
    Shows a spinner animation while performing a task.
    duration = estimated seconds for spinner loop.
    """
    spinner = Spinner(message=task_message + "...")
    spinner.start()
    time.sleep(duration)  # Simulate task duration
    spinner.stop(end_message=f"✔ {task_message} done!")