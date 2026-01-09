import os
import threading
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask

# =====================
# Flask Web Server (für Render)
# =====================
app = Flask(__name__)

@app.route("/")
def home():
    return "Discord Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

from flask import request, jsonify

API_KEY = os.getenv("API_KEY")

@app.route("/mode", methods=["GET"])
def get_mode():
    if request.headers.get("X-API-KEY") != API_KEY:
        return jsonify({"error": "unauthorized"}), 401

    return jsonify({"mode": MODE})

# =====================
# Discord Bot
# =====================
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

MODE = "NORMAL"
LAST_EVENT = "—"

class ControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == OWNER_ID

    @discord.ui.button(label="🟢 Normal", style=discord.ButtonStyle.success)
async def normal(self, interaction: discord.Interaction, button: discord.ui.Button):
    global MODE
    MODE = "NORMAL"
    await notify_owner("🟢 Modus gewechselt: NORMAL")
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
    await notify_owner("🚨 SOFORT-ALARM AKTIVIERT")
    await interaction.response.send_message("Sofort-Alarm aktiv", ephemeral=True)


   @discord.ui.button(label="👁️ Gesicht prüfen", style=discord.ButtonStyle.secondary)
async def face(self, interaction: discord.Interaction, button: discord.ui.Button):
    await notify_owner("👁️ Manuelle Gesichtserkennung angefordert")
    await interaction.response.send_message("Gesichtserkennung angefordert", ephemeral=True)


 @discord.ui.button(label="⛔ Stop", style=discord.ButtonStyle.secondary)
async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
    global MODE
    MODE = "NORMAL"
    await notify_owner("⛔ Alarm gestoppt")
    await interaction.response.send_message("Alarm gestoppt", ephemeral=True)


    
    async def notify_owner(message: str):
    user = await bot.fetch_user(OWNER_ID)
    await user.send(message)


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
        description=f"Aktueller Modus: **{MODE}**",
        color=0x00ff99
    )

    await interaction.response.send_message(
        embed=embed,
        view=ControlView(),
        ephemeral=True
    )

# =====================
# Start EVERYTHING
# =====================
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.run(TOKEN)
