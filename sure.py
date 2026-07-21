import asyncio
import io
import re
import json
import html
import os
import httpx
import pyotp
import random
import string
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler

# ==================== CONFIG SECTION ====================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8931522547:AAHtwfo1JmFS8G5V6qiSYLpef63jrJ4ME6o")

# ==================== MULTI API KEY CONFIGURATION ====================
# API KEY 01 - Primary (Same as before)
API_KEY_01 = os.environ.get("API_KEY_01", "MURAD_18A5CEE19525C2BD4E971385")
BASE_URL_01 = os.environ.get("BASE_URL_01", "https://2eee7.com/@Access/@Bot/2eee7/@public")

# API KEY 02 - New (Updated with your new endpoint)
API_KEY_02 = os.environ.get("API_KEY_02", "M7EGCC09EXI")
BASE_URL_02 = os.environ.get("BASE_URL_02", "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api")

DEFAULT_API_KEY = "API_KEY_01"

USER_DATA_FILE = "users.json"
PAID_SMS_FILE = "paid_sms.json"
STATS_FILE = "user_stats.json"
REFERRAL_DATA_FILE = "referral_data.json"
BANNED_USERS_FILE = "banned_users.json"
WITHDRAW_DATA_FILE = "withdraw_requests.json"
ACTIVITY_LOGS_FILE = "activity_logs.json"
DATA_RANGE_FILE = "datarange.json"
CUSTOM_SERVICES_FILE = "custom_services.json"
ADMINS_FILE = "admins.json"
OTP_GROUPS_FILE = "otp_groups.json"

# ==================== MULTIPLE ADMINS CONFIGURATION ====================
# ডিফল্ট অ্যাডমিন (প্রথমবার বট চালানোর জন্য)
DEFAULT_ADMINS = [2102179662]

# ডিফল্ট OTP গ্রুপ (প্রথমবার বট চালানোর জন্য)
DEFAULT_OTP_GROUPS = [-1004374381669]

# ==================== ADMINS FUNCTIONS ====================

def load_admins():
    """অ্যাডমিন লিস্ট লোড করে"""
    if not os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, "w") as f:
            json.dump(DEFAULT_ADMINS, f)
        return DEFAULT_ADMINS
    try:
        with open(ADMINS_FILE, "r") as f:
            return json.load(f)
    except:
        return DEFAULT_ADMINS

def save_admins(admins_list):
    """অ্যাডমিন লিস্ট সেভ করে"""
    with open(ADMINS_FILE, "w") as f:
        json.dump(admins_list, f, indent=4)

def is_admin(user_id):
    """ইউজার অ্যাডমিন কিনা চেক করে"""
    admins = load_admins()
    return user_id in admins

def add_admin(user_id):
    """নতুন অ্যাডমিন যোগ করে"""
    admins = load_admins()
    if user_id not in admins:
        admins.append(user_id)
        save_admins(admins)
        return True
    return False

def remove_admin(user_id):
    """অ্যাডমিন রিমুভ করে"""
    admins = load_admins()
    if user_id in admins and user_id not in DEFAULT_ADMINS:
        admins.remove(user_id)
        save_admins(admins)
        return True
    return False

# ==================== OTP GROUPS FUNCTIONS ====================

def load_otp_groups():
    """OTP গ্রুপ লিস্ট লোড করে"""
    if not os.path.exists(OTP_GROUPS_FILE):
        with open(OTP_GROUPS_FILE, "w") as f:
            json.dump(DEFAULT_OTP_GROUPS, f)
        return DEFAULT_OTP_GROUPS
    try:
        with open(OTP_GROUPS_FILE, "r") as f:
            return json.load(f)
    except:
        return DEFAULT_OTP_GROUPS

def save_otp_groups(groups_list):
    """OTP গ্রুপ লিস্ট সেভ করে"""
    with open(OTP_GROUPS_FILE, "w") as f:
        json.dump(groups_list, f, indent=4)

def add_otp_group(group_id):
    """নতুন OTP গ্রুপ যোগ করে"""
    groups = load_otp_groups()
    if group_id not in groups:
        groups.append(group_id)
        save_otp_groups(groups)
        return True
    return False

def remove_otp_group(group_id):
    """OTP গ্রুপ রিমুভ করে"""
    groups = load_otp_groups()
    if group_id in groups and group_id not in DEFAULT_OTP_GROUPS:
        groups.remove(group_id)
        save_otp_groups(groups)
        return True
    return False

# ==================== WELCOME MESSAGE CONFIGURATION ====================
WELCOME_MESSAGE = """⚡             𝗦𝗨𝗥𝗘 𝗕𝗢𝗧             ⚡ 
━━━━━━━━━━━━━━━━━━━━━━
🟢 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 & ⚡ 𝗙𝗮𝘀𝘁 𝗦𝗲𝗿𝘃𝗶𝗰𝗲 🟢

🔥 প্রতি ওটিপি রিসিভ ০.২৫ টাকা 
🔥 প্রতি রেফার এর জন্য ৫ টাকা আয়
🔥 ৫০ টাকা হলে বিকাশ-নগদে উত্তোলন
🔥 ওয়ার্কিং নাম্বার রেন্জ অটো আপডেট
🔥 ২৪/৭ ঘন্টা সাপোর্ট
"""

OTP_RATE = 0.20
REFERRAL_PRICE = 5
MIN_WITHDRAW = 50
MAX_WITHDRAW = 10000
SUPPORT_LINK = "https://t.me/sure_otp_suppor"

request_queue = asyncio.Queue()
MAX_WORKERS = 500

# ==================== USER LAST DATA STORAGE ====================
user_last_data = {}  # ইউজারের শেষ সার্ভিস/কান্ট্রি/রেঞ্জ সংরক্ষণের জন্য

# ==================== API KEY SELECTION FUNCTIONS ====================

def get_api_key_for_range(range_text):
    custom_services = load_custom_services()
    for service in custom_services:
        for rng in service.get("ranges", []):
            if rng.get("range", "").upper() == range_text.upper():
                return rng.get("api_key", DEFAULT_API_KEY)
    return DEFAULT_API_KEY

def get_api_credentials_by_choice(choice):
    if choice == "API_KEY_01":
        return API_KEY_01, BASE_URL_01
    elif choice == "API_KEY_02":
        return API_KEY_02, BASE_URL_02
    return API_KEY_01, BASE_URL_01

def get_api_key_label(choice):
    if choice == "API_KEY_01":
        return "🔑 API Key 01"
    elif choice == "API_KEY_02":
        return "🔑 API Key 02"
    return "🔑 Default"

# ==================== API RESPONSE PARSERS ====================

def parse_number_response(data, api_choice):
    """ভিন্ন API থেকে রেসপন্স পার্স করে"""
    try:
        if api_choice == "API_KEY_01":
            # প্রথম API এর ফরম্যাট (Same as before)
            if data.get("meta", {}).get("status") == "ok":
                number_data = data.get("data", {})
                return {
                    "number": number_data.get("full_number") or number_data.get("no_plus_number"),
                    "otp_now": number_data.get("otp_now", False),
                    "otp": number_data.get("otp"),
                    "sms": number_data.get("sms"),
                    "country": number_data.get("country", ""),
                    "operator": number_data.get("operator", "")
                }
        
        elif api_choice == "API_KEY_02":
            # দ্বিতীয় API এর ফরম্যাট (2oo9 API format)
            if data.get("meta", {}).get("code") == 200 and data.get("meta", {}).get("status") == "ok":
                number_data = data.get("data", {})
                return {
                    "number": number_data.get("full_number") or number_data.get("no_plus_number"),
                    "otp_now": False,
                    "otp": None,
                    "sms": None,
                    "country": number_data.get("country", ""),
                    "operator": number_data.get("operator", "")
                }
            elif data.get("meta", {}).get("code") == 2946:
                print(f"Out of stock for range")
                return None
        
        return None
    except Exception as e:
        print(f"Parse error for {api_choice}: {e}")
        return None

def parse_otp_response(data, api_choice):
    """ভিন্ন API থেকে OTP রেসপন্স পার্স করে"""
    try:
        if api_choice == "API_KEY_01":
            if isinstance(data, dict):
                if "data" in data and isinstance(data["data"], dict) and "otps" in data["data"]:
                    return data["data"]["otps"]
                elif "otps" in data:
                    return data["otps"]
                elif "data" in data and isinstance(data["data"], list):
                    return data["data"]
            elif isinstance(data, list):
                return data
        
        elif api_choice == "API_KEY_02":
            if isinstance(data, dict):
                if data.get("meta", {}).get("code") == 200 and data.get("meta", {}).get("status") == "ok":
                    otp_data = data.get("data", {})
                    otps = otp_data.get("otps", [])
                    formatted_otps = []
                    for otp in otps:
                        formatted_otps.append({
                            "number": otp.get("number", ""),
                            "message": otp.get("message", ""),
                            "otp_id": otp.get("otp_id", ""),
                            "time": otp.get("time", 0)
                        })
                    return formatted_otps
            elif isinstance(data, list):
                return data
        
        return []
    except Exception as e:
        print(f"OTP parse error for {api_choice}: {e}")
        return []

def extract_otp_from_message(message):
    """SMS মেসেজ থেকে OTP এক্সট্র্যাক্ট করে"""
    if not message:
        return None
    otp_match = re.search(r'\b\d{4,8}\b', str(message))
    return otp_match.group(0) if otp_match else None

client_async = httpx.AsyncClient(
    http2=True,
    timeout=httpx.Timeout(connect=3.0, read=30.0, write=5.0, pool=15.0),
    headers={
        "Accept": "application/json, text/plain, */*",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    },
    limits=httpx.Limits(max_connections=3000, max_keepalive_connections=1000)
)

active_numbers = {}
last_range = {}
CHECK_INTERVAL = 0.2

# ==================== HELPERS SECTION ====================

def get_bangladesh_time():
    return datetime.utcnow() + timedelta(hours=6)

def normalize_number(number):
    if not number:
        return ""
    return re.sub(r'\D', '', str(number))

def mask_number(number):
    num_str = str(number)
    if len(num_str) <= 6:
        return num_str
    return num_str[:4] + "****" + num_str[-2:]

def is_valid_bangladesh_number(number):
    clean = re.sub(r'\D', '', str(number))
    if len(clean) == 11 and clean.startswith("01"):
        return True
    if len(clean) == 13 and clean.startswith("8801"):
        return True
    return False

def format_balance(balance):
    try:
        return f"{float(balance):.2f}"
    except:
        return "0.00"

def get_date_reset_time():
    bd_now = get_bangladesh_time()
    return datetime(bd_now.year, bd_now.month, bd_now.day)

def is_range_request(param):
    return bool(re.match(r'^\d+[xX]+$', str(param)))

def is_referral_request(param):
    return str(param).isdigit()

def extract_link_and_otp(full_sms):
    if not full_sms:
        return None, None
    otp_match = re.search(r'\b\d{4,8}\b', full_sms)
    otp = otp_match.group(0) if otp_match else None
    link_match = re.search(r'https?://[^\s]+', full_sms)
    link = link_match.group(0) if link_match else None
    return otp, link

def numbers_match(num1, num2):
    n1 = re.sub(r'\D', '', str(num1))
    n2 = re.sub(r'\D', '', str(num2))
    if not n1 or not n2:
        return False
    return n1 in n2 or n2 in n1

def make_bold_unicode(text):
    out = []
    for char in text:
        codepoint = ord(char)
        if 65 <= codepoint <= 90:
            out.append(chr(codepoint - 65 + 0x1D5D4))
        elif 97 <= codepoint <= 122:
            out.append(chr(codepoint - 97 + 0x1D5EE))
        elif 48 <= codepoint <= 57:
            out.append(chr(codepoint - 48 + 0x1D7EC))
        else:
            out.append(char)
    return "".join(out)

def normalize_stylized_text(text):
    if not text:
        return ""
    out = []
    for char in text:
        cp = ord(char)
        if 0x1D5D4 <= cp <= 0x1D5ED:
            out.append(chr(cp - 0x1D5D4 + 65))
        elif 0x1D5EE <= cp <= 0x1D607:
            out.append(chr(cp - 0x1D5EE + 97))
        elif 0x1D7EC <= cp <= 0x1D7F5:
            out.append(chr(cp - 0x1D7EC + 48))
        else:
            out.append(char)
    return "".join(out)

def clean_country_display(val):
    if not val:
        return ""
    return re.sub(r'\s+', ' ', str(val)).strip().lower()

# ==================== WITHDRAW DATA FUNCTIONS ====================

