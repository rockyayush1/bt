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
message_queue = []
last_processed_msg = {}

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

def handle_command(gid, sender_name, text):
    """Handle all commands including /help"""
    text_lower = text.strip().lower()
    
    # Auto replies first
    for keyword, reply in AUTO_REPLIES.items():
        if keyword in text_lower:
            try:
                client.direct_send(reply, [gid])
                log(f"🤖 Auto-reply to @{sender_name}: {keyword}")
                return True
            except:
                pass
    
    # Commands
    for cmd, response in COMMANDS.items():
        if text_lower.startswith(cmd):
            try:
                if cmd == "/stats":
                    client.direct_send(f"📊 Total welcomes: {STATS['total']}", [gid])
                else:
                    client.direct_send(response, [gid])
                log(f"📱 @{sender_name} used {cmd}")
                return True
            except Exception as e:
                log(f"⚠️ Command error: {str(e)[:30]}")
    
    return False

def message_checker():
    """Background thread - checks messages every 3 seconds"""
    global message_queue, last_processed_msg
    
    while client:
        try:
            for gid in GROUP_IDS:
                if gid not in last_processed_msg:
                    last_processed_msg[gid] = 0
                
                thread = client.direct_thread(gid)
                messages = thread.messages
                
                if messages:
                    latest_msg_id = messages[0].id
                    
                    # Process new messages
                    if latest_msg_id != last_processed_msg[gid]:
                        new_msg = messages[0]
                        
                        sender = next((u for u in thread.users if u.pk == new_msg.user_id), None)
                        if sender and sender.username != client.user_id:
                            handled = handle_command(gid, sender.username, new_msg.text or "")
                            if handled:
                                log(f"✅ Command processed in {gid[:8]}")
                        
                        last_processed_msg[gid] = latest_msg_id
            
            time.sleep(3)  # Check every 3 seconds
            
        except Exception as e:
            log(f"⚠️ Message check error: {str(e)[:40]}")
            time.sleep(5)

def member_checker():
    """Background thread - checks new members"""
    global known_members
    
    while client:
        try:
            for gid in GROUP_IDS:
                if gid not in known_members:
                    known_members[gid] = set()
                
                thread = client.direct_thread(gid)
                current_members = {u.pk for u in thread.users}
                new_members = current_members - known_members[gid]
                
                for user in thread.users:
                    if (user.pk in new_members and 
                        user.username and 
                        user.username != SESSION_TOKEN.split(':')[0]):
                        
                        log(f"👋 NEW MEMBER: @{user.username}")
                        STATS["total"] += 1
                        
                        for msg_template in WELCOME_MSGS:
                            welcome_msg = msg_template.replace("@user", f"@{user.username}")
                            try:
                                client.direct_send(welcome_msg, [gid])
                                time.sleep(DELAY)
                            except:
                                break
                        
                        known_members[gid] = current_members
                        break
                
                known_members[gid] = current_members
            
            time.sleep(POLL)
            
        except Exception as e:
            log(f"⚠️ Member check error: {str(e)[:40]}")
            time.sleep(10)

def start_bot():
    """Start both background threads"""
    global client
    
    if token_login():
        # Start message checker thread
        threading.Thread(target=message_checker, daemon=True).start()
        log("✅ Message checker started")
        
        # Start member checker thread  
        threading.Thread(target=member_checker, daemon=True).start()
        log("✅ Member checker started")
        
        log("🎉 ALL SYSTEMS LIVE!")
        return True
    return False

@app.route('/')
def health():
    return f"🤖 NEON BOT LIVE! Total: {STATS['total']} | Groups: {len(GROUP_IDS)}"

@app.route('/ping')
def ping():
    return "✅ Bot Active! Commands working!"

@app.route('/stats')
def stats():
    return f"📊 Welcomes: {STATS['total']} | Groups monitored: {len(GROUP_IDS)}"

if __name__ == "__main__":
    start_bot()
    port = int(os.environ.get('PORT', 10000))
    log(f"🌐 Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
