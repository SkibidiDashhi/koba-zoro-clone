import os
import time
import json
import random
import asyncio
from io import BytesIO
from datetime import datetime, timedelta
from collections import defaultdict

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram.enums import ChatType

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    PIL_AVAILABLE = True
except:
    PIL_AVAILABLE = False
    print("Pillow not installed. Install with: pip install Pillow")

# ==================== CONFIGURATION ====================
API_ID = 20230268
API_HASH = "72c3bf193f58a0e4b83bfd2b78dadf8c"
BOT_TOKEN = "8716575725:AAFa-dXG83dNJ2bobC4WPU6Siaiq5fjSIfg"
BOT_NAME = "@Grand_Line_Sentinel_bot"
OWNER_ID = 8403514080

# ==================== MAIN GROUP SETTINGS ====================
MAIN_GROUP_ID = -1003599158196
MAIN_GROUP_LINK = "https://t.me/World_Governmentt"

# Image paths
WANTED_IMAGE = "wanted_template.jpg"
SHOP_IMAGE = "shop_image.jpg"
TOP_IMAGE = "top_image.jpg"
HAKI_IMAGE = "haki_image.jpg"
FRUIT_IMAGE = "fruit_image.jpg"
IMU_IMAGE = "img_image.jpg"

# Level Up Images
LEVEL_UP_IMAGE = "level_up.jpg"
LEVEL_UP_GIF = "level_up.gif"
LEVEL_UP_GROUP_IMAGE = "level_up_group.jpg"
LEVEL_UP_GROUP_GIF = "level_up_group.gif"

# Level Down Images
LEVEL_DOWN_IMAGE = "level_down.jpg"
LEVEL_DOWN_GIF = "level_down.gif"
LEVEL_DOWN_GROUP_IMAGE = "level_down_group.jpg"
LEVEL_DOWN_GROUP_GIF = "level_down_group.gif"

# PVP Images
WIN_GIF = "victory.gif"
WIN_IMAGE = "victory.jpg"
LOSE_GIF = "defeat.gif"
LOSE_IMAGE = "defeat.jpg"
PVP_VICTORY_GIF = "pvp_victory.gif"
PVP_VICTORY_IMAGE = "pvp_victory.jpg"
PVP_DEFEAT_GIF = "pvp_defeat.gif"
PVP_DEFEAT_IMAGE = "pvp_defeat.jpg"

# Create directories
if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists("temp"):
    os.makedirs("temp")

