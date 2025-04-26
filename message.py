import discord
from discord.ext import commands
import json
import os

# Intents et bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Fichiers de données
DATA_FILE = "avions_data.json"
MESSAGE_INFO_FILE = "message_info.json"

# Dictionnaire des avions valides (hors FC3 global, FC3 listé individuellement)
AVIONS_VALIDES = {
    # Modules non-FC3
    "A-10C":             ["a10", "a10c", "warthog"],
    "A-10C II":          ["a10cii", "a10c2"],
    "AH-64D":            ["ah64", "apache", "ah-64"],
    "AV-8B N/A":         ["av8", "av8b", "harrier"],
    "C-101CC":           ["c101", "c101cc", "c-101"],
    "F-14A/B":           ["f14", "f-14", "f14a", "f-14a", "f14b", "f-14b", "tomcat"],
    "F-15E":             ["f15e", "f-15e", "strikeeagle", "strike eagle"],
    "F-16C":             ["f16", "f-16", "f16c", "viper"],
    "F/A-18C":           ["f18", "f-18", "f18c", "fa18", "hornet"],
    "F-4E":              ["f4e", "f-4e", "phantom"],
    "FW 190 A-8":        ["fw190a8", "fw-190a8"],
    "FW 190 D-9":        ["fw190d9", "fw-190d9", "dora"],
    "I-16":              ["i16"],
    "JF-17":             ["jf17", "thunder"],
    "Ka-50":             ["ka-50", "ka50", "blackshark"],
    "Ka-50 III":         ["ka-50iii", "ka50iii", "ka-50-iii", "ka-503"],
    "L-39C":             ["l-39", "l39", "l-39c", "l39c"],
    "M-2000C":           ["m-2000c", "m2000c", "mirage2000"],
    "MB-339A":           ["mb-339", "mb339", "mb-339a", "mb339a"],
    "Mi-24P":            ["mi-24", "mi24", "mi-24p", "mi24p", "hind"],
    "Mi-8MTV2":          ["mi-8", "mi8", "mi-8mtv2", "mi8mtv2"],
    "MiG-19P":           ["mig-19", "mig19", "mig-19p", "mig19p"],
    "MiG-21bis":         ["mig-21", "mig21", "mig-21bis", "mig21bis"],
    "OH-58D Kiowa":      ["oh-58d", "oh58d", "kiowa"],
    "P-47D":             ["p-47", "p47", "p-47d", "p47d", "thunderbolt"],
    "P-51D":             ["p-51", "p51", "p-51d", "p51d", "mustang"],
    "SA342 Gazelle":     ["sa-342", "sa342", "gazelle"],
    "Spitfire LF Mk. IX":["spitfire", "spit"],
    "UH-1H Huey":        ["uh-1", "uh1", "uh-1h", "uh1h", "huey"],
    "Yak-52":            ["yak-52", "yak52", "yak"],

    # Modules FC3 listés individuellement
    "A-10A FC":          ["a-10a", "a10a"],
    "F-15C FC":          ["f-15c", "f15c"],
    "J-11A FC":          ["j-11a", "j11a"],
    "MiG-29A FC":        ["mig-29a", "mig29a"],
    "MiG-29G FC":        ["mig-29g", "mig29g"],
    "MiG-29S FC":        ["mig-29s", "mig29s"],
    "Su-25 FC":          ["su-25", "su25"],
    "Su-25T FC":         ["su-25t", "su25t"],
    "Su-27 FC":          ["su-27", "su27"],
    "Su-33 FC":          ["su-33", "su33"]
}

# Liste des maps valides
MAPS_VALIDES = [
    "Normandy",
    "Persian Gulf",
    "Mariana Islands",
    "Nevada",
    "Syria",
    "Irak",
    "Afghanistan",
    "Germany"
]

# --- Gestion des données ---

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_message_info():
    if os.path.exists(MESSAGE_INFO_FILE):
        with open(MESSAGE_INFO_FILE, "r") as f:
            return json.load(f)
    return {}

