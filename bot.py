import os
import threading
import discord
from discord.ext import commands
from flask import Flask, request

# =====================
# ENV
# =====================
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
API_KEY = os.getenv("API_KEY")

# =====================
# STATE
# =====================
MODE = "ALARM"   # 🔴 STARTET DIREKT IM ALARM
LAST_EVENT = "—"
ALERT_MESSAGES = []

# =====================
# FLASK API
# =====================
app = Flask(__name__)

@app.route("/event", methods=["POST"])
def event():
    global LAST_EVENT

    if request.headers.get("X-API-KEY") != API_KEY:
        return {"error": "unauthorized"}, 401

    event_type = request.form.get("type", "UNKNOWN")
    LAST_EVENT = event_type
    image = request.files.get("image")

    async def notify():
        user = await bot.fetch_user(OWNER_ID)

        if MODE == "NORMAL":
            return

        content = f"<@{OWNER_ID}> 🚨 **PERSON ERKANNT** ({MODE})"

        if image:
            file = discord.File(image.stream, filename="alert.jpg")
            msg = await user.send(content, file=file)
        else:
            msg = await user.send(content)

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
class ControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction):
        return interaction.user.id == OWNER_ID

    @discord.ui.button(label="🟢 Normal", style=discord.ButtonStyle.success)
    async def normal(self, interaction, button):
        global MODE
        MODE = "NORMAL"
        await clear_alerts()
        await interaction.response.send_message("🟢 NORMAL", ephemeral=True)

    @discord.ui.button(label="🟡 Alarm", style=discord.ButtonStyle.primary)
    async def alarm(self, interaction, button):
        global MODE
        MODE = "ALARM"
        await interaction.response.send_message("🟡 ALARM", ephemeral=True)

    @discord.ui.button(label="🔴 Alarm sofort", style=discord.ButtonStyle.danger)
    async def alarm_now(self, interaction, button):
        global MODE
        MODE = "ALARM_NOW"
        await interaction.response.send_message("🔴 SOFORT-ALARM", ephemeral=True)

# =====================
# STATUS COMMAND
# =====================
@bot.tree.command(name="status", description="Live Status")
async def status(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🧠 Live-Überwachung",
        description=f"**Modus:** {MODE}\n**Letztes Event:** {LAST_EVENT}",
        color=0xff0000 if MODE != "NORMAL" else 0x00ff99
    )

    await interaction.response.send_message(
        embed=embed,
        view=ControlView(),
        ephemeral=False,
        delete_after=300  # ⏱️ 5 Minuten
    )

# =====================
# START
# =====================
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.run(TOKEN)