def load_withdraw_requests():
    if not os.path.exists(WITHDRAW_DATA_FILE):
        with open(WITHDRAW_DATA_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(WITHDRAW_DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_withdraw_requests(data):
    with open(WITHDRAW_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def generate_payment_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

# ==================== BANNED USERS FUNCTIONS ====================

def load_banned_users():
    if not os.path.exists(BANNED_USERS_FILE):
        with open(BANNED_USERS_FILE, "w") as f:
            json.dump([], f)
        return []
    try:
        with open(BANNED_USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_banned_users(banned_list):
    with open(BANNED_USERS_FILE, "w") as f:
        json.dump(banned_list, f, indent=4)

def is_user_banned(uid):
    banned_list = load_banned_users()
    return str(uid) in banned_list

def ban_user(uid):
    banned_list = load_banned_users()
    uid_str = str(uid)
    if uid_str not in banned_list:
        banned_list.append(uid_str)
        save_banned_users(banned_list)
        return True
    return False

def unban_user(uid):
    banned_list = load_banned_users()
    uid_str = str(uid)
    if uid_str in banned_list:
        banned_list.remove(uid_str)
        save_banned_users(banned_list)
        return True
    return False

# ==================== REFERRAL DATA FUNCTIONS ====================

def load_referral_data():
    if not os.path.exists(REFERRAL_DATA_FILE):
        with open(REFERRAL_DATA_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(REFERRAL_DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_referral_data(data):
    with open(REFERRAL_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_referral_count(uid, count):
    referral_data = load_referral_data()
    uid_str = str(uid)
    if uid_str not in referral_data:
        referral_data[uid_str] = {"referral_count": 0}
    referral_data[uid_str]["referral_count"] = count
    save_referral_data(referral_data)

def get_referral_count(uid):
    referral_data = load_referral_data()
    uid_str = str(uid)
    return referral_data.get(uid_str, {}).get("referral_count", 0)

# ==================== DATA RANGE FILE ====================

def load_range_db():
    if not os.path.exists(DATA_RANGE_FILE):
        return {}
    try:
        with open(DATA_RANGE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_range_db(data):
    with open(DATA_RANGE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def save_number_range_info(uid, number, range_text):
    db = load_range_db()
    flag, name = get_country_info(number)
    db[normalize_number(number)] = {
        "user_id": str(uid),
        "number": f"+{normalize_number(number)}",
        "range": range_text,
        "country": f"{flag} {name}"
    }
    save_range_db(db)

# ==================== CUSTOM SERVICE CONFIG ====================

def load_custom_services():
    if not os.path.exists(CUSTOM_SERVICES_FILE):
        with open(CUSTOM_SERVICES_FILE, "w") as f:
            json.dump([], f)
        return []
    try:
        with open(CUSTOM_SERVICES_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_custom_services(data):
    with open(CUSTOM_SERVICES_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ==================== COUNTRY MAPPING SECTION ====================

def get_country_info(number):
    number = str(number).strip()
    country_map = {
        "2376": ("🇨🇲", "Cameroon"), "2250": ("🇨🇮", "Ivory Coast"), "2613": ("🇲🇬", "Madagascar"),
        "4077": ("🇷🇴", "Romania"), "237": ("🇨🇲", "Cameroon"), "225": ("🇨🇮", "Ivory Coast"),
        "261": ("🇲🇬", "Madagascar"), "20": ("🇪🇬", "Egypt"), "27": ("🇿🇦", "South Africa"),
        "234": ("🇳🇬", "Nigeria"), "254": ("🇰🇪", "Kenya"), "233": ("🇬🇭", "Ghana"),
        "212": ("🇲🇦", "Morocco"), "213": ("🇩🇿", "Algeria"), "216": ("🇹🇳", "Tunisia"),
        "218": ("🇱🇾", "Libya"), "249": ("🇸🇩", "Sudan"), "251": ("🇪🇹", "Ethiopia"),
        "252": ("🇸🇴", "Somalia"), "253": ("🇩🇯", "Djibouti"), "255": ("🇹🇿", "Tanzania"),
        "256": ("🇺🇬", "Uganda"), "257": ("🇧🇮", "Burundi"), "258": ("🇲🇿", "Mozambique"),
        "260": ("🇿🇲", "Zambia"), "263": ("🇿🇼", "Zimbabwe"), "264": ("🇳🇦", "Namibia"),
        "265": ("🇲🇼", "Malawi"), "266": ("🇱🇸", "Lesotho"), "267": ("🇧🇼", "Botswana"),
        "268": ("🇸🇿", "Swaziland"), "269": ("🇰🇲", "Comoros"), "220": ("🇬🇲", "Gambia"),
        "221": ("🇸🇳", "Senegal"), "222": ("🇲🇷", "Mauritania"), "223": ("🇲🇱", "Mali"),
        "224": ("🇬🇳", "Guinea"), "226": ("🇧🇫", "Burkina Faso"), "227": ("🇳🇪", "Niger"),
        "228": ("🇹🇬", "Togo"), "229": ("🇧🇯", "Benin"), "230": ("🇲🇺", "Mauritius"),
        "231": ("🇱🇷", "Liberia"), "232": ("🇸🇱", "Sierra Leone"), "235": ("🇹🇩", "Chad"),
        "236": ("🇨🇫", "Central African Republic"), "238": ("🇨🇻", "Cape Verde"),
        "239": ("🇸🇹", "Sao Tome and Principe"), "240": ("🇬🇶", "Equatorial Guinea"),
        "241": ("🇬🇦", "Gabon"), "242": ("🇨🇬", "Congo"), "243": ("🇨🇩", "DR Congo"),
        "244": ("🇦🇴", "Angola"), "245": ("🇬🇼", "Guinea-Bissau"), "247": ("🇸🇭", "Saint Helena"),
        "248": ("🇸🇨", "Seychelles"), "250": ("🇷🇼", "Rwanda"), "290": ("🇸🇭", "Saint Helena"),
        "291": ("🇪🇷", "Eritrea"), "40": ("🇷🇴", "Romania"), "44": ("🇬🇧", "United Kingdom"),
        "33": ("🇫🇷", "France"), "49": ("🇩🇪", "Germany"), "39": ("🇮🇹", "Italy"),
        "34": ("🇪🇸", "Spain"), "31": ("🇳🇱", "Netherlands"), "32": ("🇧🇪", "Belgium"),
        "41": ("🇨🇭", "Switzerland"), "43": ("🇦🇹", "Austria"), "46": ("🇸🇪", "Sweden"),
        "47": ("🇳🇴", "Norway"), "45": ("🇩👑", "Denmark"), "358": ("🇫🇮", "Finland"),
        "351": ("🇵🇹", "Portugal"), "353": ("🇮🇪", "Ireland"), "36": ("🇭🇺", "Hungary"),
        "48": ("🇵🇱", "Poland"), "380": ("🇺🇦", "Ukraine"), "370": ("🇱🇹", "Lithuania"),
        "371": ("🇱🇻", "Latvia"), "372": ("🇪🇪", "Estonia"), "373": ("🇲🇩", "Moldova"),
        "374": ("🇦🇲", "Armenia"), "375": ("🇧🇾", "Belarus"), "376": ("🇦🇩", "Andorra"),
        "377": ("🇲🇨", "Monaco"), "381": ("🇷🇸", "Serbia"), "382": ("🇲🇪", "Montenegro"),
        "385": ("🇭🇷", "Croatia"), "386": ("🇸🇮", "Slovenia"), "387": ("🇧🇦", "Bosnia and Herzegovina"),
        "389": ("🇲🇰", "North Macedonia"), "350": ("🇬🇮", "Gibraltar"), "352": ("🇱🇺", "Luxembourg"),
        "354": ("🇮🇸", "Iceland"), "355": ("🇦🇱", "Albania"), "356": ("🇲🇹", "Malta"),
        "357": ("🇨🇾", "Cyprus"), "359": ("🇧🇬", "Bulgaria"), "421": ("🇸🇰", "Slovakia"),
        "420": ("🇨🇿", "Czech Republic"), "298": ("🇫🇴", "Faroe Islands"), "299": ("🇬🇱", "Greenland"),
        "1": ("🇺🇸", "United States"), "7": ("🇷🇺", "Russia"), "91": ("🇮🇳", "India"),
        "92": ("🇵🇰", "Pakistan"), "880": ("🇧🇩", "Bangladesh"), "86": ("🇨🇳", "China"),
        "81": ("🇯🇵", "Japan"), "82": ("🇰🇷", "South Korea"), "84": ("🇻🇳", "Vietnam"),
        "66": ("🇹🇭", "Thailand"), "62": ("🇮🇩", "Indonesia"), "60": ("🇲🇾", "Malaysia"),
        "65": ("🇸🇬", "Singapore"), "63": ("🇵🇭", "Philippines"), "95": ("🇲🇲", "Myanmar"),
        "94": ("🇱🇰", "Sri Lanka"), "977": ("🇳🇵", "Nepal"), "93": ("🇦𝒇", "Afghanistan"),
        "98": ("🇮🇷", "Iran"), "90": ("🇹🇷", "Turkey"), "964": ("🇮🇶", "Iraq"),
        "963": ("🇸🇾", "Syria"), "961": ("🇱🇧", "Lebanon"), "962": ("🇯🇴", "Jordan"),
        "965": ("🇰🇼", "Kuwait"), "966": ("🇸🇦", "Saudi Arabia"), "967": ("🇾🇲", "Yemen"),
        "968": ("🇴🇲", "Oman"), "971": ("🇦🇪", "United Arab Emirates"), "972": ("🇮🇱", "Israel"),
        "973": ("🇧🇭", "Bahrain"), "974": ("🇶🇦", "Qatar"), "994": ("🇦🇿", "Azerbaijan"),
        "995": ("🇬🇪", "Georgia"), "996": ("🇰🇬", "Kyrgyzstan"), "992": ("🇹𝒋", "Tajikistan"),
        "993": ("🇹🇲", "Turkmenistan"), "998": ("🇺🇿", "Uzbekistan"), "855": ("🇰🇭", "Cambodia"),
        "856": ("🇱🇦", "Laos"), "976": ("🇲🇳", "Mongolia"), "850": ("🇰🇵", "North Korea"),
        "55": ("🇧🇷", "Brazil"), "52": ("🇲🇽", "Mexico"), "54": ("🇦🇷", "Argentina"),
        "57": ("🇨🇴", "Colombia"), "51": ("🇵🇪", "Peru"), "58": ("🇻🇪", "Venezuela"),
        "56": ("🇨🇱", "Chile"), "593": ("🇪🇨", "Ecuador"), "591": ("🇧🇴", "Bolivia"),
        "595": ("🇵🇾", "Paraguay"), "598": ("🇺🇾", "Uruguay"), "502": ("🇬🇹", "Guatemala"),
        "503": ("🇸𝑽", "El Salvador"), "504": ("🇭🇳", "Honduras"), "506": ("🇨🇷", "Costa Rica"),
        "507": ("🇵🇦", "Panama"), "509": ("🇭🇹", "Haiti"), "501": ("🇧🇿", "Belize"),
        "61": ("🇦🇺", "Australia"), "64": ("🇳🇿", "New Zealand"), "675": ("🇵🇬", "Papua New Guinea"),
        "679": ("🇫يج", "Fiji"), "1246": ("🇧🇧", "Barbados"), "1876": ("🇯🇲", "Jamaica"),
        "53": ("🇨🇺", "Cuba"), "592": ("🇬🇾", "Guyana"),
    }
    clean_num = str(number).replace('+', '').replace(' ', '').replace('-', '').strip()
    sorted_prefixes = sorted(country_map.keys(), key=len, reverse=True)
    for prefix in sorted_prefixes:
        if clean_num.startswith(prefix):
            return country_map[prefix]
    return ("🌍", "Unknown")

# ==================== SERVICE DETECTION SECTION ====================

def detect_service(full_sms):
    if not full_sms:
        return "SMS SERVICE"
    sms_lower = full_sms.lower()
    service_keywords = {
        "facebook": "FACEBOOK", "fb": "FACEBOOK", "instagram": "INSTAGRAM", "insta": "INSTAGRAM",
        "tiktok": "TIKTOK", "twitter": "TWITTER", "x.com": "TWITTER", "snapchat": "SNAPCHAT",
        "snap": "SNAPCHAT", "whatsapp": "WHATSAPP", "telegram": "TELEGRAM", "discord": "DISCORD",
        "messenger": "MESSENGER", "linkedin": "LINKEDIN", "google": "GOOGLE", "gmail": "GOOGLE",
        "amazon": "AMAZON", "microsoft": "MICROSOFT", "outlook": "MICROSOFT", "yahoo": "YAHOO",
        "paypal": "PAYPAL", "binance": "BINANCE", "coinbase": "COINBASE", "spotify": "SPOTIFY",
        "netflix": "NETFLIX", "uber": "UBER", "apple": "APPLE", "icloud": "APPLE",
        "bkash": "BKASH", "nagad": "NAGAD", "stripe": "STRIPE", "line": "LINE",
        "wechat": "WECHAT", "viber": "VIBER", "signal": "SIGNAL", "pubg": "PUBG",
        "free fire": "FREE FIRE",
    }
    for keyword, service_name in sorted(service_keywords.items(), key=lambda x: len(x[0]), reverse=True):
        if keyword in sms_lower:
            return service_name
    return "SMS SERVICE"

# ==================== KEYBOARDS SECTION ====================

def main_keyboard(user_id):
    keyboard = [
        [KeyboardButton(text=f"📞 {make_bold_unicode('GET NUMBER')}")],
        [
            KeyboardButton(text=f"👥 {make_bold_unicode('REFER AND EARN')}"),
            KeyboardButton(text=f"👤 {make_bold_unicode('PROFILE')}")
        ],
        [KeyboardButton(text=f"🏆 {make_bold_unicode('LEADERBOARD')}")],
        [KeyboardButton(text=f"💬 {make_bold_unicode('SUPPORT')}")]
    ]
    if is_admin(user_id):
        keyboard.append([KeyboardButton(text=f"⚙️ {make_bold_unicode('ADMIN PANEL')} ⚙️")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def cancel_keyboard():
    keyboard = [[KeyboardButton(f"❌ {make_bold_unicode('CANCEL')}")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def withdraw_method_keyboard():
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton(f"📱 {make_bold_unicode('BKASH')}"), KeyboardButton(f"💵 {make_bold_unicode('NAGAD')}")],
        [KeyboardButton(f"🚀 {make_bold_unicode('ROCKET')}"), KeyboardButton(f"🏦 {make_bold_unicode('BINANCE')}")],
        [KeyboardButton(f"❌ {make_bold_unicode('CANCEL')}")]
    ], resize_keyboard=True)
    return keyboard

# ==================== ADMIN PANEL KEYBOARDS ====================

def get_grouped_countries_for_service(service):
    grouped = {}
    for r in service.get("ranges", []):
        r_text = r.get("range", "")
        country_display = r.get("country", "")
        match = re.match(r'^([^\w\s]*)\s*(.*)$', country_display)
        if match:
            flag = match.group(1).strip()
            cname = match.group(2).strip()
        else:
            flag = "🌍"
            cname = "Unknown"
        if not cname:
            cname = "Unknown"
        if cname not in grouped:
            grouped[cname] = {"flag": flag, "ranges": []}
        if r_text not in grouped[cname]["ranges"]:
            grouped[cname]["ranges"].append(r_text)
    return grouped

def build_admin_main_inline_keyboard():
    buttons = [
        [InlineKeyboardButton(make_bold_unicode("👥 USER MANAGEMENT"), callback_data="adm_menu_user_mgnt")],
        [InlineKeyboardButton(make_bold_unicode("⚙️ SYSTEM CONFIGURATION"), callback_data="adm_menu_sys_config")],
        [InlineKeyboardButton(make_bold_unicode("🛠️ MANAGE SERVICES"), callback_data="manage_svc_back_to_list")],
        [InlineKeyboardButton(make_bold_unicode("🔙 BACK TO MAIN MENU"), callback_data="adm_menu_back_to_main")]
    ]
    return InlineKeyboardMarkup(buttons)

def build_user_management_inline_keyboard():
    buttons = [
        [InlineKeyboardButton(make_bold_unicode("📢 BROADCAST TO ALL"), callback_data="adm_usermgnt_broadcast")],
        [InlineKeyboardButton(make_bold_unicode("🆔 GET ALL USER ID"), callback_data="adm_usermgnt_get_ids")],
        [InlineKeyboardButton(make_bold_unicode("💰 ALL USER BALANCE"), callback_data="adm_usermgnt_all_balance")],
        [InlineKeyboardButton(make_bold_unicode("🔙 BACK"), callback_data="adm_menu_back_to_admin")]
    ]
    return InlineKeyboardMarkup(buttons)

# ==================== UPDATED SYSTEM CONFIG KEYBOARD ====================
def build_system_config_inline_keyboard():
    buttons = [
        [
            InlineKeyboardButton(make_bold_unicode("📈 SYSTEM STATS"), callback_data="adm_sys_stats"),
            InlineKeyboardButton(make_bold_unicode("👤 USER CHECK"), callback_data="adm_sys_user_check")
        ],
        [
            InlineKeyboardButton(make_bold_unicode("⛔ BAN USER"), callback_data="adm_sys_ban"),
            InlineKeyboardButton(make_bold_unicode("🔓 UNBAN USER"), callback_data="adm_sys_unban")
        ],
        [InlineKeyboardButton(make_bold_unicode("📜 BANNED LIST"), callback_data="adm_sys_banned_list")],
        [
            InlineKeyboardButton(make_bold_unicode("➕ ADD BALANCE"), callback_data="adm_sys_add_bal"),
            InlineKeyboardButton(make_bold_unicode("➖ REMOVE BALANCE"), callback_data="adm_sys_rem_bal")
        ],
        # ============ NEW: OTP Group Management ============
        [InlineKeyboardButton(make_bold_unicode("📢 OTP GROUP MANAGEMENT"), callback_data="admin_otp_group_menu")],
        # ============ NEW: Admin Management ============
        [InlineKeyboardButton(make_bold_unicode("👑 ADMIN MANAGEMENT"), callback_data="admin_admin_management")],
        [InlineKeyboardButton(make_bold_unicode("🔙 BACK"), callback_data="adm_menu_back_to_admin")]
    ]
    return InlineKeyboardMarkup(buttons)

# ==================== OTP GROUP MANAGEMENT KEYBOARDS ====================
def build_otp_group_management_keyboard():
    """OTP গ্রুপ ম্যানেজমেন্ট কীবোর্ড"""
    groups = load_otp_groups()
    buttons = []
    
    for idx, group_id in enumerate(groups, 1):
        is_default = "⭐" if group_id in DEFAULT_OTP_GROUPS else ""
        label = f"{is_default} Group {idx}: {group_id}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"admin_otp_group_detail_{idx}")])
    
    buttons.append([InlineKeyboardButton("➕ ADD GROUP", callback_data="admin_otp_group_add")])
    buttons.append([InlineKeyboardButton("🔙 BACK", callback_data="adm_menu_back_to_admin")])
    
    return InlineKeyboardMarkup(buttons)

def build_otp_group_detail_keyboard(group_idx):
    """একটি OTP গ্রুপের ডিটেইল কীবোর্ড"""
    groups = load_otp_groups()
    if group_idx > len(groups):
        return None
    
    group_id = groups[group_idx - 1]
    is_default = group_id in DEFAULT_OTP_GROUPS
    
    buttons = []
    if not is_default:
        buttons.append([InlineKeyboardButton("🗑️ REMOVE GROUP", callback_data=f"admin_otp_group_remove_{group_idx}")])
    else:
        buttons.append([InlineKeyboardButton("⭐ DEFAULT GROUP (Cannot Remove)", callback_data="admin_otp_group_default")])
    
    buttons.append([InlineKeyboardButton("🔙 BACK", callback_data="admin_otp_group_menu")])
    return InlineKeyboardMarkup(buttons)

# ==================== ADMIN MANAGEMENT KEYBOARDS ====================
def build_admin_management_keyboard():
    """অ্যাডমিন ম্যানেজমেন্ট কীবোর্ড"""
    admins = load_admins()
    buttons = []
    
    for idx, admin_id in enumerate(admins, 1):
        is_default = "⭐" if admin_id in DEFAULT_ADMINS else ""
        label = f"{is_default} Admin {idx}: {admin_id}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"admin_admin_detail_{idx}")])
    
    buttons.append([InlineKeyboardButton("➕ ADD ADMIN", callback_data="admin_admin_add")])
    buttons.append([InlineKeyboardButton("🔙 BACK", callback_data="adm_menu_back_to_admin")])
    
    return InlineKeyboardMarkup(buttons)

def build_admin_detail_keyboard(admin_idx):
    """একটি অ্যাডমিনের ডিটেইল কীবোর্ড"""
    admins = load_admins()
    if admin_idx > len(admins):
        return None
    
    admin_id = admins[admin_idx - 1]
    is_default = admin_id in DEFAULT_ADMINS
    
    buttons = []
    if not is_default:
        buttons.append([InlineKeyboardButton("🗑️ REMOVE ADMIN", callback_data=f"admin_admin_remove_{admin_idx}")])
    else:
        buttons.append([InlineKeyboardButton("⭐ DEFAULT ADMIN (Cannot Remove)", callback_data="admin_admin_default")])
    
    buttons.append([InlineKeyboardButton("🔙 BACK", callback_data="admin_admin_management")])
    return InlineKeyboardMarkup(buttons)

def build_manage_services_inline_keyboard():
    custom_svcs = load_custom_services()
    buttons = []
    for s in custom_svcs:
        sid = s.get("sid", "UNKNOWN")
        ranges_count = len(s.get("ranges", []))
        buttons.append([InlineKeyboardButton(make_bold_unicode(f"📁 {sid.upper()} ({ranges_count})"), callback_data=f"manage_svc_view_{sid}")])
    buttons.append([InlineKeyboardButton(make_bold_unicode("➕ ADD SERVICE"), callback_data="manage_svc_add")])
    buttons.append([InlineKeyboardButton(make_bold_unicode("🔙 BACK"), callback_data="adm_menu_back_to_admin")])
    return InlineKeyboardMarkup(buttons)

def build_service_detail_keyboard(service_name):
    custom_svcs = load_custom_services()
    target_svc = next((s for s in custom_svcs if s.get("sid", "").upper() == service_name.upper()), None)
    if not target_svc:
        return None
    grouped = get_grouped_countries_for_service(target_svc)
    buttons = []
    for cname, info in grouped.items():
        flag = info["flag"]
        buttons.append([InlineKeyboardButton(make_bold_unicode(f"{flag} {cname.upper()}"), callback_data=f"manage_svc_country_view_{service_name}_{cname}")])
    buttons.append([
        InlineKeyboardButton(make_bold_unicode("➕ ADD RANGE"), callback_data=f"manage_svc_add_range_{service_name}"),
        InlineKeyboardButton(make_bold_unicode("✏️ RENAME"), callback_data=f"manage_svc_rename_init_{service_name}")
    ])
    buttons.append([
        InlineKeyboardButton(make_bold_unicode("🗑️ DELETE SERVICE"), callback_data=f"manage_svc_delete_init_{service_name}")
    ])
    buttons.append([InlineKeyboardButton(make_bold_unicode("🔙 BACK"), callback_data="manage_svc_back_to_list")])
    return InlineKeyboardMarkup(buttons)

def build_country_detail_keyboard(service_name, country_name):
    custom_svcs = load_custom_services()
    target_svc = next((s for s in custom_svcs if s.get("sid", "").upper() == service_name.upper()), None)
    if not target_svc:
        return None
    grouped = get_grouped_countries_for_service(target_svc)
    info = grouped.get(country_name, {"flag": "🌍", "ranges": []})
    buttons = []
    for r_val in info["ranges"]:
        api_label = ""
        for r in target_svc.get("ranges", []):
            if r.get("range", "").upper() == r_val.upper():
                api_choice = r.get("api_key", DEFAULT_API_KEY)
                api_label = get_api_key_label(api_choice)
                break
        buttons.append([
            InlineKeyboardButton(make_bold_unicode(f"❌ {r_val} {api_label}"), callback_data=f"manage_svc_delete_range_{service_name}_{country_name}_{r_val}"),
            InlineKeyboardButton(make_bold_unicode("✏️ EDIT"), callback_data=f"manage_svc_edit_range_init_{service_name}_{country_name}_{r_val}")
        ])
    buttons.append([
        InlineKeyboardButton(make_bold_unicode("➕ ADD RANGE"), callback_data=f"manage_svc_add_range_{service_name}_{country_name}"),
        InlineKeyboardButton(make_bold_unicode("✏️ RENAME COUNTRY"), callback_data=f"manage_svc_rename_country_init_{service_name}_{country_name}")
    ])
    buttons.append([InlineKeyboardButton(make_bold_unicode("🗑️ DELETE COUNTRY"), callback_data=f"manage_svc_delete_country_confirm_{service_name}_{country_name}")])
    buttons.append([InlineKeyboardButton(make_bold_unicode("🔙 BACK"), callback_data=f"manage_svc_view_{service_name}")])
    return InlineKeyboardMarkup(buttons)

def get_admin_panel_text():
    users_list = get_all_users()
    users = len(users_list)
    banned = len(load_banned_users())
    custom_svcs = load_custom_services()
    total_ranges = sum(len(s.get("ranges", [])) for s in custom_svcs)
    stats_data = load_stats()
    total_otps = 0
    for u in stats_data.values():
        total_otps += len(u.get("otps_received", []))
    
    admins = load_admins()
    otp_groups = load_otp_groups()
    
    text = (
        "👑 <b>ADMIN CONTROL PANEL</b> 👑\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 <b>REAL-TIME DATABASE STATS</b>\n\n"
        f"👥 <b>Total Users:</b> <code>{users}</code>\n"
        f"📶 <b>Active Ranges:</b> <code>{total_ranges}</code>\n"
        f"🔑 <b>Processed OTPs:</b> <code>{total_otps}</code>\n"
        f"🚫 <b>Banned Accounts:</b> <code>{banned}</code>\n"
        f"👑 <b>Total Admins:</b> <code>{len(admins)}</code>\n"
        f"📢 <b>OTP Groups:</b> <code>{len(otp_groups)}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💎 <i>PANEL X SMS Bot • Live & Operating</i>"
    )
    return text

# ==================== DATABASE FUNCTIONS SECTION ====================

def load_data(filename=USER_DATA_FILE):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data, filename=USER_DATA_FILE):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def get_user(uid):
    uid = str(uid)
    data = load_data()
    if uid not in data:
        data[uid] = {"user_id": uid, "balance": 0.0, "total_numbers": 0, "referral_count": 0}
        save_data(data)
    return data[uid]

async def update_db_balance(uid, amount):
    uid = str(uid)
    data = load_data()
    if uid in data:
        data[uid]["balance"] = round(data[uid].get("balance", 0.0) + amount, 2)
        save_data(data)
        return data[uid]["balance"]
    return 0.0

def get_all_users():
    data = load_data(USER_DATA_FILE)
    return list(data.keys()) if data else []

def user_exists(uid):
    data = load_data(USER_DATA_FILE)
    return str(uid) in data

# ==================== STATS FUNCTIONS SECTION ====================

def load_stats():
    if not os.path.exists(STATS_FILE):
        with open(STATS_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)

def add_number_taken(uid, count=1):
    uid = str(uid)
    stats = load_stats()
    if uid not in stats:
        stats[uid] = {"numbers_taken": [], "otps_received": []}
    if "numbers_taken" not in stats[uid]:
        stats[uid]["numbers_taken"] = []
    now = get_bangladesh_time().isoformat()
    for _ in range(count):
        stats[uid]["numbers_taken"].append(now)
    log_global_activity(uid, "NUMBER_TAKEN", {"count": count})
    save_stats(stats)

def add_otp_received(uid):
    uid = str(uid)
    stats = load_stats()
    if uid not in stats:
        stats[uid] = {"numbers_taken": [], "otps_received": []}
    if "otps_received" not in stats[uid]:
        stats[uid]["otps_received"] = []
    stats[uid]["otps_received"].append(get_bangladesh_time().isoformat())
    save_stats(stats)

def get_user_stats(uid):
    uid = str(uid)
    stats = load_stats()
    user_stats = stats.get(uid, {"numbers_taken": [], "otps_received": []})
    now = get_bangladesh_time()
    today_midnight = get_date_reset_time()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    numbers_taken = user_stats.get("numbers_taken", [])
    otps_received = user_stats.get("otps_received", [])
    today_numbers = 0
    today_otps = 0
    last24h_numbers = 0
    last24h_otps = 0
    last7d_numbers = 0
    last7d_otps = 0
    for t in numbers_taken:
        try:
            dt = datetime.fromisoformat(t)
            if dt >= today_midnight: today_numbers += 1
            if dt > last_24h: last24h_numbers += 1
            if dt > last_7d: last7d_numbers += 1
        except:
            continue
    for t in otps_received:
        try:
            dt = datetime.fromisoformat(t)
            if dt >= today_midnight: today_otps += 1
            if dt > last_24h: last24h_otps += 1
            if dt > last_7d: last7d_otps += 1
        except:
            continue
    total_numbers = len(numbers_taken)
    total_otps = len(otps_received)
    return {
        "total_numbers": total_numbers, "total_otps": total_otps,
        "today_numbers": today_numbers, "today_otps": today_otps,
        "last24h_numbers": last24h_numbers, "last24h_otps": last24h_otps,
        "last7d_numbers": last7d_numbers, "last7d_otps": last7d_otps
    }

def log_global_activity(uid, action, details):
    if not os.path.exists(ACTIVITY_LOGS_FILE):
        with open(ACTIVITY_LOGS_FILE, "w") as f:
            json.dump([], f)
    try:
        with open(ACTIVITY_LOGS_FILE, "r") as f:
            logs = json.load(f)
    except:
        logs = []
    now = get_bangladesh_time()
    logs.append({
        "uid": str(uid), "action": action, "details": details,
        "timestamp": now.isoformat(),
        "date": now.strftime("%d/%m/%Y"),
        "time": now.strftime("%H:%M:%S")
    })
    with open(ACTIVITY_LOGS_FILE, "w") as f:
        json.dump(logs, f, indent=4)

def get_global_system_stats():
    stats = load_stats()
    now = get_bangladesh_time()
    today_midnight = datetime(now.year, now.month, now.day)
    last_7d = now - timedelta(days=7)
    total_n = total_o = today_n = today_o = seven_n = seven_o = 0
    for uid in stats:
        u = stats[uid]
        n_list = u.get("numbers_taken", [])
        o_list = u.get("otps_received", [])
        total_n += len(n_list)
        total_o += len(o_list)
        for t in n_list:
            try:
                dt = datetime.fromisoformat(t)
                if dt >= today_midnight: today_n += 1
                if dt >= last_7d: seven_n += 1
            except:
                continue
        for t in o_list:
            try:
                dt = datetime.fromisoformat(t)
                if dt >= today_midnight: today_o += 1
                if dt >= last_7d: seven_o += 1
            except:
                continue
    return today_n, today_o, seven_n, seven_o, total_n, total_o

# ==================== LEADERBOARD SECTION ====================

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    stats_data = load_stats()
    today_midnight = get_date_reset_time()
    user_data_all = load_data(USER_DATA_FILE)
    user_today_counts = []
    for uid_str, user_stats in stats_data.items():
        otps_received = user_stats.get("otps_received", [])
        today_count = 0
        for ts in otps_received:
            try:
                dt = datetime.fromisoformat(ts)
                if dt >= today_midnight:
                    today_count += 1
            except:
                continue
        if today_count > 0:
            name = user_data_all.get(uid_str, {}).get("full_name")
            if not name:
                name = user_data_all.get(uid_str, {}).get("username")
            if not name:
                name = f"User {uid_str}"
            user_today_counts.append((uid_str, today_count, html.escape(name)))
    user_today_counts.sort(key=lambda x: x[1], reverse=True)
    top10 = user_today_counts[:10]
    if not top10:
        msg = (
            "<b>🏆 TOP 10 OTP LEADERBOARD 🏆</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "❌ আজ পর্যন্ত কেউ OTP পায়নি।\n"
        )
    else:
        msg = (
            "<b>🏆 TOP 10 OTP RECEIVERS (TODAY) 🏆</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        for idx, (uid_str, count, name) in enumerate(top10, 1):
            if idx == 1:
                medal = "🥇"
            elif idx == 2:
                medal = "🥈"
            elif idx == 3:
                medal = "🥉"
            else:
                medal = f"{idx}️⃣"
            msg += f"{medal} <b>{name}</b>\n   🔑 <code>{count}</code> OTPs\n\n"
        msg += (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📊 <i>প্রতিদিন রাত ১২টায় রিসেট হয়</i>"
        )
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=main_keyboard(uid))

# ==================== GET NUMBER — SERVICE SELECTION ====================

def _build_services_keyboard(services):
    temp_btns = []
    for i, svc in enumerate(services):
        sid = svc.get("sid", f"Service {i+1}")
        ranges = svc.get("ranges", [])
        label = f"🚀 {sid} ({len(ranges)})"
        temp_btns.append(InlineKeyboardButton(label, callback_data=f"svc_{i}"))
    rows = [temp_btns[j:j+2] for j in range(0, len(temp_btns), 2)]
    return InlineKeyboardMarkup(rows)

def _build_countries_keyboard(ranges, service_idx):
    btns = []
    seen = {}
    for i, r_item in enumerate(ranges[:24]):
        r_text = r_item.get("range", "")
        country_display = r_item.get("country", "")
        if not country_display:
            prefix = re.sub(r'[xX]+$', '', str(r_text)).strip()
            prefix_clean = re.sub(r'\D', '', prefix)
            flag, cname = get_country_info(prefix_clean)
            country_display = f"{flag} {cname}"
        label = f"{country_display}"
        if label not in seen:
            seen[label] = i
            btns.append(InlineKeyboardButton(label, callback_data=f"rng_{i}"))
    rows = [btns[j:j+2] for j in range(0, len(btns), 2)]
    rows.append([InlineKeyboardButton("◀️ BACK", callback_data="back_services")])
    return InlineKeyboardMarkup(rows)

async def show_app_selection(update, context):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    services = load_custom_services()
    if not services:
        await update.message.reply_text(
            "⚠️ <b>দুঃখিত, এই মুহূর্তে কোনো সার্ভিস উপলব্ধ নেই।</b>\n⏳ অ্যাডমিন কর্তৃক সার্ভিস অ্যাড করার জন্য অপেক্ষা করুন।",
            parse_mode="HTML",
            reply_markup=main_keyboard(uid)
        )
        return
    context.user_data["la_services"] = services
    keyboard = _build_services_keyboard(services)
    await update.message.reply_text(
        "📞 <b>GET NUMBER</b>\n\n"
        "<blockquote>✨ নিচ থেকে আপনার পছন্দের <b>Service</b> নির্বাচন করুন:</blockquote>",
        parse_mode="HTML",
        reply_markup=keyboard
    )

# ==================== AUTO OTP MONITOR SECTION ====================

async def monitor_loop(app):
    while True:
        try:
            # Check API 01
            api_key_01, base_url_01 = get_api_credentials_by_choice("API_KEY_01")
            headers_01 = {
                "X-API-Key": api_key_01,
                "Accept": "application/json, text/plain, */*",
                "Connection": "keep-alive"
            }
            r = await client_async.get(f"{base_url_01}/api/success-otp-info", headers=headers_01)
            if r.status_code == 200:
                try:
                    res = r.json()
                    otps = parse_otp_response(res, "API_KEY_01")
                    if otps:
                        await process_otps(otps, "API_KEY_01", app)
                except:
                    pass
            
            # Check API 02 (New 2oo9 API)
            api_key_02, base_url_02 = get_api_credentials_by_choice("API_KEY_02")
            headers_02 = {
                "mauthapi": api_key_02,
                "Accept": "application/json, text/plain, */*",
                "Connection": "keep-alive"
            }
            r2 = await client_async.get(f"{base_url_02}/success-otp", headers=headers_02)
            if r2.status_code == 200:
                try:
                    res2 = r2.json()
                    otps = parse_otp_response(res2, "API_KEY_02")
                    if otps:
                        await process_otps(otps, "API_KEY_02", app)
                except:
                    pass
            
        except Exception as e:
            print(f"Monitor Error: {e}")
        await asyncio.sleep(CHECK_INTERVAL)

async def send_otp_to_groups(app, group_msg, group_buttons):
    """সকল OTP গ্রুপে মেসেজ পাঠায়"""
    groups = load_otp_groups()
    success_count = 0
    fail_count = 0
    
    for group_id in groups:
        try:
            await app.bot.send_message(
                group_id, 
                group_msg, 
                parse_mode="HTML", 
                reply_markup=group_buttons
            )
            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f"❌ Group Send Fail ({group_id}): {e}")
    
    return success_count, fail_count

async def process_otps(otps, api_choice, app):
    """OTP প্রসেস করে"""
    paid_data = load_data(PAID_SMS_FILE)
    range_db = load_data(DATA_RANGE_FILE)
    paid_keys_set = set(paid_data.keys())
    processed_in_session = set()
    
    for otp in otps:
        num = normalize_number(otp.get("number") or "")
        full_sms = otp.get("message") or otp.get("sms") or otp.get("text") or "No SMS Content"
        
        otp_code = extract_otp_from_message(full_sms)
        if not otp_code:
            continue
        
        service_name = detect_service(full_sms)
        sms_key = f"{num}_{full_sms[:50]}"
        
        matched_key = None
        for active_num in active_numbers.keys():
            if numbers_match(num, active_num):
                matched_key = active_num
                break
        
        if (matched_key is not None and
                sms_key not in paid_keys_set and
                sms_key not in processed_in_session):
            details = active_numbers[matched_key]
            paid_keys_set.add(sms_key)
            processed_in_session.add(sms_key)
            paid_data[sms_key] = {"uid": details["uid"], "otp": otp_code}
            await update_db_balance(details["uid"], OTP_RATE)
            add_otp_received(details["uid"])
            log_global_activity(details["uid"], "OTP_RECEIVED", {"number": matched_key, "otp": otp_code, "sms": full_sms})
            
            num_range_info = range_db.get(matched_key, {}).get("range", "")
            if not num_range_info:
                num_range_info = active_numbers.get(matched_key, {}).get("range", "")
            if not num_range_info and matched_key:
                _d = re.sub(r'\D', '', str(matched_key))
                num_range_info = (_d[:-3] + 'XXX') if len(_d) > 3 else (_d + 'XXX')
            
            country_flag, country_name = get_country_info(matched_key)
            clean_num = matched_key.replace('+', '').strip()
            full_number = f"+{clean_num}"
            masked_number = f"+{mask_number(clean_num)}"
            safe_full_sms = html.escape(str(full_sms))
            safe_otp_code = html.escape(str(otp_code))
            
            # ইউজারের শেষ ডেটা সংরক্ষণ
            user_last_data[details["uid"]] = {
                "last_range": num_range_info,
                "last_service": service_name,
                "last_country": f"{country_flag} {country_name}",
                "last_number": matched_key
            }
            
            # ============ UPDATED USER MESSAGE WITH BUTTONS ============
            user_msg = (
                f"✅ <b>OTP RECEIVE SUCCESSFUL</b> ✅\n\n"
                f"<blockquote>🌍 COUNTRY: <code>{country_flag} {country_name}</code></blockquote>\n"
                f"<blockquote>📱 SERVICE: <code>{service_name}</code></blockquote>\n"
                f"<blockquote>📞 NUMBER: <code>{full_number}</code></blockquote>\n"
                f"<blockquote>🔑 OTP: <code>{safe_otp_code}</code></blockquote>\n"
                f"<blockquote>📩 FULL SMS:\n<code>{safe_full_sms}</code></blockquote>\n\n"
                f"<b>💵 ADD BALANCE FOR {OTP_RATE:.2f} BDT</b>"
            )
            
            # ============ NEW INLINE BUTTONS ============
            user_buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 CHANGE NUMBER", callback_data=f"change_number_{details['uid']}"),
                    InlineKeyboardButton("🌏 CHANGE COUNTRY", callback_data=f"change_country_{details['uid']}")
                ],
                [
                    InlineKeyboardButton("📢 OTP GROUP", url="https://t.me/sure_otp_suppor")
                ]
            ])
            
            group_msg = (
                f"✅ <b>OTP RECEIVE SUCCESSFUL</b> ✅\n\n"
                f"<blockquote>📶 RANGE: <code>{num_range_info}</code></blockquote>\n"
                f"<blockquote>🌍 COUNTRY: <code>{country_flag} {country_name}</code></blockquote>\n"
                f"<blockquote>📱 SERVICE: <code>{service_name}</code></blockquote>\n"
                f"<blockquote>📞 NUMBER: <code>{masked_number}</code></blockquote>\n"
                f"<blockquote>🔑 OTP: <code>{safe_otp_code}</code></blockquote>\n"
                f"<blockquote>📩 FULL SMS:\n<code>{safe_full_sms}</code></blockquote>"
            )
            
            group_buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("‼️ NUMBER ", url="https://t.me/Sure_otp07_bot"),
                    InlineKeyboardButton("📢 CHANNEL", url="https://t.me/sure_otp_suppor")
                ]
            ])
            
            try:
                await app.bot.send_message(
                    details["uid"], 
                    user_msg, 
                    parse_mode="HTML",
                    reply_markup=user_buttons
                )
            except Exception as e:
                print(f"❌ User Message Send Fail: {e}")
            
            # ============ SEND TO ALL OTP GROUPS ============
            success, fail = await send_otp_to_groups(app, group_msg, group_buttons)
            print(f"📊 OTP Groups: Success={success}, Failed={fail}")
            
            save_data(paid_data, PAID_SMS_FILE)
    
    current_time = datetime.now()
    for num_key in list(active_numbers.keys()):
        entry = active_numbers[num_key]
        if 'timestamp' not in entry:
            entry['timestamp'] = current_time
        elif (current_time - entry['timestamp']).total_seconds() > 3600:
            del active_numbers[num_key]

# ==================== WORKER & API SECTION ====================

async def fetch_number_async(range_str):
    try:
        api_choice = get_api_key_for_range(range_str)
        api_key, base_url = get_api_credentials_by_choice(api_choice)
        
        if api_choice == "API_KEY_01":
            url = f"{base_url}/api/getnum"
            payload = {"range": range_str}
            headers = {
                "X-API-Key": api_key,
                "Accept": "application/json, text/plain, */*",
                "Connection": "keep-alive",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            r = await client_async.post(url, json=payload, headers=headers)
            if r.status_code != 200:
                return None
            try:
                data = r.json()
            except:
                return None
            return parse_number_response(data, "API_KEY_01")
        
        elif api_choice == "API_KEY_02":
            clean_range = re.sub(r'[xX]+$', '', str(range_str)).strip()
            url = f"{base_url}/getnum"
            payload = {"rid": clean_range}
            headers = {
                "mauthapi": api_key,
                "Accept": "application/json, text/plain, */*",
                "Connection": "keep-alive",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            r = await client_async.post(url, json=payload, headers=headers)
            if r.status_code != 200:
                print(f"2oo9 API Error: HTTP {r.status_code}")
                return None
            try:
                data = r.json()
            except:
                return None
            return parse_number_response(data, "API_KEY_02")
        
        return None
        
    except httpx.ReadTimeout:
        print(f"Fetch number error: ReadTimeout for range {range_str}")
    except Exception as e:
        print(f"Fetch number error: {e}")
    return None

async def fast_allocate_number_multi(query, context, ranges_list, sid):
    uid = query.from_user.id
    if is_user_banned(uid):
        await query.message.edit_text("🚫 YOU ARE BANNED 🚫")
        return
    try:
        await query.message.edit_text(
            "⚡ <b>ALLOCATING YOUR NUMBER</b> ⚡\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔍 <i>Searching active pool... Please wait.</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Edit loading state error: {e}")
    
    res = None
    successful_range = None
    for r_text in ranges_list:
        try:
            res = await fetch_number_async(r_text)
            if res and res.get("number"):
                successful_range = r_text
                break
        except Exception as e:
            print(f"Error trying range {r_text}: {e}")
            continue
    
    if not res or not res.get("number"):
        try:
            await query.message.edit_text(
                "❌ <b>Number পাওয়া যায়নি।</b>\n\n"
                "<blockquote>⚠️ এই range/country-তে এখন number নেই বা server busy।\n"
                "অন্য কোনো সার্ভিস বা কান্ট্রি চেষ্টা করুন।</blockquote>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 BACK", callback_data="back_services")
                ]])
            )
        except:
            pass
        return
    
    clean_num = normalize_number(res["number"])
    add_number_taken(uid, 1)
    last_range[uid] = successful_range
    active_numbers[clean_num] = {"uid": uid, "range": successful_range, "timestamp": datetime.now()}
    save_number_range_info(uid, clean_num, successful_range)
    country_flag, country_name = get_country_info(clean_num)
    
    # ইউজারের শেষ ডেটা সংরক্ষণ
    user_last_data[uid] = {
        "last_range": successful_range,
        "last_service": sid,
        "last_country": f"{country_flag} {country_name}",
        "last_number": clean_num
    }
    
    text = (
        f"✅ <b>YOUR NUMBER</b> ✅\n\n"
        f"<blockquote>🌍 COUNTRY: <code>{country_flag} {html.escape(country_name)}</code></blockquote>\n"
        f"<blockquote>📶 RANGE: <code>{successful_range}</code></blockquote>\n"
        f"<blockquote>📞 NUMBER: <code>+{clean_num}</code></blockquote>\n\n"
        f"<b>📩 SMS STATUS: ⏳ WAITING...</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 CHANGE NUMBER", callback_data=f"change_number_{uid}"),
            InlineKeyboardButton("🌏 CHANGE COUNTRY", callback_data=f"change_country_{uid}")
        ],
        [InlineKeyboardButton("📢 OTP GROUP", url="https://t.me/SURE_OTP_GROUP")]
    ])
    try:
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        print(f"fast_allocate edit error: {e}")

