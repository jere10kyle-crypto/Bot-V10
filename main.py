from flask import Flask, render_template, jsonify
import threading
import discord
from discord.ext import commands
import os
import json

app = Flask(__name__)

# ---------------- DASHBOARD STATS ----------------
stats = {
    "messages": 0,
    "joins": 0,
    "leaves": 0
}

# ---------------- BANNED WORDS ----------------
def load_words():
    try:
        with open("banned_words.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_words(words):
    with open("banned_words.json", "w") as f:
        json.dump(words, f)

banned_words = load_words()

# ---------------- FLASK ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html", stats=stats)

@app.route("/stats")
def api_stats():
    return jsonify(stats)

@app.route("/banned")
def get_banned():
    return jsonify({"banned_words": banned_words})

@app.route("/add/<word>")
def add_word(word):
    word = word.lower()
    if word not in banned_words:
        banned_words.append(word)
        save_words(banned_words)
    return jsonify({"added": word})

@app.route("/remove/<word>")
def remove_word(word):
    word = word.lower()
    if word in banned_words:
        banned_words.remove(word)
        save_words(banned_words)
    return jsonify({"removed": word})

# ---------------- DISCORD BOT ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", 0))

# ---------------- LOGGING (EMBEDS) ----------------
async def log_event(guild, title, description, color=0x00ffcc):
    if not LOG_CHANNEL_ID:
        return

    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title=title, description=description, color=color)
        await channel.send(embed=embed)

# ---------------- EVENTS ----------------
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}")

@bot.event
async def on_member_join(member):
    stats["joins"] += 1
    await log_event(member.guild, "👋 Member Joined", str(member))

@bot.event
async def on_member_remove(member):
    stats["leaves"] += 1
    await log_event(member.guild, "👋 Member Left", str(member))

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    stats["messages"] += 1
    content = message.content.lower()

    # ---------------- BAN FILTER ----------------
    for word in banned_words:
        if word in content:
            await message.delete()
            await message.channel.send("🚫 Message blocked (banned word)")
            return

    await bot.process_commands(message)

# ---------------- SLASH COMMANDS ----------------
@tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 Pong! {round(bot.latency * 1000)}ms"
    )

@tree.command(name="stats", description="Server stats")
async def stats_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="📊 Stats", color=0x00ffcc)
    embed.add_field(name="Messages", value=stats["messages"], inline=False)
    embed.add_field(name="Joins", value=stats["joins"], inline=False)
    embed.add_field(name="Leaves", value=stats["leaves"], inline=False)

    await interaction.response.send_message(embed=embed)

# ---------------- RUN BOT ----------------
def run_bot():
    bot.run(os.environ["DISCORD_TOKEN"])

threading.Thread(target=run_bot).start()

# ---------------- RUN FLASK ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
