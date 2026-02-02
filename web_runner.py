import os
import threading
from flask import Flask

def start_bot():
    import bot

t = threading.Thread(target=start_bot, daemon=True)
t.start()

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)