async def worker():
    while True:
        task = await request_queue.get()
        try:
            if task['type'] == 'process_numbers':
                await process_numbers(task['update'], task['context'], task['range_text'], task['count'])
            elif task['type'] == 'auto_number':
                await process_auto_number(task['update'], task['context'], task['range_text'])
        except Exception as e:
            print(f"Worker Error: {e}")
        finally:
            request_queue.task_done()

# ==================== AUTO NUMBER FROM LINK / DEEP LINK ====================

async def process_auto_number(update, context, range_text):
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    if is_user_banned(uid):
        await context.bot.send_message(chat_id=chat_id, text="🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    status_msg = await context.bot.send_message(chat_id=chat_id, text="🔍 SEARCHING...")
    try:
        res = await fetch_number_async(range_text)
        if not res:
            await status_msg.edit_text("❌ NO NUMBERS FOUND. TRY A VALID RANGE.")
            return
        generated_num = normalize_number(res["number"]) if res else None
        if not generated_num:
            await status_msg.edit_text("❌ NO NUMBERS FOUND. TRY A VALID RANGE.")
            return
        add_number_taken(uid, 1)
        last_range[uid] = range_text
        active_numbers[generated_num] = {"uid": uid, "range": range_text, "timestamp": datetime.now()}
        save_number_range_info(uid, generated_num, range_text)
        country_flag, country_name = get_country_info(generated_num)
        
        final_text = (
            f"✅ <b>YOUR NUMBER DETAILS</b> ✅\n\n"
            f"<blockquote>🌍 COUNTRY: <code>{country_flag} {country_name}</code></blockquote>\n"
            f"<blockquote>📶 RANGE: <code>{range_text}</code></blockquote>\n\n"
            f"<blockquote>📞 NUMBER: <code>+{generated_num}</code></blockquote>\n\n"
            f"<b>📩 SMS STATUS: ⏳ WAITING...</b>"
        )
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 CHANGE NUMBER", callback_data=f"change_number_{uid}"),
                InlineKeyboardButton("🌏 CHANGE COUNTRY", callback_data=f"change_country_{uid}")
            ],
            [InlineKeyboardButton("📢 OTP GROUP", url="https://t.me/panelx_sk_otp")]
        ])
        await status_msg.edit_text(final_text, parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        print(f"Auto Number Error: {e}")
        await status_msg.edit_text(f"❌ Error: {str(e)}")

# ==================== USER PANEL — PROCESS NUMBERS ====================

async def process_numbers(update_or_query, context, range_text, count):
    if isinstance(update_or_query, Update) and update_or_query.callback_query:
        uid = update_or_query.callback_query.from_user.id
        chat_id = update_or_query.callback_query.message.chat_id
    else:
        uid = update_or_query.effective_user.id
        chat_id = update_or_query.effective_chat.id

    if is_user_banned(uid):
        await context.bot.send_message(chat_id=chat_id, text="🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return

    status_msg = await context.bot.send_message(chat_id=chat_id, text="🔍 SEARCHING . . .")

    try:
        add_number_taken(uid, count)
        last_range[uid] = range_text
        
        tasks = [fetch_number_async(range_text) for _ in range(count)]
        results = await asyncio.gather(*tasks)
        valid_results = [r for r in results if r and r.get("number")]

        if not valid_results:
            await status_msg.edit_text("❌ NO NUMBERS FOUND. TRY A VALID RANGE.")
            return

        num_entries = []
        for r in valid_results:
            clean_num = normalize_number(r["number"])
            if clean_num:
                active_numbers[clean_num] = {"uid": uid, "range": range_text, "timestamp": datetime.now()}
                save_number_range_info(uid, clean_num, range_text)
                num_entries.append({
                    "num": clean_num,
                    "otp_now": r.get("otp_now", False),
                    "otp": r.get("otp"),
                    "sms": r.get("sms"),
                })

        if not num_entries:
            await status_msg.edit_text("❌ NO NUMBERS FOUND. TRY A VALID RANGE.")
            return

        country_flag, country_name = get_country_info(num_entries[0]["num"])

        num_lines = []
        for entry in num_entries:
            line = f"<blockquote>📞 NUMBER: <code>+{entry['num']}</code></blockquote>"
            num_lines.append(line)

        num_list_text = "\n".join(num_lines)

        final_text = (
            f"✅ <b>YOUR NUMBER DETAILS</b> ✅\n\n"
            f"<blockquote>🌍 COUNTRY: <code>{country_flag} {country_name}</code></blockquote>\n"
            f"<blockquote>📶 RANGE: <code>{range_text}</code></blockquote>\n\n"
            f"{num_list_text}\n\n"
            f"<b>📩 SMS STATUS: ⏳ WAITING...</b>"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 CHANGE NUMBER", callback_data=f"change_number_{uid}"),
                InlineKeyboardButton("🌏 CHANGE COUNTRY", callback_data=f"change_country_{uid}")
            ],
            [InlineKeyboardButton("📢 OTP GROUP", url="https://t.me/panelx_sk_otp")]
        ])

        await status_msg.edit_text(final_text, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        print(f"Process Number Error: {e}")
        await status_msg.edit_text(f"❌ System Error: {str(e)}")

# ==================== REFER AND EARN SECTION ====================

async def refer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    user_data = get_user(uid)
    bot_info = await context.bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start={uid}"
    successful_refers = get_referral_count(uid)
    total_reward = float(successful_refers) * REFERRAL_PRICE
    refer_msg = (
        f"🎁 <b>REFER AND EARN SYSTEM</b> 🎁\n\n"
        f"<blockquote>🚀 INVITE FRIENDS &amp; EARN {int(REFERRAL_PRICE)} BDT EACH! 💸</blockquote>\n\n"
        f"<b>🔗 YOUR REFERRAL LINK:</b>\n"
        f"<blockquote><code>{referral_link}</code></blockquote>\n\n"
        f"<b>📊 YOUR STATS:</b>\n"
        f"<blockquote>👥 TOTAL REFERS: {successful_refers}\n"
        f"💰 TOTAL EARNED: {format_balance(total_reward)} BDT</blockquote>\n\n"
        f"✨ <b>SHARE LINK &amp; EARN MONEY!</b> ✨"
    )
    await update.message.reply_text(
        refer_msg,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("👥 YOUR REFERRAL", callback_data=f"my_ref_{uid}")
        ]])
    )

