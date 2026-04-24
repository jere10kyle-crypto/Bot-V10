from flask import Flask
import threading
import discord
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

intents = discord.Intents.default()
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

def run_bot():
    bot.run(os.environ.get("DISCORD_TOKEN"))

threading.Thread(target=run_bot).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
