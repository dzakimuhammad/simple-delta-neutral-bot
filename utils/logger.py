from datetime import datetime

def log(msg: str):
    ts = datetime.now().strftime("[%H:%M:%S]")
    print(ts, msg)
