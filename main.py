from flask import Flask
import threading
import discord
from discord.ext import commands
import os
import time
import json

app = Flask(__name__)

# ---------------- DASHBOARD ----------------
stats = {
    "messages": 0,
    "joins": 0,
    "leaves": 0
}

@app.route("/")
def home():
    return "Bot is running!"

@app.route("/stats")
def dashboard():
    return stats

# ---------------- DISCORD BOT ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- DATA ----------------
banned_words = ["badword1", "badword2"]

user_messages = {}
user_strikes = {}

def save_strikes():
    with open("strikes.json", "w") as f:
        json.dump(user_strikes, f)

def load_strikes():
    global user_strikes
    try:
        with open("strikes.json", "r") as f:
            user_strikes = json.load(f)
    except:
        user_strikes = {}

load_strikes()

# ---------------- ANTI SPAM ----------------
def is_spamming(user_id):
    now = time.time()
    if user_id not in user_messages:
        user_messages[user_id] = []

    user_messages[user_id].append(now)

    # keep last 5 seconds
    user_messages[user_id] = [t for t in user_messages[user_id] if now - t < 5]

    return len(user_messages[user_id]) > 5

# ---------------- EVENTS ----------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_member_join(member):
    stats["joins"] += 1

@bot.event
async def on_member_remove(member):
    stats["leaves"] += 1

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    stats["messages"] += 1

    content = message.content.lower()

    # WORD FILTER
    for word in banned_words:
        if word in content:
            await message.delete()
            await warn_user(message.author, message.guild, "Used banned word")
            return

    # ANTI SPAM
    if is_spamming(message.author.id):
        await warn_user(message.author, message.guild, "Spamming detected")
        return

    await bot.process_commands(message)

# ---------------- STRIKE SYSTEM ----------------
async def warn_user(user, guild, reason):
    uid = str(user.id)

    user_strikes[uid] = user_strikes.get(uid, 0) + 1
    save_strikes()

    if user_strikes[uid] >= 3:
        member = guild.get_member(user.id)
        if member:
            await member.ban(reason="3 strikes")
    else:
        print(f"Warned {user} - {reason}")

# ---------------- COMMANDS ----------------
@bot.command()
async def strikes(ctx, member: discord.Member):
    uid = str(member.id)
    await ctx.send(f"{member} has {user_strikes.get(uid, 0)} strikes")

# ---------------- RUN ----------------
def run_bot():
    bot.run(os.environ.get("DISCORD_TOKEN"))

threading.Thread(target=run_bot).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
