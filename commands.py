COMMANDS = {
    "/help": "🔥 /ping /stats /music /funny /masti /welcome /token",
    "/ping": "✅ Bot 100% LIVE! 🔥",
    "/stats": "📊 Stats loading...", 
    "/music": "🎵🎶🎤 Music mode ON! 🎧",
    "/funny": "😂😂😂 Hahaha mast bhai!",
    "/masti": "🎉🥳 Full party time!",
    "/welcome": "Test welcome msg 👋",
    "/token": "🔑 Token login active!"
}

AUTO_REPLIES = {
    "hi": "Hey bro! Kya haal? 😎",
    "hello": "Namaste bhai! 🔥",
    "kya": "Sab theek bhai! Bol na! 😄",
    "good": "Good ji! Mast! 👍"
}

def is_admin(username, admin_list):
    return username.lower() in [a.lower() for a in admin_list]