def save_message_info(info):
    with open(MESSAGE_INFO_FILE, "w") as f:
        json.dump(info, f, indent=2)

# --- Normalisation des noms ---

def get_official_name(input_name: str):
    key = input_name.lower().replace(" ", "").replace("-", "")
    for official, aliases in AVIONS_VALIDES.items():
        # compare à la forme officielle
        if key == official.lower().replace(" ", "").replace("-", ""):
            return official
        # compare aux alias
        for alias in aliases:
            if key == alias.lower().replace("-", "").replace(" ", ""):
                return official
    return None

# --- Mise à jour de l'embed permanent ---

async def update_embed():
    data = load_data()
    info = load_message_info()
    if not info:
        return

    channel = bot.get_channel(info["channel_id"])
    if not channel:
        return

    try:
        msg = await channel.fetch_message(info["message_id"])
    except discord.NotFound:
        return

    embed = discord.Embed(title="✈️ Tableau récapitulatif des modules MAIN et Maps des Pilotes", color=0x3498db)
    # Colonne Pilote
    embed.add_field(
        name="Pilote",
        value="\n".join(f"<@{uid}>" for uid in data),
        inline=True
    )
    # Colonnes Avion 1-3
    for i in range(3):
        embed.add_field(
            name=f"Avion {i+1}",
            value="\n".join(
                data[uid]["avions"][i] if data[uid]["avions"][i] else "–"
                for uid in data
            ),
            inline=True
        )
    # Colonne Maps
    embed.add_field(
        name="Maps",
        value="\n".join(
            ", ".join(data[uid]["maps"]) if data[uid]["maps"] else "–"
            for uid in data
        ),
        inline=True
    )

    await msg.edit(embed=embed)

# --- Commande d'initialisation (admin) ---

@bot.command()
@commands.has_permissions(administrator=True)
async def initavions(ctx):
    """Crée le message tableau et stocke son ID."""
    embed = discord.Embed(
        title="✈️ Tableau récapitulatif des modules MAIN et Maps des Pilotes",
        description="Initialisation…",
        color=0x3498db
    )
    message = await ctx.send(embed=embed)
    save_message_info({
        "channel_id": ctx.channel.id,
        "message_id": message.id
    })
    await update_embed()

# --- Commande pour définir un avion (slot 1–3) ---

@bot.command()
async def avion(ctx, slot: int, *, avion_nom: str):
    """!avion <1|2|3> <nom_avion>"""
    if slot not in (1, 2, 3):
        await ctx.send("❌ Le slot doit être 1, 2 ou 3.")
        return

    official = get_official_name(avion_nom)
    if not official:
        await ctx.send("❌ Nom invalide")  # Nom invalide
        return

    data = load_data()
    uid = str(ctx.author.id)
    if uid not in data:
        data[uid] = {"avions": ["", "", ""], "maps": []}

    data[uid]["avions"][slot - 1] = official
    save_data(data)

    await ctx.send(f"✅ Avion {slot} mis à jour : {official}")
    await update_embed()

# --- Commande pour ajouter une map ---

@bot.command(name="map")
async def add_map(ctx, *, map_nom: str):
    """!map <nom_map>"""
    candidate = map_nom.strip().capitalize()
    if candidate not in MAPS_VALIDES:
        await ctx.send(f"❌ Map invalide. Disponibles : {', '.join(MAPS_VALIDES)}.")
        return

    data = load_data()
    uid = str(ctx.author.id)
    if uid not in data:
        data[uid] = {"avions": ["", "", ""], "maps": []}

    if candidate not in data[uid]["maps"]:
        data[uid]["maps"].append(candidate)
        save_data(data)

    await ctx.send(f"✅ Map ajoutée : {candidate}")
    await update_embed()

# --- Démarrage du bot ---

bot.run("TOKEN")