# Initialize bot
app = Client("game_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
# ==================== GLOBAL VARIABLES ====================
user_data = {}
normal_characters = []
mythical_characters = []
active_challenges = {}
message_count = defaultdict(int)
pending_trades = {}
GBANNED = set()
TEMP_BANNED = {}
ADMINS = set()

bet_patterns = {"pattern1": 70, "pattern2": 33, "pattern3": 20}
current_pattern = "pattern1"
last_command_time = defaultdict(float)

VAULT_CAPS = {1: 25000000, 2: 25000000000, 3: 500000000000}
HAKI_NAMES = {"obv": "Observation", "arm": "Armament", "conq": "Conqueror's"}

# World Boss variables
world_boss_active = False
world_boss_hp = 0
world_boss_damage = defaultdict(int)

# Giveaway variables
active_giveaways = {}

# ==================== XP SYSTEM ====================
def get_xp_needed(level):
    """XP needed to level up"""
    return 100 + (level * 10)

def get_rank(level):
    if level <= 10: return "🏴‍☠️ Rookie Pirate"
    if level <= 25: return "🧹 Cabin Boy"
    if level <= 40: return "⚓ Pirate Apprentice"
    if level <= 60: return "🎯 Bounty Hunter"
    if level <= 80: return "🗺️ Grand Line Traveler"
    if level <= 100: return "💥 Supernova"
    if level <= 125: return "⚔️ Warlord of the Sea"
    if level <= 150: return "👑 Yonko Commander"
    if level <= 180: return "🌊 Marine Admiral"
    if level < 200: return "🏴‍☠️ Pirate King Candidate"
    return "👑🔥 Pirate King"

# ==================== HELPER FUNCTIONS ====================
def check_cooldown(user_id, cooldown_seconds=2):
    now = time.time()
    if user_id in last_command_time:
        elapsed = now - last_command_time[user_id]
        if elapsed < cooldown_seconds:
            return False, round(cooldown_seconds - elapsed, 1)
    last_command_time[user_id] = now
    return True, 0

def parse_amount(amount_str):
    try:
        return int(amount_str.replace(",", ""))
    except:
        return None

def is_admin_or_owner(user_id):
    return user_id == OWNER_ID or user_id in ADMINS
# ==================== PVP DM NOTIFICATIONS ====================
async def send_pvp_victory_dm(user_id, attacker_name, target_name, steal_amount, new_bounty, old_level, new_level, target_id=None):
    """Send victory notification via DM with clickable mention"""
    try:
        if target_id:
            target_mention = f"[{target_name}](tg://user?id={target_id})"
        else:
            target_mention = target_name
        
        message_text = (
            f"     You Stolen from {target_mention}!💥\n\n"
            f"💰 **Stolen Bounty:** ฿{steal_amount:,}\n"
            f"🏆 **Your New Bounty:** ฿{new_bounty:,}\n\n\n"
            f"💪 Continue your journey to become the Pirate King!\n\n"
            f"🤖 {BOT_NAME}"
        )
        
        if os.path.exists(PVP_VICTORY_GIF):
            await app.send_animation(user_id, PVP_VICTORY_GIF, caption=message_text)
        elif os.path.exists(PVP_VICTORY_IMAGE):
            await app.send_photo(user_id, PVP_VICTORY_IMAGE, caption=message_text)
        else:
            await app.send_message(user_id, message_text)
    except Exception as e:
        print(f"Failed to send victory DM to {user_id}: {e}")

async def send_pvp_defeat_dm(user_id, attacker_name, target_name, lost_amount, new_bounty, old_level, new_level, attacker_id=None):
    """Send defeat notification via DM with clickable mention"""
    try:
        if attacker_id:
            attacker_mention = f"[{attacker_name}](tg://user?id={attacker_id})"
        else:
            attacker_mention = attacker_name
        
        message_text = (
            f"     You were stolen by {attacker_mention}!💀\n\n"
            f"💰 **Lost Bounty:** ฿{lost_amount:,}\n"
            f"🏆 **Your New Bounty:** ฿{new_bounty:,}\n\n\n"
            f"💪 Train harder and come back stronger!\n\n"
            f"🤖 {BOT_NAME}"
        )
        
        if os.path.exists(PVP_DEFEAT_GIF):
            await app.send_animation(user_id, PVP_DEFEAT_GIF, caption=message_text)
        elif os.path.exists(PVP_DEFEAT_IMAGE):
            await app.send_photo(user_id, PVP_DEFEAT_IMAGE, caption=message_text)
        else:
            await app.send_message(user_id, message_text)
    except Exception as e:
        print(f"Failed to send defeat DM to {user_id}: {e}")

# ==================== LEVEL UP DM NOTIFICATION ====================
async def send_level_up_notification(user_id, old_level, new_level, source="game"):
    """Send level up notification via DM with image/GIF"""
    try:
        if new_level >= 200:
            medal = "👑🔥"
            title = "PIRATE KING!"
        elif new_level >= 180:
            medal = "🌊"
            title = "ADMIRAL!"
        elif new_level >= 150:
            medal = "👑"
            title = "YONKO COMMANDER!"
        elif new_level >= 125:
            medal = "⚔️"
            title = "WARLORD!"
        elif new_level >= 100:
            medal = "💥"
            title = "SUPERNOVA!"
        elif new_level >= 80:
            medal = "🗺️"
            title = "GRAND LINE TRAVELER!"
        elif new_level >= 60:
            medal = "🎯"
            title = "BOUNTY HUNTER!"
        elif new_level >= 40:
            medal = "⚓"
            title = "PIRATE APPRENTICE!"
        elif new_level >= 25:
            medal = "🧹"
            title = "CABIN BOY!"
        else:
            medal = "🏴‍☠️"
            title = "ROOKIE!"
        
        rank = get_rank(new_level)
        
        if source == "pvp_win":
            source_text = "⚔️ **PVP VICTORY!** ⚔️"
        elif source == "pvp_loss":
            source_text = "💀 **PVP DEFEAT REVENGE!** 💀"
        elif source == "game":
            source_text = "🎮 **GAME WIN!** 🎮"
        elif source == "daily":
            source_text = "📅 **DAILY REWARD!** 📅"
        elif source == "weekly":
            source_text = "📆 **WEEKLY REWARD!** 📆"
        elif source == "claim":
            source_text = "🎁 **CLAIM REWARD!** 🎁"
        elif source == "challenge":
            source_text = "👹 **CHARACTER DEFEATED!** 👹"
        elif source == "world_boss":
            source_text = "🌑 **WORLD BOSS REWARD!** 🌑"
        else:
            source_text = "✨ **LEVEL UP!** ✨"
        
        message_text = (
            f"{medal} **LEVEL UP!** {medal}\n\n"
            f"{source_text}\n\n"
            f"⚔️ **{old_level}** → **{new_level}** ⚔️\n"
            f"🏆 **New Rank:** {rank}\n"
            f"👑 **Title:** {title}\n\n"
            f"💪 Continue your journey to become the Pirate King!\n\n"
            f"🤖 {BOT_NAME}"
        )
        
        if os.path.exists(LEVEL_UP_GIF):
            try:
                await app.send_animation(user_id, LEVEL_UP_GIF, caption=message_text)
            except:
                if os.path.exists(LEVEL_UP_IMAGE):
                    await app.send_photo(user_id, LEVEL_UP_IMAGE, caption=message_text)
                else:
                    await app.send_message(user_id, message_text)
        elif os.path.exists(LEVEL_UP_IMAGE):
            await app.send_photo(user_id, LEVEL_UP_IMAGE, caption=message_text)
        else:
            await app.send_message(user_id, message_text)
            
    except Exception as e:
        print(f"Failed to send level up DM to {user_id}: {e}")

async def send_level_up_group_notification(chat_id, user_name, old_level, new_level):
    """Send level up notification in group with image/GIF"""
    try:
        caption = f"🎉 **{user_name}** reached Level {new_level}! 🎉\n\n⚔️ {old_level} → {new_level}"
        
        if os.path.exists(LEVEL_UP_GROUP_GIF):
            await app.send_animation(chat_id, LEVEL_UP_GROUP_GIF, caption=caption)
        elif os.path.exists(LEVEL_UP_GROUP_IMAGE):
            await app.send_photo(chat_id, LEVEL_UP_GROUP_IMAGE, caption=caption)
    except Exception as e:
        print(f"Failed to send level up group notification: {e}")

# ==================== LEVEL DOWN DM NOTIFICATION ====================
async def send_level_down_notification(user_id, old_level, new_level, source="pvp_loss"):
    """Send level down notification via DM with image/GIF"""
    try:
        if new_level >= 200:
            medal = "👑🔥"
        elif new_level >= 180:
            medal = "🌊"
        elif new_level >= 150:
            medal = "👑"
        elif new_level >= 125:
            medal = "⚔️"
        elif new_level >= 100:
            medal = "💥"
        elif new_level >= 80:
            medal = "🗺️"
        elif new_level >= 60:
            medal = "🎯"
        elif new_level >= 40:
            medal = "⚓"
        elif new_level >= 25:
            medal = "🧹"
        else:
            medal = "🏴‍☠️"
        
        rank = get_rank(new_level)
        
        if source == "pvp_loss":
            source_text = "💀 **PVP DEFEAT!** 💀"
        elif source == "game":
            source_text = "🎮 **GAME LOSS!** 🎮"
        else:
            source_text = "💀 **LEVEL DOWN!** 💀"
        
        message_text = (
            f"{medal} **LEVEL DOWN!** {medal}\n\n"
            f"{source_text}\n\n"
            f"⚔️ **{old_level}** → **{new_level}** ⚔️\n"
            f"🏆 **New Rank:** {rank}\n\n"
            f"💪 Train harder and come back stronger!\n\n"
            f"🤖 {BOT_NAME}"
        )
        
        if os.path.exists(LEVEL_DOWN_GIF):
            try:
                await app.send_animation(user_id, LEVEL_DOWN_GIF, caption=message_text)
            except:
                if os.path.exists(LEVEL_DOWN_IMAGE):
                    await app.send_photo(user_id, LEVEL_DOWN_IMAGE, caption=message_text)
                else:
                    await app.send_message(user_id, message_text)
        elif os.path.exists(LEVEL_DOWN_IMAGE):
            await app.send_photo(user_id, LEVEL_DOWN_IMAGE, caption=message_text)
        else:
            await app.send_message(user_id, message_text)
            
    except Exception as e:
        print(f"Failed to send level down DM to {user_id}: {e}")

async def send_level_down_group_notification(chat_id, user_name, old_level, new_level):
    """Send level down notification in group with image/GIF"""
    try:
        caption = f"💀 **{user_name}** dropped to Level {new_level}! 💀\n\n⚔️ {old_level} → {new_level}"
        
        if os.path.exists(LEVEL_DOWN_GROUP_GIF):
            await app.send_animation(chat_id, LEVEL_DOWN_GROUP_GIF, caption=caption)
        elif os.path.exists(LEVEL_DOWN_GROUP_IMAGE):
            await app.send_photo(chat_id, LEVEL_DOWN_GROUP_IMAGE, caption=caption)
    except Exception as e:
        print(f"Failed to send level down group notification: {e}")
        # ==================== DEVIL FRUITS ====================
DEVIL_FRUITS = {
    "Good": [
        {"name": "Hito Hito no Mi", "model": "Model: Nika", "type": "Mythical Zoan", "full": "Hito Hito no Mi, Model: Nika"},
        {"name": "Mera Mera no Mi", "model": "Logia", "type": "Logia", "full": "Mera Mera no Mi"},
        {"name": "Pika Pika no Mi", "model": "Logia", "type": "Logia", "full": "Pika Pika no Mi"},
        {"name": "Gura Gura no Mi", "model": "Paramecia", "type": "Paramecia", "full": "Gura Gura no Mi"},
        {"name": "Ope Ope no Mi", "model": "Paramecia", "type": "Paramecia", "full": "Ope Ope no Mi"},
        {"name": "Magu Magu no Mi", "model": "Logia", "type": "Logia", "full": "Magu Magu no Mi"}
    ],
    "Medium": [
        {"name": "Sube Sube no Mi", "model": "Paramecia", "type": "Paramecia", "full": "Sube Sube no Mi"},
        {"name": "Bara Bara no Mi", "model": "Paramecia", "type": "Paramecia", "full": "Bara Bara no Mi"},
        {"name": "Doru Doru no Mi", "model": "Paramecia", "type": "Paramecia", "full": "Doru Doru no Mi"},
        {"name": "Baku Baku no Mi", "model": "Paramecia", "type": "Paramecia", "full": "Baku Baku no Mi"},
        {"name": "Noro Noro no Mi", "model": "Paramecia", "type": "Paramecia", "full": "Noro Noro no Mi"},
        {"name": "Kilo Kilo no Mi", "model": "Paramecia", "type": "Paramecia", "full": "Kilo Kilo no Mi"}
    ],
    "Bad": [
        {"name": "Jake Jake no Mi", "model": "Paramecia", "type": "Paramecia", "full": "Jake Jake no Mi"},
        {"name": "Guru Guru no Mi", "model": "Paramecia", "type": "Paramecia", "full": "Guru Guru no Mi"},
        {"name": "Beri Beri no Mi", "model": "Paramecia", "type": "Paramecia", "full": "Beri Beri no Mi"},
        {"name": "Sabi Sabi no Mi", "model": "Paramecia", "type": "Paramecia", "full": "Sabi Sabi no Mi"},
        {"name": "Ori Ori no Mi", "model": "Paramecia", "type": "Paramecia", "full": "Ori Ori no Mi"},
        {"name": "Beta Beta no Mi", "model": "Paramecia", "type": "Paramecia", "full": "Beta Beta no Mi"}
    ]
}

def get_random_fruit(tier):
    if tier == 1:
        category = random.choice(["Bad", "Medium"])
        pool = DEVIL_FRUITS[category]
    elif tier == 2:
        category = random.choices(["Bad", "Medium", "Good"], weights=[30, 40, 30])[0]
        pool = DEVIL_FRUITS[category]
    else:
        category = random.choices(["Medium", "Good"], weights=[30, 70])[0]
        pool = DEVIL_FRUITS[category]
    return random.choice(pool), category
    # ==================== PLAYER CLASS ====================
class Player:
    def __init__(self, user_id):
        self.user_id = user_id
        self.bounty = 0
        self.level = 1
        self.xp = 0
        self.haki = None
        self.haki_level = 0
        self.haki_uses = 0
        self.haki_cd = 0
        self.shield_level = 0
        self.shield_uses = 0
        self.shield_cd = 0
        self.passive_enabled = True
        self.pvp_enabled = True
        self.devil_fruit = None
        self.fruit_category = None
        self.name = ""
        self.username = ""
        self.daily = 0
        self.weekly = 0
        self.vault = 0
        self.vault_level = 1
        self.nika_awakened = False
        self.captured_chars = []
        self.advanced_token = 0
        self.advanced_haki = False
        self.claimed_main = False
        self.boost_end = 0

    def to_dict(self):
        return {
            "bounty": self.bounty, "level": self.level, "xp": self.xp,
            "haki": self.haki, "haki_level": self.haki_level,
            "haki_uses": self.haki_uses, "haki_cd": self.haki_cd,
            "shield_level": self.shield_level, "shield_uses": self.shield_uses,
            "shield_cd": self.shield_cd,
            "passive_enabled": self.passive_enabled,
            "pvp_enabled": self.pvp_enabled,
            "devil_fruit": self.devil_fruit, "fruit_category": self.fruit_category,
            "name": self.name, "username": self.username,
            "daily": self.daily, "weekly": self.weekly,
            "vault": self.vault, "vault_level": self.vault_level,
            "nika_awakened": self.nika_awakened, "captured_chars": self.captured_chars,
            "advanced_token": self.advanced_token, "advanced_haki": self.advanced_haki,
            "claimed_main": self.claimed_main, "boost_end": self.boost_end
        }

    @classmethod
    def from_dict(cls, uid, data):
        p = cls(uid)
        p.bounty = data.get("bounty", 0)
        p.level = data.get("level", 1)
        p.xp = data.get("xp", 0)
        p.haki = data.get("haki")
        p.haki_level = data.get("haki_level", 0)
        p.haki_uses = data.get("haki_uses", 0)
        p.haki_cd = data.get("haki_cd", 0)
        p.shield_level = data.get("shield_level", 0)
        p.shield_uses = data.get("shield_uses", 0)
        p.shield_cd = data.get("shield_cd", 0)
        p.passive_enabled = data.get("passive_enabled", True)
        p.pvp_enabled = data.get("pvp_enabled", True)
        p.devil_fruit = data.get("devil_fruit")
        p.fruit_category = data.get("fruit_category")
        p.name = data.get("name", "")
        p.username = data.get("username", "")
        p.daily = data.get("daily", 0)
        p.weekly = data.get("weekly", 0)
        p.vault = data.get("vault", 0)
        p.vault_level = data.get("vault_level", 1)
        p.nika_awakened = data.get("nika_awakened", False)
        p.captured_chars = data.get("captured_chars", [])
        p.advanced_token = data.get("advanced_token", 0)
        p.advanced_haki = data.get("advanced_haki", False)
        p.claimed_main = data.get("claimed_main", False)
        p.boost_end = data.get("boost_end", 0)
        return p
        # ==================== DATA MANAGEMENT ====================
def get_player(uid):
    uid = str(uid)
    if uid not in user_data:
        user_data[uid] = Player(uid)
    return user_data[uid]

def save_data():
    try:
        data = {uid: p.to_dict() for uid, p in user_data.items()}
        with open("data/users.json", "w") as f:
            json.dump(data, f, indent=2)
    except:
        pass

def load_data():
    global user_data
    try:
        with open("data/users.json", "r") as f:
            data = json.load(f)
            for uid, pdata in data.items():
                user_data[uid] = Player.from_dict(int(uid), pdata)
    except:
        pass

def load_characters():
    global normal_characters, mythical_characters
    try:
        with open("data/normal_chars.json", "r") as f:
            normal_characters = json.load(f)
    except:
        normal_characters = []
    try:
        with open("data/mythical_chars.json", "r") as f:
            mythical_characters = json.load(f)
    except:
        mythical_characters = []

def save_normal_chars():
    with open("data/normal_chars.json", "w") as f:
        json.dump(normal_characters, f, indent=2)

def save_mythical_chars():
    with open("data/mythical_chars.json", "w") as f:
        json.dump(mythical_characters, f, indent=2)

def save_banned():
    with open("data/gbanned.json", "w") as f:
        json.dump(list(GBANNED), f, indent=2)

def load_banned():
    global GBANNED
    try:
        with open("data/gbanned.json", "r") as f:
            GBANNED = set(json.load(f))
    except:
        GBANNED = set()

def save_temp_banned():
    data = {uid: unban_time for uid, unban_time in TEMP_BANNED.items()}
    with open("data/temp_banned.json", "w") as f:
        json.dump(data, f, indent=2)

def load_temp_banned():
    global TEMP_BANNED
    try:
        with open("data/temp_banned.json", "r") as f:
            data = json.load(f)
            TEMP_BANNED = {int(uid): unban_time for uid, unban_time in data.items()}
    except:
        TEMP_BANNED = {}

def save_admins():
    with open("data/admins.json", "w") as f:
        json.dump(list(ADMINS), f, indent=2)

def load_admins():
    global ADMINS
    try:
        with open("data/admins.json", "r") as f:
            ADMINS = set(json.load(f))
    except:
        ADMINS = set()

def check_temp_bans():
    now = time.time()
    expired = [uid for uid, unban_time in TEMP_BANNED.items() if unban_time <= now]
    for uid in expired:
        del TEMP_BANNED[uid]
    if expired:
        save_temp_banned()

# Load all data
load_data()
load_characters()
load_banned()
load_temp_banned()
load_admins()
# ==================== WANTED POSTER FUNCTIONS ====================
async def download_pfp(user_id):
    pfp_path = f"temp/pfp_{user_id}.jpg"
    if os.path.exists(pfp_path):
        return pfp_path
    try:
        async for photo in app.get_chat_photos(int(user_id), limit=1):
            return await app.download_media(photo.file_id, file_name=pfp_path)
    except:
        return None
    return None

def load_name_font(size):
    font_paths = [
        "times_new_roman_extra_bold.ttf",
        "TimesNewRomanExtraBold.ttf",
        "TimesNewRoman-Bold.ttf",
        "times.ttf",
        "arial.ttf"
    ]
    for path in font_paths:
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()

def load_bounty_font(size):
    font_paths = [
        "Vrinda.ttf",
        "vrinda.ttf",
        "Vrinda Regular.ttf",
        "arial.ttf"
    ]
    for path in font_paths:
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()

async def create_wanted_poster_only(user_id, player_name, bounty):
    if not PIL_AVAILABLE:
        return None
    if not os.path.exists(WANTED_IMAGE):
        return None
    try:
        poster = Image.open(WANTED_IMAGE).convert("RGB")
        poster = poster.resize((1000, 1400))
        pfp = await download_pfp(user_id)
        if pfp:
            img = Image.open(pfp).convert("RGB")
            img = ImageOps.fit(img, (820, 588), Image.Resampling.LANCZOS)
            poster.paste(img, (90, 298))
        draw = ImageDraw.Draw(poster)
        name_font = load_name_font(150)
        bounty_font = load_bounty_font(110)
        if player_name and player_name.lower() != "nameless":
            name_text = player_name.upper()
            bbox = draw.textbbox((0, 0), name_text, font=name_font)
            x = (1000 - (bbox[2] - bbox[0])) // 2
            draw.text((x, 996), name_text, fill=(80, 55, 25), font=name_font)
        bounty_text = f"{bounty:,} -"
        bbox = draw.textbbox((0, 0), bounty_text, font=bounty_font)
        x = (1000 - (bbox[2] - bbox[0])) // 2
        draw.text((x, 1155), bounty_text, fill=(80, 55, 25), font=bounty_font)
        img_bytes = BytesIO()
        poster.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes
    except:
        return None
        # ==================== BASIC COMMANDS ====================
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    p = get_player(message.from_user.id)
    p.name = message.from_user.first_name
    if message.from_user.username:
        p.username = message.from_user.username
    save_data()
    await message.reply(
        f"🏴‍☠️ **GRAND LINE SENTINEL** 🏴‍☠️\n\n"
        f"**{BOT_NAME} is now working!**\n\n"
        f"⚓ Welcome to the Grand Line, Pirate!\n"
        f"💪 Start your journey to become the Pirate King!\n\n"
        f"⚔️ **Good luck on your adventure!** ⚔️"
    )

@app.on_message(filters.command("help"))
async def help_cmd(client, message):
    await message.reply(
        f"📜 **COMMANDS** 📜\n\n"
        f"💰 **GAMES (CD: 2s):**\n"
        f"/bet [amount] [t/h] - 🪙 Coin flip\n"
        f"/dice [amount] [e/o] - 🎲 Dice game\n"
        f"/dart [amount] - 🎯 Dart game\n"
        f"/bowl [amount] - 🎳 Bowling game\n"
        f"/soccer [amount] - ⚽ Soccer game\n\n"
        f"👤 **PROFILE:**\n"
        f"/info - 📸 Your wanted poster\n"
        f"/bal - 💰 Check balance\n"
        f"/tokens - 🔮 Check advanced tokens\n"
        f"/daily - 📅 Daily reward (10k)\n"
        f"/weekly - 📆 Weekly reward (1M)\n"
        f"/claim - 🎁 Main group join reward\n"
        f"/top - 🏆 Top 10 bounty\n"
        f"/xtop - ⚔️ Top 10 level\n\n"
        f"🛒 **SHOP:**\n"
        f"/shop - 🏪 Buy items\n"
        f"/sell_fruit - 🍎 Sell fruit (50%)\n\n"
        f"⚔️ **PVP & FIGHT:**\n"
        f"/attack - ⚔️ Fight player (reply) (CD: 3s)\n"
        f"/challenge [name] - 👹 Fight character\n"
        f"/timeleft - ⏰ Check character despawn time\n"
        f"/mychars - 📦 Your captured characters\n"
        f"/trade [amount] - 💰 Sell character (reply to buyer)\n"
        f"/battle - 🌑 Fight World Boss\n\n"
        f"🏦 **VAULT:**\n"
        f"/deposit [amount] - 📥 Store bounty\n"
        f"/dig [amount] - 📤 Withdraw bounty\n\n"
        f"⚙️ **SETTINGS:**\n"
        f"/pvp - ⚔️ Toggle PVP Mode\n"
        f"/passive - 🛡️ Toggle Shield Protection\n\n"
        f"🎁 **GIVEAWAY:**\n"
        f"/tgiveaway [time] [prize] [winners] [desc] - Start giveaway (Admin)\n"
        f"/join - Join active giveaway\n"
        f"/endgiveaway [msg_id] - End giveaway early (Admin)\n\n"
        f"🤖 {BOT_NAME}"
    )

@app.on_message(filters.command("info"))
async def info_cmd(client, message):
    p = get_player(message.from_user.id)
    need = get_xp_needed(p.level)
    rank = get_rank(p.level)
    haki_name = HAKI_NAMES.get(p.haki, "None") if p.haki else "None"
    
    passive_status = "🟢 ON" if p.passive_enabled else "🔴 OFF"
    passive_icon = "" if p.passive_enabled else ""
    pvp_status = "🟢 ON" if p.pvp_enabled else "🔴 OFF"
    pvp_icon = "" if p.pvp_enabled else ""
    
    fruit_display = "None None No Mi"
    fruit_emoji = " "
    if p.devil_fruit:
        for category, fruits in DEVIL_FRUITS.items():
            for fruit in fruits:
                if fruit["full"] == p.devil_fruit:
                    fruit_emoji = "☄️" if category == "Good" else "⚡" if category == "Medium" else "🌀"
                    fruit_display = f"{fruit['name']} ({fruit['model']})"
                    break
            else:
                continue
            break
    if message.from_user.username:
        p.username = message.from_user.username
    save_data()
    percent = int((p.xp / need) * 10) if need > 0 else 0
    bar = "█" * percent + "░" * (10 - percent)
    xp_needed = need - p.xp
    sorted_players = sorted(user_data.values(), key=lambda x: x.bounty, reverse=True)
    global_rank = 1
    for i, player in enumerate(sorted_players, 1):
        if player.user_id == p.user_id:
            global_rank = i
            break
    shield_text = f"🛡️ Lv.{p.shield_level}" if p.shield_level > 0 else "❌ No"
    stats_text = (
        f"**{p.name}**  [`{p.user_id}`]\n──────────────────\n"
        f"Username: @{p.username or 'None'}\nRank: {rank}\n"
        f"Shield: {shield_text}\n"
        f"Passive: {passive_status} {passive_icon}\n"
        f"PVP Mode: {pvp_status} {pvp_icon}\n"
        f"Haki: {haki_name} Lv.{p.haki_level if p.haki else ''}\n"
        f"Global Rank: {global_rank}\n──────────────────\n"
        f"Bounty: ฿{p.bounty:,}\nToken: ⚜️{p.advanced_token}\n"
        f"Vault: ฿{p.vault:,}/{VAULT_CAPS.get(p.vault_level, 25000000):,}\n───────────────────\n"
        f"Level: {p.level}\n[{bar}] ({xp_needed} XP for next level)\n───────────────────\n"
        f"Devil Fruit: {fruit_display} {fruit_emoji}\n\n"
        f"💡 `/passive` - Toggle Shield Protection\n"
        f"💡 `/pvp` - Toggle PVP Mode\n\n"
        f"🤖 {BOT_NAME}"
    )
    poster = await create_wanted_poster_only(message.from_user.id, p.name, p.bounty)
    if poster:
        await message.reply_photo(poster, caption=stats_text)
    elif os.path.exists(WANTED_IMAGE):
        await message.reply_photo(WANTED_IMAGE, caption=stats_text)
    else:
        await message.reply(stats_text)

@app.on_message(filters.command("bal"))
async def balance_cmd(client, message):
    if message.reply_to_message:
        p = get_player(message.reply_to_message.from_user.id)
        name = message.reply_to_message.from_user.first_name
    else:
        p = get_player(message.from_user.id)
        name = message.from_user.first_name
    cap = VAULT_CAPS.get(p.vault_level, 20000000)
    await message.reply(f"**{name}'s Bounty:** ฿{p.bounty:,}\n**Vault:** ฿{p.vault:,} / {cap:,}")

@app.on_message(filters.command("tokens"))
async def tokens_cmd(client, message):
    p = get_player(message.from_user.id)
    text = f"🔮 **ADVANCED TOKENS** 🔮\n\n📦 Tokens: ⚜️**{p.advanced_token}**\n"
    text += f"✨ Advanced Haki: **{'✅ Unlocked' if p.advanced_haki else '❌ Locked'}**\n"
    await message.reply(text)
    # ==================== DAILY, WEEKLY, TOP COMMANDS ====================
@app.on_message(filters.command("daily"))
async def daily_cmd(client, message):
    p = get_player(message.from_user.id)
    now = int(time.time())
    if now - p.daily < 86400:
        left = 86400 - (now - p.daily)
        await message.reply(f"📅 Daily claimed! Next in {left//3600}h")
        return
    p.daily = now
    p.bounty += 10000
    p.xp += 50
    if p.boost_end > time.time():
        p.xp += 25
    
    old_level = p.level
    while p.xp >= get_xp_needed(p.level) and p.level < 200:
        p.xp -= get_xp_needed(p.level)
        p.level += 1
    
    save_data()
    
    if p.level > old_level:
        await send_level_up_notification(message.from_user.id, old_level, p.level, "daily")
        await send_level_up_group_notification(message.chat.id, p.name, old_level, p.level)
    
    level_text = f"\n\n🎉 **LEVEL UP!** {old_level} → {p.level}" if p.level > old_level else ""
    await message.reply(f"🎁 **Daily reward:** 10,000 Bounty + 50 XP!{level_text}")

@app.on_message(filters.command("weekly"))
async def weekly_cmd(client, message):
    p = get_player(message.from_user.id)
    now = int(time.time())
    if now - p.weekly < 604800:
        left = 604800 - (now - p.weekly)
        await message.reply(f"📆 Weekly claimed! Next in {left//86400}d")
        return
    p.weekly = now
    p.bounty += 1000000
    p.xp += 500
    if p.boost_end > time.time():
        p.xp += 250
    
    old_level = p.level
    while p.xp >= get_xp_needed(p.level) and p.level < 200:
        p.xp -= get_xp_needed(p.level)
        p.level += 1
    
    save_data()
    
    if p.level > old_level:
        await send_level_up_notification(message.from_user.id, old_level, p.level, "weekly")
        await send_level_up_group_notification(message.chat.id, p.name, old_level, p.level)
    
    level_text = f"\n\n🎉 **LEVEL UP!** {old_level} → {p.level}" if p.level > old_level else ""
    await message.reply(f"🎁 **Weekly reward:** 1,000,000 Bounty + 500 XP!{level_text}")

@app.on_message(filters.command("top"))
async def top_cmd(client, message):
    sorted_players = sorted(user_data.values(), key=lambda x: x.bounty, reverse=True)[:10]
    if not sorted_players:
        await message.reply("No players found!")
        return
    
    text = "🏆 **TOP 10 BOUNTY** 🏆\n────────────────────────────────\n\n"
    for i, p in enumerate(sorted_players, 1):
        name = p.name if p.name else f"User_{p.user_id}"
        
        if p.username:
            mention = f"[{name}](https://t.me/{p.username})"
        else:
            mention = f"[{name}](tg://user?id={p.user_id})"
        
        medal = "👑" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} {mention}\n   💰 ฿{p.bounty:,}\n\n"
    
    text += f"────────────────────────────────\n🤖 {BOT_NAME}"
    
    if os.path.exists(TOP_IMAGE):
        await message.reply_photo(TOP_IMAGE, caption=text)
    else:
        await message.reply(text)