# ==================== WITHDRAW FUNCTIONS ====================

async def withdraw_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id
    if text == "❌ CANCEL":
        context.user_data["withdraw_mode"] = None
        await update.message.reply_text("❌ WITHDRAW CANCELLED", reply_markup=main_keyboard(uid))
        return
    method_map = {"📱 BKASH": "BKASH", "💵 NAGAD": "NAGAD", "🚀 ROCKET": "ROCKET", "🏦 BINANCE": "BINANCE"}
    if text in method_map:
        balance = get_user(uid)['balance']
        context.user_data["withdraw_method"] = method_map[text]
        context.user_data["withdraw_mode"] = "amount"
        msg = (
            f"<blockquote>💸 SEND YOUR AMOUNT!\n"
            f"💵 TOTAL BALANCE: {format_balance(balance)} BDT</blockquote>\n\n"
            f"<blockquote>📉 MINIMUM WITHDRAW {MIN_WITHDRAW} BDT</blockquote>"
        )
        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=cancel_keyboard())
    else:
        await update.message.reply_text("⚠️ PLEASE SELECT A VALID PAYMENT METHOD!", reply_markup=withdraw_method_keyboard())

async def withdraw_amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id
    if text == "❌ CANCEL":
        context.user_data["withdraw_mode"] = None
        await update.message.reply_text("❌ WITHDRAW CANCELLED", reply_markup=main_keyboard(uid))
        return
    try:
        amount = float(text)
    except:
        await update.message.reply_text("⚠️ PLEASE SEND A VALID AMOUNT!", reply_markup=cancel_keyboard())
        return
    balance = get_user(uid)['balance']
    if amount < MIN_WITHDRAW or amount > MAX_WITHDRAW:
        await update.message.reply_text(f"📉 MIN: {MIN_WITHDRAW} BDT | MAX: {MAX_WITHDRAW} BDT", reply_markup=cancel_keyboard())
        return
    if amount > balance:
        await update.message.reply_text("🚫 INSUFFICIENT BALANCE!", reply_markup=cancel_keyboard())
        return
    context.user_data["withdraw_amount"] = amount
    context.user_data["withdraw_mode"] = "number"
    await update.message.reply_text(
        "📞 PLEASE SEND YOUR PAYMENT NUMBER!\n\n<blockquote>🔢 EXAMPLE: 017XXXXXXXX</blockquote>",
        parse_mode="HTML", reply_markup=cancel_keyboard()
    )

