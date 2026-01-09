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

# =====================
# Flask Web Server (für Render + API)
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

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =====================
# Discord Bot
# =====================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

async def notify_owner(message: str):
    user = await bot.fetch_user(OWNER_ID)
    await user.send(message)

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
        await notify_owner("👁️ Gesichtserkennung MANUELL angefordert")
        await interaction.response.send_message("Gesichtserkennung gestartet", ephemeral=True)

    @discord.ui.button(label="⛔ Stop", style=discord.ButtonStyle.secondary)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        global MODE
        MODE = "NORMAL"
        await notify_owner("⛔ Alarm gestoppt")
        await interaction.response.send_message("Alarm gestoppt", ephemeral=True)

# =====================
# EVENTS & COMMANDS
# =====================
@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")
    await bot.tree.sync()

@bot.tree.command(name="status", description="Zeigt Status & Steuerung")
async def status(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Kein Zugriff", ephemeral=True)
        return

    embed = discord.Embed(
        title="🧠 KI-Überwachung",
        description=f"**Modus:** {MODE}\n**Letztes Event:** {LAST_EVENT}",
        color=0x00ff99
    )

    await interaction.response.send_message(
        embed=embed,
        view=ControlView(),
        ephemeral=True
    )

# =====================
# START
# =====================
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.run(TOKEN)
