import os, time, random
from datetime import datetime
from instagrapi import Client

exec(open("config.py").read())
exec(open("commands.py").read())

STATS = {"total": 0}
known_members = {}
client = None

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}")
    with open("bot.log", "a") as f:
        f.write(f"[{ts}] {msg}
")

def login():
    global client
    client = Client()
    try:
        if os.path.exists("session.json"):
            client.load_settings("session.json")
            client.login(USERNAME, PASSWORD)
            log("✅ SESSION LOADED")
        else:
            client.login(USERNAME, PASSWORD)
            client.dump_settings("session.json")
            log("✅ LOGIN SUCCESS")
        return True
    except:
        log("💥 LOGIN FAILED")
        return False

def start():
    log("🚀 NEON BOT STARTING...")
    if not login(): return False
    
    for gid in GROUP_IDS:
        try:
            t = client.direct_thread(gid)
            known_members[gid] = {u.pk for u in t.users}
            log(f"✅ Group {gid[:8]} OK")
        except:
            known_members[gid] = set()
    
    log("🎉 BOT LIVE!")
    return True

def handle_msg(gid, t, msg):
    text = msg.text.lower().strip() if msg.text else ""
    if msg.user_id == client.user_id: return
    
    sender = next((u for u in t.users if u.pk == msg.user_id), None)
    if not sender: return
    
    # Auto reply
    for k, v in AUTO_REPLIES.items():
        if k in text:
            client.direct_send(v, [gid])
            return
    
    # Commands
    for cmd in COMMANDS:
        if text.startswith(cmd):
            if cmd == "/stats":
                client.direct_send(f"📊 Total: {STATS['total']}", [gid])
            else:
                client.direct_send(COMMANDS[cmd], [gid])
            return

if __name__ == "__main__":
    if start():
        last_msgs = {}
        while True:
            for gid in GROUP_IDS:
                try:
                    t = client.direct_thread(gid)
                    
                    # New messages
                    if last_msgs.get(gid):
                        new_msgs = [m for m in t.messages if m.id != last_msgs[gid]]
                        for msg in reversed(new_msgs):
                            handle_msg(gid, t, msg)
                    
                    last_msgs[gid] = t.messages[0].id if t.messages else None
                    
                    # New members
                    cur = {u.pk for u in t.users}
                    newm = cur - known_members.get(gid, set())
                    
                    for u in t.users:
                        if u.pk in newm and u.username != USERNAME:
                            log(f"👋 NEW: @{u.username}")
                            for msgt in WELCOME_MSGS:
                                msg = msgt.replace("@user", f"@{u.username}")
                                client.direct_send(msg, [gid])
                                STATS["total"] += 1
                                time.sleep(DELAY)
                            known_members[gid] = cur
                            break
                    
                    known_members[gid] = cur
                except:
                    pass
            time.sleep(POLL)
