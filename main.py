import json
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
from flask import Flask, render_template
import threading
import discord
from discord.ext import commands
import os

app = Flask(__name__)

# ---------------- DASHBOARD STATS ----------------
stats = {
    "messages": 0,
    "joins": 0,
    "leaves": 0
}

@app.route("/")
def home():
    return render_template("index.html", stats=stats)

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
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
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
    await bot.process_commands(message)

# ---------------- SLASH COMMANDS ----------------

@tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 Pong! {round(bot.latency * 1000)}ms"
    )

@tree.command(name="stats", description="Server stats")
async def stats_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="📊 Server Stats", color=0x00ffcc)
    embed.add_field(name="Messages", value=stats["messages"], inline=False)
    embed.add_field(name="Joins", value=stats["joins"], inline=False)
    embed.add_field(name="Leaves", value=stats["leaves"], inline=False)

    await interaction.response.send_message(embed=embed)

# ---------------- RUN BOT ----------------
def run_bot():
    bot.run(os.environ["DISCORD_TOKEN"])

threading.Thread(target=run_bot).start()

# ---------------- FLASK ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