async def withdraw_number_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id
    if text == "❌ CANCEL":
        context.user_data["withdraw_mode"] = None
        await update.message.reply_text("❌ WITHDRAW CANCELLED", reply_markup=main_keyboard(uid))
        return
    if not is_valid_bangladesh_number(text):
        await update.message.reply_text("⚠️ PLEASE SEND VALID NUMBER! 017XXXXXXXX", reply_markup=cancel_keyboard())
        return
    method = context.user_data.get("withdraw_method")
    amount = context.user_data.get("withdraw_amount")
    payment_number = text
    payment_id = generate_payment_id()
    context.user_data["temp_withdraw"] = {
        "method": method, "amount": amount,
        "number": payment_number, "payment_id": payment_id
    }
    msg = (
        "✨ <b>YOUR PAYMENT DETAILS!</b> ✨\n\n"
        f"<blockquote>📝 METHOD: {method}\n"
        f"📞 NUMBER: {payment_number}\n\n"
        f"✅ CORRECT → CONFIRM\n❌ WRONG → CANCEL</blockquote>"
    )
    await update.message.reply_text(
        msg, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ CANCEL", callback_data="withdraw_cancel"),
            InlineKeyboardButton("✅ CONFIRM", callback_data="withdraw_confirm")
        ]])
    )

async def process_withdraw_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()
    temp_data = context.user_data.get("temp_withdraw")
    if not temp_data:
        await query.message.reply_text("⚠️ SESSION EXPIRED.", reply_markup=main_keyboard(uid))
        return
    method = temp_data["method"]
    amount = temp_data["amount"]
    payment_number = temp_data["number"]
    payment_id = temp_data["payment_id"]
    new_balance = await update_db_balance(uid, -amount)
    wr = load_withdraw_requests()
    wr[str(payment_id)] = {
        "user_id": uid, "method": method, "amount": amount,
        "number": payment_number, "payment_id": payment_id,
        "status": "pending", "timestamp": datetime.now().isoformat()
    }
    save_withdraw_requests(wr)
    await query.message.edit_text(
        f"✅ <b>WITHDRAWAL REQUEST SUBMITTED</b> ✅\n\n"
        f"<blockquote>📝 METHOD: <code>{method}</code>\n"
        f"📞 NUMBER: <code>{payment_number}</code>\n"
        f"💰 AMOUNT: <code>{format_balance(amount)} BDT</code>\n"
        f"🆔 ID: <code>{payment_id}</code></blockquote>",
        parse_mode="HTML"
    )
    await context.bot.send_message(uid, "🎉 <b>WITHDRAW REQUEST SUBMITTED!</b>", parse_mode="HTML", reply_markup=main_keyboard(uid))
    admin_msg = (
        f"✅ <b>NEW WITHDRAWAL REQUEST</b>\n\n"
        f"<blockquote>🆔 USER: <code>{uid}</code>\n"
        f"📝 METHOD: <code>{method}</code>\n"
        f"📞 NUMBER: <code>{payment_number}</code>\n"
        f"💰 AMOUNT: <code>{format_balance(amount)} BDT</code>\n"
        f"🆔 ID: <code>{payment_id}</code></blockquote>"
    )
    admin_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ REJECT", callback_data=f"admin_reject_{payment_id}"),
        InlineKeyboardButton("✅ APPROVE", callback_data=f"admin_approve_{payment_id}")
    ]])
    for admin_id in load_admins():
        try:
            await context.bot.send_message(admin_id, admin_msg, parse_mode="HTML", reply_markup=admin_kb)
        except Exception as e:
            print(f"Admin notify fail {admin_id}: {e}")
    context.user_data["temp_withdraw"] = None
    context.user_data["withdraw_mode"] = None

async def process_withdraw_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()
    context.user_data["temp_withdraw"] = None
    context.user_data["withdraw_mode"] = None
    await query.message.edit_text("❌ WITHDRAW CANCELLED")
    await context.bot.send_message(uid, "🔹 PLEASE USE THE BUTTONS BELOW:", reply_markup=main_keyboard(uid))

# ==================== ADMIN PANEL - WITHDRAW APPROVAL ====================

async def admin_approve_withdraw(update, context, payment_id):
    query = update.callback_query
    await query.answer()
    wr = load_withdraw_requests()
    if payment_id not in wr:
        await query.message.reply_text("⚠️ REQUEST NOT FOUND!")
        return
    rd = wr[payment_id]
    uid = rd["user_id"]
    method = rd["method"]
    amount = rd["amount"]
    payment_number = rd["number"]
    wr[payment_id]["status"] = "approved"
    save_withdraw_requests(wr)
    try:
        await context.bot.send_message(
            uid,
            f"🎉 <b>WITHDRAWAL APPROVED!</b>\n\n"
            f"<blockquote>📝 METHOD: <code>{method}</code>\n"
            f"📞 NUMBER: <code>{payment_number}</code>\n"
            f"💰 AMOUNT: <code>{format_balance(amount)} BDT</code></blockquote>",
            parse_mode="HTML"
        )
    except:
        pass
    await query.message.edit_text(f"✅ APPROVED | User: {uid} | Amount: {format_balance(amount)} BDT")

async def admin_reject_withdraw(update, context, payment_id):
    query = update.callback_query
    await query.answer()
    wr = load_withdraw_requests()
    if payment_id not in wr:
        await query.message.reply_text("⚠️ REQUEST NOT FOUND!")
        return
    rd = wr[payment_id]
    uid = rd["user_id"]
    amount = rd["amount"]
    wr[payment_id]["status"] = "rejected"
    save_withdraw_requests(wr)
    try:
        await context.bot.send_message(uid, "❌ **WITHDRAWAL REQUEST REJECTED**\n\nContact admin for more info.", parse_mode="Markdown")
    except:
        pass
    await query.message.edit_text(f"❌ REJECTED | User: {uid} | Amount: {format_balance(amount)} BDT")

# ==================== ADMIN PANEL - BAN/UNBAN & BALANCE ====================

async def process_add_balance_user(update, context):
    uid_to_add = update.message.text.strip()
    if not uid_to_add.isdigit():
        await update.message.reply_text("❌ INVALID USER ID!")
        return
    uid_to_add_int = int(uid_to_add)
    if not user_exists(uid_to_add_int):
        await update.message.reply_text("❌ USER NOT FOUND!")
        context.user_data["add_balance_mode"] = False
        return
    context.user_data["pending_add_user"] = uid_to_add_int
    await update.message.reply_text("💵 SEND AMOUNT TO ADD:")

async def process_remove_balance_user(update, context):
    uid_to_remove = update.message.text.strip()
    if not uid_to_remove.isdigit():
        await update.message.reply_text("❌ INVALID USER ID!")
        return
    uid_to_remove_int = int(uid_to_remove)
    if not user_exists(uid_to_remove_int):
        await update.message.reply_text("❌ USER NOT FOUND!")
        context.user_data["remove_balance_mode"] = False
        return
    context.user_data["pending_remove_user"] = uid_to_remove_int
    await update.message.reply_text("💸 SEND AMOUNT TO REMOVE:")

async def process_add_balance_amount(update, context):
    try:
        amount = float(update.message.text.strip())
        if amount <= 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ INVALID AMOUNT!")
        return
    uid = context.user_data.get("pending_add_user")
    if not uid:
        context.user_data["add_balance_mode"] = False
        await update.message.reply_text("⚠️ SESSION EXPIRED.")
        return
    old_balance = get_user(uid).get("balance", 0)
    new_balance = await update_db_balance(uid, amount)
    await update.message.reply_text(
        f"✅ **ADD BALANCE SUCCESSFUL**\n🆔 USER: `{uid}`\n"
        f"💰 ADDED: `{format_balance(amount)} BDT`\n"
        f"📈 NEW BALANCE: `{format_balance(new_balance)} BDT`",
        parse_mode="Markdown"
    )
    try:
        await context.bot.send_message(uid, f"🎉 ADMIN ADDED `{format_balance(amount)} BDT` TO YOUR ACCOUNT!\n💵 NEW BALANCE: `{format_balance(new_balance)} BDT`", parse_mode="Markdown")
    except:
        pass
    context.user_data["add_balance_mode"] = False
    context.user_data["pending_add_user"] = None

async def process_remove_balance_amount(update, context):
    try:
        amount = float(update.message.text.strip())
        if amount <= 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ INVALID AMOUNT!")
        return
    uid = context.user_data.get("pending_remove_user")
    if not uid:
        context.user_data["remove_balance_mode"] = False
        await update.message.reply_text("⚠️ SESSION EXPIRED.")
        return
    old_balance = get_user(uid).get("balance", 0)
    if amount > old_balance:
        await update.message.reply_text(f"❌ INSUFFICIENT BALANCE! Current: {format_balance(old_balance)} BDT")
        context.user_data["remove_balance_mode"] = False
        context.user_data["pending_remove_user"] = None
        return
    new_balance = await update_db_balance(uid, -amount)
    await update.message.reply_text(
        f"✅ **REMOVE BALANCE SUCCESSFUL**\n🆔 USER: `{uid}`\n"
        f"💸 REMOVED: `{format_balance(amount)} BDT`\n"
        f"📉 NEW BALANCE: `{format_balance(new_balance)} BDT`",
        parse_mode="Markdown"
    )
    try:
        await context.bot.send_message(uid, f"⚠️ ADMIN REMOVED `{format_balance(amount)} BDT` FROM YOUR ACCOUNT!\n💵 NEW BALANCE: `{format_balance(new_balance)} BDT`", parse_mode="Markdown")
    except:
        pass
    context.user_data["remove_balance_mode"] = False
    context.user_data["pending_remove_user"] = None

async def process_ban_user(update, context):
    uid_to_ban = update.message.text.strip()
    if not uid_to_ban.isdigit():
        await update.message.reply_text("❌ INVALID USER ID!")
        return
    uid_to_ban_int = int(uid_to_ban)
    if not user_exists(uid_to_ban_int):
        await update.message.reply_text("❌ USER NOT FOUND!")
        context.user_data["admin_ban_mode"] = False
        return
    if is_user_banned(uid_to_ban_int):
        await update.message.reply_text("⚠️ USER IS ALREADY BANNED!")
        context.user_data["admin_ban_mode"] = False
        return
    ban_user(uid_to_ban_int)
    try:
        await context.bot.send_message(uid_to_ban_int, "🚫 **YOU HAVE BEEN BANNED**\n📞 Contact support.", parse_mode="Markdown")
    except:
        pass
    await update.message.reply_text(f"✅ USER `{uid_to_ban}` BANNED!", parse_mode="Markdown")
    context.user_data["admin_ban_mode"] = False

async def process_unban_user(update, context):
    uid_to_unban = update.message.text.strip()
    if not uid_to_unban.isdigit():
        await update.message.reply_text("❌ INVALID USER ID!")
        return
    uid_to_unban_int = int(uid_to_unban)
    if not is_user_banned(uid_to_unban_int):
        await update.message.reply_text("⚠️ THIS USER IS NOT BANNED!")
        context.user_data["admin_unban_mode"] = False
        return
    unban_user(uid_to_unban_int)
    try:
        await context.bot.send_message(uid_to_unban_int, "✅ **YOU HAVE BEEN UNBANNED!** Use /start", parse_mode="Markdown")
    except:
        pass
    await update.message.reply_text(f"✅ USER `{uid_to_unban}` UNBANNED!", parse_mode="Markdown")
    context.user_data["admin_unban_mode"] = False