@app.on_message(filters.command("xtop"))
async def xtop_cmd(client, message):
    sorted_players = sorted(user_data.values(), key=lambda x: x.level, reverse=True)[:10]
    if not sorted_players:
        await message.reply("No players found!")
        return
    
    text = "🏆 **TOP 10 LEVEL** 🏆\n────────────────────────────────\n\n"
    for i, p in enumerate(sorted_players, 1):
        name = p.name if p.name else f"User_{p.user_id}"
        
        if p.username:
            mention = f"[{name}](https://t.me/{p.username})"
        else:
            mention = f"[{name}](tg://user?id={p.user_id})"
        
        medal = "👑" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} {mention}\n   ⚔️ Lv.{p.level}\n\n"
    
    text += f"────────────────────────────────\n🤖 {BOT_NAME}"
    
    if os.path.exists(TOP_IMAGE):
        await message.reply_photo(TOP_IMAGE, caption=text)
    else:
        await message.reply(text)
        # ==================== GAME COMMANDS ====================
@app.on_message(filters.command("bet"))
async def bet_cmd(client, message):
    user_id = message.from_user.id
    can_use, remaining = check_cooldown(user_id, 2)
    if not can_use:
        await message.reply(f"⏰ Slow down! Please wait {remaining} second(s)!")
        return
    
    args = message.text.split()
    if len(args) != 3:
        await message.reply("Usage: `/bet [amount] [t/h]`\n\n`t` = Tails\n`h` = Heads")
        return
    
    amount = parse_amount(args[1])
    if amount is None:
        await message.reply("Invalid amount!")
        return
    
    choice = args[2].lower()
    if choice not in ["t", "h"]:
        await message.reply("Choose 't' (tails) or 'h' (heads)!")
        return
    
    p = get_player(user_id)
    if p.bounty < amount:
        await message.reply(f"Need ฿{amount:,}! You have ฿{p.bounty:,}")
        return
    
    result = random.choice(["h", "t"])
    win = (choice == result)
    result_display = "HEADS" if result == "h" else "TAILS"
    
    xp_amount = max(1, amount // 100000)
    if p.boost_end > time.time() and win:
        xp_amount = int(xp_amount * 1.5)
    
    old_level = p.level
    
    if win:
        p.bounty += amount
        p.xp += xp_amount
        while p.xp >= get_xp_needed(p.level) and p.level < 200:
            p.xp -= get_xp_needed(p.level)
            p.level += 1
        
        if p.level > old_level:
            await send_level_up_notification(user_id, old_level, p.level, "game")
            await send_level_up_group_notification(message.chat.id, p.name, old_level, p.level)
        
        level_msg = f"\n\n🎉 **LEVEL UP!** {old_level} → {p.level}" if p.level > old_level else ""
        await message.reply(f"🎉 Coin landed on **{result_display}**!\n✅ **You won ฿{amount:,}!**\n⭐ **+{xp_amount} XP**{level_msg}")
    else:
        p.bounty -= amount
        p.xp -= xp_amount
        old_level = p.level
        level_down_msg = ""
        while p.xp < 0 and p.level > 1:
            p.level -= 1
            p.xp += get_xp_needed(p.level)
            level_down_msg = f"\n\n💀 **LEVEL DOWN!** {old_level} → {p.level}"
        
        if p.level < old_level:
            await send_level_down_notification(user_id, old_level, p.level, "game")
            await send_level_down_group_notification(message.chat.id, p.name, old_level, p.level)
        
        if p.xp < 0:
            p.xp = 0
            p.level = 1
        await message.reply(f"😢 Coin landed on **{result_display}**!\n❌ **You lost ฿{amount:,}!**\n⭐ **-{xp_amount} XP**{level_down_msg}")
    
    save_data()

@app.on_message(filters.command("dice"))
async def dice_cmd(client, message):
    user_id = message.from_user.id
    can_use, remaining = check_cooldown(user_id, 2)
    if not can_use:
        await message.reply(f"⏰ Slow down! Please wait {remaining} second(s)!")
        return
    args = message.text.split()
    if len(args) != 3:
        await message.reply("Usage: `/dice [amount] [e/o]`")
        return
    amount = parse_amount(args[1])
    if amount is None:
        await message.reply("Invalid amount!")
        return
    choice = args[2].lower()
    if choice not in ["e", "o"]:
        await message.reply("Choose 'e' (even) or 'o' (odd)!")
        return
    p = get_player(user_id)
    if p.bounty < amount:
        await message.reply(f"Need ฿{amount:,}! You have ฿{p.bounty:,}")
        return
    
    dice_msg = await client.send_dice(message.chat.id, emoji="🎲")
    await asyncio.sleep(2)
    roll = dice_msg.dice.value
    is_even = (roll % 2 == 0)
    win = (choice == "e" and is_even) or (choice == "o" and not is_even)
    
    xp_amount = max(1, amount // 100000)
    if p.boost_end > time.time() and win:
        xp_amount = int(xp_amount * 1.5)
    
    old_level = p.level
    
    if win:
        p.bounty += amount
        p.xp += xp_amount
        while p.xp >= get_xp_needed(p.level) and p.level < 200:
            p.xp -= get_xp_needed(p.level)
            p.level += 1
        
        if p.level > old_level:
            await send_level_up_notification(user_id, old_level, p.level, "game")
            await send_level_up_group_notification(message.chat.id, p.name, old_level, p.level)
        
        level_msg = f"\n\n🎉 **LEVEL UP!** {old_level} → {p.level}" if p.level > old_level else ""
        await message.reply(f"🎲 You rolled **{roll}**!\n✅ You won ฿{amount:,}!\n⭐ **+{xp_amount} XP**{level_msg}")
    else:
        p.bounty -= amount
        p.xp -= xp_amount
        old_level = p.level
        level_down_msg = ""
        while p.xp < 0 and p.level > 1:
            p.level -= 1
            p.xp += get_xp_needed(p.level)
            level_down_msg = f"\n\n💀 **LEVEL DOWN!** {old_level} → {p.level}"
        
        if p.level < old_level:
            await send_level_down_notification(user_id, old_level, p.level, "game")
            await send_level_down_group_notification(message.chat.id, p.name, old_level, p.level)
        
        if p.xp < 0:
            p.xp = 0
            p.level = 1
        await message.reply(f"🎲 You rolled **{roll}**!\n❌ You lost ฿{amount:,}!\n⭐ **-{xp_amount} XP**{level_down_msg}")
    
    save_data()

@app.on_message(filters.command("dart"))
async def dart_cmd(client, message):
    user_id = message.from_user.id
    can_use, remaining = check_cooldown(user_id, 2)
    if not can_use:
        await message.reply(f"⏰ Slow down! Please wait {remaining} second(s)!")
        return
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: `/dart [amount]`")
        return
    amount = parse_amount(args[1])
    if amount is None:
        await message.reply("Invalid amount!")
        return
    p = get_player(user_id)
    if p.bounty < amount:
        await message.reply(f"Need ฿{amount:,}! You have ฿{p.bounty:,}")
        return
    
    dart_msg = await client.send_dice(message.chat.id, emoji="🎯")
    await asyncio.sleep(2)
    dart_value = dart_msg.dice.value
    
    if p.haki == "obv" and p.advanced_haki:
        win = dart_value >= 3
    else:
        win = dart_value >= 4
    
    xp_amount = max(1, amount // 100000)
    if p.boost_end > time.time() and win:
        xp_amount = int(xp_amount * 1.5)
    
    old_level = p.level
    
    if win:
        p.bounty += amount
        p.xp += xp_amount
        while p.xp >= get_xp_needed(p.level) and p.level < 200:
            p.xp -= get_xp_needed(p.level)
            p.level += 1
        
        if p.level > old_level:
            await send_level_up_notification(user_id, old_level, p.level, "game")
            await send_level_up_group_notification(message.chat.id, p.name, old_level, p.level)
        
        level_msg = f"\n\n🎉 **LEVEL UP!** {old_level} → {p.level}" if p.level > old_level else ""
        if dart_value == 6:
            await message.reply(f"🎯 **BULLSEYE!** 🎯\n+฿{amount:,}!\n⭐ **+{xp_amount} XP**{level_msg}")
        else:
            await message.reply(f"🎯 You scored {dart_value}!\n+฿{amount:,}!\n⭐ **+{xp_amount} XP**{level_msg}")
    else:
        p.bounty -= amount
        p.xp -= xp_amount
        old_level = p.level
        level_down_msg = ""
        while p.xp < 0 and p.level > 1:
            p.level -= 1
            p.xp += get_xp_needed(p.level)
            level_down_msg = f"\n\n💀 **LEVEL DOWN!** {old_level} → {p.level}"
        
        if p.level < old_level:
            await send_level_down_notification(user_id, old_level, p.level, "game")
            await send_level_down_group_notification(message.chat.id, p.name, old_level, p.level)
        
        if p.xp < 0:
            p.xp = 0
            p.level = 1
        await message.reply(f"💨 **MISSED!** 💨\nYou scored {dart_value}!\n-฿{amount:,}!\n⭐ **-{xp_amount} XP**{level_down_msg}")
    
    save_data()

@app.on_message(filters.command("bowl"))
async def bowl_cmd(client, message):
    user_id = message.from_user.id
    can_use, remaining = check_cooldown(user_id, 2)
    if not can_use:
        await message.reply(f"⏰ Slow down! Please wait {remaining} second(s)!")
        return
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: `/bowl [amount]`")
        return
    amount = parse_amount(args[1])
    if amount is None:
        await message.reply("Invalid amount!")
        return
    p = get_player(user_id)
    if p.bounty < amount:
        await message.reply(f"Need ฿{amount:,}! You have ฿{p.bounty:,}")
        return
    
    bowl_msg = await client.send_dice(message.chat.id, emoji="🎳")
    await asyncio.sleep(2)
    pins_left = bowl_msg.dice.value

    if pins_left == 1:
        win = True
        result_text = "🎳 **STRIKE!** 🎳\nAll pins knocked down!"
    elif pins_left == 2:
        win = True
        result_text = "🎳 **SPARE!** 🎳\n1 pin remaining!"
    elif pins_left == 3:
        win = True
        result_text = "🎳 **GOOD!** 🎳\n2 pins remaining!"
    elif pins_left == 4:
        win = random.random() < 0.5
        result_text = f"🎳 **{pins_left-1} pins remaining!** " + ("✅ You win!" if win else "❌ You lose!")
    else:
        win = False
        result_text = f"💨 **GUTTER!** 💨\n{pins_left-1} pins remaining! You lose!"

    xp_amount = max(1, amount // 100000)
    if p.boost_end > time.time() and win:
        xp_amount = int(xp_amount * 1.5)
    
    old_level = p.level
    
    if win:
        p.bounty += amount
        p.xp += xp_amount
        while p.xp >= get_xp_needed(p.level) and p.level < 200:
            p.xp -= get_xp_needed(p.level)
            p.level += 1
        
        if p.level > old_level:
            await send_level_up_notification(user_id, old_level, p.level, "game")
            await send_level_up_group_notification(message.chat.id, p.name, old_level, p.level)
        
        level_msg = f"\n\n🎉 **LEVEL UP!** {old_level} → {p.level}" if p.level > old_level else ""
        await message.reply(f"{result_text}\n+฿{amount:,}!\n⭐ **+{xp_amount} XP**{level_msg}")
    else:
        p.bounty -= amount
        p.xp -= xp_amount
        old_level = p.level
        level_down_msg = ""
        while p.xp < 0 and p.level > 1:
            p.level -= 1
            p.xp += get_xp_needed(p.level)
            level_down_msg = f"\n\n💀 **LEVEL DOWN!** {old_level} → {p.level}"
        
        if p.level < old_level:
            await send_level_down_notification(user_id, old_level, p.level, "game")
            await send_level_down_group_notification(message.chat.id, p.name, old_level, p.level)
        
        if p.xp < 0:
            p.xp = 0
            p.level = 1
        await message.reply(f"{result_text}\n-฿{amount:,}!\n⭐ **-{xp_amount} XP**{level_down_msg}")
    
    save_data()

@app.on_message(filters.command("soccer"))
async def soccer_cmd(client, message):
    user_id = message.from_user.id
    can_use, remaining = check_cooldown(user_id, 2)
    if not can_use:
        await message.reply(f"⏰ Slow down! Please wait {remaining} second(s)!")
        return
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: `/soccer [amount]`")
        return
    amount = parse_amount(args[1])
    if amount is None:
        await message.reply("Invalid amount!")
        return
    p = get_player(user_id)
    if p.bounty < amount:
        await message.reply(f"Need ฿{amount:,}! You have ฿{p.bounty:,}")
        return
    
    soccer_msg = await client.send_dice(message.chat.id, emoji="⚽")
    await asyncio.sleep(2)
    soccer_value = soccer_msg.dice.value
    
    if p.haki == "obv" and p.advanced_haki:
        win = soccer_value >= 3
    else:
        win = soccer_value >= 4
    
    xp_amount = max(1, amount // 100000)
    if p.boost_end > time.time() and win:
        xp_amount = int(xp_amount * 1.5)
    
    old_level = p.level
    
    if win:
        p.bounty += amount
        p.xp += xp_amount
        while p.xp >= get_xp_needed(p.level) and p.level < 200:
            p.xp -= get_xp_needed(p.level)
            p.level += 1
        
        if p.level > old_level:
            await send_level_up_notification(user_id, old_level, p.level, "game")
            await send_level_up_group_notification(message.chat.id, p.name, old_level, p.level)
        
        level_msg = f"\n\n🎉 **LEVEL UP!** {old_level} → {p.level}" if p.level > old_level else ""
        await message.reply(f"⚽ **GOAL!** ⚽\n+฿{amount:,}!\n⭐ **+{xp_amount} XP**{level_msg}")
    else:
        p.bounty -= amount
        p.xp -= xp_amount
        old_level = p.level
        level_down_msg = ""
        while p.xp < 0 and p.level > 1:
            p.level -= 1
            p.xp += get_xp_needed(p.level)
            level_down_msg = f"\n\n💀 **LEVEL DOWN!** {old_level} → {p.level}"
        
        if p.level < old_level:
            await send_level_down_notification(user_id, old_level, p.level, "game")
            await send_level_down_group_notification(message.chat.id, p.name, old_level, p.level)
        
        if p.xp < 0:
            p.xp = 0
            p.level = 1
        await message.reply(f"🥅 **MISSED!** 🥅\n-฿{amount:,}!\n⭐ **-{xp_amount} XP**{level_down_msg}")
    
    save_data()
    # ==================== PVP ATTACK COMMAND ====================
@app.on_message(filters.command("attack"))
async def attack_cmd(client, message):
    user_id = message.from_user.id
    can_use, remaining = check_cooldown(user_id, 3)
    if not can_use:
        await message.reply(f"⏰ Slow down! Please wait {remaining} second(s)!")
        return
    if not message.reply_to_message:
        await message.reply("⚔️ **Reply to someone to attack!**")
        return
    
    attacker = get_player(user_id)
    target = get_player(message.reply_to_message.from_user.id)
    
    if target.user_id == user_id:
        await message.reply("❌ You can't attack yourself!")
        return
    
    # ========== PVP MODE CHECK ==========
    if not attacker.pvp_enabled:
        await message.reply(
            f"❌ **You cannot attack!**\n\n"
            f"Your PVP mode is OFF.\n"
            f"Use `/pvp` to turn it ON.\n\n"
            f"🤖 {BOT_NAME}"
        )
        return
    
    if not target.pvp_enabled:
        await message.reply(
            f"❌ **You cannot attack {target.name}!**\n\n"
            f"{target.name} has PVP mode OFF.\n"
            f"They cannot be attacked right now.\n\n"
            f"🤖 {BOT_NAME}"
        )
        return
    
    attacker_name = attacker.name or f"User_{attacker.user_id}"
    target_name = target.name or f"User_{target.user_id}"
    attacker_mention = f"[{attacker_name}](tg://user?id={attacker.user_id})"
    target_mention = f"[{target_name}](tg://user?id={target.user_id})"
    
    # Send fight started message
    fight_msg = await message.reply(f"⚔️ **BATTLE STARTED!** ⚔️\n\n{attacker_mention} vs {target_mention}\n\n📊 Calculating power...", disable_web_page_preview=True)
    await asyncio.sleep(0.5)
    
    # Calculate power
    ap, tp = attacker.level, target.level
    if attacker.haki == "arm":
        ap = int(ap * (1 + attacker.haki_level * 0.3))
    if target.haki == "arm":
        tp = int(tp * (1 + target.haki_level * 0.3))
    
    is_victory = ap > tp
    
    # Store old levels
    attacker_old_level = attacker.level
    target_old_level = target.level
    
    if is_victory:
        # ========== WINNER (Attacker wins) ==========
        if target.passive_enabled and target.shield_level > 0 and target.shield_uses > 0:
            target.shield_uses -= 1
            steal = max(1, int(target.bounty * 0.05))
            shield_msg = f"\n\n🛡️ **{target_name}'s SHIELD activated!** 🛡️\nReduced stolen amount!"
            
            if target.shield_uses == 0:
                target.shield_level = 0
                shield_msg += f"\n💔 {target_name}'s shield broke!"
        else:
            steal = max(1, int(target.bounty * 0.1))
            shield_msg = ""
        
        if steal > target.bounty:
            steal = target.bounty
        
        attacker.bounty += steal
        target.bounty -= steal
        
        # XP calculation
        xp_gain = max(1, steal // 100000)
        if attacker.boost_end > time.time():
            xp_gain = int(xp_gain * 1.5)
        attacker.xp += xp_gain
        
        # Level up for attacker
        while attacker.xp >= get_xp_needed(attacker.level) and attacker.level < 200:
            attacker.xp -= get_xp_needed(attacker.level)
            attacker.level += 1
        
        # XP loss for target
        xp_loss = max(1, steal // 200000)
        target.xp -= xp_loss
        
        # Level down for target
        while target.xp < 0 and target.level > 1:
            target.level -= 1
            target.xp += get_xp_needed(target.level)
        
        if target.xp < 0:
            target.xp = 0
            target.level = 1
        
        save_data()
        
        # Level up/down messages
        level_text = ""
        if attacker.level > attacker_old_level:
            level_text = f"\n\n🎉 **LEVEL UP!** {attacker_old_level} → {attacker.level} 🎉"
        
        target_level_text = ""
        if target.level < target_old_level:
            target_level_text = f"\n\n💀 **{target_name} LEVEL DOWN!** {target_old_level} → {target.level} 💀"
        
        result_text = (
            f"🎉 **VICTORY!** 🎉\n\n"
            f"{attacker_mention} defeated {target_mention}!\n"
            f"{shield_msg}\n\n"
            f"💰 **Stole:** ฿{steal:,}\n"
            f"⭐ **XP Gained:** +{xp_gain}\n"
            f"🏆 **New Bounty:** ฿{attacker.bounty:,}{level_text}{target_level_text}"
        )
        
        # Delete fight started message
        await fight_msg.delete()
        
        # Send result with GIF/Image
        if os.path.exists(WIN_GIF):
            try:
                await message.reply_animation(WIN_GIF, caption=result_text)
            except:
                if os.path.exists(WIN_IMAGE):
                    await message.reply_photo(WIN_IMAGE, caption=result_text)
                else:
                    await message.reply(result_text)
        elif os.path.exists(WIN_IMAGE):
            await message.reply_photo(WIN_IMAGE, caption=result_text)
        else:
            await message.reply(result_text)
        
        # ========== SEND DM WITH CLICKABLE MENTIONS ==========
        # Send DM to winner (attacker) - with target.user_id
        asyncio.create_task(send_pvp_victory_dm(attacker.user_id, attacker_name, target_name, steal, attacker.bounty, attacker_old_level, attacker.level, target.user_id))
        
        # Send DM to loser (target) - with attacker.user_id
        asyncio.create_task(send_pvp_defeat_dm(target.user_id, attacker_name, target_name, steal, target.bounty, target_old_level, target.level, attacker.user_id))
        
        # Level up/down notifications
        if attacker.level > attacker_old_level:
            asyncio.create_task(send_level_up_notification(attacker.user_id, attacker_old_level, attacker.level, "pvp_win"))
            asyncio.create_task(send_level_up_group_notification(message.chat.id, attacker_name, attacker_old_level, attacker.level))
        
        if target.level < target_old_level:
            asyncio.create_task(send_level_down_notification(target.user_id, target_old_level, target.level, "pvp_loss"))
            asyncio.create_task(send_level_down_group_notification(message.chat.id, target_name, target_old_level, target.level))
    
    else:
        # ========== LOSER (Attacker loses) ==========
        if attacker.passive_enabled and attacker.shield_level > 0 and attacker.shield_uses > 0:
            attacker.shield_uses -= 1
            steal = max(1, int(attacker.bounty * 0.05))
            shield_msg = f"\n\n🛡️ **Your SHIELD activated!** 🛡️\nReduced stolen amount!"
            
            if attacker.shield_uses == 0:
                attacker.shield_level = 0
                shield_msg += f"\n💔 Your shield broke!"
        else:
            steal = max(1, int(attacker.bounty * 0.1))
            shield_msg = ""
        
        if steal > attacker.bounty:
            steal = attacker.bounty
        
        target.bounty += steal
        attacker.bounty -= steal
        
        # XP loss for attacker
        xp_loss = max(1, steal // 100000)
        attacker.xp -= xp_loss
        
        # Level down for attacker
        while attacker.xp < 0 and attacker.level > 1:
            attacker.level -= 1
            attacker.xp += get_xp_needed(attacker.level)
        
        if attacker.xp < 0:
            attacker.xp = 0
            attacker.level = 1
        
        # XP gain for target
        xp_gain = max(1, steal // 200000)
        if target.boost_end > time.time():
            xp_gain = int(xp_gain * 1.5)
        target.xp += xp_gain
        
        # Level up for target
        while target.xp >= get_xp_needed(target.level) and target.level < 200:
            target.xp -= get_xp_needed(target.level)
            target.level += 1
        
        save_data()
        
        # Level up/down messages
        level_text = ""
        if attacker.level < attacker_old_level:
            level_text = f"\n\n💀 **LEVEL DOWN!** {attacker_old_level} → {attacker.level} 💀"
        
        target_level_text = ""
        if target.level > target_old_level:
            target_level_text = f"\n\n🎉 **{target_name} LEVEL UP!** {target_old_level} → {target.level} 🎉"
        
        result_text = (
            f"💀 **DEFEAT!** 💀\n\n"
            f"{attacker_mention} lost to {target_mention}!\n"
            f"{shield_msg}\n\n"
            f"💰 **Lost:** ฿ -{steal:,}\n"
            f"⭐ **XP Lost:** -{xp_loss}\n"
            f"🏆 **New Bounty:** ฿{attacker.bounty:,}{level_text}{target_level_text}"
        )
        
        # Delete fight started message
        await fight_msg.delete()
        
        # Send result with GIF/Image
        if os.path.exists(LOSE_GIF):
            try:
                await message.reply_animation(LOSE_GIF, caption=result_text)
            except:
                if os.path.exists(LOSE_IMAGE):
                    await message.reply_photo(LOSE_IMAGE, caption=result_text)
                else:
                    await message.reply(result_text)
        elif os.path.exists(LOSE_IMAGE):
            await message.reply_photo(LOSE_IMAGE, caption=result_text)
        else:
            await message.reply(result_text)
        
        # ========== SEND DM WITH CLICKABLE MENTIONS ==========
        # Send DM to loser (attacker) - with target.user_id
        asyncio.create_task(send_pvp_defeat_dm(attacker.user_id, target_name, attacker_name, steal, attacker.bounty, attacker_old_level, attacker.level, target.user_id))
        
        # Send DM to winner (target) - with attacker.user_id
        asyncio.create_task(send_pvp_victory_dm(target.user_id, target_name, attacker_name, steal, target.bounty, target_old_level, target.level, attacker.user_id))
        
        # Level up/down notifications
        if attacker.level < attacker_old_level:
            asyncio.create_task(send_level_down_notification(attacker.user_id, attacker_old_level, attacker.level, "pvp_loss"))
            asyncio.create_task(send_level_down_group_notification(message.chat.id, attacker_name, attacker_old_level, attacker.level))
        
        if target.level > target_old_level:
            asyncio.create_task(send_level_up_notification(target.user_id, target_old_level, target.level, "pvp_win"))
            asyncio.create_task(send_level_up_group_notification(message.chat.id, target_name, target_old_level, target.level))

            # ==================== VAULT AND SHOP COMMANDS ====================
@app.on_message(filters.command("deposit"))
async def deposit_cmd(client, message):
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: `/deposit [amount]`")
        return
    amount = parse_amount(args[1])
    if amount is None:
        await message.reply("Invalid amount!")
        return
    p = get_player(message.from_user.id)
    cap = VAULT_CAPS.get(p.vault_level, 25000000)
    if amount > p.bounty:
        await message.reply(f"Not enough! You have ฿{p.bounty:,}")
        return
    if p.vault + amount > cap:
        await message.reply(f"Vault full! Capacity: ฿{cap:,}")
        return
    p.bounty -= amount
    p.vault += amount
    save_data()
    await message.reply(f"💰 Deposited ฿{amount:,}!\n📦 Vault: ฿{p.vault:,}\n💵 Bounty: ฿{p.bounty:,}")

@app.on_message(filters.command("dig"))
async def dig_cmd(client, message):
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: `/dig [amount]`")
        return
    amount = parse_amount(args[1])
    if amount is None:
        await message.reply("Invalid amount!")
        return
    p = get_player(message.from_user.id)
    if amount > p.vault:
        await message.reply(f"Not enough! Vault: ฿{p.vault:,}")
        return
    p.vault -= amount
    p.bounty += amount
    save_data()
    await message.reply(f"🏦 Withdrew ฿{amount:,}!\n📦 Vault: ฿{p.vault:,}\n💵 Bounty: ฿{p.bounty:,}")

@app.on_message(filters.command("sell_fruit"))
async def sell_fruit_cmd(client, message):
    p = get_player(message.from_user.id)
    if not p.devil_fruit:
        await message.reply("❌ You don't have a devil fruit!")
        return
    prices = {"Bad": 12500000, "Medium": 25000000, "Good": 500000000}
    refund = prices.get(p.fruit_category, 12500000)
    fruit_name = p.devil_fruit
    p.bounty += refund
    p.devil_fruit = None
    p.fruit_category = None
    save_data()
    await message.reply(f"💰 **Fruit Sold!** 💰\n\n🍎 **Fruit:** {fruit_name}\n💵 **Refund:** ฿{refund:,} (50%)\n🏆 **New Bounty:** ฿{p.bounty:,}")

@app.on_message(filters.command("shop"))
async def shop_cmd(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Haki", callback_data="shop_haki")],
        [InlineKeyboardButton("🛡️ Shield", callback_data="shop_shield")],
        [InlineKeyboardButton("🍎 Devil Fruit", callback_data="shop_fruit")],
        [InlineKeyboardButton("💰 Vault Upgrade", callback_data="shop_vault")],
        [InlineKeyboardButton("⚡ 2x XP (50M)", callback_data="shop_boost")],
        [InlineKeyboardButton("🔄 Switch Haki", callback_data="shop_switch_haki")]
    ])
    shop_text = f"🏴‍☠️ **SHOP** 🏴‍☠️\n\nSelect a category.\n\n🤖 {BOT_NAME}"
    if os.path.exists(SHOP_IMAGE):
        await message.reply_photo(SHOP_IMAGE, caption=shop_text, reply_markup=keyboard)
    else:
        await message.reply(shop_text, reply_markup=keyboard)

# ==================== TRADE AND MYCHARS ====================
@app.on_message(filters.command("mychars"))
async def mychars_cmd(client, message):
    p = get_player(message.from_user.id)
    if not p.captured_chars:
        await message.reply("❌ No captured characters yet!\n\n💡 Fight spawned characters using `/challenge`!")
        return
    text = "📦 **YOUR CAPTURED CHARACTERS** 📦\n\n"
    for i, char in enumerate(p.captured_chars, 1):
        text += f"{i}. {char['name']}\n"
    text += "\n💡 Sell using: `/trade [amount]` (reply to buyer)"
    await message.reply(text)

@app.on_message(filters.command("trade"))
async def trade_cmd(client, message):
    if not message.reply_to_message:
        await message.reply("❌ **Reply to a user to trade!**\n\n**Usage:** `/trade [amount]` (reply to buyer)")
        return
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: `/trade [amount]`")
        return
    amount = parse_amount(args[1])
    if amount is None:
        await message.reply("Invalid amount!")
        return
    seller = get_player(message.from_user.id)
    buyer = get_player(message.reply_to_message.from_user.id)
    if seller.user_id == buyer.user_id:
        await message.reply("❌ Cannot trade with yourself!")
        return
    if not seller.captured_chars:
        await message.reply("❌ You have no captured characters to trade!")
        return
    trade_id = f"{seller.user_id}_{buyer.user_id}_{int(time.time())}"
    pending_trades[trade_id] = {
        "seller_id": seller.user_id, "buyer_id": buyer.user_id, "amount": amount,
        "seller_name": seller.name, "buyer_name": buyer.name,
        "chars": seller.captured_chars.copy(), "selected_char": None
    }
    buttons = []
    for i, char in enumerate(seller.captured_chars):
        buttons.append([InlineKeyboardButton(f"📦 {char['name']}", callback_data=f"trade_select_{trade_id}_{i}")])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data=f"trade_cancel_{trade_id}")])
    await message.reply(f"📦 **TRADE OFFER** 📦\n\n💰 Amount: ฿{amount:,}\n🏴‍☠️ Seller: {seller.name}\n👤 Buyer: {buyer.name}\n\nSelect character:", reply_markup=InlineKeyboardMarkup(buttons))
    # ==================== CHARACTER SPAWN SYSTEM ====================
async def spawn_character(chat_id, chat_name):
    global active_challenges
    is_mythical = random.random() < 0.1 and mythical_characters
    if is_mythical and mythical_characters:
        char = random.choice(mythical_characters)
        msg = f"⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️\n**⚠️ MYTHICAL CHARACTER APPEARED!**\n⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️\n\n👹 **Character:** ???\n💀 **Type:** MYTHICAL\n🏆 **Reward:** 10,000,000,000 Bounty + ⚜️1 Token!\n\n⏰ **Despawns in:** 5 minutes or 150 messages!\n\n❓ Type `/challenge [name]` to fight!"
        active_challenges[chat_id] = {
            "char": char,
            "is_mythical": True,
            "challenger": None,
            "spawn_time": time.time(),
            "message_count": 0,
            "chat_name": chat_name
        }
        if char.get("image") and os.path.exists(char.get("image", "")):
            await app.send_photo(chat_id, char["image"], caption=msg)
        else:
            await app.send_message(chat_id, msg)
    elif normal_characters:
        char = random.choice(normal_characters)
        msg = f"🏴‍☠️ **A Wild Character Appeared!** 🏴‍☠️\n\n👤 **Character:** ???\n⭐ **Type:** Normal\n💰 **Reward:** Random Bounty + XP\n\n⏰ **Despawns in:** 5 minutes or 150 messages!\n\n❓ Type `/challenge [name]` to fight!"
        active_challenges[chat_id] = {
            "char": char,
            "is_mythical": False,
            "challenger": None,
            "spawn_time": time.time(),
            "message_count": 0,
            "chat_name": chat_name
        }
        if char.get("image") and os.path.exists(char.get("image", "")):
            await app.send_photo(chat_id, char["image"], caption=msg)
        else:
            await app.send_message(chat_id, msg)

@app.on_message(filters.group, group=-1)
async def message_counter(client, message):
    global message_count, active_challenges
    if message.from_user and not message.from_user.is_bot:
        group_id = message.chat.id
        message_count[group_id] = message_count.get(group_id, 0) + 1
        if message_count[group_id] >= 150:
            message_count[group_id] = 0
            if group_id not in active_challenges:
                await spawn_character(group_id, message.chat.title or "Group")
        if group_id in active_challenges:
            active_challenges[group_id]["message_count"] = active_challenges[group_id].get("message_count", 0) + 1
            if active_challenges[group_id]["message_count"] >= 150:
                char_name = active_challenges[group_id]["char"]["name"]
                await app.send_message(group_id, f"💨 **{char_name}** got tired of waiting and left! 💨")
                del active_challenges[group_id]
    message.continue_propagation()

async def despawn_checker():
    while True:
        await asyncio.sleep(60)
        current_time = time.time()
        expired = []
        for chat_id, challenge in active_challenges.items():
            if current_time - challenge["spawn_time"] >= 300:
                expired.append(chat_id)
        for chat_id in expired:
            char_name = active_challenges[chat_id]["char"]["name"]
            try:
                await app.send_message(chat_id, f" **{char_name}**has left the island 💨")
            except:
                pass
            del active_challenges[chat_id]

@app.on_message(filters.command("challenge"))
async def challenge_cmd(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if chat_id not in active_challenges:
        await message.reply("❌ **No character to challenge!**\n\n💡 Wait for a character to appear (every 150 messages).")
        return
    
    challenge = active_challenges[chat_id]
    if challenge["challenger"] is not None:
        await message.reply("⚠️ Someone is already challenging this character!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply(
            f"❌ **You must guess the character name!**\n\n"
            f"⚔️ Type `/challenge [name]` to fight!\n"
            f"💡 Try using partial names!\n\n"
            f"🤖 {BOT_NAME}"
        )
        return
    
    guessed = " ".join(args[1:]).lower()
    actual_name = challenge["char"]["name"].lower()
    actual_parts = actual_name.split()
    
    is_match = False
    match_type = ""
    
    if guessed == actual_name:
        is_match = True
        match_type = "exact"
    elif guessed in actual_parts:
        is_match = True
        match_type = "partial word"
    elif len(guessed) >= 3 and (actual_name.startswith(guessed) or actual_name.endswith(guessed) or guessed in actual_name):
        is_match = True
        match_type = "partial"
    
    if not is_match:
        # WRONG GUESS - No hint, just try again
        time_left = max(0, 300 - (time.time() - challenge["spawn_time"]))
        minutes_left = int(time_left // 60)
        seconds_left = int(time_left % 60)
        
        await message.reply(
            f"❌ **Wrong guess!**\n\n"
            f"⏰ **Time remaining:** {minutes_left}m {seconds_left}s\n"
            f"🎯 **Try again!** The character is still here.\n\n"
            f"🤖 {BOT_NAME}"
        )
        # DO NOT delete the character - keep it for another try
        return
    
    # CORRECT GUESS - Challenge starts
    challenge["challenger"] = user_id
    p = get_player(user_id)
    
    match_message = "exact" if match_type == "exact" else f"using partial name (`{guessed}`)"
    await message.reply(f"⚔️ **{message.from_user.first_name}** challenges **{challenge['char']['name']}**! ({match_message})\n💪 Fighting...")
    await asyncio.sleep(1.5)
    
    if challenge["is_mythical"]:
        win_chance = min(0.8, 0.1 + (p.level / 500) + (p.haki_level * 0.05))
        reward_bounty, reward_xp, reward_token = 10000000000, 5000, 1
    else:
        win_chance = min(0.95, 0.4 + (p.level / 200) + (p.haki_level * 0.05))
        reward_bounty, reward_xp, reward_token = random.randint(10000, 500000), random.randint(50, 500), 0
    
    win = random.random() < win_chance
    
    if win:
        p.bounty += reward_bounty
        p.xp += reward_xp
        p.advanced_token += reward_token
        old_level = p.level
        while p.xp >= get_xp_needed(p.level) and p.level < 200:
            p.xp -= get_xp_needed(p.level)
            p.level += 1
        if not challenge["is_mythical"]:
            p.captured_chars.append(challenge["char"])
        save_data()
        
        if p.level > old_level:
            await send_level_up_notification(user_id, old_level, p.level, "challenge")
            await send_level_up_group_notification(message.chat.id, p.name, old_level, p.level)
        
        reward_text = f"💰 Bounty: +{reward_bounty:,}\n⭐ XP: +{reward_xp}"
        if reward_token:
            reward_text += f"\n🔮 Advanced Token: +⚜️1"
        level_text = f"\n\n🎉 **LEVEL UP!** {old_level} → {p.level}" if p.level > old_level else ""
        await message.reply(f"🎉 **VICTORY!** 🎉\n\n⚔️ You defeated **{challenge['char']['name']}**!\n\n🏆 **Rewards:**\n{reward_text}{level_text}")
    else:
        # Lose - lose XP
        xp_loss = max(1, reward_xp // 2)
        p.xp -= xp_loss
        old_level = p.level
        while p.xp < 0 and p.level > 1:
            p.level -= 1
            p.xp += get_xp_needed(p.level)
        if p.xp < 0:
            p.xp = 0
            p.level = 1
        save_data()
        
        if p.level < old_level:
            await send_level_down_notification(user_id, old_level, p.level, "challenge")
            await send_level_down_group_notification(message.chat.id, p.name, old_level, p.level)
        
        level_text = f"\n\n💀 **LEVEL DOWN!** {old_level} → {p.level}" if p.level < old_level else ""
        await message.reply(f"💀 **DEFEAT!** 💀\n\n😢 You were defeated by **{challenge['char']['name']}**!\n\n⭐ **-{xp_loss} XP**{level_text}\n\n💪 Level up and try again!")
    
    # Delete character only after the fight (win or lose)
    del active_challenges[chat_id]

@app.on_message(filters.command("timeleft"))
async def timeleft_cmd(client, message):
    chat_id = message.chat.id
    if chat_id not in active_challenges:
        await message.reply("❌ No active character in this chat!")
        return
    
    challenge = active_challenges[chat_id]
    current_time = time.time()
    time_passed = current_time - challenge["spawn_time"]
    time_left = max(0, 300 - time_passed)
    minutes_left = int(time_left // 60)
    seconds_left = int(time_left % 60)
    messages_used = challenge.get("message_count", 0)
    messages_left = max(0, 150 - messages_used)
    
    await message.reply(
        f"⏰ **Character Status** ⏰\n\n"
        f"👤 **Character:** {challenge['char']['name']}\n"
        f"⭐ **Type:** {'MYTHICAL' if challenge['is_mythical'] else 'Normal'}\n\n"
        f"📊 **Time remaining:** {minutes_left}m {seconds_left}s\n"
        f"💬 **Messages until despawn:** {messages_left}\n\n"
        f"💡 Use `/challenge [name]` to fight!"
    )
    # ==================== CLAIM COMMAND WITH BUTTON ====================
@app.on_message(filters.command("claim"))
async def claim_cmd(client, message):
    p = get_player(message.from_user.id)
    
    if message.chat.id != MAIN_GROUP_ID:
        join_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Join Main Group", url=MAIN_GROUP_LINK)],
            [InlineKeyboardButton("🔄 Try Again", callback_data="try_claim")]
        ])
        await message.reply(
            f"❌ **This command can only be used in the main group!**\n\n"
            f"🔗 **Please join our main group first:**\n{MAIN_GROUP_LINK}\n\n"
            f"After joining, click the button below to claim.",
            reply_markup=join_button,
            disable_web_page_preview=True
        )
        return
    
    if p.claimed_main:
        await message.reply("❌ You have already claimed this reward!")
        return
    
    p.claimed_main = True
    p.bounty += 3000000
    p.xp += 200
    p.boost_end = max(p.boost_end, time.time() + 900)
    
    old_level = p.level
    while p.xp >= get_xp_needed(p.level) and p.level < 200:
        p.xp -= get_xp_needed(p.level)
        p.level += 1
    
    save_data()
    
    if p.level > old_level:
        await send_level_up_notification(message.from_user.id, old_level, p.level, "claim")
        await send_level_up_group_notification(message.chat.id, p.name, old_level, p.level)
    
    level_text = f"\n\n🎉 **LEVEL UP!** {old_level} → {p.level}" if p.level > old_level else ""
    
    await message.reply(
        f"🎁 **CLAIM REWARD!** 🎁\n\n"
        f"✅ Claimed successfully!\n"
        f"💰 +3,000,000 Bounty\n"
        f"⭐ +200 XP\n"
        f"⚡ 2x XP Boost (15 minutes){level_text}\n\n"
        f"🏆 Bounty: ฿{p.bounty:,}\n"
        f"⚔️ Level: {p.level}\n\n"
        f"🤖 {BOT_NAME}"
    )
    # ==================== PVP ON/OFF COMMAND ====================
@app.on_message(filters.command("pvp"))
async def pvp_cmd(client, message):
    p = get_player(message.from_user.id)
    
    p.pvp_enabled = not p.pvp_enabled
    save_data()
    
    if p.pvp_enabled:
        await message.reply(
            f"⚔️ **PVP MODE: ON** ⚔️\n\n"
            f"✅ You can now attack and be attacked by other players!\n"
            f"💰 You can steal and be stolen from.\n\n"
            f"Use `/pvp` again to turn OFF.\n\n"
            f"🤖 {BOT_NAME}"
        )
    else:
        await message.reply(
            f"🛡️ **PVP MODE: OFF** 🛡️\n\n"
            f"❌ You cannot attack or be attacked by other players!\n"
            f"💰 Your bounty is safe from PVP.\n\n"
            f"Use `/pvp` again to turn ON.\n\n"
            f"🤖 {BOT_NAME}"
        )

# ==================== PASSIVE ON/OFF COMMAND ====================
@app.on_message(filters.command("passive"))
async def passive_cmd(client, message):
    p = get_player(message.from_user.id)
    
    p.passive_enabled = not p.passive_enabled
    save_data()
    
    if p.passive_enabled:
        await message.reply(
            f"🛡️ **PASSIVE MODE: ON** 🛡️\n\n"
            f"✅ Your shield will now protect you in PVP battles!\n"
            f"💡 Shield reduces stolen bounty by 50%\n\n"
            f"Use `/passive` again to turn OFF.\n\n"
            f"🤖 {BOT_NAME}"
        )
    else:
        await message.reply(
            f"⚔️ **PASSIVE MODE: OFF** ⚔️\n\n"
            f"❌ Your shield will NOT protect you in PVP battles!\n"
            f"💡 You can still use shield items from shop.\n\n"
            f"Use `/passive` again to turn ON.\n\n"
            f"🤖 {BOT_NAME}"
        )
        # ==================== CALLBACK HANDLER ====================
@app.on_callback_query()
async def handle_callback(client, callback):
    try:
        p = get_player(callback.from_user.id)
        data = callback.data
        
        # ========== TRY CLAIM CALLBACK ==========
        if data == "try_claim":
            if callback.message.chat.id == MAIN_GROUP_ID:
                if p.claimed_main:
                    await callback.message.edit_text("❌ You have already claimed this reward!")
                else:
                    p.claimed_main = True
                    p.bounty += 3000000
                    p.xp += 200
                    p.boost_end = max(p.boost_end, time.time() + 900)
                    
                    old_level = p.level
                    while p.xp >= get_xp_needed(p.level) and p.level < 200:
                        p.xp -= get_xp_needed(p.level)
                        p.level += 1
                    
                    save_data()
                    
                    if p.level > old_level:
                        await send_level_up_notification(callback.from_user.id, old_level, p.level, "claim")
                        await send_level_up_group_notification(callback.message.chat.id, p.name, old_level, p.level)
                    
                    level_text = f"\n\n🎉 **LEVEL UP!** {old_level} → {p.level}" if p.level > old_level else ""
                    
                    await callback.message.edit_text(
                        f"🎁 **CLAIM REWARD!** 🎁\n\n"
                        f"✅ Claimed successfully!\n"
                        f"💰 +3,000,000 Bounty\n"
                        f"⭐ +200 XP\n"
                        f"⚡ 2x XP Boost (15 minutes){level_text}\n\n"
                        f"🏆 Bounty: ฿{p.bounty:,}\n"
                        f"⚔️ Level: {p.level}\n\n"
                        f"🤖 {BOT_NAME}"
                    )
                await callback.answer("Reward claimed!")
            else:
                join_button = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 Join Main Group", url=MAIN_GROUP_LINK)],
                    [InlineKeyboardButton("🔄 Try Again", callback_data="try_claim")]
                ])
                await callback.message.edit_text(
                    f"❌ **You still need to join the main group!**\n\n"
                    f"🔗 {MAIN_GROUP_LINK}\n\n"
                    f"After joining, click the button below to claim.",
                    reply_markup=join_button
                )
                await callback.answer("Please join the group first!", show_alert=True)
            return
        
        # ========== TRADE CALLBACKS ==========
        if data.startswith("trade_select_"):
            parts = data.split("_")
            trade_id = f"{parts[2]}_{parts[3]}_{parts[4]}"
            char_index = int(parts[5])
            if trade_id not in pending_trades:
                await callback.answer("❌ Trade expired!", show_alert=True)
                return
            trade = pending_trades[trade_id]
            selected_char = trade["chars"][char_index]
            trade["selected_char"] = selected_char
            trade_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Buy", callback_data=f"trade_confirm_{trade_id}")],
                [InlineKeyboardButton("❌ Cancel", callback_data=f"trade_cancel_{trade_id}")]
            ])
            await callback.message.reply(f"🎁 **Character:** {selected_char['name']}\n💰 **Price:** ฿{trade['amount']:,}\n🏴‍☠️ **Seller:** {trade['seller_name']}\n\nConfirm?", reply_markup=trade_keyboard)
            await callback.answer()
            await callback.message.delete()
            return
        
        if data.startswith("trade_confirm_"):
            trade_id = data.replace("trade_confirm_", "")
            if trade_id not in pending_trades:
                await callback.answer("❌ Trade expired!", show_alert=True)
                return
            trade = pending_trades[trade_id]
            if callback.from_user.id != trade["buyer_id"]:
                await callback.answer("❌ Only buyer can confirm!", show_alert=True)
                return
            seller = get_player(trade["seller_id"])
            buyer = get_player(trade["buyer_id"])
            if buyer.bounty < trade["amount"]:
                await callback.answer(f"❌ Buyer needs ฿{trade['amount']:,}!", show_alert=True)
                return
            buyer.bounty -= trade["amount"]
            seller.bounty += trade["amount"]
            seller.captured_chars.remove(trade["selected_char"])
            buyer.captured_chars.append(trade["selected_char"])
            save_data()
            del pending_trades[trade_id]
            await callback.message.edit_text(f"✅ **TRADE COMPLETED!**\n\n🎁 {trade['selected_char']['name']}\n💰 ฿{trade['amount']:,}\n🏴‍☠️ New Owner: {buyer.name}")
            await callback.answer("Trade completed!", show_alert=True)
            return
        
        if data.startswith("trade_cancel_"):
            trade_id = data.replace("trade_cancel_", "")
            if trade_id in pending_trades:
                del pending_trades[trade_id]
            await callback.message.edit_text("❌ Trade cancelled!")
            await callback.answer("Cancelled!", show_alert=True)
            return
        
        # ========== SHOP BACK BUTTON ==========
        if data == "shop_back":
            back_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⚔️ Haki", callback_data="shop_haki")],
                [InlineKeyboardButton("🛡️ Shield", callback_data="shop_shield")],
                [InlineKeyboardButton("🍎 Fruit", callback_data="shop_fruit")],
                [InlineKeyboardButton("💰 Vault", callback_data="shop_vault")],
                [InlineKeyboardButton("⚡ 2x XP", callback_data="shop_boost")],
                [InlineKeyboardButton("🔄 Switch Haki", callback_data="shop_switch_haki")]
            ])
            await callback.message.edit_text(f"🏴‍☠️ **SHOP**\n\nSelect category.\n🤖 {BOT_NAME}", reply_markup=back_keyboard)
            await callback.answer()
            return
        
        # ========== SHOP CALLBACKS ==========
        if data == "shop_haki":
            haki_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👁️ Observation (25M)", callback_data="buy_haki_obv")],
                [InlineKeyboardButton("⚔️ Armament (25M)", callback_data="buy_haki_arm")],
                [InlineKeyboardButton("👑 Conqueror (25M)", callback_data="buy_haki_conq")],
                [InlineKeyboardButton("◀️ Back", callback_data="shop_back")]
            ])
            await callback.message.edit_text("⚔️ **HAKI SHOP**\n\nSelect type:", reply_markup=haki_keyboard)
            await callback.answer()
            return
        
        if data == "shop_shield":
            shield_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🛡️ Lv1 (25M)", callback_data="buy_shield_1")],
                [InlineKeyboardButton("🛡️ Lv2 (250M)", callback_data="buy_shield_2")],
                [InlineKeyboardButton("🛡️ Lv3 (25B)", callback_data="buy_shield_3")],
                [InlineKeyboardButton("◀️ Back", callback_data="shop_back")]
            ])
            await callback.message.edit_text("🛡️ **SHIELD SHOP**\n\nSelect level:", reply_markup=shield_keyboard)
            await callback.answer()
            return
        
        if data == "shop_fruit":
            fruit_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🍎 Basic (25M)", callback_data="buy_fruit_1")],
                [InlineKeyboardButton("🍎 Rare (250M)", callback_data="buy_fruit_2")],
                [InlineKeyboardButton("🍎 Legendary (25B)", callback_data="buy_fruit_3")],
                [InlineKeyboardButton("◀️ Back", callback_data="shop_back")]
            ])
            await callback.message.edit_text("🍎 **FRUIT SHOP**\n\nChoose gamble tier:", reply_markup=fruit_keyboard)
            await callback.answer()
            return
        
        if data == "shop_vault":
            vault_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Lv2 (25B)", callback_data="buy_vault_2")],
                [InlineKeyboardButton("💰 Lv3 (500B)", callback_data="buy_vault_3")],
                [InlineKeyboardButton("◀️ Back", callback_data="shop_back")]
            ])
            await callback.message.edit_text("💰 **VAULT SHOP**\n\nUpgrade capacity:", reply_markup=vault_keyboard)
            await callback.answer()
            return
        
        if data == "shop_boost":
            await callback.message.edit_text("⚡ **2x XP Boost**\n\nPrice: 50,000,000\n\nUse `/shop` and select Boost to purchase.")
            await callback.answer()
            return
        
        if data == "shop_switch_haki":
            current_haki = p.haki if p.haki else "None"
            current_name = HAKI_NAMES.get(p.haki, "None") if p.haki else "None"
            
            switch_keyboard = []
            haki_options = [
                ("None", "switch_haki_none", "❌ None"),
                ("Observation", "switch_haki_obv", "👁️ Observation"),
                ("Armament", "switch_haki_arm", "⚔️ Armament"),
                ("Conqueror's", "switch_haki_conq", "👑 Conqueror's")
            ]
            
            for name, cb, display in haki_options:
                if (name == "None" and p.haki is None) or (name.lower() == p.haki):
                    switch_keyboard.append([InlineKeyboardButton(f"✅ {display} (Current)", callback_data=cb)])
                else:
                    switch_keyboard.append([InlineKeyboardButton(display, callback_data=cb)])
            
            switch_keyboard.append([InlineKeyboardButton("◀️ Back", callback_data="shop_back")])
            
            await callback.message.edit_text(
                f"🔄 **SWITCH HAKI** 🔄\n\n"
                f"Current: **{current_name}** Lv.{p.haki_level if p.haki else ''}\n\n"
                f"Select a new Haki type (costs 5M to switch):",
                reply_markup=InlineKeyboardMarkup(switch_keyboard)
            )
            await callback.answer()
            return
        
        if data.startswith("switch_haki_"):
            haki_type = data.replace("switch_haki_", "")
            if (haki_type == "none" and p.haki is None) or (haki_type != "none" and p.haki == haki_type):
                await callback.answer("❌ You already have this Haki!", show_alert=True)
                return
            if p.bounty < 5000000:
                await callback.answer(f"❌ Need 5M to switch Haki! You have {p.bounty:,}", show_alert=True)
                return
            
            p.bounty -= 5000000
            
            if haki_type == "none":
                p.haki = None
                p.haki_level = 0
                await callback.message.edit_text(f"✅ **Haki Removed!**\n\n💰 You paid 5,000,000.\n🏆 New Bounty: ฿{p.bounty:,}")
            else:
                p.haki = haki_type
                if p.haki_level == 0:
                    p.haki_level = 1
                await callback.message.edit_text(f"✅ **Haki Switched to {HAKI_NAMES.get(haki_type, haki_type)}!**\n\n💰 You paid 5,000,000.\n🏆 New Bounty: ฿{p.bounty:,}")
            
            save_data()
            await callback.answer("Haki switched!", show_alert=True)
            return
        
        # ========== BUY HAKI ==========
        if data.startswith("buy_haki_"):
            haki_type = data.replace("buy_haki_", "")
            price = 25000000
            haki_display = {"obv": "Observation", "arm": "Armament", "conq": "Conqueror's"}[haki_type]
            
            if p.haki:
                await callback.answer(f"You already have {HAKI_NAMES.get(p.haki, 'a Haki')}! Use Switch Haki to change.", show_alert=True)
                return
            if p.bounty < price:
                await callback.answer(f"Need 25M! You have {p.bounty:,}", show_alert=True)
                return
            
            confirm_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_haki_{haki_type}")],
                [InlineKeyboardButton("❌ Cancel", callback_data="shop_haki")]
            ])
            await callback.message.edit_text(
                f"👁️ **Confirm Purchase** 👁️\n\n"
                f"Item: **{haki_display} Haki**\n"
                f"Price: **25,000,000**\n"
                f"Your Bounty: **{p.bounty:,}**\n\n"
                f"Are you sure?",
                reply_markup=confirm_keyboard
            )
            await callback.answer()
            return
        
        if data.startswith("confirm_haki_"):
            haki_type = data.replace("confirm_haki_", "")
            if p.bounty >= 25000000 and not p.haki:
                p.bounty -= 25000000
                p.haki = haki_type
                p.haki_level = 1
                save_data()
                await callback.message.edit_text(f"✅ **You got {HAKI_NAMES.get(haki_type, haki_type)} Haki!**\n\n💰 Left: ฿{p.bounty:,}")
                await callback.answer("Haki obtained!", show_alert=True)
            else:
                await callback.answer("Purchase failed!", show_alert=True)
            return
        
        # ========== BUY SHIELD ==========
        if data.startswith("buy_shield_"):
            level = int(data.split("_")[2])
            price = {1: 25000000, 2: 250000000, 3: 25000000000}[level]
            if p.bounty < price:
                await callback.answer(f"Need {price:,} bounty!", show_alert=True)
                return
            
            confirm_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_shield_{level}")],
                [InlineKeyboardButton("❌ Cancel", callback_data="shop_shield")]
            ])
            await callback.message.edit_text(
                f"🛡️ **Confirm Purchase** 🛡️\n\n"
                f"Item: **Shield Lv{level}**\n"
                f"Price: **{price:,}**\n"
                f"Your Bounty: **{p.bounty:,}**\n\n"
                f"Are you sure?",
                reply_markup=confirm_keyboard
            )
            await callback.answer()
            return
        
        if data.startswith("confirm_shield_"):
            level = int(data.split("_")[2])
            price = {1: 25000000, 2: 250000000, 3: 25000000000}[level]
            if p.bounty >= price:
                p.bounty -= price
                p.shield_level = level
                p.shield_uses = 3
                save_data()
                await callback.message.edit_text(f"✅ **Shield Lv{level} obtained!** 🛡️\n\n💰 Left: ฿{p.bounty:,}")
                await callback.answer("Shield obtained!", show_alert=True)
            else:
                await callback.answer("Purchase failed!", show_alert=True)
            return
        
        # ========== BUY FRUIT ==========
        if data.startswith("buy_fruit_"):
            tier = int(data.split("_")[2])
            price = {1: 25000000, 2: 250000000, 3: 25000000000}[tier]
            if p.bounty < price:
                await callback.answer(f"Need {price:,} bounty!", show_alert=True)
                return
            if p.devil_fruit:
                await callback.answer("You already have a fruit! Sell it first.", show_alert=True)
                return
            
            confirm_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_fruit_{tier}")],
                [InlineKeyboardButton("❌ Cancel", callback_data="shop_fruit")]
            ])
            await callback.message.edit_text(
                f"🍎 **Confirm Purchase** 🍎\n\n"
                f"Price: **{price:,}**\n"
                f"Your Bounty: **{p.bounty:,}**\n\n"
                f"⚠️ You will get a random fruit!\n\n"
                f"Are you sure?",
                reply_markup=confirm_keyboard
            )
            await callback.answer()
            return
        
        if data.startswith("confirm_fruit_"):
            tier = int(data.split("_")[2])
            price = {1: 25000000, 2: 250000000, 3: 25000000000}[tier]
            if p.bounty >= price and not p.devil_fruit:
                p.bounty -= price
                fruit, category = get_random_fruit(tier)
                p.devil_fruit = fruit["full"]
                p.fruit_category = category
                save_data()
                emoji = "☄️" if category == "Good" else "⚡" if category == "Medium" else "🌀"
                await callback.message.edit_text(f"{emoji} **You got {fruit['full']}!** {emoji}\n\n💰 Left: ฿{p.bounty:,}")
                await callback.answer(f"You got {fruit['full']}!", show_alert=True)
            else:
                await callback.answer("Purchase failed!", show_alert=True)
            return
        
        # ========== BUY VAULT ==========
        if data.startswith("buy_vault_"):
            level = int(data.split("_")[2])
            price = {2: 25000000000, 3: 500000000000}[level]
            if level > p.vault_level and p.bounty >= price:
                confirm_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_vault_{level}")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="shop_vault")]
                ])
                await callback.message.edit_text(
                    f"💰 **Confirm Upgrade** 💰\n\n"
                    f"Item: **Vault Lv{level}**\n"
                    f"Capacity: **{VAULT_CAPS[level]:,}**\n"
                    f"Price: **{price:,}**\n"
                    f"Your Bounty: **{p.bounty:,}**\n\n"
                    f"Are you sure?",
                    reply_markup=confirm_keyboard
                )
                await callback.answer()
                return
            else:
                await callback.answer(f"Need {price:,} bounty!", show_alert=True)
            return
        
        if data.startswith("confirm_vault_"):
            level = int(data.split("_")[2])
            price = {2: 25000000000, 3: 500000000000}[level]
            if level > p.vault_level and p.bounty >= price:
                p.bounty -= price
                p.vault_level = level
                save_data()
                await callback.message.edit_text(f"✅ **Vault upgraded to Lv{level}!** 💰\n\nCapacity: **{VAULT_CAPS[level]:,}**\n💰 Left: ฿{p.bounty:,}")
                await callback.answer("Vault upgraded!", show_alert=True)
            else:
                await callback.answer("Upgrade failed!", show_alert=True)
            return
        
        await callback.answer("Loading...", show_alert=False)
        
    except Exception as e:
        print(f"Callback error: {e}")
        try:
            await callback.answer("An error occurred!", show_alert=True)
        except:
            pass
            # ==================== GIVEAWAY SYSTEM ====================
