import os
import threading
import discord
from discord.ext import commands
from flask import Flask, request

TOKEN = os.getenv("DISCORD_TOKEN")
API_KEY = os.getenv("API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

MODE = "NORMAL"
status_message = None

# ---------------- FLASK ----------------
app = Flask(__name__)

@app.route("/event", methods=["POST"])
def event():
    global status_message

    if request.headers.get("X-API-KEY") != API_KEY:
        return "unauthorized", 401

    event_type = request.form.get("type")
    image = request.files.get("image")

    async def handle():
        global status_message

        channel = bot.get_channel(CHANNEL_ID)

        if MODE != "ALARM":
            return

        embed = discord.Embed(
            title="🚨 Bewegung erkannt",
            description="Eine Person wurde erkannt",
            color=0xff0000
        )

        if status_message:
            await status_message.edit(embed=embed)
        else:
            status_message = await channel.send(
                content="<@Paul>",
                embed=embed
            )

        if image:
            await channel.send(file=discord.File(image.stream, "screenshot.jpg"))

    bot.loop.create_task(handle())
    return "ok"

def run_web():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

# ---------------- DISCORD ----------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("Bot online")

@bot.command()
async def alarm(ctx):
    global MODE
    MODE = "ALARM"
    await ctx.send("🚨 Alarm aktiviert")

@bot.command()
async def normal(ctx):
    global MODE, status_message
    MODE = "NORMAL"
    if status_message:
        await status_message.delete()
        status_message = None
    await ctx.send("🟢 Normalmodus")

# ---------------- START ----------------
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.run(TOKEN)