# ==================== MESSAGE HANDLER SECTION ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    uid = update.effective_user.id
    raw_text = update.message.text.strip() if update.message.text else ""
    text = normalize_stylized_text(raw_text).strip()

    if is_state_cancelling_input(text):
        context.user_data["admin_state"] = None
        context.user_data["temp_target_service"] = None
        context.user_data["temp_target_country"] = None
        context.user_data["temp_target_range"] = None
        context.user_data["add_balance_mode"] = False
        context.user_data["remove_balance_mode"] = False
        context.user_data["pending_add_user"] = None
        context.user_data["pending_remove_user"] = None
        context.user_data["admin_ban_mode"] = False
        context.user_data["admin_unban_mode"] = False
        context.user_data["withdraw_mode"] = None
        context.user_data["broadcast_mode"] = False
        context.user_data["mode"] = None

    admin_state = context.user_data.get("admin_state")
    if admin_state and is_admin(uid):
        if admin_state == "waiting_for_add_service_name_inline":
            svc_name = text.strip().upper()
            custom_svcs = load_custom_services()
            exists = any(s.get("sid", "").upper() == svc_name for s in custom_svcs)
            if exists:
                await update.message.reply_text(f"❌ **Service '{svc_name}' already exists!**", parse_mode="Markdown")
            else:
                custom_svcs.append({"sid": svc_name, "ranges": []})
                save_custom_services(custom_svcs)
                await update.message.reply_text(f"✅ **Service '{svc_name}' added successfully!**", parse_mode="Markdown")
            context.user_data["admin_state"] = None
            kb = build_manage_services_inline_keyboard()
            await update.message.reply_text(
                "⚙️ MANAGE SERVICES\n"
                "───────────────────\n"
                "SELECT A SERVICE:",
                reply_markup=kb
            )
            return

        elif admin_state == "waiting_for_rename_service_inline":
            new_name = text.strip().upper()
            old_name = context.user_data.get("temp_target_service")
            custom_svcs = load_custom_services()
            for s in custom_svcs:
                if s.get("sid", "").upper() == old_name.upper():
                    s["sid"] = new_name
                    break
            save_custom_services(custom_svcs)
            await update.message.reply_text(f"✅ **Service renamed from '{old_name}' to '{new_name}' successfully!**", parse_mode="Markdown")
            context.user_data["admin_state"] = None
            context.user_data["temp_target_service"] = None
            kb = build_manage_services_inline_keyboard()
            await update.message.reply_text(
                "⚙️ MANAGE SERVICES\n"
                "───────────────────\n"
                "SELECT A SERVICE:",
                reply_markup=kb
            )
            return

        elif admin_state == "waiting_for_add_range_inline":
            range_val = text.strip().upper()
            svc_name = context.user_data.get("temp_target_service")
            country_name = context.user_data.get("temp_target_country")
            selected_api = context.user_data.get("selected_api_key", DEFAULT_API_KEY)
            
            if not svc_name:
                await update.message.reply_text("❌ Service not found! Please try again.", parse_mode="Markdown")
                context.user_data["admin_state"] = None
                return
            
            custom_svcs = load_custom_services()
            target_svc = next((s for s in custom_svcs if s.get("sid", "").upper() == svc_name.upper()), None)
            
            if not target_svc:
                await update.message.reply_text("❌ Service not found!", parse_mode="Markdown")
                context.user_data["admin_state"] = None
                return
            
            dup = any(r.get("range", "").upper() == range_val for r in target_svc.get("ranges", []))
            if dup:
                await update.message.reply_text(f"❌ **Range '{range_val}' already exists under '{svc_name}'!**", parse_mode="Markdown")
                context.user_data["admin_state"] = None
                return
            
            prefix = re.sub(r'[xX]+$', '', range_val).strip()
            prefix_clean = re.sub(r'\D', '', prefix)
            
            if country_name:
                cname = country_name
                flag, _ = get_country_info(prefix_clean)
            else:
                flag, cname = get_country_info(prefix_clean)
            
            target_svc["ranges"].append({
                "range": range_val,
                "country": f"{flag} {cname}",
                "api_key": selected_api
            })
            save_custom_services(custom_svcs)
            
            api_label = get_api_key_label(selected_api)
            await update.message.reply_text(
                f"✅ **Range '{range_val}' ({flag} {cname}) added to '{svc_name}' successfully!**\n"
                f"🔑 **API Key:** {api_label}",
                parse_mode="Markdown"
            )
            
            context.user_data["admin_state"] = None
            context.user_data["temp_target_service"] = None
            context.user_data["temp_target_country"] = None
            context.user_data["selected_api_key"] = None
            
            kb = build_country_detail_keyboard(svc_name, cname)
            if kb:
                await update.message.reply_text(
                    f"RANGES → {svc_name.upper()} → {cname.upper()}\n"
                    f"───────────────────\n"
                    f"TAP TO DELETE / EDIT:",
                    reply_markup=kb
                )
            return

        elif admin_state == "waiting_for_rename_country_inline":
            new_country_name = text.strip()
            svc_name = context.user_data.get("temp_target_service")
            old_country_name = context.user_data.get("temp_target_country")
            
            custom_svcs = load_custom_services()
            target_svc = next((s for s in custom_svcs if s.get("sid", "").upper() == svc_name.upper()), None)
            
            if target_svc:
                flag = "🌍"
                for r in target_svc.get("ranges", []):
                    country_display = r.get("country", "")
                    match = re.match(r'^([^\w\s]*)\s*(.*)$', country_display)
                    cname = match.group(2).strip() if match else "Unknown"
                    if cname.upper() == old_country_name.upper():
                        flag = match.group(1).strip() if match else "🌍"
                        r["country"] = f"{flag} {new_country_name}"
                save_custom_services(custom_svcs)
                await update.message.reply_text(f"✅ **Country renamed from '{old_country_name}' to '{new_country_name}' successfully!**", parse_mode="Markdown")
            
            context.user_data["admin_state"] = None
            context.user_data["temp_target_service"] = None
            context.user_data["temp_target_country"] = None
            
            kb = build_country_detail_keyboard(svc_name, new_country_name)
            if kb:
                await update.message.reply_text(
                    f"RANGES → {svc_name.upper()} → {new_country_name.upper()}\n"
                    f"───────────────────\n"
                    f"TAP TO DELETE / EDIT:",
                    reply_markup=kb
                )
            return

        elif admin_state == "waiting_for_edit_range_inline":
            new_range = text.strip().upper()
            svc_name = context.user_data.get("temp_target_service")
            country_name = context.user_data.get("temp_target_country")
            old_range = context.user_data.get("temp_target_range")
            
            custom_svcs = load_custom_services()
            target_svc = next((s for s in custom_svcs if s.get("sid", "").upper() == svc_name.upper()), None)
            
            if target_svc:
                for r in target_svc.get("ranges", []):
                    if r.get("range", "").upper() == old_range.upper():
                        r["range"] = new_range
                        prefix = re.sub(r'[xX]+$', '', new_range).strip()
                        prefix_clean = re.sub(r'\D', '', prefix)
                        flag, _ = get_country_info(prefix_clean)
                        r["country"] = f"{flag} {country_name}"
                        break
                save_custom_services(custom_svcs)
                await update.message.reply_text(f"✅ **Range edited from '{old_range}' to '{new_range}' successfully!**", parse_mode="Markdown")
            
            context.user_data["admin_state"] = None
            context.user_data["temp_target_service"] = None
            context.user_data["temp_target_country"] = None
            context.user_data["temp_target_range"] = None
            
            kb = build_country_detail_keyboard(svc_name, country_name)
            if kb:
                await update.message.reply_text(
                    f"RANGES → {svc_name.upper()} → {country_name.upper()}\n"
                    f"───────────────────\n"
                    f"TAP TO DELETE / EDIT:",
                    reply_markup=kb
                )
            return

        # ============ NEW: OTP Group Add ============
        elif admin_state == "waiting_for_otp_group_add":
            try:
                group_id = int(text.strip())
                if add_otp_group(group_id):
                    await update.message.reply_text(
                        f"✅ OTP Group <code>{group_id}</code> added successfully!\n\n"
                        f"📊 Total Groups: {len(load_otp_groups())}",
                        parse_mode="HTML",
                        reply_markup=main_keyboard(uid)
                    )
                else:
                    await update.message.reply_text(
                        f"⚠️ Group <code>{group_id}</code> already exists!",
                        parse_mode="HTML",
                        reply_markup=main_keyboard(uid)
                    )
            except ValueError:
                await update.message.reply_text(
                    "❌ Invalid Group ID! Please send a valid numeric ID.",
                    reply_markup=main_keyboard(uid)
                )
            context.user_data["admin_state"] = None
            return

        # ============ NEW: Admin Add ============
        elif admin_state == "waiting_for_admin_add":
            try:
                admin_id = int(text.strip())
                if add_admin(admin_id):
                    await update.message.reply_text(
                        f"✅ Admin <code>{admin_id}</code> added successfully!\n\n"
                        f"👑 Total Admins: {len(load_admins())}",
                        parse_mode="HTML",
                        reply_markup=main_keyboard(uid)
                    )
                else:
                    await update.message.reply_text(
                        f"⚠️ Admin <code>{admin_id}</code> already exists!",
                        parse_mode="HTML",
                        reply_markup=main_keyboard(uid)
                    )
            except ValueError:
                await update.message.reply_text(
                    "❌ Invalid Admin ID! Please send a valid numeric ID.",
                    reply_markup=main_keyboard(uid)
                )
            context.user_data["admin_state"] = None
            return

    if context.user_data.get("withdraw_mode") == "select_method":
        await withdraw_method_selected(update, context)
        return
    if context.user_data.get("withdraw_mode") == "amount":
        await withdraw_amount_received(update, context)
        return
    if context.user_data.get("withdraw_mode") == "number":
        await withdraw_number_received(update, context)
        return

    if context.user_data.get("add_balance_mode") and is_admin(uid):
        if context.user_data.get("pending_add_user"):
            await process_add_balance_amount(update, context)
        else:
            await process_add_balance_user(update, context)
        return
    if context.user_data.get("remove_balance_mode") and is_admin(uid):
        if context.user_data.get("pending_remove_user"):
            await process_remove_balance_amount(update, context)
        else:
            await process_remove_balance_user(update, context)
        return
    if context.user_data.get("admin_ban_mode") and is_admin(uid):
        await process_ban_user(update, context)
        return
    if context.user_data.get("admin_unban_mode") and is_admin(uid):
        await process_unban_user(update, context)
        return

    if context.user_data.get("mode") == "input_user_id" and is_admin(uid):
        target_uid = text.strip()
        if not target_uid.isdigit():
            await update.message.reply_text("❌ INVALID ID!")
            return
        context.user_data["mode"] = None
        stats = get_user_stats(target_uid)
        msg = (
            f"👤 <b>USER STATUS</b> — <code>{target_uid}</code>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ TODAY: 📱 {stats['today_numbers']} | 🔑 {stats['today_otps']}\n"
            f"🔥 7 DAYS: 📱 {stats['last7d_numbers']} | 🔑 {stats['last7d_otps']}\n"
            f"🌐 ALL TIME: 📱 {stats['total_numbers']} | 🔑 {stats['total_otps']}"
        )
        await update.message.reply_text(
            msg, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(make_bold_unicode("📂 CHECK ALL DATA"), callback_data=f"full_logs_{target_uid}")],
                [InlineKeyboardButton(make_bold_unicode("🔙 BACK"), callback_data="adm_menu_back_to_admin")]
            ])
        )
        return

    if not is_admin(uid) and is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return

    if text == "❌ CANCEL":
        context.user_data.clear()
        await update.message.reply_text("❌ CANCELLED", reply_markup=main_keyboard(uid))
        return

    if "PROFILE" in text:
        user_data = get_user(uid)
        stats = get_user_stats(uid)
        user = update.effective_user
        full_name = html.escape(user.full_name)
        username = html.escape(user.username or "No username")
        balance = user_data.get('balance', 0)
        profile_text = (
            f"👤 <b>ACCOUNT PROFILE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 <b>Name:</b> <code>{full_name}</code>\n"
            f"🆔 <b>Username:</b> <code>@{username}</code>\n"
            f"🗝 <b>ID:</b> <code>{uid}</code>\n\n"
            f"💰 <b>Current Balance:</b> <code>{format_balance(balance)} BDT</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>ACTIVITY STATS:</b>\n\n"
            f"📅 <b>Today:</b>\n"
            f"├ 📱 Numbers: <code>{stats['today_numbers']}</code>\n"
            f"└ 🔑 Received OTPs: <code>{stats['today_otps']}</code>\n\n"
            f"🔥 <b>Last 7 Days:</b>\n"
            f"├ 📱 Numbers: <code>{stats['last7d_numbers']}</code>\n"
            f"└ 🔑 Received OTPs: <code>{stats['last7d_otps']}</code>\n\n"
            f"🌐 <b>All-Time:</b>\n"
            f"├ 📱 Numbers: <code>{stats['total_numbers']}</code>\n"
            f"└ 🔑 Received OTPs: <code>{stats['total_otps']}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"💸 {make_bold_unicode('WITHDRAW')}", callback_data="withdraw_start")]
        ])
        await update.message.reply_text(profile_text, parse_mode="HTML", reply_markup=keyboard)
        return

    if "REFER AND EARN" in text:
        await refer_command(update, context)
        return

    if "GET NUMBER" in text:
        await show_app_selection(update, context)
        return

    if "LEADERBOARD" in text:
        await leaderboard_command(update, context)
        return

    if "SUPPORT" in text:
        support_text = "💬 SUPPORT PANEL 🎧\n\nCLICK THE BUTTONS BELOW TO CONTACT SUPPORT"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 SUPPORT", url=SUPPORT_LINK)],
            [InlineKeyboardButton("👨‍💻 DEVELOPER", url="https://t.me/shuvojit46")]
        ])
        await update.message.reply_text(support_text, reply_markup=keyboard, parse_mode="Markdown")
        return

    if "ADMIN PANEL" in text and is_admin(uid):
        context.user_data["admin_mode"] = "main"
        admin_text = get_admin_panel_text()
        await update.message.reply_text(
            admin_text,
            parse_mode="HTML",
            reply_markup=build_admin_main_inline_keyboard()
        )
        return

    if context.user_data.get("broadcast_mode") and is_admin(uid):
        context.user_data["broadcast_mode"] = False
        user_db = load_data(USER_DATA_FILE)
        all_uids = list(user_db.keys())
        if not all_uids:
            await update.message.reply_text("❌ পাঠানোর জন্য কোনো ইউজার পাওয়া যায়নি!")
            return
        success_ids, fail_ids = [], []
        status_msg = await update.message.reply_text(f"🚀 <b>ব্রডকাস্ট শুরু হয়েছে...</b>\n🎯 টার্গেট: {len(all_uids)} জন ইউজার।", parse_mode="HTML")
        
        def format_broadcast_caption(caption_text):
            if not caption_text:
                return "<blockquote>📢 <b>ADMIN NOTICE :</b></blockquote>"
            formatted = re.sub(r'(\d{3,}[xX]{3,})', r'<code>\1</code>', str(caption_text))
            return f"<blockquote>📢 <b>ADMIN NOTICE :</b></blockquote>\n\n{formatted}"
        
        for user_id_str in all_uids:
            try:
                target_id = int(user_id_str)
                if update.message.text:
                    await context.bot.send_message(
                        chat_id=target_id,
                        text=format_broadcast_caption(update.message.text),
                        parse_mode="HTML"
                    )
                elif update.message.photo:
                    caption = format_broadcast_caption(update.message.caption) if update.message.caption else None
                    await context.bot.send_photo(
                        chat_id=target_id,
                        photo=update.message.photo[-1].file_id,
                        caption=caption,
                        parse_mode="HTML" if caption else None
                    )
                elif update.message.video:
                    caption = format_broadcast_caption(update.message.caption) if update.message.caption else None
                    await context.bot.send_video(
                        chat_id=target_id,
                        video=update.message.video.file_id,
                        caption=caption,
                        parse_mode="HTML" if caption else None
                    )
                elif update.message.document:
                    caption = format_broadcast_caption(update.message.caption) if update.message.caption else None
                    await context.bot.send_document(
                        chat_id=target_id,
                        document=update.message.document.file_id,
                        caption=caption,
                        parse_mode="HTML" if caption else None
                    )
                else:
                    try:
                        await context.bot.copy_message(
                            chat_id=target_id,
                            from_chat_id=update.message.chat_id,
                            message_id=update.message.message_id
                        )
                    except:
                        await context.bot.send_message(
                            chat_id=target_id,
                            text="📢 <b>ADMIN NOTICE :</b>\n\nআপনার জন্য একটি নতুন বার্তা আছে, কিন্তু এটি প্রদর্শন করা সম্ভব হয়নি।",
                            parse_mode="HTML"
                        )
                success_ids.append(user_id_str)
            except Exception as e:
                print(f"Broadcast fail to {user_id_str}: {e}")
                fail_ids.append(user_id_str)
            await asyncio.sleep(0.05)
        
        report_text = (
            f"✅ <b>ADMIN NOTICE COMPLETE !</b>\n\n"
            f"📊 <b>BROADCAST REPORT:</b>\n\n"
            f"<blockquote>✅ SUCCESSFULLY SENT: {len(success_ids)} USERS !</blockquote>\n"
            f"<blockquote>❌ FAILED TO SEND: {len(fail_ids)} USERS !</blockquote>"
        )
        await status_msg.delete()
        await context.bot.send_message(chat_id=uid, text=report_text, parse_mode="HTML", reply_markup=main_keyboard(uid))
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        if success_ids:
            s_file = io.BytesIO(("\n".join(success_ids)).encode()); s_file.name = f"SUCCESS_{random_suffix}.txt"
            await context.bot.send_document(chat_id=uid, document=s_file, caption="✅ Success User List")
        if fail_ids:
            f_file = io.BytesIO(("\n".join(fail_ids)).encode()); f_file.name = f"FAILED_{random_suffix}.txt"
            await context.bot.send_document(chat_id=uid, document=f_file, caption="❌ Failed User List")
        return

    await update.message.reply_text("🔹 PLEASE USE THE BUTTONS BELOW:", reply_markup=main_keyboard(uid))

def is_state_cancelling_input(text_input):
    if not text_input:
        return False
    clean_text = text_input.strip().upper()
    if clean_text.startswith("/"):
        return True
    cancelling_keywords = [
        "👥 USER MANAGEMENT", "⚙️ SYSTEM CONFIGURATION", "🛠️ MANAGE SERVICES",
        "🔙 BACK TO MAIN", "⚙️ ADMIN PANEL ⚙️", "📞 GET NUMBER", "💰 BALANCE",
        "👥 REFER AND EARN", "👤 PROFILE", "🏆 LEADERBOARD", "💬 SUPPORT", "❌ CANCEL"
    ]
    return clean_text in cancelling_keywords

# ==================== COMMAND HANDLERS SECTION ====================

async def get1number_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    await show_app_selection(update, context)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    balance = get_user(uid)['balance']
    await update.message.reply_text(f"💰 BALANCE: `{format_balance(balance)} BDT`", parse_mode="Markdown", reply_markup=main_keyboard(uid))

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    user_data = get_user(uid)
    stats = get_user_stats(uid)
    user = update.effective_user
    profile_text = (
        f"👤 **YOUR PROFILE**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏷️ NAME: `{user.full_name}`\n"
        f"🆔 USERNAME: @{user.username or 'No username'}\n"
        f"🗝️ ID: `{uid}`\n\n"
        f"💵 BALANCE: {format_balance(user_data.get('balance', 0))} BDT\n\n"
        f"✨ TODAY: 📱 {stats['today_numbers']} | 🔑 {stats['today_otps']}\n"
        f"🔥 7 DAYS: 📱 {stats['last7d_numbers']} | 🔑 {stats['last7d_otps']}\n"
        f"🌐 ALL TIME: 📱 {stats['total_numbers']} | 🔑 {stats['total_otps']}"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💸 {make_bold_unicode('WITHDRAW')}", callback_data="withdraw_start")]
    ])
    await update.message.reply_text(profile_text, parse_mode="Markdown", reply_markup=keyboard)

async def refer_command_slash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    await refer_command(update, context)

async def leaderboard_command_slash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    await leaderboard_command(update, context)

