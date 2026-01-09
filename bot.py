import os
import threading
import discord
from discord.ext import commands
from flask import Flask, request

TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
API_KEY = os.getenv("API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

MODE = "NORMAL"
STATUS_MSG = None

app = Flask(__name__)

@app.route("/mode")
def mode():
    if request.headers.get("X-API-KEY") != API_KEY:
        return {"error": "unauthorized"}, 401
    return {"mode": MODE}

@app.route("/motion", methods=["POST"])
def motion():
    if request.headers.get("X-API-KEY") != API_KEY:
        return {"error": "unauthorized"}, 401

    async def notify():
        global STATUS_MSG
        if MODE != "ALARM":
            return

        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            return

        embed = discord.Embed(
            title="🚨 Bewegung erkannt",
            description="Eine Person wurde erkannt.",
            color=0xff0000
        )

        view = AlarmView()

        if STATUS_MSG:
            await STATUS_MSG.edit(embed=embed, view=view)
        else:
            STATUS_MSG = await channel.send(
                content=f"<@{OWNER_ID}>",
                embed=embed,
                view=view
            )

    bot.loop.create_task(notify())
    return {"ok": True}

def run_api():
    port = int(os.environ.get("PORT", 10000))
    app.run("0.0.0.0", port)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

class AlarmView(discord.ui.View):
    @discord.ui.button(label="📸 Screenshot", style=discord.ButtonStyle.primary)
    async def screenshot(self, interaction, button):
        await interaction.response.send_message(
            "📸 Screenshot-Funktion kommt gleich 🔧",
            ephemeral=True
        )

class ControlView(discord.ui.View):
    async def interaction_check(self, interaction):
        return interaction.user.id == OWNER_ID

    @discord.ui.button(label="🟢 Normal", style=discord.ButtonStyle.success)
    async def normal(self, interaction, button):
        global MODE, STATUS_MSG
        MODE = "NORMAL"
        if STATUS_MSG:
            await STATUS_MSG.delete()
            STATUS_MSG = None
        await interaction.response.send_message("NORMAL aktiv", ephemeral=True)

    @discord.ui.button(label="🚨 Alarm", style=discord.ButtonStyle.danger)
    async def alarm(self, interaction, button):
        global MODE
        MODE = "ALARM"
        await interaction.response.send_message("ALARM aktiv", ephemeral=True)

@bot.tree.command(name="status")
async def status(interaction: discord.Interaction):
    global STATUS_MSG

    embed = discord.Embed(
        title="🧠 Überwachung",
        description=f"Modus: **{MODE}**",
        color=0x00ff00 if MODE == "NORMAL" else 0xff0000
    )

    view = ControlView()

    if STATUS_MSG:
        await STATUS_MSG.edit(embed=embed, view=view)
    else:
        STATUS_MSG = await interaction.channel.send(embed=embed, view=view)

    await interaction.response.send_message("Status aktualisiert", ephemeral=True)

@bot.event
async def on_ready():
    print("✅ Bot online")

if __name__ == "__main__":
    threading.Thread(target=run_api, daemon=True).start()
    bot.run(TOKEN)
