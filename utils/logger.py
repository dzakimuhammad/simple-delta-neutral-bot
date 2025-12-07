from datetime import datetime

LOG_FILE = "bot.log"

def log(msg: str):
    ts = datetime.now().strftime("[%H:%M:%S]")
    log_msg = f"{ts} {msg}"
    print(log_msg)
    
    # Append to log file
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")
