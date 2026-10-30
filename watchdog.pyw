# 分流管家守护：由计划任务定时运行，9123 端口不通就在后台重新拉起 app.py（不弹窗）
import os
import socket
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "watchdog.log")
PORT = 9123


def alive():
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=3):
            return True
    except OSError:
        return False


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")


if not alive():
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    subprocess.Popen(
        [pythonw, os.path.join(HERE, "app.py")],
        cwd=HERE,
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
        close_fds=True,
    )
    time.sleep(5)
    log("9123 不通，已重新启动 app.py" + ("，启动成功" if alive() else "，启动后仍不通"))
