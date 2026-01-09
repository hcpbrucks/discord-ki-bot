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
# STATE
# =====================
MODE = "NORMAL"
ALERT_MESSAGES = []

# =====================
# FLASK API
# =====================
app = Flask(__name__)

@app.route("/mode")
def mode():
    if request.headers.get("X-API-KEY") != API_KEY:
        return {"error": "unauthorized"}, 401
    return {"mode": MODE}

@app.route("/event", methods=["POST"])
def event():
    if request.headers.get("X-API-KEY") != API_KEY:
        return {"error": "unauthorized"}, 401

    async def notify():
        if MODE != "ALARM":
            return

        user = await bot.fetch_user(OWNER_ID)

        view = ScreenshotView()
        msg = await user.send(
            f"<@{OWNER_ID}> 🚨 **Bewegung erkannt**",
            view=view
        )
        ALERT_MESSAGES.append(msg)

    bot.loop.create_task(notify())
    return {"ok": True}

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =====================
# DISCORD BOT
# =====================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

async def clear_alerts():
    global ALERT_MESSAGES
    for msg in ALERT_MESSAGES:
        try:
            await msg.delete()
        except:
            pass
    ALERT_MESSAGES = []

# =====================
# UI
# =====================
class ScreenshotView(discord.ui.View):
    @discord.ui.button(label="📸 Screenshot", style=discord.ButtonStyle.primary)
    async def screenshot(self, interaction, button):
        await interaction.response.send_message(
            "📸 Screenshot angefordert",
            ephemeral=True
        )

class ControlView(discord.ui.View):
    async def interaction_check(self, interaction):
        return interaction.user.id == OWNER_ID

    @discord.ui.button(label="🟢 Normal", style=discord.ButtonStyle.success)
    async def normal(self, interaction, button):
        global MODE
        MODE = "NORMAL"
        await clear_alerts()
        await interaction.response.send_message("🟢 NORMAL", ephemeral=True)

    @discord.ui.button(label="🟡 Alarm", style=discord.ButtonStyle.danger)
    async def alarm(self, interaction, button):
        global MODE
        MODE = "ALARM"
        await interaction.response.send_message("🚨 ALARM AKTIV", ephemeral=True)

# =====================
# COMMAND
# =====================
@bot.event
async def on_ready():
    print("✅ Bot online")

@bot.tree.command(name="status")
async def status(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🧠 Überwachung",
        description=f"Modus: **{MODE}**",
        color=0xff5555 if MODE == "ALARM" else 0x55ff55
    )

    await interaction.response.send_message(
        embed=embed,
        view=ControlView(),
        ephemeral=False
    )

# =====================
# START
# =====================
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.run(TOKEN)
