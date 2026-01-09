import os
import threading
import discord
from discord.ext import commands
from flask import Flask, request, jsonify

TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
API_KEY = os.getenv("API_KEY")

MODE = "NORMAL"
LAST_EVENT = "—"
ALERT_MESSAGES = []

# =====================
# Flask API
# =====================
app = Flask(__name__)

@app.route("/mode", methods=["GET"])
def get_mode():
    if request.headers.get("X-API-KEY") != API_KEY:
        return jsonify({"error": "unauthorized"}), 401
    return jsonify({"mode": MODE})

@app.route("/event", methods=["POST"])
def event():
    global LAST_EVENT
    if request.headers.get("X-API-KEY") != API_KEY:
        return jsonify({"error": "unauthorized"}), 401

    LAST_EVENT = "PERSON_DETECTED"
    image = request.files.get("image")

    async def notify():
        if MODE != "ALARM":
            return

        channel = await bot.fetch_user(OWNER_ID)

        content = f"🚨 <@{OWNER_ID}> **Bewegung erkannt!**"
        if image:
            file = discord.File(image.stream, filename="alarm.jpg")
            msg = await channel.send(content, file=file)
        else:
            msg = await channel.send(content)

        ALERT_MESSAGES.append(msg)

    bot.loop.create_task(notify())
    return {"ok": True}

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =====================
# Discord Bot
# =====================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

async def clear_alerts():
    for m in ALERT_MESSAGES:
        try:
            await m.delete()
        except:
            pass
    ALERT_MESSAGES.clear()

class ControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🟢 Normal", style=discord.ButtonStyle.success)
    async def normal(self, interaction, button):
        global MODE
        MODE = "NORMAL"
        await clear_alerts()
        await interaction.response.send_message("🟢 NORMAL", ephemeral=True)

    @discord.ui.button(label="🚨 Alarm", style=discord.ButtonStyle.danger)
    async def alarm(self, interaction, button):
        global MODE
        MODE = "ALARM"
        await interaction.response.send_message("🚨 ALARM AKTIV", ephemeral=True)

@bot.tree.command(name="status")
async def status(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🧠 Überwachung",
        description=f"Modus: **{MODE}**\nLetztes Event: **{LAST_EVENT}**",
        color=0xff0000 if MODE == "ALARM" else 0x00ff99
    )
    await interaction.response.send_message(embed=embed, view=ControlView())

@bot.event
async def on_ready():
    print("✅ Bot online")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.run(TOKEN)