# ==================== START & CALLBACK SECTION ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    uid_str = str(uid)
    existing_data = load_data(USER_DATA_FILE)
    is_new_user = uid_str not in existing_data
    if is_new_user:
        get_user(uid)
    args = context.args
    if args:
        param = args[0]
        if is_range_request(param):
            await request_queue.put({'type': 'auto_number', 'update': update, 'context': context, 'range_text': param})
            return
        elif is_referral_request(param) and is_new_user:
            try:
                referrer_id = int(param)
                if referrer_id != uid and str(referrer_id) in existing_data:
                    current_count = get_referral_count(referrer_id)
                    new_count = current_count + 1
                    update_referral_count(referrer_id, new_count)
                    await update_db_balance(referrer_id, REFERRAL_PRICE)
                    log_global_activity(referrer_id, "REFERRAL_JOINED", {"referred_user": uid})
                    try:
                        await context.bot.send_message(
                            referrer_id,
                            f"🎉 <b>NEW REFERRAL!</b>\n\n<blockquote>🗝️ ID: <code>{uid}</code>\n💰 REWARD: {format_balance(REFERRAL_PRICE)} BDT\n👥 TOTAL REFERS: {new_count}</blockquote>",
                            parse_mode="HTML"
                        )
                    except:
                        pass
            except Exception as e:
                print(f"Referral error: {e}")
    context.user_data.clear()
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")
    await update.message.reply_text("🔹 PLEASE USE THE BUTTONS BELOW:", reply_markup=main_keyboard(uid))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    data = query.data
    await query.answer()

    if not is_admin(uid) and is_user_banned(uid):
        await query.edit_message_text("🚫 YOU ARE BANNED 🚫")
        return

    context.user_data["admin_state"] = None
    context.user_data["add_balance_mode"] = False
    context.user_data["remove_balance_mode"] = False
    context.user_data["admin_ban_mode"] = False
    context.user_data["admin_unban_mode"] = False
    context.user_data["withdraw_mode"] = None
    context.user_data["broadcast_mode"] = False
    context.user_data["mode"] = None

    # ============ CHANGE NUMBER BUTTON ============
    if data.startswith("change_number_"):
        user_id = int(data.replace("change_number_", ""))
        
        if uid not in user_last_data:
            await query.message.reply_text(
                "❌ আপনার আগের ডেটা পাওয়া যায়নি। দয়া করে নতুন করে GET NUMBER করুন।",
                reply_markup=main_keyboard(uid)
            )
            return
        
        last_data = user_last_data[uid]
        last_range = last_data.get("last_range", "")
        last_service = last_data.get("last_service", "")
        
        if not last_range:
            await query.message.reply_text(
                "❌ রেঞ্জ তথ্য পাওয়া যায়নি। দয়া করে নতুন করে GET NUMBER করুন।",
                reply_markup=main_keyboard(uid)
            )
            return
        
        await query.message.edit_text(
            f"🔄 <b>FETCHING NEW NUMBER</b>\n\n"
            f"<blockquote>📱 SERVICE: <code>{last_service}</code></blockquote>\n"
            f"<blockquote>📶 RANGE: <code>{last_range}</code></blockquote>\n\n"
            f"<i>⏳ Searching for new number...</i>",
            parse_mode="HTML"
        )
        
        res = await fetch_number_async(last_range)
        
        if not res or not res.get("number"):
            await query.message.edit_text(
                f"❌ <b>No number available</b>\n\n"
                f"<blockquote>📶 RANGE: <code>{last_range}</code></blockquote>\n"
                f"⚠️ এই রেঞ্জে এখন নম্বর নেই। অন্য রেঞ্জ চেষ্টা করুন।",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🌏 CHANGE COUNTRY", callback_data=f"change_country_{uid}")
                ]])
            )
            return
        
        clean_num = normalize_number(res["number"])
        add_number_taken(uid, 1)
        last_range[uid] = last_range
        active_numbers[clean_num] = {"uid": uid, "range": last_range, "timestamp": datetime.now()}
        save_number_range_info(uid, clean_num, last_range)
        
        country_flag, country_name = get_country_info(clean_num)
        
        new_number_msg = (
            f"✅ <b>NEW NUMBER ALLOCATED</b> ✅\n\n"
            f"<blockquote>🌍 COUNTRY: <code>{country_flag} {country_name}</code></blockquote>\n"
            f"<blockquote>📱 SERVICE: <code>{last_service}</code></blockquote>\n"
            f"<blockquote>📞 NUMBER: <code>+{clean_num}</code></blockquote>\n\n"
            f"<b>📩 SMS STATUS: ⏳ WAITING...</b>"
        )
        
        new_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 CHANGE NUMBER", callback_data=f"change_number_{uid}"),
                InlineKeyboardButton("🌏 CHANGE COUNTRY", callback_data=f"change_country_{uid}")
            ],
            [InlineKeyboardButton("📢 OTP GROUP", url="https://t.me/sure_otp_suppor")]
        ])
        
        await query.message.edit_text(
            new_number_msg, 
            parse_mode="HTML", 
            reply_markup=new_buttons
        )
        return

    # ============ CHANGE COUNTRY BUTTON ============
    if data.startswith("change_country_"):
        user_id = int(data.replace("change_country_", ""))
        
        if uid not in user_last_data:
            await query.message.reply_text(
                "❌ আপনার আগের ডেটা পাওয়া যায়নি। দয়া করে নতুন করে GET NUMBER করুন।",
                reply_markup=main_keyboard(uid)
            )
            return
        
        last_data = user_last_data[uid]
        last_service = last_data.get("last_service", "")
        
        if not last_service:
            await query.message.reply_text(
                "❌ সার্ভিস তথ্য পাওয়া যায়নি। দয়া করে নতুন করে GET NUMBER করুন।",
                reply_markup=main_keyboard(uid)
            )
            return
        
        services = load_custom_services()
        if not services:
            await query.message.edit_text(
                "⚠️ <b>দুঃখিত, এই মুহূর্তে কোনো সার্ভিস উপলব্ধ নেই।</b>",
                parse_mode="HTML",
                reply_markup=main_keyboard(uid)
            )
            return
        
        target_service = None
        target_idx = 0
        for idx, svc in enumerate(services):
            if svc.get("sid", "").upper() == last_service.upper():
                target_service = svc
                target_idx = idx
                break
        
        if not target_service:
            target_service = services[0]
            target_idx = 0
        
        ranges = target_service.get("ranges", [])
        if not ranges:
            await query.message.edit_text(
                f"❌ <b>No ranges available for {last_service}</b>\n\n"
                f"অন্য সার্ভিস নির্বাচন করুন।",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 BACK TO SERVICES", callback_data="back_services")
                ]])
            )
            return
        
        context.user_data["la_services"] = services
        context.user_data["la_svc_idx"] = target_idx
        context.user_data["la_sid"] = target_service.get("sid", "")
        context.user_data["la_ranges"] = ranges
        
        keyboard = _build_countries_keyboard(ranges, target_idx)
        
        await query.message.edit_text(
            f"📞 <b>CHANGE COUNTRY</b>\n\n"
            f"<blockquote>📱 Service: <b>{html.escape(target_service.get('sid', ''))}</b></blockquote>\n"
            f"<blockquote>🌍 আপনার পছন্দের <b>Country</b> সিলেক্ট করুন:</blockquote>",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return

    # ============ ADMIN ROUTING ============
    if data == "adm_menu_back_to_admin":
        admin_text = get_admin_panel_text()
        await query.message.edit_text(
            admin_text,
            parse_mode="HTML",
            reply_markup=build_admin_main_inline_keyboard()
        )
        return

    if data == "adm_menu_back_to_main":
        await query.message.delete()
        await context.bot.send_message(
            chat_id=uid,
            text="🔙 Returned to main user panel.",
            reply_markup=main_keyboard(uid)
        )
        return

    if data == "adm_menu_user_mgnt":
        await query.message.edit_text(
            "👥 <b>USER MANAGEMENT PANEL</b>\n───────────────────\nSelect an action from below:",
            parse_mode="HTML",
            reply_markup=build_user_management_inline_keyboard()
        )
        return

    if data == "adm_menu_sys_config":
        await query.message.edit_text(
            "⚙️ <b>SYSTEM CONFIGURATION PANEL</b>\n───────────────────\nSelect an action from below:",
            parse_mode="HTML",
            reply_markup=build_system_config_inline_keyboard()
        )
        return

    # ============ NEW: OTP Group Management ============
    if data == "admin_otp_group_menu":
        groups = load_otp_groups()
        text = f"📢 <b>OTP GROUP MANAGEMENT</b>\n───────────────────\n📊 Total Groups: <code>{len(groups)}</code>\n\n"
        for idx, gid in enumerate(groups, 1):
            is_default = "⭐" if gid in DEFAULT_OTP_GROUPS else ""
            text += f"{is_default} Group {idx}: <code>{gid}</code>\n"
        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=build_otp_group_management_keyboard()
        )
        return

    if data == "admin_otp_group_add":
        context.user_data["admin_state"] = "waiting_for_otp_group_add"
        await query.message.edit_text(
            "➕ <b>ADD OTP GROUP</b>\n\n"
            "Please send the Group ID (e.g., <code>-1004374381669</code>)\n\n"
            "<i>You can get the Group ID by adding @getmyid_bot to your group.</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ CANCEL", callback_data="admin_otp_group_menu")
            ]])
        )
        return

    if data.startswith("admin_otp_group_detail_"):
        idx = int(data.replace("admin_otp_group_detail_", ""))
        groups = load_otp_groups()
        if idx <= len(groups):
            group_id = groups[idx - 1]
            is_default = "⭐" if group_id in DEFAULT_OTP_GROUPS else ""
            text = f"📢 <b>OTP GROUP DETAIL</b>\n───────────────────\n"
            text += f"ID: <code>{group_id}</code>\n"
            text += f"Status: {'⭐ Default' if is_default else '🟢 Active'}\n"
            await query.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=build_otp_group_detail_keyboard(idx)
            )
        return

    if data.startswith("admin_otp_group_remove_"):
        idx = int(data.replace("admin_otp_group_remove_", ""))
        groups = load_otp_groups()
        if idx <= len(groups):
            group_id = groups[idx - 1]
            if group_id not in DEFAULT_OTP_GROUPS:
                if remove_otp_group(group_id):
                    await query.answer("✅ Group removed!", show_alert=True)
                    await query.message.edit_text(
                        f"✅ OTP Group <code>{group_id}</code> removed successfully!",
                        parse_mode="HTML",
                        reply_markup=build_otp_group_management_keyboard()
                    )
                else:
                    await query.answer("❌ Failed to remove!", show_alert=True)
            else:
                await query.answer("❌ Cannot remove default group!", show_alert=True)
        return

    # ============ NEW: Admin Management ============
    if data == "admin_admin_management":
        admins = load_admins()
        text = f"👑 <b>ADMIN MANAGEMENT</b>\n───────────────────\n👑 Total Admins: <code>{len(admins)}</code>\n\n"
        for idx, aid in enumerate(admins, 1):
            is_default = "⭐" if aid in DEFAULT_ADMINS else ""
            text += f"{is_default} Admin {idx}: <code>{aid}</code>\n"
        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=build_admin_management_keyboard()
        )
        return

    if data == "admin_admin_add":
        context.user_data["admin_state"] = "waiting_for_admin_add"
        await query.message.edit_text(
            "➕ <b>ADD ADMIN</b>\n\n"
            "Please send the Telegram User ID:\n\n"
            "<i>You can get User ID from @userinfobot</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ CANCEL", callback_data="admin_admin_management")
            ]])
        )
        return

    if data.startswith("admin_admin_detail_"):
        idx = int(data.replace("admin_admin_detail_", ""))
        admins = load_admins()
        if idx <= len(admins):
            admin_id = admins[idx - 1]
            is_default = "⭐" if admin_id in DEFAULT_ADMINS else ""
            text = f"👑 <b>ADMIN DETAIL</b>\n───────────────────\n"
            text += f"ID: <code>{admin_id}</code>\n"
            text += f"Status: {'⭐ Default' if is_default else '🟢 Active'}\n"
            await query.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=build_admin_detail_keyboard(idx)
            )
        return

    if data.startswith("admin_admin_remove_"):
        idx = int(data.replace("admin_admin_remove_", ""))
        admins = load_admins()
        if idx <= len(admins):
            admin_id = admins[idx - 1]
            if admin_id not in DEFAULT_ADMINS:
                if remove_admin(admin_id):
                    await query.answer("✅ Admin removed!", show_alert=True)
                    await query.message.edit_text(
                        f"✅ Admin <code>{admin_id}</code> removed successfully!",
                        parse_mode="HTML",
                        reply_markup=build_admin_management_keyboard()
                    )
                else:
                    await query.answer("❌ Failed to remove!", show_alert=True)
            else:
                await query.answer("❌ Cannot remove default admin!", show_alert=True)
        return

    # ============ USER MANAGEMENT ============
    if data == "adm_usermgnt_broadcast":
        context.user_data["broadcast_mode"] = True
        await query.message.edit_text(
            "📢 <b>ADMIN BROADCAST SYSTEM</b>\n───────────────────\n"
            "💬 Please send the message (Text/Photo/Video/Document etc.) - which will be sent to all users with a professional notification header.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(make_bold_unicode("❌ CANCEL"), callback_data="adm_menu_user_mgnt")]])
        )
        return

    if data == "adm_usermgnt_get_ids":
        users = get_all_users()
        if users:
            content = "\n".join(f"{i}. {u}" for i, u in enumerate(users, 1))
            f = io.BytesIO(content.encode()); f.name = f"ALL_USERS_{len(users)}.txt"
            await context.bot.send_document(chat_id=uid, document=f, caption=f"👥 Total Users: {len(users)}")
        else:
            await query.message.reply_text("No users found.")
        return

    if data == "adm_usermgnt_all_balance":
        user_db = load_data(USER_DATA_FILE)
        if user_db:
            total_bal = sum(v.get("balance", 0) for v in user_db.values())
            lines = [f"{i}. {uid_}: {v.get('balance', 0):.2f} BDT" for i, (uid_, v) in enumerate(user_db.items(), 1)]
            content = f"💰 TOTAL BALANCE: {total_bal:.2f} BDT\n\n" + "\n".join(lines)
            f = io.BytesIO(content.encode()); f.name = f"BALANCES_{total_bal:.0f}.txt"
            await context.bot.send_document(chat_id=uid, document=f, caption=f"💵 Total Balance: {total_bal:.2f} BDT")
        else:
            await query.message.reply_text("No data.")
        return

    # ============ SYSTEM CONFIG ============
    if data == "adm_sys_stats":
        t_n, t_o, s_n, s_o, tot_n, tot_o = get_global_system_stats()
        msg = (
            f"📊 <b>SYSTEM STATUS</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ <b>TODAY</b>\n📱 NUMBERS: {t_n}\n🔑 OTPS: {t_o}\n\n"
            f"🔥 <b>LAST 7 DAYS</b>\n📱 NUMBERS: {s_n}\n🔑 OTPS: {s_o}\n\n"
            f"🌐 <b>ALL TIME</b>\n📱 NUMBERS: {tot_n}\n🔑 OTPS: {tot_o}"
        )
        await query.message.edit_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(make_bold_unicode("🔙 BACK"), callback_data="adm_menu_sys_config")]]))
        return

    if data == "adm_sys_user_check":
        context.user_data["mode"] = "input_user_id"
        await query.message.edit_text(
            "🔍 <b>USER STATUS CHECK</b>\n───────────────────\nPlease send the target Telegram ID:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(make_bold_unicode("❌ CANCEL"), callback_data="adm_menu_sys_config")]])
        )
        return

    if data == "adm_sys_ban":
        context.user_data["admin_ban_mode"] = True
        await query.message.edit_text(
            "🚫 <b>BAN USER</b>\n───────────────────\nPlease send the Telegram ID to BAN:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(make_bold_unicode("❌ CANCEL"), callback_data="adm_menu_sys_config")]])
        )
        return

    if data == "adm_sys_unban":
        context.user_data["admin_unban_mode"] = True
        await query.message.edit_text(
            "🔓 <b>UNBAN USER</b>\n───────────────────\nPlease send the Telegram ID to UNBAN:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(make_bold_unicode("❌ CANCEL"), callback_data="adm_menu_sys_config")]])
        )
        return

    if data == "adm_sys_banned_list":
        banned_list = load_banned_users()
        if not banned_list:
            await query.message.edit_text("📜 NO BANNED USERS.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(make_bold_unicode("🔙 BACK"), callback_data="adm_menu_sys_config")]]))
            return
        text = "📜 <b>BANNED USER LIST</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, b_id in enumerate(banned_list, 1):
            text += f"{i}. <code>{b_id}</code>\n"
        text += f"\n📊 Total: {len(banned_list)}"
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(make_bold_unicode("🔙 BACK"), callback_data="adm_menu_sys_config")]]))
        return

    if data == "adm_sys_add_bal":
        context.user_data["add_balance_mode"] = True
        await query.message.edit_text(
            "💰 <b>ADD BALANCE</b>\n───────────────────\nPlease send the Telegram ID to add balance:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(make_bold_unicode("❌ CANCEL"), callback_data="adm_menu_sys_config")]])
        )
        return

    if data == "adm_sys_rem_bal":
        context.user_data["remove_balance_mode"] = True
        await query.message.edit_text(
            "💸 <b>REMOVE BALANCE</b>\n───────────────────\nPlease send the Telegram ID to remove balance:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(make_bold_unicode("❌ CANCEL"), callback_data="adm_menu_sys_config")]])
        )
        return

    # ============ MANAGE SERVICES ============
    if data == "manage_svc_back_to_list":
        kb = build_manage_services_inline_keyboard()
        await query.message.edit_text(
            "⚙️ MANAGE SERVICES\n"
            "───────────────────\n"
            "SELECT A SERVICE:",
            reply_markup=kb
        )
        return

    if data == "manage_svc_add":
        context.user_data["admin_state"] = "waiting_for_add_service_name_inline"
        await query.message.edit_text(
            "📝 <b>Send the new service name (e.g. FACEBOOK):</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(make_bold_unicode("❌ CANCEL"), callback_data="manage_svc_back_to_list")]])
        )
        return

    if data.startswith("manage_svc_rename_init_"):
        svc_name = data.replace("manage_svc_rename_init_", "")
        context.user_data["admin_state"] = "waiting_for_rename_service_inline"
        context.user_data["temp_target_service"] = svc_name
        await query.message.edit_text(
            f"✏️ <b>RENAME SERVICE: {svc_name.upper()}</b>\n───────────────────\n"
            f"Please send the new name for this service:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(make_bold_unicode("❌ CANCEL"), callback_data=f"manage_svc_view_{svc_name}")]])
        )
        return

    if data.startswith("manage_svc_delete_init_"):
        svc_name = data.replace("manage_svc_delete_init_", "")
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(make_bold_unicode("✅ CONFIRM"), callback_data=f"manage_svc_delete_do_{svc_name}"),
                InlineKeyboardButton(make_bold_unicode("❌ CANCEL"), callback_data=f"manage_svc_view_{svc_name}")
            ]
        ])
        await query.message.edit_text(
            f"🗑️ <b>Are you sure you want to delete service {svc_name.upper()} and all of its countries/ranges?</b>",
            parse_mode="HTML",
            reply_markup=kb
        )
        return

    if data.startswith("manage_svc_delete_do_"):
        svc_name = data.replace("manage_svc_delete_do_", "")
        custom_svcs = load_custom_services()
        custom_svcs = [s for s in custom_svcs if s.get("sid", "").upper() != svc_name.upper()]
        save_custom_services(custom_svcs)
        await query.answer(f"Deleted {svc_name}", show_alert=True)
        kb = build_manage_services_inline_keyboard()
        await query.message.edit_text(
            "⚙️ MANAGE SERVICES\n"
            "───────────────────\n"
            "SELECT A SERVICE:",
            reply_markup=kb
        )
        return

    if data.startswith("manage_svc_view_"):
        svc_name = data.replace("manage_svc_view_", "")
        kb = build_service_detail_keyboard(svc_name)
        if not kb:
            await query.answer("Service not found!", show_alert=True)
            return
        await query.message.edit_text(
            f"📁 SERVICE: <b>{svc_name.upper()}</b>\n"
            f"───────────────────\n"
            f"SELECT A COUNTRY TO MANAGE RANGES:",
            parse_mode="HTML",
            reply_markup=kb
        )
        return

    if data.startswith("manage_svc_country_view_"):
        parts = data.replace("manage_svc_country_view_", "").split("_", 1)
        svc_name = parts[0]
        country_name = parts[1]
        custom_svcs = load_custom_services()
        target_svc = next((s for s in custom_svcs if s.get("sid", "").upper() == svc_name.upper()), None)
        if not target_svc:
            await query.answer("Service not found!", show_alert=True)
            return
        grouped = get_grouped_countries_for_service(target_svc)
        info = grouped.get(country_name, {"flag": "🌍", "ranges": []})
        flag = info["flag"]
        kb = build_country_detail_keyboard(svc_name, country_name)
        await query.message.edit_text(
            f"{flag} RANGES → {svc_name.upper()} → {country_name.upper()}\n"
            f"───────────────────\n"
            f"TAP TO DELETE / EDIT:",
            reply_markup=kb
        )
        return

    if data.startswith("manage_svc_add_range_"):
        parts = data.replace("manage_svc_add_range_", "").split("_", 1)
        svc_name = parts[0]
        country_name = parts[1] if len(parts) > 1 else None
        
        context.user_data["admin_state"] = "waiting_for_add_range_inline"
        context.user_data["temp_target_service"] = svc_name
        context.user_data["temp_target_country"] = country_name
        
        api_buttons = [
            [InlineKeyboardButton("🔑 API Key 01", callback_data=f"api_sel_range_01_{svc_name}")],
            [InlineKeyboardButton("🔑 API Key 02", callback_data=f"api_sel_range_02_{svc_name}")],
        ]
        cancel_cb = f"manage_svc_country_view_{svc_name}_{country_name}" if country_name else f"manage_svc_view_{svc_name}"
        api_buttons.append([InlineKeyboardButton(make_bold_unicode("❌ CANCEL"), callback_data=cancel_cb)])
        
        await query.message.edit_text(
            f"📶 <b>SERVICE: {svc_name.upper()}</b>\n"
            f"───────────────────\n\n"
            f"<b>Step 1: Select API Key for this range</b>\n"
            f"(This will be used to fetch numbers for this range)",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(api_buttons)
        )
        return

    if data.startswith("api_sel_range_01_"):
        svc_name = data.replace("api_sel_range_01_", "")
        context.user_data["selected_api_key"] = "API_KEY_01"
        context.user_data["temp_target_service"] = svc_name
        context.user_data["admin_state"] = "waiting_for_add_range_inline"
        await query.message.edit_text(
            f"✅ Selected: <b>API Key 01</b>\n\n"
            f"<b>Step 2: Send the range value</b>\n"
            f"(e.g. 017XXX or 23672XXX)\n\n"
            f"<i>Type the range in the chat:</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(make_bold_unicode("❌ CANCEL"), callback_data=f"manage_svc_view_{svc_name}")]])
        )
        return

    if data.startswith("api_sel_range_02_"):
        svc_name = data.replace("api_sel_range_02_", "")
        context.user_data["selected_api_key"] = "API_KEY_02"
        context.user_data["temp_target_service"] = svc_name
        context.user_data["admin_state"] = "waiting_for_add_range_inline"
        await query.message.edit_text(
            f"✅ Selected: <b>API Key 02</b>\n\n"
            f"<b>Step 2: Send the range value</b>\n"
            f"(e.g. 017XXX or 23672XXX)\n\n"
            f"<i>Type the range in the chat:</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(make_bold_unicode("❌ CANCEL"), callback_data=f"manage_svc_view_{svc_name}")]])
        )
        return

    if data.startswith("manage_svc_delete_range_"):
        parts = data.replace("manage_svc_delete_range_", "").rsplit("_", 2)
        if len(parts) < 3:
            await query.answer("Invalid request!", show_alert=True)
            return
        svc_name, country_name, range_val = parts[0], parts[1], parts[2]
        custom_svcs = load_custom_services()
        target_svc = next((s for s in custom_svcs if s.get("sid", "").upper() == svc_name.upper()), None)
        if target_svc:
            target_svc["ranges"] = [r for r in target_svc.get("ranges", []) if r.get("range", "").upper() != range_val.upper()]
            save_custom_services(custom_svcs)
            await query.answer(f"Deleted range {range_val}", show_alert=True)
            grouped = get_grouped_countries_for_service(target_svc)
            if country_name in grouped:
                kb = build_country_detail_keyboard(svc_name, country_name)
                flag = grouped[country_name]["flag"]
                await query.message.edit_text(
                    f"{flag} RANGES → {svc_name.upper()} → {country_name.upper()}\n"
                    f"───────────────────\n"
                    f"TAP TO DELETE / EDIT:",
                    reply_markup=kb
                )
            else:
                kb = build_service_detail_keyboard(svc_name)
                await query.message.edit_text(
                    f"📁 SERVICE: <b>{svc_name.upper()}</b>\n"
                    f"───────────────────\n"
                    f"SELECT A COUNTRY TO MANAGE RANGES:",
                    parse_mode="HTML",
                    reply_markup=kb
                )
        return

    if data.startswith("manage_svc_delete_country_confirm_"):
        parts = data.replace("manage_svc_delete_country_confirm_", "").split("_", 1)
        svc_name = parts[0]
        country_name = parts[1]
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(make_bold_unicode("✅ CONFIRM"), callback_data=f"manage_svc_delete_country_do_{svc_name}_{country_name}"),
                InlineKeyboardButton(make_bold_unicode("❌ CANCEL"), callback_data=f"manage_svc_country_view_{svc_name}_{country_name}")
            ]
        ])
        await query.message.edit_text(
            f"🗑️ <b>Are you sure you want to delete {country_name.upper()} and all of its ranges from {svc_name.upper()}?</b>",
            parse_mode="HTML",
            reply_markup=kb
        )
        return

    if data.startswith("manage_svc_delete_country_do_"):
        parts = data.replace("manage_svc_delete_country_do_", "").split("_", 1)
        svc_name = parts[0]
        country_name = parts[1]
        custom_svcs = load_custom_services()
        target_svc = next((s for s in custom_svcs if s.get("sid", "").upper() == svc_name.upper()), None)
        if target_svc:
            new_ranges = []
            for r in target_svc.get("ranges", []):
                country_display = r.get("country", "")
                match = re.match(r'^([^\w\s]*)\s*(.*)$', country_display)
                cname = match.group(2).strip() if match else "Unknown"
                if cname.upper() != country_name.upper():
                    new_ranges.append(r)
            target_svc["ranges"] = new_ranges
            save_custom_services(custom_svcs)
            await query.answer(f"Deleted {country_name}", show_alert=True)
            kb = build_service_detail_keyboard(svc_name)
            await query.message.edit_text(
                f"📁 SERVICE: <b>{svc_name.upper()}</b>\n"
                f"───────────────────\n"
                f"SELECT A COUNTRY TO MANAGE RANGES:",
                parse_mode="HTML",
                reply_markup=kb
            )
        return

    if data.startswith("manage_svc_rename_country_init_"):
        parts = data.replace("manage_svc_rename_country_init_", "").split("_", 1)
        svc_name = parts[0]
        country_name = parts[1]
        context.user_data["admin_state"] = "waiting_for_rename_country_inline"
        context.user_data["temp_target_service"] = svc_name
        context.user_data["temp_target_country"] = country_name
        await query.message.edit_text(
            f"✏️ <b>RENAME COUNTRY: {country_name.upper()}</b>\n"
            f"───────────────────\n"
            f"Please send the new name for this country:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(make_bold_unicode("❌ CANCEL"), callback_data=f"manage_svc_country_view_{svc_name}_{country_name}")]])
        )
        return

    if data.startswith("manage_svc_edit_range_init_"):
        parts = data.replace("manage_svc_edit_range_init_", "").rsplit("_", 2)
        svc_name, country_name, range_val = parts[0], parts[1], parts[2]
        context.user_data["admin_state"] = "waiting_for_edit_range_inline"
        context.user_data["temp_target_service"] = svc_name
        context.user_data["temp_target_country"] = country_name
        context.user_data["temp_target_range"] = range_val
        await query.message.edit_text(
            f"✏️ <b>EDIT RANGE: {range_val}</b>\n"
            f"───────────────────\n"
            f"Please send the new range value (e.g. <code>23672XXX</code>):",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(make_bold_unicode("❌ CANCEL"), callback_data=f"manage_svc_country_view_{svc_name}_{country_name}")]])
        )
        return

    # ============ USER BOT CALLBACKS ============
    if data.startswith("svc_"):
        idx = int(data.replace("svc_", ""))
        services = context.user_data.get("la_services", [])
        if not services:
            services = load_custom_services()
            context.user_data["la_services"] = services
        if idx >= len(services):
            await query.answer("Service not found. Please try again.", show_alert=True)
            return
        svc = services[idx]
        sid = svc.get("sid", "Service")
        ranges = svc.get("ranges", [])
        if not ranges:
            await query.answer("No ranges available for this service.", show_alert=True)
            return
        context.user_data["la_svc_idx"] = idx
        context.user_data["la_sid"] = sid
        context.user_data["la_ranges"] = ranges
        keyboard = _build_countries_keyboard(ranges, idx)
        await query.message.edit_text(
            f"📞 <b>GET NUMBER</b>\n\n"
            f"<blockquote>📱 Service: <b>{html.escape(sid)}</b></blockquote>\n"
            f"<blockquote>🌍 আপনার পছন্দের <b>Country</b> সিলেক্ট করুন:</blockquote>",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return

    if data.startswith("rng_"):
        idx = int(data.replace("rng_", ""))
        ranges = context.user_data.get("la_ranges", [])
        if idx >= len(ranges):
            await query.answer("Range not found. Please try again.", show_alert=True)
            return
        range_item = ranges[idx]
        target_country = range_item.get("country", "")
        if not target_country:
            r_text = range_item.get("range", "")
            prefix = re.sub(r'[xX]+$', '', str(r_text)).strip()
            prefix_clean = re.sub(r'\D', '', prefix)
            flag, cname = get_country_info(prefix_clean)
            target_country = f"{flag} {cname}"
        all_country_ranges = []
        target_clean = clean_country_display(target_country)
        for r_item in ranges:
            c_disp = r_item.get("country", "")
            if not c_disp:
                pref = re.sub(r'[xX]+$', '', str(r_item.get("range", ""))).strip()
                pref_cl = re.sub(r'\D', '', pref)
                flg, cn = get_country_info(pref_cl)
                c_disp = f"{flg} {cn}"
            if clean_country_display(c_disp) == target_clean:
                all_country_ranges.append(r_item.get("range", ""))
        sid = context.user_data.get("la_sid", "")
        asyncio.create_task(fast_allocate_number_multi(query, context, all_country_ranges, sid))
        return

    if data == "back_services":
        services = load_custom_services()
        if not services:
            await query.message.edit_text("❌ Services লোড করা যায়নি।")
            return
        context.user_data["la_services"] = services
        keyboard = _build_services_keyboard(services)
        await query.message.edit_text(
            "📞 <b>GET NUMBER</b>\n\n"
            "<blockquote>📱 নিচ থেকে একটি <b>Service</b> সিলেক্ট করুন:</blockquote>",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return

    if data == "same_range":
        r_text = last_range.get(uid)
        if r_text:
            try:
                await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 OTP GROUP", url="https://t.me/panelx_sk_otp")
                ]]))
            except:
                pass
            await process_numbers(update, context, r_text, 1)
        return

    if data == "withdraw_start":
        balance = get_user(uid)['balance']
        if balance < MIN_WITHDRAW:
            await query.message.reply_text(
                f"<blockquote>💵 BALANCE: {format_balance(balance)} BDT\n📉 MIN WITHDRAW: {MIN_WITHDRAW} BDT</blockquote>",
                parse_mode="HTML"
            )
            return
        context.user_data["withdraw_mode"] = "select_method"
        await query.message.reply_text("💳 SELECT YOUR PAYMENT METHOD!", reply_markup=withdraw_method_keyboard())
        return

    if data == "withdraw_confirm":
        await process_withdraw_confirm(update, context)
        return

    if data == "withdraw_cancel":
        await process_withdraw_cancel(update, context)
        return

    if data.startswith("admin_approve_"):
        await admin_approve_withdraw(update, context, data.replace("admin_approve_", ""))
        return

    if data.startswith("admin_reject_"):
        await admin_reject_withdraw(update, context, data.replace("admin_reject_", ""))
        return

    if data.startswith("my_ref_"):
        target_uid = data.replace("my_ref_", "")
        all_logs = load_data(ACTIVITY_LOGS_FILE)
        my_referrals = [log for log in all_logs if str(log.get('uid')) == str(target_uid) and log.get('action') == "REFERRAL_JOINED"]
        content = f"👥 REFERRAL REPORT — {target_uid}\n━━━━━━━━━━━━\nTOTAL: {len(my_referrals)}\n\n"
        for i, log in enumerate(my_referrals, 1):
            try:
                dt_obj = datetime.fromisoformat(log['timestamp'])
                ref_id = log.get('details', {}).get('referred_user', 'N/A')
                content += f"{i}. ID: {ref_id} | {dt_obj.strftime('%d/%m/%Y %I:%M %p')}\n"
            except:
                continue
        f = io.BytesIO(content.encode())
        f.name = f"REF_{target_uid}.txt"
        await context.bot.send_document(chat_id=uid, document=f, caption="✅ **REFERRAL DATA**", parse_mode="Markdown")
        return

    if data.startswith("full_logs_"):
        target_uid = data.replace("full_logs_", "")
        stats = get_user_stats(target_uid)
        all_logs = load_data(ACTIVITY_LOGS_FILE)
        user_db = load_data(USER_DATA_FILE)
        user_info = user_db.get(str(target_uid), {})
        user_otps = [log for log in all_logs if str(log.get('uid')) == str(target_uid) and log.get('action') == "OTP_RECEIVED"]
        content = (
            f"📊 USER DATA REPORT — {target_uid}\n"
            f"💰 BALANCE: {user_info.get('balance', 0):.2f} BDT\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"TODAY NUMBERS: {stats['today_numbers']}\n"
            f"TODAY OTPS: {stats['today_otps']}\n"
            f"7D NUMBERS: {stats['last7d_numbers']}\n"
            f"7D OTPS: {stats['last7d_otps']}\n"
            f"TOTAL NUMBERS: {stats['total_numbers']}\n"
            f"TOTAL OTPS: {stats['total_otps']}\n"
            f"━━━━━━━━━━━━━━━━━━\n\nOTP LOGS:\n"
        )
        for i, log in enumerate(user_otps, 1):
            try:
                dt_obj = datetime.fromisoformat(log['timestamp'])
                d = log.get('details', {})
                content += f"{i}. {dt_obj.strftime('%d/%m/%Y %I:%M %p')}\n   📞 {d.get('number', 'N/A')}\n   🔑 {d.get('otp', 'N/A')}\n\n"
            except:
                continue
        f = io.BytesIO(content.encode())
        f.name = f"USER_{target_uid}.txt"
        await context.bot.send_document(
            chat_id=uid, document=f,
            caption=f"✅ <b>DATA FOR USER: <code>{target_uid}</code></b>",
            parse_mode="HTML"
        )
        return

# ==================== MAIN & POST INIT SECTION ====================

async def post_init(application):
    for _ in range(20):
        asyncio.create_task(worker())
    asyncio.create_task(monitor_loop(application))

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).concurrent_updates(True).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get1number", get1number_command))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("refer", refer_command_slash))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command_slash))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("🚀 BOT RUNNING...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
