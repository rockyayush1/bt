import os
import time
import threading
from datetime import datetime
from instagrapi import Client
from flask import Flask

exec(open("config.py").read())
exec(open("commands.py").read())

app = Flask(__name__)
STATS = {"total": 0}
known_members = {}
client = None
bot_thread = None

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}")

def token_login():
    global client
    client = Client()
    try:
        client.login_by_sessionid(SESSION_TOKEN)
        client.dump_settings("session.json")
        log("✅ TOKEN LOGIN SUCCESS!")
        return True
    except Exception as e:
        log(f"💥 LOGIN ERROR: {str(e)[:50]}")
        return False

def bot_loop():
    """Main bot loop - runs in background"""
    global known_members
    last_msgs = {}
    
    while True:
        try:
            for gid in GROUP_IDS:
                t = client.direct_thread(gid)
                
                # New members check
                current_members = {u.pk for u in t.users}
                new_members = current_members - known_members.get(gid, set())
                
                for user in t.users:
                    if (user.pk in new_members and user.username):
                        log(f"👋 NEW: @{user.username}")
                        STATS["total"] += 1
                        
                        for msgt in WELCOME_MSGS:
                            welcome = msgt.replace("@user", f"@{user.username}")
                            client.direct_send(welcome, [gid])
                            time.sleep(DELAY)
                        
                        known_members[gid] = current_members
                        break
                
                known_members[gid] = current_members
                last_msgs[gid] = t.messages[0].id if t.messages else None
                
        except Exception as e:
            log(f"⚠️ Bot loop: {str(e)[:40]}")
        
        time.sleep(POLL)

def start_bot():
    """Start bot in background thread"""
    global bot_thread
    if token_login():
        bot_thread = threading.Thread(target=bot_loop, daemon=True)
        bot_thread.start()
        log("🎉 BOT FULLY LIVE!")
        return True
    return False

@app.route('/')
def health():
    return f"🤖 NEON BOT LIVE! Welcomes: {STATS['total']}"

@app.route('/ping')
def ping():
    return "✅ Bot Active!"

@app.route('/stats')
def stats():
    return f"📊 Total: {STATS['total']}"

if __name__ == "__main__":
    start_bot()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