def calculate_tiered_prizes(total_prize, winner_count):
    prizes = {}
    if winner_count >= 1:
        prizes[1] = int(total_prize * 0.50)
    if winner_count >= 2:
        prizes[2] = int(total_prize * 0.20)
    if winner_count >= 3:
        prizes[3] = int(total_prize * 0.10)
    if winner_count >= 4:
        remaining = int(total_prize * 0.20)
        remaining_winners = winner_count - 3
        prize_per_winner = remaining // remaining_winners
        for i in range(4, winner_count + 1):
            prizes[i] = prize_per_winner
        total_given = prizes[1] + prizes[2] + prizes[3] + (prize_per_winner * remaining_winners)
        leftover = total_prize - total_given
        if leftover > 0 and winner_count >= 4:
            prizes[4] += leftover
    return prizes

async def end_tiered_giveaway_task(msg_id, duration):
    await asyncio.sleep(duration)
    if msg_id not in active_giveaways:
        return
    giveaway = active_giveaways[msg_id]
    participants = giveaway["participants"]
    winner_count = min(giveaway["winner_count"], len(participants))
    prizes = giveaway["prizes"]
    if len(participants) == 0:
        try:
            await app.send_message(giveaway["chat_id"], f"❌ **Giveaway Ended!**\n\n📦 Total Prize: ฿{giveaway['total_prize']:,}\n😢 No one joined!")
        except:
            pass
        del active_giveaways[msg_id]
        return
    shuffled = participants.copy()
    random.shuffle(shuffled)
    winners = shuffled[:winner_count]
    winner_details = []
    for position, winner_id in enumerate(winners, 1):
        if position in prizes:
            prize_amount = prizes[position]
        else:
            prize_amount = 0
        if prize_amount > 0:
            p = get_player(winner_id)
            p.bounty += prize_amount
            save_data()
        try:
            user = await app.get_users(winner_id)
            mention = f"[{user.first_name}](tg://user?id={winner_id})"
        except:
            mention = f"User `{winner_id}`"
        suffix = "st" if position == 1 else "nd" if position == 2 else "rd" if position == 3 else "th"
        medal = "🥇" if position == 1 else "🥈" if position == 2 else "🥉" if position == 3 else "🎖️"
        winner_details.append(f"{medal} **{position}{suffix}** - {mention} → ฿{prize_amount:,}")
    winner_text = "\n".join(winner_details)
    result_text = (
        f"🎊 **TIERED GIVEAWAY ENDED!** 🎊\n\n"
        f"📦 **Total Prize:** ฿{giveaway['total_prize']:,}\n"
        f"🎁 **Description:** {giveaway['description']}\n"
        f"👥 **Total Participants:** {len(participants)}\n\n"
        f"🏆 **WINNERS:**\n{winner_text}\n\n✨ Congratulations! ✨"
    )
    try:
        await app.send_message(giveaway["chat_id"], result_text, disable_web_page_preview=True)
    except:
        pass
    del active_giveaways[msg_id]

