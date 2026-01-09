import os
import threading
import discord
from discord.ext import commands
from flask import Flask, request, jsonify

# =====================
# ENV
# =====================
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
API_KEY = os.getenv("API_KEY")

# =====================
# GLOBAL STATE
# =====================
MODE = "NORMAL"
LAST_EVENT = "—"

STATUS_MESSAGE_ID = None
STATUS_CHANNEL_ID = None
ALARM_MESSAGES = []

# =====================
# Flask Web Server (Render + API)
# =====================
app = Flask(__name__)

@app.route("/")
def home():
    return "Discord Bot is running!"

@app.route("/mode", methods=["GET"])
def get_mode():
    if request.headers.get("X-API-KEY") != API_KEY:
        return jsonify({"error": "unauthorized"}), 401

    return jsonify({
        "mode": MODE,
        "last_event": LAST_EVENT
    })

@app.route("/event", methods=["POST"])
def event():
    global LAST_EVENT

    if request.headers.get("X-API-KEY") != API_KEY:
        return jsonify({"error": "unauthorized"}), 401

    data = request.json or {}
    event_type = data.get("type", "UNKNOWN")

    LAST_EVENT = event_type

    async def notify():
        if event_type == "PERSON_DETECTED":
            await notify_owner("👤 Person erkannt")
        elif event_type == "FACE_UNKNOWN":
            await notify_owner("🚨 UNBEKANNTES GESICHT")
        else:
            await notify_owner(f"ℹ️ Event: {event_type}")

    bot.loop.create_task(notify())
    return jsonify({"ok": True})

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =====================
# Discord Bot
# =====================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# =====================
# HELPERS
# =====================
async def update_status_dm():
    global STATUS_MESSAGE_ID, STATUS_CHANNEL_ID

    user = await bot.fetch_user(OWNER_ID)

    embed = discord.Embed(
        title="🛡️ Live-Überwachung",
        color=0x00ff99
    )
    embed.add_field(name="🧠 Modus", value=MODE, inline=False)
    embed.add_field(name="📡 Letztes Event", value=LAST_EVENT, inline=False)

    if STATUS_MESSAGE_ID is None:
        msg = await user.send(embed=embed, view=ControlView())
        STATUS_MESSAGE_ID = msg.id
        STATUS_CHANNEL_ID = msg.channel.id
    else:
        channel = await bot.fetch_channel(STATUS_CHANNEL_ID)
        msg = await channel.fetch_message(STATUS_MESSAGE_ID)
        await msg.edit(embed=embed, view=ControlView())

async def send_alarm_ping(text: str):
    user = await bot.fetch_user(OWNER_ID)
    msg = await user.send(f"🚨 <@{OWNER_ID}> {text}")
    ALARM_MESSAGES.append(msg)

async def clear_alarms():
    global ALARM_MESSAGES
    for msg in ALARM_MESSAGES:
        try:
            await msg.delete()
        except:
            pass
    ALARM_MESSAGES = []

async def notify_owner(message: str):
    global LAST_EVENT
    LAST_EVENT = message

    if MODE in ["ALARM", "ALARM_NOW"]:
        await send_alarm_ping(message)

    await update_status_dm()

# =====================
# UI VIEW
# =====================
class ControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == OWNER_ID

    @discord.ui.button(label="🟢 Normal", style=discord.ButtonStyle.success)
    async def normal(self, interaction: discord.Interaction, button: discord.ui.Button):
        global MODE
        MODE = "NORMAL"
        await clear_alarms()
        await notify_owner("🟢 Modus: NORMAL")
        await interaction.response.send_message("Normalmodus aktiv", ephemeral=True)

    @discord.ui.button(label="🟡 Alarm", style=discord.ButtonStyle.primary)
    async def alarm(self, interaction: discord.Interaction, button: discord.ui.Button):
        global MODE
        MODE = "ALARM"
        await notify_owner("⚠️ Alarmmodus AKTIV")
        await interaction.response.send_message("Alarmmodus aktiv", ephemeral=True)

    @discord.ui.button(label="🔴 Alarm sofort", style=discord.ButtonStyle.danger)
    async def alarm_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        global MODE
        MODE = "ALARM_NOW"
        await notify_owner("🚨 SOFORT-ALARM")
        await interaction.response.send_message("Sofort-Alarm aktiv", ephemeral=True)

    @discord.ui.button(label="👁️ Gesicht prüfen", style=discord.ButtonStyle.secondary)
    async def face(self, interaction: discord.Interaction, button: discord.ui.Button):
        await notify_owner("👁️ Manuelle Gesichtserkennung")
        await interaction.response.send_message("Gesichtserkennung angefordert", ephemeral=True)

    @discord.ui.button(label="⛔ Stop", style=discord.ButtonStyle.secondary)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        global MODE
        MODE = "NORMAL"
        await clear_alarms()
        await notify_owner("⛔ Alarm gestoppt")
        await interaction.response.send_message("Alarm gestoppt", ephemeral=True)

# =====================
# EVENTS & COMMANDS
# =====================
@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")
    await bot.tree.sync()
    await update_status_dm()

@bot.tree.command(name="status", description="Zeigt Status & Steuerung")
async def status(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Kein Zugriff", ephemeral=True)
        return

    await interaction.response.send_message(
        "📊 Live-Status geöffnet",
        view=ControlView(),
        ephemeral=True
    )

# =====================
# START
# =====================
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.run(TOKEN)
