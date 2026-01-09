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

# =====================
# FLASK API
# =====================
app = Flask(__name__)

@app.route("/mode")
def get_mode():
    if request.headers.get("X-API-KEY") != API_KEY:
        return {"error": "unauthorized"}, 401
    return {"mode": MODE}

@app.route("/motion", methods=["POST"])
def motion():
    if request.headers.get("X-API-KEY") != API_KEY:
        return {"error": "unauthorized"}, 401

    async def notify():
        global STATUS_MESSAGE
        if MODE != "ALARM":
            return

        channel = bot.get_channel(int(os.getenv("CHANNEL_ID")))
        if not channel:
            return

        view = ScreenshotView()

        if STATUS_MESSAGE:
            await STATUS_MESSAGE.edit(
                content=f"<@{OWNER_ID}> 🚨 **Bewegung erkannt**",
                view=view
            )
        else:
            STATUS_MESSAGE = await channel.send(
                f"<@{OWNER_ID}> 🚨 **Bewegung erkannt**",
                view=view
            )

    bot.loop.create_task(notify())
    return {"ok": True}

def run_api():
    port = int(os.environ.get("PORT", 10000))
    app.run("0.0.0.0", port)

# =====================
# DISCORD BOT
# =====================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

class ScreenshotView(discord.ui.View):
    @discord.ui.button(label="📸 Screenshot", style=discord.ButtonStyle.primary)
    async def screenshot(self, interaction, button):
        await interaction.response.send_message(
            "📸 Screenshot wird erstellt…",
            ephemeral=True
        )

@bot.tree.command(name="status")
async def status(interaction: discord.Interaction):
    global MODE, STATUS_MESSAGE

    embed = discord.Embed(
        title="🧠 Überwachung",
        description=f"Modus: **{MODE}**",
        color=0xff5555 if MODE == "ALARM" else 0x55ff55
    )

    view = ControlView()

    if STATUS_MESSAGE:
        await STATUS_MESSAGE.edit(embed=embed, view=view)
    else:
        STATUS_MESSAGE = await interaction.channel.send(embed=embed, view=view)

    await interaction.response.send_message("Status aktualisiert", ephemeral=True)

class ControlView(discord.ui.View):
    async def interaction_check(self, interaction):
        return interaction.user.id == OWNER_ID

    @discord.ui.button(label="🟢 Normal", style=discord.ButtonStyle.success)
    async def normal(self, interaction, button):
        global MODE, STATUS_MESSAGE
        MODE = "NORMAL"
        if STATUS_MESSAGE:
            await STATUS_MESSAGE.delete()
            STATUS_MESSAGE = None
        await interaction.response.send_message("🟢 NORMAL", ephemeral=True)

    @discord.ui.button(label="🚨 Alarm", style=discord.ButtonStyle.danger)
    async def alarm(self, interaction, button):
        global MODE
        MODE = "ALARM"
        await interaction.response.send_message("🚨 ALARM AKTIV", ephemeral=True)

@bot.event
async def on_ready():
    print("✅ Bot online")

# =====================
# START
# =====================
if __name__ == "__main__":
    threading.Thread(target=run_api, daemon=True).start()
    bot.run(TOKEN)