@app.on_message(filters.command("tgiveaway") & filters.group)
async def start_tiered_giveaway(client, message):
    if not is_admin_or_owner(message.from_user.id):
        await message.reply("❌ **Admin Only Command!**")
        return
    args = message.text.split(maxsplit=4)
    if len(args) < 4:
        await message.reply(
            "🏆 **TIERED GIVEAWAY** 🏆\n\n"
            "**Prize Distribution:**\n"
            "• 🥇 1st: 50%\n• 🥈 2nd: 20%\n• 🥉 3rd: 10%\n• 4th-10th: Remaining 20%\n\n"
            "**Command:** `/tgiveaway [time] [prize] [winners] [desc]`\n\n"
            "**Examples:**\n`/tgiveaway 10m 10000000 10 Grand Prize`\n`/tgiveaway 1h 50000000 5 Special Event`"
        )
        return
    time_str = args[1].lower()
    total_prize = parse_amount(args[2])
    winner_count = int(args[3]) if args[3].isdigit() else 10
    description = " ".join(args[4:]) if len(args) > 4 else "Tiered Giveaway!"
    if total_prize is None or total_prize <= 0:
        await message.reply("❌ Invalid prize amount!")
        return
    if winner_count < 1:
        winner_count = 1
    if winner_count > 10:
        winner_count = 10
    time_map = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    unit = time_str[-1]
    if unit not in time_map:
        await message.reply("❌ Invalid time format! Use: `30s`, `5m`, `1h`, `1d`")
        return
    try:
        duration = int(time_str[:-1]) * time_map[unit]
    except:
        await message.reply("❌ Invalid time value!")
        return
    if duration < 10:
        await message.reply("❌ Giveaway must be at least 10 seconds!")
        return
    end_time = time.time() + duration
    prizes = calculate_tiered_prizes(total_prize, winner_count)
    prize_text = "🏆 **PRIZE DISTRIBUTION** 🏆\n\n"
    for place, amount in prizes.items():
        if place == 1:
            prize_text += f"🥇 **1st Place:** ฿{amount:,} (50%)\n"
        elif place == 2:
            prize_text += f"🥈 **2nd Place:** ฿{amount:,} (20%)\n"
        elif place == 3:
            prize_text += f"🥉 **3rd Place:** ฿{amount:,} (10%)\n"
        else:
            prize_text += f"🎖️ **{place}th Place:** ฿{amount:,}\n"
    time_text = ""
    if unit == "s":
        time_text = f"{int(time_str[:-1])} seconds"
    elif unit == "m":
        time_text = f"{int(time_str[:-1])} minutes"
    elif unit == "h":
        time_text = f"{int(time_str[:-1])} hours"
    else:
        time_text = f"{int(time_str[:-1])} days"
    giveaway_text = (
        f"🎉 **TIERED GIVEAWAY!** 🎉\n\n"
        f"📦 **Total Prize:** ฿{total_prize:,}\n"
        f"🎁 **Description:** {description}\n"
        f"👥 **Winners:** {winner_count} (1st to {winner_count}th)\n"
        f"⏰ **Ends in:** {time_text}\n\n{prize_text}\n\n💫 **Click below to join!**"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Join Giveaway", callback_data="join_tgiveaway")],
        [InlineKeyboardButton("👥 View Participants", callback_data="view_tparticipants")]
    ])
    sent_msg = await message.reply(giveaway_text, reply_markup=keyboard)
    active_giveaways[sent_msg.id] = {
        "chat_id": message.chat.id, "total_prize": total_prize, "description": description,
        "end_time": end_time, "participants": [], "winner_count": winner_count, "prizes": prizes,
        "message_id": sent_msg.id, "started_by": message.from_user.id, "is_tiered": True
    }
    asyncio.create_task(end_tiered_giveaway_task(sent_msg.id, duration))
    await message.reply(f"✅ **Giveaway Started!**\n\n⏰ {time_text}\n💰 ฿{total_prize:,}\n👥 {winner_count} winners")

