import os
import threading
import discord
from discord.ext import commands
from flask import Flask, request

TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
API_KEY = os.getenv("API_KEY")

MODE = "NORMAL"
STATUS_MESSAGE = None
ALERT_MESSAGES = []

app = Flask(__name__)

@app.route("/mode", methods=["GET"])
def mode():
    if request.headers.get("X-API-KEY") != API_KEY:
        return {"error": "unauthorized"}, 401
    return {"mode": MODE}

@app.route("/event", methods=["POST"])
def event():
    if request.headers.get("X-API-KEY") != API_KEY:
        return {"error": "unauthorized"}, 401

    image = request.files.get("image")

    async def notify():
        user = await bot.fetch_user(OWNER_ID)

        # ❌ NIE im NORMAL alarmieren
        if MODE == "NORMAL":
            return

        content = f"<@{OWNER_ID}> 🚨 **Bewegung erkannt** ({MODE})"

        if image:
            file = discord.File(image, filename="alert.jpg")
            msg = await user.send(content, file=file)
        else:
            msg = await user.send(content + "\n⚠️ (kein Bild)")

        ALERT_MESSAGES.append(msg)

    bot.loop.create_task(notify())
    return {"ok": True}

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run("0.0.0.0", port)

# =====================

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

async def clear_alerts():
    for msg in ALERT_MESSAGES:
        try:
            await msg.delete()
        except:
            pass
    ALERT_MESSAGES.clear()

def status_embed():
    return discord.Embed(
        title="🧠 Überwachung",
        description=f"**Modus:** {MODE}",
        color=0xff0000 if MODE != "NORMAL" else 0x00ff99
    )

class ControlView(discord.ui.View):
    @discord.ui.button(label="🟢 Normal", style=discord.ButtonStyle.success)
    async def normal(self, interaction, button):
        global MODE
        MODE = "NORMAL"
        await clear_alerts()
        await STATUS_MESSAGE.edit(embed=status_embed(), view=self)
        await interaction.response.defer()

    @discord.ui.button(label="🟡 Alarm", style=discord.ButtonStyle.primary)
    async def alarm(self, interaction, button):
        global MODE
        MODE = "ALARM"
        await STATUS_MESSAGE.edit(embed=status_embed(), view=self)
        await interaction.response.defer()

@bot.tree.command(name="status")
async def status(interaction: discord.Interaction):
    global STATUS_MESSAGE
    if interaction.user.id != OWNER_ID:
        return
    STATUS_MESSAGE = await interaction.channel.send(
        embed=status_embed(),
        view=ControlView()
    )
    await interaction.response.send_message("Status aktiv", ephemeral=True)

@bot.event
async def on_ready():
    print("Bot online")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.run(TOKEN)
