import os
import discord
from discord.ext import commands
from discord import app_commands

# ENV VARS (Render / lokal)
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# GLOBALER STATUS
MODE = "NORMAL"  # NORMAL | ALARM | ALARM_NOW


# =======================
# UI (Buttons)
# =======================
class ControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == OWNER_ID

    @discord.ui.button(label="🟢 Normal", style=discord.ButtonStyle.success)
    async def normal(self, interaction: discord.Interaction, button: discord.ui.Button):
        global MODE
        MODE = "NORMAL"
        await interaction.response.send_message(
            "✅ **Normalmodus aktiv**\nDu wirst erkannt, kein Alarm.",
            ephemeral=True
        )

    @discord.ui.button(label="🟡 Alarm (Überwachung)", style=discord.ButtonStyle.primary)
    async def alarm(self, interaction: discord.Interaction, button: discord.ui.Button):
        global MODE
        MODE = "ALARM"
        await interaction.response.send_message(
            "⚠️ **Alarmmodus aktiv**\nIch melde Personen im Zimmer.",
            ephemeral=True
        )

    @discord.ui.button(label="🔴 Alarm sofort", style=discord.ButtonStyle.danger)
    async def alarm_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        global MODE
        MODE = "ALARM_NOW"
        await interaction.response.send_message(
            "🚨 **Alarm SOFORT ausgelöst**",
            ephemeral=True
        )

    @discord.ui.button(label="👁️ Gesicht prüfen", style=discord.ButtonStyle.secondary)
    async def face(self, interaction: discord.Interaction, button: discord.ui.Button):
        if MODE != "ALARM":
            await interaction.response.send_message(
                "❌ Gesicht prüfen ist nur im Alarmmodus möglich.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "👁️ **Gesichtserkennung gestartet**",
            ephemeral=True
        )

    @discord.ui.button(label="⛔ Stop", style=discord.ButtonStyle.secondary)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        global MODE
        MODE = "NORMAL"
        await interaction.response.send_message(
            "⛔ **Alarm gestoppt** – zurück zu Normal.",
            ephemeral=True
        )


# =======================
# Events
# =======================
@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")
    await bot.tree.sync()


# =======================
# Slash Command
# =======================
@bot.tree.command(name="status", description="Zeigt Status & Steuerung")
async def status(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Kein Zugriff", ephemeral=True)
        return

    embed = discord.Embed(
        title="🧠 KI-Überwachung",
        description=f"**Aktueller Modus:** `{MODE}`",
        color=0x00ff99
    )

    embed.add_field(name="👤 Person", value="Wird erkannt", inline=True)
    embed.add_field(name="👁️ Gesicht", value="Manuell", inline=True)

    await interaction.response.send_message(
        embed=embed,
        view=ControlView(),
        ephemeral=True
    )


bot.run(TOKEN)