@app.on_message(filters.command("join"))
async def join_giveaway_by_command(client, message):
    active = None
    for msg_id, g in active_giveaways.items():
        if g["chat_id"] == message.chat.id:
            active = g
            break
    if not active:
        await message.reply("❌ No active giveaway in this chat!")
        return
    user_id = message.from_user.id
    if user_id in active["participants"]:
        await message.reply("✅ You already joined this giveaway!")
        return
    active["participants"].append(user_id)
    await message.reply(f"✅ **You joined the giveaway!**\n\n📦 Prize: ฿{active['total_prize']:,}\n👥 Total: {len(active['participants'])}")

# Giveaway Callbacks - Add to callback handler
async def join_tgiveaway_callback(callback):
    msg_id = callback.message.id
    if msg_id not in active_giveaways:
        await callback.answer("❌ This giveaway has ended!", show_alert=True)
        return
    giveaway = active_giveaways[msg_id]
    user_id = callback.from_user.id
    if user_id in giveaway["participants"]:
        await callback.answer("✅ You already joined!", show_alert=True)
        return
    giveaway["participants"].append(user_id)
    count = len(giveaway["participants"])
    try:
        new_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"🎁 Joined! ({count})", callback_data="join_tgiveaway")],
            [InlineKeyboardButton("👥 View Participants", callback_data="view_tparticipants")]
        ])
        await callback.message.edit_reply_markup(reply_markup=new_keyboard)
    except:
        pass
    await callback.answer(f"✅ Joined! Total: {count}", show_alert=True)

