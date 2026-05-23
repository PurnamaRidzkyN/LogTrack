from datetime import datetime
import pytz

def now_wib():
    wib = pytz.timezone("Asia/Jakarta")
    return datetime.now(wib).strftime("%Y-%m-%d %H:%M:%S")