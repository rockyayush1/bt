import os, time, random
from datetime import datetime
from instagrapi import Client

exec(open("config.py").read())
exec(open("commands.py").read())

STATS = {"total": 0}
known_members = {}
client = None
spam_targets = {}

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}")
    with open("bot.log", "a") as f:
        f.write(f"[{ts}] {msg}")

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

def is_admin_user(username):
    """Check if user is admin"""
    return is_admin(username, ADMIN_USERS)

def start():
    log("🚀 NEON BOT v5.0 - ADMIN SYSTEM!")
    log(f"👑 Admins: {ADMIN_USERS}")
    log(f"👥 Groups: {len(GROUP_IDS)}")
    
    if not login(): return False
    
    for gid in GROUP_IDS:
        try:
            t = client.direct_thread(gid)
            known_members[gid] = {u.pk for u in t.users}
            log(f"✅ Group {gid[:8]} OK ({len(t.users)} members)")
        except:
            known_members[gid] = set()
    
    log("🎉 ADMIN BOT LIVE!")
    return True

def handle_admin_commands(gid, t, msg, sender_name):
    """Handle admin only commands"""
    text = msg.text.strip() if msg.text else ""
    
    if text.startswith("/kick "):
        target = text.split(" ")[1].replace("@", "")
        target_user = next((u for u in t.users if u.username.lower() == target.lower()), None)
        if target_user:
            try:
                client.direct_thread_remove_user(gid, target_user.pk)
                client.direct_send(f"👢 @{target} kicked by admin!", [gid])
                log(f"👑 @{sender_name} kicked @{target}")
            except:
                client.direct_send("❌ Cannot kick", [gid])
    
    elif text.startswith("/spam "):
        parts = text.split(" ", 2)
        if len(parts) == 3:
            target = parts[1].replace("@", "")
            spam_targets[gid] = {"target": target, "msg": parts[2]}
            client.direct_send(f"💥 Spam started on @{target}", [gid])
            log(f"👑 @{sender_name} spam @{target}")
    
    elif text.startswith("/ban "):
        target = text.split(" ")[1].replace("@", "")
        client.direct_send(f"🚫 @{target} banned by @{sender_name}!", [gid])
        log(f"👑 @{sender_name} banned @{target}")

def handle_msg(gid, t, msg):
    text = msg.text.lower().strip() if msg.text else ""
    if msg.user_id == client.user_id: return
    
    sender = next((u for u in t.users if u.pk == msg.user_id), None)
    if not sender: return
    
    sender_name = sender.username
    
    # Auto replies
    for k, v in AUTO_REPLIES.items():
        if k in text:
            client.direct_send(v, [gid])
            log(f"🤖 Auto: @{sender_name}")
            return
    
    # ADMIN COMMANDS
    if is_admin_user(sender_name):
        handle_admin_commands(gid, t, msg, sender_name)
        return
    
    # Normal commands
    for cmd in COMMANDS:
        if text.startswith(cmd):
            if cmd == "/stats":
                client.direct_send(f"📊 Total welcomes: {STATS['total']}", [gid])
            elif cmd in ["/kick", "/spam", "/ban"]:
                client.direct_send(f"👑 Admin only: {COMMANDS[cmd]}", [gid])
            else:
                client.direct_send(COMMANDS[cmd], [gid])
            log(f"📱 @{sender_name}: {text}")
            return

if __name__ == "__main__":
    if start():
        last_msgs = {}
        while True:
            for gid in GROUP_IDS:
                try:
                    t = client.direct_thread(gid)
                    
                    # SPAM SYSTEM
                    if gid in spam_targets:
                        target = spam_targets[gid]["target"]
                        msg = spam_targets[gid]["msg"]
                        client.direct_send(f"@{target} {msg}", [gid])
                    
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