async def view_tparticipants_callback(callback):
    msg_id = callback.message.id
    if msg_id not in active_giveaways:
        await callback.answer("❌ Giveaway not found!", show_alert=True)
        return
    giveaway = active_giveaways[msg_id]
    participants = giveaway["participants"]
    if not participants:
        await callback.answer("No participants yet!", show_alert=True)
        return
    participant_list = []
    for i, uid in enumerate(participants[:20], 1):
        try:
            user = await app.get_users(uid)
            name = user.first_name
            participant_list.append(f"{i}. {name}")
        except:
            participant_list.append(f"{i}. User `{uid}`")
    text = f"👥 **Participants ({len(participants)})**\n\n" + "\n".join(participant_list)
    if len(participants) > 20:
        text += f"\n\n... and {len(participants) - 20} more"
    await callback.message.reply(text)
    await callback.answer()
    # ==================== WORLD BOSS ====================
async def start_world_boss():
    global world_boss_active, world_boss_hp, world_boss_damage
    try:
        await app.get_chat(MAIN_GROUP_ID)
    except Exception as e:
        print(f"Cannot access main group: {e}")
        return
    world_boss_active = True
    world_boss_hp = 100000000000
    world_boss_damage.clear()
    if os.path.exists(IMU_IMAGE):
        try:
            await app.send_photo(MAIN_GROUP_ID, IMU_IMAGE, caption="🌑 **WORLD BOSS APPEARED!** 🌑\n\n👑 **IMU HAS AWAKENED!** 👑\n\n💀 **HP:** 100,000,000,000\n⚔️ **Use `/battle` to attack!**")
        except:
            await app.send_message(MAIN_GROUP_ID, "🌑 **WORLD BOSS APPEARED!** 🌑\n\n👑 **IMU HAS AWAKENED!** 👑\n\n💀 **HP:** 100,000,000,000\n⚔️ **Use `/battle` to attack!**")
    else:
        await app.send_message(MAIN_GROUP_ID, "🌑 **WORLD BOSS APPEARED!** 🌑\n\n👑 **IMU HAS AWAKENED!** 👑\n\n💀 **HP:** 100,000,000,000\n⚔️ **Use `/battle` to attack!**")

async def end_world_boss():
    global world_boss_active, world_boss_damage
    if not world_boss_active:
        return
    world_boss_active = False
    if world_boss_hp <= 0:
        top = sorted(world_boss_damage.items(), key=lambda x: x[1], reverse=True)[:3]
        text = "🎉 **IMU DEFEATED!** 🎉\n\n**Top Damage Dealers:**\n"
        for i, (uid, dmg) in enumerate(top, 1):
            p = get_player(uid)
            p.advanced_token += 1
            save_data()
            text += f"{i}. `{uid}` - {dmg:,} damage +⚜️1\n"
        await app.send_message(MAIN_GROUP_ID, text)
    else:
        await app.send_message(MAIN_GROUP_ID, "🌑 Imu escaped! Better luck next time!")

@app.on_message(filters.command("battle"))
async def battle_cmd(client, message):
    global world_boss_active, world_boss_hp, world_boss_damage
    if not world_boss_active:
        await message.reply("🌑 No active World Boss! Next raid at 10 PM.")
        return
    if world_boss_hp <= 0:
        await message.reply("✅ World Boss already defeated!")
        return
    p = get_player(message.from_user.id)
    damage = p.level * 1000
    if p.haki == "arm":
        damage = int(damage * (1 + p.haki_level * 0.3))
    if p.devil_fruit and p.fruit_category == "Good":
        damage = int(damage * 1.5)
    world_boss_hp -= damage
    world_boss_damage[message.from_user.id] = world_boss_damage.get(message.from_user.id, 0) + damage
    await message.reply(f"⚔️ **You attacked IMU!** ⚔️\n💥 Damage: {damage:,}\n❤️ Boss HP: {max(0, world_boss_hp):,}")
    if world_boss_hp <= 0:
        await end_world_boss()
    save_data()

async def world_boss_scheduler():
    while True:
        try:
            now = datetime.now()
            target_time = now.replace(hour=22, minute=0, second=0, microsecond=0)
            if now.hour >= 22:
                target_time = target_time + timedelta(days=1)
            wait_seconds = (target_time - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            try:
                await start_world_boss()
            except Exception as e:
                print(f"Failed to start world boss: {e}")
            await asyncio.sleep(1800)
            if world_boss_active:
                await end_world_boss()
        except Exception as e:
            print(f"Scheduler error: {e}")
            await asyncio.sleep(60)
            # ==================== ADMIN COMMANDS ====================
@app.on_message(filters.command("adda"))
async def add_admin_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Owner Only Command!")
        return
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: `/adda [user_id]`")
        return
    try:
        admin_id = int(args[1])
        ADMINS.add(admin_id)
        save_admins()
        await message.reply(f"✅ Added admin: `{admin_id}`")
    except:
        await message.reply("❌ Invalid user ID!")

@app.on_message(filters.command("removeadmin"))
async def remove_admin_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Owner Only Command!")
        return
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: `/removeadmin [user_id]`")
        return
    try:
        admin_id = int(args[1])
        if admin_id in ADMINS:
            ADMINS.remove(admin_id)
            save_admins()
            await message.reply(f"✅ Removed admin: `{admin_id}`")
        else:
            await message.reply(f"❌ Not an admin!")
    except:
        await message.reply("❌ Invalid user ID!")

@app.on_message(filters.command("setb"))
async def set_bounty_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Owner Only Command!")
        return
    if not message.reply_to_message:
        await message.reply("❌ Reply to a user!")
        return
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: `/setb [amount]`")
        return
    try:
        amount = int(args[1])
        p = get_player(message.reply_to_message.from_user.id)
        p.bounty = amount
        save_data()
        await message.reply(f"✅ Set {p.name}'s bounty to ฿{amount:,}")
    except:
        await message.reply("❌ Invalid amount!")

@app.on_message(filters.command("setf"))
async def set_fruit_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Owner Only Command!")
        return
    if not message.reply_to_message:
        await message.reply("❌ Reply to a user!")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: `/setf [fruit name]`")
        return
    fruit_name = " ".join(args[1:])
    p = get_player(message.reply_to_message.from_user.id)
    fruit_category = "Medium"
    for category, fruits in DEVIL_FRUITS.items():
        for fruit in fruits:
            if fruit["full"].lower() == fruit_name.lower():
                fruit_name = fruit["full"]
                fruit_category = category
                break
    p.devil_fruit = fruit_name
    p.fruit_category = fruit_category
    save_data()
    await message.reply(f"✅ Gave {p.name}: {fruit_name}")

@app.on_message(filters.command("gban"))
async def global_ban_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Owner Only Command!")
        return
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: `/gban [user_id]`")
        return
    try:
        user_id = int(args[1])
        GBANNED.add(user_id)
        save_banned()
        await message.reply(f"✅ Globally banned: `{user_id}`")
    except:
        await message.reply("❌ Invalid user ID!")

@app.on_message(filters.command("ungban"))
async def global_unban_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Owner Only Command!")
        return
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: `/ungban [user_id]`")
        return
    try:
        user_id = int(args[1])
        if user_id in GBANNED:
            GBANNED.remove(user_id)
            save_banned()
            await message.reply(f"✅ Unbanned: `{user_id}`")
        else:
            await message.reply(f"❌ Not globally banned!")
    except:
        await message.reply("❌ Invalid user ID!")

@app.on_message(filters.command("spawn"))
async def spawn_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Owner Only Command!")
        return
    if message.chat.id in active_challenges:
        await message.reply("❌ Already active! Use `/despawn` first.")
    else:
        await spawn_character(message.chat.id, "Chat")
        await message.reply("✅ Character spawned!")

@app.on_message(filters.command("despawn"))
async def despawn_cmd(client, message):
    if not is_admin_or_owner(message.from_user.id):
        await message.reply("❌ Admin Only Command!")
        return
    chat_id = message.chat.id
    if chat_id in active_challenges:
        char_name = active_challenges[chat_id]["char"]["name"]
        del active_challenges[chat_id]
        await message.reply(f"✅ **{char_name}** despawned!")
    else:
        await message.reply("❌ No active character!")

@app.on_message(filters.command("reset"))
async def reset_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Owner Only Command!")
        return
    if str(message.chat.id) in active_challenges:
        del active_challenges[str(message.chat.id)]
        await message.reply("✅ Character reset!")
    else:
        await message.reply("❌ No active character!")

@app.on_message(filters.command("check"))
async def check_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Owner Only Command!")
        return
    active_count = len(active_challenges)
    text = f"**🔍 SYSTEM CHECK**\n\n"
    text += f"Template: {'✅' if os.path.exists(WANTED_IMAGE) else '❌'}\n"
    text += f"Normal Chars: {len(normal_characters)}\nMythical Chars: {len(mythical_characters)}\n"
    text += f"Users: {len(user_data)}\nAdmins: {len(ADMINS)}\n"
    text += f"Global Bans: {len(GBANNED)}\nTemp Bans: {len(TEMP_BANNED)}\n"
    text += f"Active Challenges: {active_count}\nActive Giveaways: {len(active_giveaways)}"
    await message.reply(text)

@app.on_message(filters.command("adminlist"))
async def admin_list_cmd(client, message):
    if not is_admin_or_owner(message.from_user.id):
        await message.reply("❌ Admin Only Command!")
        return
    text = f"👑 **Owner:** `{OWNER_ID}`\n\n👥 **Admins:**\n"
    for admin_id in ADMINS:
        text += f"   • `{admin_id}`\n"
    await message.reply(text)

@app.on_message(filters.command("ban"))
async def temp_ban_cmd(client, message):
    if not is_admin_or_owner(message.from_user.id):
        await message.reply("❌ Admin Only Command!")
        return
    args = message.text.split()
    if len(args) != 3:
        await message.reply("Usage: `/ban [user_id] [hours]`")
        return
    try:
        user_id = int(args[1])
        hours = int(args[2])
        TEMP_BANNED[user_id] = time.time() + (hours * 3600)
        save_temp_banned()
        await message.reply(f"✅ Banned `{user_id}` for {hours}h")
    except:
        await message.reply("❌ Invalid!")

@app.on_message(filters.command("unban"))
async def temp_unban_cmd(client, message):
    if not is_admin_or_owner(message.from_user.id):
        await message.reply("❌ Admin Only Command!")
        return
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: `/unban [user_id]`")
        return
    try:
        user_id = int(args[1])
        if user_id in TEMP_BANNED:
            del TEMP_BANNED[user_id]
            save_temp_banned()
            await message.reply(f"✅ Unbanned `{user_id}`")
        else:
            await message.reply(f"❌ Not banned!")
    except:
        await message.reply("❌ Invalid!")

@app.on_message(filters.command("banlist"))
async def banlist_cmd(client, message):
    if not is_admin_or_owner(message.from_user.id):
        await message.reply("❌ Admin Only Command!")
        return
    check_temp_bans()
    text = "🚫 **BANS**\n\n🌍 **Global:**\n"
    for uid in GBANNED:
        text += f"   • `{uid}`\n"
    text += "\n⏰ **Temp:**\n"
    for uid, t in TEMP_BANNED.items():
        remaining = int(t - time.time())
        hours = remaining // 3600
        text += f"   • `{uid}` - {hours}h left\n"
    await message.reply(text)

@app.on_message(filters.command("ncradd"))
async def add_normal_char(client, message):
    if not is_admin_or_owner(message.from_user.id):
        await message.reply("❌ Admin Only Command!")
        return
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("📸 Reply to an image with `/ncradd Zoro`")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❌ Provide character name!")
        return
    name = " ".join(args[1:])
    photo = await message.reply_to_message.download()
    normal_characters.append({"name": name, "image": photo})
    save_normal_chars()
    await message.reply(f"✅ Added normal: {name}")

@app.on_message(filters.command("mcradd"))
async def add_mythical_char(client, message):
    if not is_admin_or_owner(message.from_user.id):
        await message.reply("❌ Admin Only Command!")
        return
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("📸 Reply to an image with `/mcradd Kaido`")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❌ Provide character name!")
        return
    name = " ".join(args[1:])
    photo = await message.reply_to_message.download()
    mythical_characters.append({"name": name, "image": photo})
    save_mythical_chars()
    await message.reply(f"✅ Added mythical: {name}")

@app.on_message(filters.command("ncrdelete"))
async def delete_normal_char(client, message):
    if not is_admin_or_owner(message.from_user.id):
        await message.reply("❌ Admin Only Command!")
        return
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: `/ncrdelete [id]`")
        return
    try:
        idx = int(args[1]) - 1
        if 0 <= idx < len(normal_characters):
            deleted = normal_characters.pop(idx)
            save_normal_chars()
            await message.reply(f"✅ Deleted: {deleted['name']}")
        else:
            await message.reply(f"❌ ID 1-{len(normal_characters)}")
    except:
        await message.reply("❌ Invalid ID!")

@app.on_message(filters.command("mcrdelete"))
async def delete_mythical_char(client, message):
    if not is_admin_or_owner(message.from_user.id):
        await message.reply("❌ Admin Only Command!")
        return
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: `/mcrdelete [id]`")
        return
    try:
        idx = int(args[1]) - 1
        if 0 <= idx < len(mythical_characters):
            deleted = mythical_characters.pop(idx)
            save_mythical_chars()
            await message.reply(f"✅ Deleted: {deleted['name']}")
        else:
            await message.reply(f"❌ ID 1-{len(mythical_characters)}")
    except:
        await message.reply("❌ Invalid ID!")

@app.on_message(filters.command("charslist"))
async def chars_list_cmd(client, message):
    if not is_admin_or_owner(message.from_user.id):
        await message.reply("❌ Admin Only Command!")
        return
    text = "**📋 CHARACTERS**\n\n**Normal:**\n"
    for i, c in enumerate(normal_characters, 1):
        text += f"{i}. {c['name']}\n"
    text += "\n**Mythical:**\n"
    for i, c in enumerate(mythical_characters, 1):
        text += f"{i}. {c['name']}\n"
    await message.reply(text)

@app.on_message(filters.command("id"))
async def get_id_cmd(client, message):
    if not is_admin_or_owner(message.from_user.id):
        await message.reply("❌ Admin Only Command!")
        return
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        await message.reply(f"**User ID:** `{user.id}`\n**Name:** {user.first_name}")
    else:
        await message.reply("❌ Reply to a user!")

# ==================== RESET PLAYER COMMAND ====================
@app.on_message(filters.command("resetplayer"))
async def reset_player_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ **Owner Only Command!**")
        return
    
    args = message.text.split()
    if len(args) != 2:
        await message.reply(
            "🔄 **RESET PLAYER** 🔄\n\n"
            "Usage: `/resetplayer [user_id]`\n\n"
            "⚠️ This will reset the player completely!\n"
            "• Bounty → 0\n• Level → 1\n• Haki → None\n• Shield → None\n• Devil Fruit → None\n• Vault → 0\n• Tokens → 0"
        )
        return
    
    try:
        target_id = int(args[1])
    except:
        await message.reply("❌ **Invalid User ID!**")
        return
    
    target_id_str = str(target_id)
    if target_id_str not in user_data:
        await message.reply(f"❌ **Player `{target_id}` not found!**")
        return
    
    old_player = user_data[target_id_str]
    old_name = old_player.name or f"User_{target_id}"
    old_bounty = old_player.bounty
    old_level = old_player.level
    
    user_data[target_id_str] = Player(target_id)
    new_player = user_data[target_id_str]
    new_player.name = old_name
    new_player.username = old_player.username
    
    save_data()
    
    await message.reply(
        f"🔄 **PLAYER RESET COMPLETED!** 🔄\n\n"
        f"👤 **Player:** {old_name} (`{target_id}`)\n"
        f"📊 **Before:** Bounty ฿{old_bounty:,} | Level {old_level}\n"
        f"📊 **After:** Bounty ฿0 | Level 1\n\n"
        f"🤖 {BOT_NAME}"
    )
    
    try:
        await app.send_message(
            target_id,
            f"🔄 **YOUR ACCOUNT HAS BEEN RESET!** 🔄\n\n"
            f"📊 Before: Bounty ฿{old_bounty:,} | Level {old_level}\n"
            f"📊 After: Bounty ฿0 | Level 1\n\n"
            f"💪 Start your journey again!\n\n🤖 {BOT_NAME}"
        )
    except:
        pass

# ==================== RESET ALL PLAYERS COMMAND ====================
@app.on_message(filters.command("resetall"))
async def reset_all_players_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ **Owner Only Command!**")
        return
    
    args = message.text.split()
    if len(args) != 2 or args[1].lower() != "confirm":
        await message.reply(
            "⚠️ **RESET ALL PLAYERS** ⚠️\n\n"
            f"📊 Total Players: {len(user_data)}\n\n"
            "To confirm, type:\n`/resetall confirm`"
        )
        return
    
    total_players = len(user_data)
    
    backup_data = {uid: p.to_dict() for uid, p in user_data.items()}
    with open("data/users_backup.json", "w") as f:
        json.dump(backup_data, f, indent=2)
    
    for uid, player in user_data.items():
        old_name = player.name
        old_username = player.username
        user_data[uid] = Player(int(uid))
        user_data[uid].name = old_name
        user_data[uid].username = old_username
    
    save_data()
    
    await message.reply(
        f"🔄 **ALL PLAYERS RESET COMPLETED!** 🔄\n\n"
        f"📊 **Total Players Reset:** {total_players}\n"
        f"💾 **Backup saved:** `data/users_backup.json`\n\n"
        f"🤖 {BOT_NAME}"
    )
    # ==================== BAN CHECK ====================
@app.on_message(filters.all, group=-2)
async def check_banned(client, message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    if user_id in GBANNED:
        await message.reply("🚫 You are globally banned!")
        message.stop_propagation()
        return
    if user_id in TEMP_BANNED:
        t = TEMP_BANNED[user_id]
        if t > time.time():
            remaining = int(t - time.time())
            hours = remaining // 3600
            await message.reply(f"⏰ Temporarily banned! {hours}h left")
            message.stop_propagation()
            return
        else:
            del TEMP_BANNED[user_id]
            save_temp_banned()
    message.continue_propagation()

# ==================== BOT RUNNER ====================
if __name__ == "__main__":
    print("=" * 50)
    print("🏴‍☠️ GRAND LINE SENTINEL BOT")
    print("=" * 50)
    print(f"{BOT_NAME} is running...")
    print("Send /start on Telegram")
    print("=" * 50)
    
    loop = asyncio.get_event_loop()
    loop.create_task(world_boss_scheduler())
    loop.create_task(despawn_checker())
    
    app.run()