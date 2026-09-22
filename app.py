import os
import sys
import json
import uuid
import datetime
from flask import Flask, request, jsonify, render_template_string, send_from_directory

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# Determine base directories based on runtime environment:
if getattr(sys, 'frozen', False):
    # PyInstaller temporary bundle directory
    BUNDLE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    # Persistent directory next to .exe
    DATA_DIR = os.path.dirname(sys.executable)
elif os.environ.get("VERCEL"):
    # Vercel serverless environment (read-only filesystem except /tmp)
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = "/tmp"
else:
    # Standard local python run
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = BUNDLE_DIR

STATIC_DIR = os.path.join(BUNDLE_DIR, 'static')
app = Flask(__name__, static_folder=STATIC_DIR)

LEADS_FILE = os.path.join(DATA_DIR, "leads.json")
CONFIG_FILE = os.path.join(DATA_DIR, "portal_config.json")
BUNDLE_CONFIG_FILE = os.path.join(BUNDLE_DIR, "portal_config.json")

def load_portal_config():
    default_config = {
        "owner_whatsapp": "918115361348", # Port owner's WhatsApp number
        "owner_name": "Sandeep MNP Agent",
        "telegram_bot_token": "",          # Free Telegram Bot Token
        "telegram_chat_id": "",            # Free Telegram Chat ID
        "admin_pin": "1234"                # Simple PIN to view admin panel
    }
    # Check bundled fallback config first if DATA_DIR config doesn't exist yet
    if not os.path.exists(CONFIG_FILE) and os.path.exists(BUNDLE_CONFIG_FILE):
        try:
            with open(BUNDLE_CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                default_config.update(cfg)
        except Exception:
            pass

    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2)
        except Exception:
            pass
        return default_config

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            default_config.update(cfg)
            return default_config
    except Exception:
        return default_config

def save_portal_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")

def send_telegram_alert(lead):
    """Sends 100% FREE instant VIP push notification to SIM Porter's phone via Telegram Bot"""
    cfg = load_portal_config()
    token = cfg.get("telegram_bot_token", "").strip()
    chat_id = cfg.get("telegram_chat_id", "").strip()
    if not token or not chat_id:
        return False

    gps_str = ""
    if lead.get("gps_location"):
        gps_str = f"📍 <b>लाइव GPS मैप:</b> <a href='{lead['gps_location']}'>गूगल मैप्स पर रास्ता देखें 🗺️</a>\n"

    msg = (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>SIM MNP GROUP • नया पोर्टिंग ऑर्डर</b> ⚡\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>बुकिंग रेफरेंस:</b> <code>#{lead['id']}</code>\n"
        f"📅 <b>तारीख व समय:</b> {lead['created_at']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>ग्राहक का नाम:</b> <b>{lead['full_name']}</b>\n"
        f"📱 <b>पोर्ट करने का नंबर:</b> <code>+91 {lead['phone_number']}</code>\n"
        f"💬 <b>व्हाट्सएप:</b> +91 {lead['whatsapp_number']}\n\n"
        f"🔄 <b>पोर्टिंग रूट:</b> <b>{lead['current_operator']}</b> ➔ <b>{lead['target_operator']}</b>\n"
        f"🛵 <b>डिलीवरी मोड:</b> {lead['delivery_type']}\n"
        f"⏰ <b>पसंदीदा समय:</b> {lead.get('preferred_time', 'जल्द से जल्द (ASAP)')}\n"
        f"🏠 <b>पता / लोकेशन:</b> {lead['city_pincode']}\n"
        f"{gps_str}"
        f"🔑 <b>UPC कोड:</b> <code>{lead.get('upc_code') or '⏳ एग्जीक्यूटिव की मदद चाहिए'}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 <i>ग्राहक को तुरंत कॉल या व्हाट्सएप करके सिम डिलीवरी रवाना करें!</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    try:
        import requests
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": False}, timeout=5)
        return True
    except Exception as e:
        print(f"Telegram notification error: {e}")
        return False

def load_leads():
    if not os.path.exists(LEADS_FILE):
        bundle_leads = os.path.join(BUNDLE_DIR, "leads.json")
        if os.path.exists(bundle_leads):
            try:
                with open(bundle_leads, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []
    try:
        with open(LEADS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_leads(leads):
    try:
        with open(LEADS_FILE, "w", encoding="utf-8") as f:
            json.dump(leads, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving leads: {e}")

@app.route("/api/config", methods=["GET"])
def get_config():
    cfg = load_portal_config()
    # Don't expose sensitive tokens fully, but send owner WhatsApp
    return jsonify({
        "success": True,
        "owner_whatsapp": cfg.get("owner_whatsapp", "919876543210"),
        "owner_name": cfg.get("owner_name", "SIM Port Master"),
        "telegram_enabled": bool(cfg.get("telegram_bot_token") and cfg.get("telegram_chat_id"))
    })

@app.route("/api/config/save", methods=["POST"])
def save_config_api():
    data = request.get_json() or {}
    cfg = load_portal_config()
    if "owner_whatsapp" in data:
        # clean phone number
        p = data["owner_whatsapp"].replace("+", "").replace(" ", "").replace("-", "")
        if not p.startswith("91") and len(p) == 10:
            p = "91" + p
        cfg["owner_whatsapp"] = p
    if "owner_name" in data:
        cfg["owner_name"] = data["owner_name"]
    if "telegram_bot_token" in data:
        cfg["telegram_bot_token"] = data["telegram_bot_token"]
    if "telegram_chat_id" in data:
        cfg["telegram_chat_id"] = data["telegram_chat_id"]
    save_portal_config(cfg)
    return jsonify({"success": True, "message": "कॉन्फ़िगरेशन सेव हो गया!"})

@app.route("/api/port-request", methods=["POST"])
def submit_port_request():
    try:
        data = request.get_json() or {}
        required = ["current_operator", "target_operator", "phone_number", "full_name"]
        for field in required:
            if not data.get(field):
                return jsonify({"success": False, "message": f"Field '{field}' is required."}), 400

        lead_id = f"MNP-{datetime.datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:5].upper()}"
        cfg = load_portal_config()
        
        lead_entry = {
            "id": lead_id,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_operator": data.get("current_operator"),
            "target_operator": data.get("target_operator"),
            "phone_number": data.get("phone_number"),
            "full_name": data.get("full_name"),
            "whatsapp_number": data.get("whatsapp_number", data.get("phone_number")),
            "city_pincode": data.get("city_pincode", "Not specified"),
            "gps_location": data.get("gps_location", ""),
            "preferred_time": data.get("preferred_time", "जल्द से जल्द (ASAP)"),
            "ekyc_ready": data.get("ekyc_ready", True),
            "delivery_type": data.get("delivery_type", "Doorstep Delivery"),
            "upc_status": data.get("upc_status", "Needs Guidance"),
            "upc_code": data.get("upc_code", ""),
            "status": "New Lead",
            "ip_address": request.remote_addr
        }

        leads = load_leads()
        leads.insert(0, lead_entry)
        save_leads(leads)

        # Trigger 100% FREE Telegram Push Notification to Port Owner in background
        send_telegram_alert(lead_entry)

        return jsonify({
            "success": True,
            "message": "पोर्टिंग अनुरोध सफलतापूर्वक दर्ज किया गया है!",
            "lead": lead_entry,
            "owner_whatsapp": cfg.get("owner_whatsapp", "919876543210")
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/leads", methods=["GET"])
def get_leads():
    return jsonify({
        "success": True,
        "leads": load_leads()
    })

@app.route("/api/leads/clear", methods=["POST"])
def clear_leads():
    save_leads([])
    return jsonify({"success": True, "message": "All leads cleared"})

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="hi" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SIM MNP Portal - सही नेटवर्क सही फैसला | Instant SIM Porting</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        brand: {
                            gold: '#FFD700',
                            jio: '#0a38d1',
                            airtel: '#ed1b24',
                            vi: '#c40d2e',
                            bsnl: '#005baa',
                            dark: '#0a0d14',
                            card: '#121722',
                            cardHover: '#182030',
                            border: '#1f293d'
                        }
                    },
                    boxShadow: {
                        'neon-gold': '0 0 25px rgba(255, 215, 0, 0.4)',
                        'neon-blue': '0 0 25px rgba(10, 56, 209, 0.5)',
                        'neon-red': '0 0 25px rgba(237, 27, 36, 0.5)',
                        'neon-green': '0 0 25px rgba(34, 197, 94, 0.5)',
                    }
                }
            }
        }
    </script>
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <!-- Canvas Confetti -->
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=Rozha+One&display=swap" rel="stylesheet">

    <style>
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: #06090e;
            color: #f1f5f9;
            overflow-x: hidden;
        }

        /* Subtle glowing background grid */
        .bg-grid {
            background-image: radial-gradient(rgba(255, 215, 0, 0.08) 1px, transparent 1px);
            background-size: 28px 28px;
        }

        /* Gradient Text */
        .text-gradient-gold {
            background: linear-gradient(135deg, #FFF6B7 0%, #F6416C 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .text-gradient-mnp {
            background: linear-gradient(135deg, #FFE000 0%, #799F0C 100%);
            background: linear-gradient(90deg, #FFFFFF 0%, #FFD700 45%, #FFA500 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* Operator circle animations */
        .operator-circle {
            transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .operator-circle:hover {
            transform: translateY(-8px) scale(1.04);
        }
        .operator-circle.selected {
            transform: translateY(-6px) scale(1.05);
        }

        /* Smooth tab transition */
        .step-panel {
            transition: opacity 0.3s ease, transform 0.3s ease;
        }

        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #0b0f19;
        }
        ::-webkit-scrollbar-thumb {
            background: #25334d;
            border-radius: 4px;
        }
    </style>
</head>
<body class="min-h-screen bg-grid flex flex-col justify-between">

    <!-- TOP ANNOUNCEMENT BAR -->
    <div class="bg-gradient-to-r from-amber-600 via-yellow-500 to-amber-700 text-black py-1.5 px-4 text-xs md:text-sm font-bold text-center tracking-wide flex items-center justify-center gap-2 shadow-md">
        <span class="animate-pulse">🔥</span>
        <span>घर बैठे 15 मिनट में सिम पोर्ट कराएं | Free Doorstep Delivery & ₹299 Welcome Plan Free!</span>
        <span class="bg-black text-yellow-400 px-2 py-0.5 rounded-full text-[10px] uppercase font-black">Limited Offer</span>
    </div>

    <!-- NAVBAR / HEADER -->
    <header class="border-b border-gray-800/80 bg-gray-950/80 backdrop-blur-xl sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
            <!-- Brand & User Logo -->
            <div class="flex items-center gap-3 cursor-pointer" onclick="goToStep(1)">
                <div class="relative w-12 h-12 rounded-full overflow-hidden p-0.5 bg-gradient-to-tr from-yellow-400 via-red-500 to-blue-600 shadow-neon-gold">
                    <img src="/static/brand_logo.jpg" alt="SIM MNP GROUP" class="w-full h-full object-cover rounded-full" onerror="this.src='https://placehold.co/100x100/10121b/ffd700?text=MNP'">
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <span class="font-black text-lg md:text-xl tracking-tight text-white flex items-center">
                            SIM <span class="text-yellow-400 mx-1">MNP</span> GROUP
                        </span>
                        <span class="bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span> Live
                        </span>
                    </div>
                    <p class="text-[11px] text-gray-400 font-medium">सही नेटवर्क • सही फैसला | Official Porting Desk</p>
                </div>
            </div>

            <!-- Header Action Buttons -->
            <div class="flex items-center gap-2 sm:gap-3">
                <button onclick="toggleSettingsModal()" class="text-xs font-semibold px-3 py-2 rounded-lg bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-300 border border-yellow-500/30 flex items-center gap-1.5 transition">
                    <i data-lucide="settings" class="w-3.5 h-3.5 text-yellow-400"></i>
                    <span class="hidden sm:inline">Porter Number</span>
                </button>
                <button onclick="toggleLeadsModal()" class="text-xs font-semibold px-3 py-2 rounded-lg bg-gray-800/80 hover:bg-gray-700 text-gray-300 border border-gray-700 flex items-center gap-1.5 transition">
                    <i data-lucide="database" class="w-3.5 h-3.5 text-yellow-400"></i>
                    <span class="hidden sm:inline">Check Requests</span>
                </button>
                <a href="https://wa.me/?text=Hello%20SIM%20MNP%20Group!%20I%20need%20help%20with%20porting%20my%20SIM." target="_blank" class="text-xs font-bold px-3.5 py-2 rounded-lg bg-gradient-to-r from-emerald-500 to-green-600 text-white flex items-center gap-1.5 shadow-lg shadow-emerald-900/30 hover:scale-105 transition">
                    <i data-lucide="message-circle" class="w-4 h-4"></i>
                    <span class="hidden sm:inline">WhatsApp Group</span>
                </a>
            </div>
        </div>
    </header>

    <!-- MAIN CONTENT WRAPPER -->
    <main class="max-w-4xl mx-auto px-4 sm:px-6 py-8 flex-1 w-full">

        <!-- HERO SECTION / TITLE -->
        <div id="heroSection" class="text-center mb-8 transition-all">
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-yellow-400/10 border border-yellow-400/30 text-yellow-400 text-xs font-bold mb-3 uppercase tracking-wider">
                <i data-lucide="zap" class="w-3.5 h-3.5"></i> All India Mobile Number Portability (MNP) 2026
            </div>
            <h1 class="text-3xl sm:text-4xl md:text-5xl font-black text-white tracking-tight leading-tight">
                अपना मोबाइल नंबर <span class="text-gradient-mnp">आसानी से पोर्ट</span> करें
            </h1>
            <p class="mt-2 text-sm sm:text-base text-gray-400 max-w-xl mx-auto">
                वही पुराना नंबर रहेगा, बस नेटवर्क और ऑफर्स नए मिलेंगे। 4 सिंपल स्टेप्स में अपने मनपसंद ऑपरेटर में स्विच करें।
            </p>
        </div>

        <!-- PROGRESS STEPPER BAR -->
        <div class="bg-gray-900/90 border border-gray-800 rounded-2xl p-4 sm:p-5 mb-8 shadow-xl backdrop-blur-md">
            <div class="flex items-center justify-between relative">
                <!-- Connecting Line -->
                <div class="absolute top-1/2 left-6 right-6 -translate-y-1/2 h-1 bg-gray-800 -z-0">
                    <div id="progressBar" class="h-full bg-gradient-to-r from-yellow-400 via-amber-500 to-green-500 transition-all duration-500 w-0"></div>
                </div>

                <!-- Step 1 Indicator -->
                <div class="step-indicator flex flex-col items-center relative z-10 cursor-pointer" onclick="goToStep(1)">
                    <div id="stepDot1" class="w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm bg-yellow-400 text-black ring-4 ring-yellow-400/20 shadow-neon-gold transition">
                        1
                    </div>
                    <span class="text-[11px] sm:text-xs font-bold mt-1.5 text-yellow-400" id="stepLabel1">पुराना नेटवर्क</span>
                </div>

                <!-- Step 2 Indicator -->
                <div class="step-indicator flex flex-col items-center relative z-10 cursor-pointer" onclick="goToStep(2)">
                    <div id="stepDot2" class="w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm bg-gray-800 text-gray-400 border border-gray-700 transition">
                        2
                    </div>
                    <span class="text-[11px] sm:text-xs font-semibold mt-1.5 text-gray-500" id="stepLabel2">नया ऑपरेटर</span>
                </div>

                <!-- Step 3 Indicator -->
                <div class="step-indicator flex flex-col items-center relative z-10 cursor-pointer" onclick="goToStep(3)">
                    <div id="stepDot3" class="w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm bg-gray-800 text-gray-400 border border-gray-700 transition">
                        3
                    </div>
                    <span class="text-[11px] sm:text-xs font-semibold mt-1.5 text-gray-500" id="stepLabel3">आपका विवरण</span>
                </div>

                <!-- Step 4 Indicator -->
                <div class="step-indicator flex flex-col items-center relative z-10">
                    <div id="stepDot4" class="w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm bg-gray-800 text-gray-400 border border-gray-700 transition">
                        <i data-lucide="check" class="w-4 h-4"></i>
                    </div>
                    <span class="text-[11px] sm:text-xs font-semibold mt-1.5 text-gray-500" id="stepLabel4">सफलता</span>
                </div>
            </div>
        </div>

        <!-- ============================================================= -->
        <!-- STEP 1: CHOOSE CURRENT OPERATOR (आपकी वर्तमान सिम कौन सी है?) -->
        <!-- ============================================================= -->
        <div id="step1Panel" class="step-panel bg-gray-900/80 border border-gray-800 rounded-3xl p-6 sm:p-8 backdrop-blur-xl shadow-2xl">
            <div class="flex items-center justify-between mb-6">
                <div>
                    <span class="text-xs font-bold uppercase tracking-wider text-yellow-400">Step 1 of 3</span>
                    <h2 class="text-xl sm:text-2xl font-black text-white mt-0.5">
                        आपकी वर्तमान सिम किस कंपनी की है?
                    </h2>
                    <p class="text-xs sm:text-sm text-gray-400 mt-1">
                        जिस सिम को आप बदलना चाहते हैं, उस कंपनी के लोगो (Circle) पर क्लिक करें:
                    </p>
                </div>
                <div class="hidden sm:flex w-10 h-10 rounded-xl bg-yellow-400/10 border border-yellow-400/30 items-center justify-center text-yellow-400">
                    <i data-lucide="radio" class="w-5 h-5"></i>
                </div>
            </div>

            <!-- CIRCULAR OPERATOR GRID -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6 my-6">

                <!-- 1. JIO -->
                <div onclick="selectCurrentOperator('Jio')" id="card-current-Jio" class="operator-circle group cursor-pointer bg-gray-950/70 border-2 border-gray-800 hover:border-blue-500 rounded-2xl p-4 sm:p-5 flex flex-col items-center text-center transition-all relative overflow-hidden">
                    <div class="absolute top-2 right-2 w-5 h-5 rounded-full border border-gray-700 flex items-center justify-center text-transparent group-hover:text-blue-400 checkmark-indicator transition">
                        <i data-lucide="check" class="w-3.5 h-3.5"></i>
                    </div>
                    <!-- Jio Circle Logo -->
                    <div class="w-20 h-20 sm:w-24 sm:h-24 rounded-full bg-gradient-to-br from-blue-700 via-blue-600 to-indigo-900 p-1 flex items-center justify-center shadow-lg group-hover:shadow-blue-600/40 ring-4 ring-blue-500/20 group-hover:ring-blue-500/60 transition">
                        <div class="w-full h-full rounded-full border-2 border-white/90 flex flex-col items-center justify-center bg-[#0a38d1]">
                            <span class="text-white font-black text-2xl sm:text-3xl tracking-tighter italic font-serif">Jio</span>
                        </div>
                    </div>
                    <h3 class="font-extrabold text-white text-base sm:text-lg mt-3">Reliance Jio</h3>
                    <span class="text-[11px] text-blue-400 font-semibold bg-blue-950/80 px-2 py-0.5 rounded-full mt-1 border border-blue-800">4G / 5G True</span>
                </div>

                <!-- 2. AIRTEL -->
                <div onclick="selectCurrentOperator('Airtel')" id="card-current-Airtel" class="operator-circle group cursor-pointer bg-gray-950/70 border-2 border-gray-800 hover:border-red-500 rounded-2xl p-4 sm:p-5 flex flex-col items-center text-center transition-all relative overflow-hidden">
                    <div class="absolute top-2 right-2 w-5 h-5 rounded-full border border-gray-700 flex items-center justify-center text-transparent group-hover:text-red-400 checkmark-indicator transition">
                        <i data-lucide="check" class="w-3.5 h-3.5"></i>
                    </div>
                    <!-- Airtel Circle Logo -->
                    <div class="w-20 h-20 sm:w-24 sm:h-24 rounded-full bg-gradient-to-br from-red-600 via-red-500 to-rose-800 p-1 flex items-center justify-center shadow-lg group-hover:shadow-red-600/40 ring-4 ring-red-500/20 group-hover:ring-red-500/60 transition">
                        <div class="w-full h-full rounded-full border-2 border-white/90 flex flex-col items-center justify-center bg-[#ed1b24]">
                            <!-- Airtel Stylized Loop -->
                            <svg class="w-8 h-8 text-white mb-0.5 fill-current" viewBox="0 0 100 100">
                                <path d="M50 15 C30 15 18 32 18 52 C18 70 30 85 48 85 C62 85 75 75 75 60 C75 48 65 40 54 40 C44 40 37 47 37 55 C37 62 42 67 48 67 C53 67 56 63 56 59 C56 56 54 54 51 54 C48 54 47 56 47 58 C47 59 48 60 49 60 C46 60 44 58 44 55 C44 50 48 46 54 46 C61 46 68 52 68 60 C68 71 58 79 46 79 C32 79 25 67 25 52 C25 36 35 21 50 21 C66 21 76 34 76 50 L83 50 C83 31 71 15 50 15 Z" />
                            </svg>
                            <span class="text-white font-black text-xs tracking-wider uppercase">airtel</span>
                        </div>
                    </div>
                    <h3 class="font-extrabold text-white text-base sm:text-lg mt-3">Bharti Airtel</h3>
                    <span class="text-[11px] text-red-400 font-semibold bg-red-950/80 px-2 py-0.5 rounded-full mt-1 border border-red-800">5G Plus</span>
                </div>

                <!-- 3. VI -->
                <div onclick="selectCurrentOperator('Vi')" id="card-current-Vi" class="operator-circle group cursor-pointer bg-gray-950/70 border-2 border-gray-800 hover:border-yellow-500 rounded-2xl p-4 sm:p-5 flex flex-col items-center text-center transition-all relative overflow-hidden">
                    <div class="absolute top-2 right-2 w-5 h-5 rounded-full border border-gray-700 flex items-center justify-center text-transparent group-hover:text-yellow-400 checkmark-indicator transition">
                        <i data-lucide="check" class="w-3.5 h-3.5"></i>
                    </div>
                    <!-- Vi Circle Logo -->
                    <div class="w-20 h-20 sm:w-24 sm:h-24 rounded-full bg-gradient-to-br from-red-600 via-rose-700 to-amber-600 p-1 flex items-center justify-center shadow-lg group-hover:shadow-yellow-500/40 ring-4 ring-yellow-500/20 group-hover:ring-yellow-500/60 transition">
                        <div class="w-full h-full rounded-full border-2 border-white/90 flex flex-col items-center justify-center bg-[#c40d2e] relative">
                            <div class="flex items-baseline justify-center">
                                <span class="text-white font-black text-2xl sm:text-3xl tracking-tight">V</span>
                                <span class="text-white font-black text-2xl sm:text-3xl tracking-tight -ml-0.5">!</span>
                                <span class="w-2 h-2 rounded-full bg-yellow-400 absolute top-4 sm:top-5 right-5 sm:right-6"></span>
                            </div>
                        </div>
                    </div>
                    <h3 class="font-extrabold text-white text-base sm:text-lg mt-3">Vodafone Idea</h3>
                    <span class="text-[11px] text-yellow-400 font-semibold bg-amber-950/80 px-2 py-0.5 rounded-full mt-1 border border-amber-800">Hero 4G</span>
                </div>

                <!-- 4. BSNL -->
                <div onclick="selectCurrentOperator('BSNL')" id="card-current-BSNL" class="operator-circle group cursor-pointer bg-gray-950/70 border-2 border-gray-800 hover:border-yellow-400 rounded-2xl p-4 sm:p-5 flex flex-col items-center text-center transition-all relative overflow-hidden">
                    <div class="absolute top-2 right-2 w-5 h-5 rounded-full border border-gray-700 flex items-center justify-center text-transparent group-hover:text-yellow-400 checkmark-indicator transition">
                        <i data-lucide="check" class="w-3.5 h-3.5"></i>
                    </div>
                    <!-- BSNL Circle Logo -->
                    <div class="w-20 h-20 sm:w-24 sm:h-24 rounded-full bg-gradient-to-br from-yellow-400 via-amber-500 to-blue-700 p-1 flex items-center justify-center shadow-lg group-hover:shadow-yellow-400/40 ring-4 ring-yellow-400/20 group-hover:ring-yellow-400/60 transition">
                        <div class="w-full h-full rounded-full border-2 border-white/90 flex flex-col items-center justify-center bg-[#FFD700] text-blue-900">
                            <!-- Arrows -->
                            <div class="flex items-center gap-1">
                                <span class="text-red-600 font-bold text-xs">↗</span>
                                <span class="text-blue-900 font-bold text-xs">↙</span>
                            </div>
                            <span class="font-black text-lg sm:text-xl tracking-tighter text-blue-950">BSNL</span>
                        </div>
                    </div>
                    <h3 class="font-extrabold text-white text-base sm:text-lg mt-3">BSNL</h3>
                    <span class="text-[11px] text-yellow-300 font-semibold bg-blue-950/80 px-2 py-0.5 rounded-full mt-1 border border-yellow-700">Swadeshi 4G</span>
                </div>

            </div>

            <!-- SELECTED PREVIEW & NEXT ACTION -->
            <div class="mt-8 pt-6 border-t border-gray-800 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div class="flex items-center gap-3">
                    <div id="currentSelectedBadge" class="hidden items-center gap-2 bg-yellow-400/10 border border-yellow-400/30 px-3 py-1.5 rounded-xl text-yellow-400 text-xs font-bold">
                        <span>चयनित ऑपरेटर:</span>
                        <span id="currentSelectedText" class="font-extrabold underline text-sm text-white"></span>
                    </div>
                    <p id="currentInstructionText" class="text-xs text-gray-400">
                        👉 आगे बढ़ने के लिए कृपया ऊपर अपनी सिम कंपनी चुनें।
                    </p>
                </div>

                <button id="btnNextToStep2" onclick="validateAndGoToStep2()" disabled class="w-full sm:w-auto px-6 py-3.5 rounded-xl font-bold text-sm bg-gray-800 text-gray-500 cursor-not-allowed flex items-center justify-center gap-2 transition duration-300">
                    <span>अगला: नया ऑपरेटर चुनें (Step 2)</span>
                    <i data-lucide="arrow-right" class="w-4 h-4"></i>
                </button>
            </div>
        </div>

        <!-- ============================================================= -->
        <!-- STEP 2: CHOOSE TARGET OPERATOR (किस कंपनी में पोर्ट करवाना चाहते हैं?) -->
        <!-- ============================================================= -->
        <div id="step2Panel" class="step-panel hidden bg-gray-900/80 border border-gray-800 rounded-3xl p-6 sm:p-8 backdrop-blur-xl shadow-2xl">
            <div class="flex items-center justify-between mb-6">
                <div>
                    <span class="text-xs font-bold uppercase tracking-wider text-green-400">Step 2 of 3</span>
                    <h2 class="text-xl sm:text-2xl font-black text-white mt-0.5">
                        आप किस कंपनी में पोर्ट करवाना चाहते हैं?
                    </h2>
                    <p class="text-xs sm:text-sm text-gray-400 mt-1">
                        अपना पसंदीदा नया नेटवर्क चुनें (Port-in Exclusive Offers के साथ):
                    </p>
                </div>
                <!-- Current SIM Tag -->
                <div class="hidden sm:flex items-center gap-2 bg-gray-800/90 border border-gray-700 px-3 py-1.5 rounded-xl text-xs">
                    <span class="text-gray-400">मौजूदा सिम:</span>
                    <span id="badgeCurrentSimName" class="font-extrabold text-yellow-400"></span>
                </div>
            </div>

            <!-- TARGET OPERATOR SELECTION GRID -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 my-6">

                <!-- TARGET 1: JIO -->
                <div onclick="selectTargetOperator('Jio')" id="card-target-Jio" class="target-card group cursor-pointer bg-gray-950/70 border-2 border-gray-800 hover:border-blue-500 rounded-2xl p-4 sm:p-5 flex items-center justify-between transition-all relative">
                    <div class="flex items-center gap-4">
                        <!-- Circle Logo -->
                        <div class="w-16 h-16 rounded-full bg-[#0a38d1] border-2 border-white/80 flex items-center justify-center text-white font-black text-xl italic shadow-md">
                            Jio
                        </div>
                        <div>
                            <div class="flex items-center gap-2">
                                <h3 class="font-black text-white text-base">Reliance Jio 5G</h3>
                                <span class="bg-blue-600/30 text-blue-400 text-[10px] font-bold px-2 py-0.5 rounded-full border border-blue-500/40">Most Popular</span>
                            </div>
                            <p class="text-xs text-gray-300 mt-1 font-medium">✨ Unlimited True 5G Data + ₹299 Welcome Plan Free</p>
                            <span class="text-[11px] text-emerald-400 font-semibold flex items-center gap-1 mt-1">
                                <i data-lucide="check-circle" class="w-3 h-3"></i> Free Home Delivery & Instant Activation
                            </span>
                        </div>
                    </div>
                    <div class="w-6 h-6 rounded-full border-2 border-gray-700 flex items-center justify-center text-transparent target-check transition">
                        <i data-lucide="check" class="w-3.5 h-3.5"></i>
                    </div>
                </div>

                <!-- TARGET 2: AIRTEL -->
                <div onclick="selectTargetOperator('Airtel')" id="card-target-Airtel" class="target-card group cursor-pointer bg-gray-950/70 border-2 border-gray-800 hover:border-red-500 rounded-2xl p-4 sm:p-5 flex items-center justify-between transition-all relative">
                    <div class="flex items-center gap-4">
                        <!-- Circle Logo -->
                        <div class="w-16 h-16 rounded-full bg-[#ed1b24] border-2 border-white/80 flex items-center justify-center text-white font-black text-sm uppercase shadow-md">
                            airtel
                        </div>
                        <div>
                            <div class="flex items-center gap-2">
                                <h3 class="font-black text-white text-base">Bharti Airtel 5G</h3>
                                <span class="bg-red-600/30 text-red-400 text-[10px] font-bold px-2 py-0.5 rounded-full border border-red-500/40">Best Coverage</span>
                            </div>
                            <p class="text-xs text-gray-300 mt-1 font-medium">🚀 Unlimited 5G + 1.5GB/Day + Free OTT Subscriptions</p>
                            <span class="text-[11px] text-emerald-400 font-semibold flex items-center gap-1 mt-1">
                                <i data-lucide="check-circle" class="w-3 h-3"></i> Ultra-Fast Calling & VoLTE Crystal Sound
                            </span>
                        </div>
                    </div>
                    <div class="w-6 h-6 rounded-full border-2 border-gray-700 flex items-center justify-center text-transparent target-check transition">
                        <i data-lucide="check" class="w-3.5 h-3.5"></i>
                    </div>
                </div>

                <!-- TARGET 3: VI -->
                <div onclick="selectTargetOperator('Vi')" id="card-target-Vi" class="target-card group cursor-pointer bg-gray-950/70 border-2 border-gray-800 hover:border-yellow-500 rounded-2xl p-4 sm:p-5 flex items-center justify-between transition-all relative">
                    <div class="flex items-center gap-4">
                        <!-- Circle Logo -->
                        <div class="w-16 h-16 rounded-full bg-[#c40d2e] border-2 border-white/80 flex items-center justify-center text-white font-black text-xl shadow-md">
                            V!
                        </div>
                        <div>
                            <div class="flex items-center gap-2">
                                <h3 class="font-black text-white text-base">Vodafone Idea (Vi)</h3>
                                <span class="bg-amber-600/30 text-yellow-400 text-[10px] font-bold px-2 py-0.5 rounded-full border border-yellow-500/40">Night Binge</span>
                            </div>
                            <p class="text-xs text-gray-300 mt-1 font-medium">🌙 Free Unlimited Data 12AM-6AM + Weekend Rollover</p>
                            <span class="text-[11px] text-emerald-400 font-semibold flex items-center gap-1 mt-1">
                                <i data-lucide="check-circle" class="w-3 h-3"></i> Best for heavy night downloads & gamers
                            </span>
                        </div>
                    </div>
                    <div class="w-6 h-6 rounded-full border-2 border-gray-700 flex items-center justify-center text-transparent target-check transition">
                        <i data-lucide="check" class="w-3.5 h-3.5"></i>
                    </div>
                </div>

                <!-- TARGET 4: BSNL -->
                <div onclick="selectTargetOperator('BSNL')" id="card-target-BSNL" class="target-card group cursor-pointer bg-gray-950/70 border-2 border-gray-800 hover:border-yellow-400 rounded-2xl p-4 sm:p-5 flex items-center justify-between transition-all relative">
                    <div class="flex items-center gap-4">
                        <!-- Circle Logo -->
                        <div class="w-16 h-16 rounded-full bg-[#FFD700] border-2 border-blue-900 flex items-center justify-center text-blue-950 font-black text-base shadow-md">
                            BSNL
                        </div>
                        <div>
                            <div class="flex items-center gap-2">
                                <h3 class="font-black text-white text-base">BSNL 4G (Desh Ka Network)</h3>
                                <span class="bg-emerald-600/30 text-emerald-400 text-[10px] font-bold px-2 py-0.5 rounded-full border border-emerald-500/40">Cheapest Tariff</span>
                            </div>
                            <p class="text-xs text-gray-300 mt-1 font-medium">💰 सबसे सस्ते रीचार्ज प्लान + 365 दिन की लंबी वैलिडिटी</p>
                            <span class="text-[11px] text-emerald-400 font-semibold flex items-center gap-1 mt-1">
                                <i data-lucide="check-circle" class="w-3 h-3"></i> Budget friendly & No extra surge charges
                            </span>
                        </div>
                    </div>
                    <div class="w-6 h-6 rounded-full border-2 border-gray-700 flex items-center justify-center text-transparent target-check transition">
                        <i data-lucide="check" class="w-3.5 h-3.5"></i>
                    </div>
                </div>

            </div>

            <!-- NAVIGATION BUTTONS -->
            <div class="mt-8 pt-6 border-t border-gray-800 flex flex-col-reverse sm:flex-row items-center justify-between gap-4">
                <button onclick="goToStep(1)" class="w-full sm:w-auto px-5 py-3 rounded-xl font-bold text-sm bg-gray-800 hover:bg-gray-700 text-gray-300 flex items-center justify-center gap-2 transition">
                    <i data-lucide="arrow-left" class="w-4 h-4"></i>
                    <span>वापस जाएं (Back)</span>
                </button>

                <button id="btnNextToStep3" onclick="validateAndGoToStep3()" disabled class="w-full sm:w-auto px-6 py-3.5 rounded-xl font-bold text-sm bg-gray-800 text-gray-500 cursor-not-allowed flex items-center justify-center gap-2 transition duration-300">
                    <span>अगला: मोबाइल नंबर व विवरण भरें (Step 3)</span>
                    <i data-lucide="arrow-right" class="w-4 h-4"></i>
                </button>
            </div>
        </div>

        <!-- ============================================================= -->
        <!-- STEP 3: CUSTOMER DETAILS (नंबर और जरूरी डिटेल्स भरें) -->
        <!-- ============================================================= -->
        <div id="step3Panel" class="step-panel hidden bg-gray-900/80 border border-gray-800 rounded-3xl p-6 sm:p-8 backdrop-blur-xl shadow-2xl">
            <div class="flex items-center justify-between mb-6">
                <div>
                    <span class="text-xs font-bold uppercase tracking-wider text-yellow-400">Step 3 of 3</span>
                    <h2 class="text-xl sm:text-2xl font-black text-white mt-0.5">
                        अपनी पोर्टिंग डिटेल्स दर्ज करें
                    </h2>
                    <p class="text-xs sm:text-sm text-gray-400 mt-1">
                        हमारे प्रतिनिधि 15 मिनट में आपसे संपर्क करेंगे और सिम डिलीवरी करेंगे:
                    </p>
                </div>
            </div>

            <!-- PORT SUMMARY ROUTE BADGE -->
            <div class="bg-gradient-to-r from-gray-950 via-gray-900 to-gray-950 border border-yellow-500/30 rounded-2xl p-4 mb-6 flex items-center justify-between shadow-inner">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-xs" id="summaryOldIcon">
                        <!-- Filled by JS -->
                    </div>
                    <div>
                        <span class="text-[10px] uppercase font-bold text-gray-400">From Operator</span>
                        <div id="summaryOldName" class="font-extrabold text-sm text-white">Old</div>
                    </div>
                </div>

                <div class="flex flex-col items-center px-3">
                    <span class="text-[11px] font-bold text-yellow-400 flex items-center gap-1">
                        PORTING <i data-lucide="arrow-right" class="w-3.5 h-3.5 animate-pulse"></i>
                    </span>
                    <span class="text-[10px] text-gray-400">Same Number</span>
                </div>

                <div class="flex items-center gap-3">
                    <div class="text-right">
                        <span class="text-[10px] uppercase font-bold text-gray-400">To Operator</span>
                        <div id="summaryNewName" class="font-extrabold text-sm text-emerald-400">New</div>
                    </div>
                    <div class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-xs" id="summaryNewIcon">
                        <!-- Filled by JS -->
                    </div>
                </div>
            </div>

            <!-- FORM INPUT FIELDS -->
            <form id="portForm" onsubmit="handleFormSubmit(event)" class="space-y-4">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">

                    <!-- Mobile Number -->
                    <div>
                        <label class="block text-xs font-bold text-gray-300 mb-1.5 flex items-center justify-between">
                            <span>पोर्ट करने वाला 10-अंकों का मोबाइल नंबर *</span>
                            <span class="text-emerald-400 text-[10px]">भारतीय नंबर</span>
                        </label>
                        <div class="relative">
                            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400 font-bold text-sm">
                                +91
                            </div>
                            <input type="tel" id="inputPhoneNumber" maxlength="10" required placeholder="98765 43210" class="w-full pl-12 pr-4 py-3 rounded-xl bg-gray-950 border border-gray-700 focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20 text-white font-bold text-base tracking-wider placeholder-gray-600 outline-none transition">
                        </div>
                    </div>

                    <!-- Full Name -->
                    <div>
                        <label class="block text-xs font-bold text-gray-300 mb-1.5">
                            आपका पूरा नाम (आधार कार्ड के अनुसार) *
                        </label>
                        <div class="relative">
                            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                                <i data-lucide="user" class="w-4 h-4"></i>
                            </div>
                            <input type="text" id="inputFullName" required placeholder="उदा. राहुल शर्मा" class="w-full pl-10 pr-4 py-3 rounded-xl bg-gray-950 border border-gray-700 focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20 text-white text-sm placeholder-gray-600 outline-none transition">
                        </div>
                    </div>

                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">

                    <!-- WhatsApp Number -->
                    <div>
                        <label class="block text-xs font-bold text-gray-300 mb-1.5 flex items-center justify-between">
                            <span>व्हाट्सएप नंबर (अपडेट के लिए)</span>
                            <button type="button" onclick="copySameAsPhone()" class="text-[10px] text-yellow-400 hover:underline">Same as phone</button>
                        </label>
                        <div class="relative">
                            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-emerald-500">
                                <i data-lucide="message-square" class="w-4 h-4"></i>
                            </div>
                            <input type="tel" id="inputWhatsApp" maxlength="10" placeholder="वैकल्पिक व्हाट्सएप नंबर" class="w-full pl-10 pr-4 py-3 rounded-xl bg-gray-950 border border-gray-700 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 text-white text-sm placeholder-gray-600 outline-none transition">
                        </div>
                    </div>

                    <!-- Structured Address Fields (Street & City/Pincode) -->
                    <div class="sm:col-span-2 space-y-3">
                        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                            <label class="block text-xs font-bold text-gray-200 flex items-center gap-1.5">
                                <i data-lucide="map-pin" class="w-4 h-4 text-emerald-400"></i>
                                <span>सिम डिलीवरी का पूरा पता (Doorstep Delivery Address) *</span>
                            </label>
                            <button type="button" onclick="detectLiveLocation()" id="btnDetectGps" class="text-xs bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold px-3 py-1.5 rounded-lg flex items-center justify-center gap-1.5 shadow-md hover:scale-105 transition cursor-pointer border border-blue-400/30 w-full sm:w-auto">
                                <span id="gpsSpinner" class="hidden animate-spin">🔄</span>
                                <i data-lucide="crosshair" class="w-3.5 h-3.5 text-yellow-300"></i>
                                <span id="gpsBtnText">📍 Auto-Detect City & GPS</span>
                            </button>
                        </div>

                        <!-- 1. House, Street, Landmark -->
                        <div class="relative">
                            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                                <i data-lucide="home" class="w-4 h-4 text-yellow-400"></i>
                            </div>
                            <input type="text" id="inputHouseStreet" required placeholder="मकान नं., फ्लैट नं., गली नं., या नजदीकी लैंडमार्क (उदा. मकान 42, नियर शिव मंदिर)" class="w-full pl-10 pr-4 py-2.5 rounded-xl bg-gray-950 border border-gray-700 focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20 text-white text-xs placeholder-gray-500 outline-none transition">
                        </div>

                        <!-- 2. City, Area, Pincode (Filled automatically by GPS, or editable) -->
                        <div class="relative">
                            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                                <i data-lucide="navigation" class="w-4 h-4 text-emerald-400"></i>
                            </div>
                            <input type="text" id="inputCityPincode" required placeholder="इलाका, शहर व 6-अंकों का पिन कोड (उदा. लंका, वाराणसी - 221005)" class="w-full pl-10 pr-4 py-2.5 rounded-xl bg-gray-950 border border-gray-700 focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20 text-white text-xs placeholder-gray-500 outline-none transition">
                        </div>
                        
                        <!-- Real-time GPS Detection Result Badge -->
                        <div id="gpsStatusBadge" class="hidden p-3 rounded-xl bg-emerald-950/80 border border-emerald-500/40 text-[11px] text-emerald-300 flex flex-col sm:flex-row sm:items-center justify-between gap-2 shadow-inner">
                            <div class="flex items-start sm:items-center gap-2">
                                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping mt-1 sm:mt-0 shrink-0"></span>
                                <i data-lucide="map-pin-check" class="w-4 h-4 text-emerald-400 shrink-0"></i>
                                <span id="gpsStatusMessage">GPS लोकेशन डिटेक्टेड</span>
                            </div>
                            <a id="gpsMapLink" href="#" target="_blank" class="px-2.5 py-1 rounded-lg bg-emerald-800/80 hover:bg-emerald-700 text-yellow-300 font-bold flex items-center gap-1 underline transition w-fit shrink-0">
                                <span>Google Maps पर देखें ↗</span>
                            </a>
                        </div>
                        <input type="hidden" id="hiddenGpsLocation" value="">
                    </div>

                    <!-- Delivery Preferred Time Slot -->
                    <div>
                        <label class="block text-xs font-bold text-gray-300 mb-1.5">
                            ⏰ सिम डिलीवरी का पसंदीदा समय:
                        </label>
                        <select id="selectPreferredTime" class="w-full px-3 py-2.5 rounded-xl bg-gray-950 border border-gray-700 focus:border-yellow-400 text-white text-xs font-semibold outline-none">
                            <option value="⚡ ASAP (अगले 15-30 मिनट में)">⚡ ASAP (अगले 15-30 मिनट में)</option>
                            <option value="🌅 सुबह (9:00 AM - 1:00 PM)">🌅 सुबह (9:00 AM - 1:00 PM)</option>
                            <option value="🌇 दोपहर (1:00 PM - 5:00 PM)">🌇 दोपहर (1:00 PM - 5:00 PM)</option>
                            <option value="🌙 शाम (5:00 PM - 9:00 PM)">🌙 शाम (5:00 PM - 9:00 PM)</option>
                        </select>
                    </div>

                    <!-- Aadhaar Biometric Ready Checkbox -->
                    <div class="flex items-center">
                        <label class="cursor-pointer border border-emerald-500/30 bg-emerald-950/20 hover:bg-emerald-950/40 p-2.5 rounded-xl flex items-center gap-2.5 transition w-full">
                            <input type="checkbox" id="chkAadhaarReady" checked class="w-4 h-4 accent-emerald-500 rounded">
                            <div class="text-[11px] text-gray-300 leading-tight">
                                <span class="font-bold text-white flex items-center gap-1">
                                    <i data-lucide="shield-check" class="w-3.5 h-3.5 text-emerald-400"></i> आधार कार्ड तैयार है (Biometric eKYC)
                                </span>
                                <span class="text-gray-400 text-[10px]">सिम एक्टिवेशन के लिए ओरिजिनल आधार व फिंगरप्रिंट की जरूरत होगी।</span>
                            </div>
                        </label>
                    </div>
                </div>

                <!-- DELIVERY PREFERENCE -->
                <div class="pt-2">
                    <label class="block text-xs font-bold text-gray-300 mb-2">
                        सिम डिलीवरी का तरीका चुनें:
                    </label>
                    <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-3">
                        <label class="cursor-pointer border border-gray-700 bg-gray-950/80 p-3 rounded-xl flex items-center gap-3 hover:border-yellow-400 has-[:checked]:border-yellow-400 has-[:checked]:bg-yellow-400/10 transition">
                            <input type="radio" name="deliveryMethod" value="Free Doorstep Delivery" checked class="accent-yellow-400">
                            <div>
                                <div class="text-xs font-bold text-white flex items-center gap-1">
                                    <span>🛵 घर पर डिलीवरी</span>
                                </div>
                                <span class="text-[10px] text-emerald-400">100% Free & Quick</span>
                            </div>
                        </label>

                        <label class="cursor-pointer border border-gray-700 bg-gray-950/80 p-3 rounded-xl flex items-center gap-3 hover:border-yellow-400 has-[:checked]:border-yellow-400 has-[:checked]:bg-yellow-400/10 transition">
                            <input type="radio" name="deliveryMethod" value="Digital eSIM" class="accent-yellow-400">
                            <div>
                                <div class="text-xs font-bold text-white flex items-center gap-1">
                                    <span>⚡ Digital eSIM</span>
                                </div>
                                <span class="text-[10px] text-blue-400">Instant on Email/WhatsApp</span>
                            </div>
                        </label>

                        <label class="cursor-pointer border border-gray-700 bg-gray-950/80 p-3 rounded-xl flex items-center gap-3 hover:border-yellow-400 has-[:checked]:border-yellow-400 has-[:checked]:bg-yellow-400/10 transition">
                            <input type="radio" name="deliveryMethod" value="Store Pickup" class="accent-yellow-400">
                            <div>
                                <div class="text-xs font-bold text-white flex items-center gap-1">
                                    <span>🏪 नजदीकी दुकान</span>
                                </div>
                                <span class="text-[10px] text-gray-400">Visit Store</span>
                            </div>
                        </label>
                    </div>
                </div>

                <!-- UPC STATUS ACCORDION -->
                <div class="p-3 bg-gray-950 border border-gray-800 rounded-xl">
                    <div class="flex items-center justify-between cursor-pointer" onclick="toggleUpcBox()">
                        <div class="flex items-center gap-2">
                            <i data-lucide="help-circle" class="w-4 h-4 text-yellow-400"></i>
                            <span class="text-xs font-bold text-white">क्या आपके पास 1900 का MNP पोर्टिंग कोड (UPC) है?</span>
                        </div>
                        <span class="text-xs text-yellow-400 font-bold" id="upcToggleBtn">[+] कोड डालें</span>
                    </div>
                    <div id="upcInputBox" class="hidden mt-3 pt-3 border-t border-gray-800">
                        <label class="block text-[11px] text-gray-400 mb-1">
                            अगर आपने 1900 पर PORT SMS भेजा है, तो 8-अंकों का UPC कोड यहाँ लिखें (वैकल्पिक):
                        </label>
                        <input type="text" id="inputUpcCode" placeholder="उदा. AB123456" class="w-full px-3 py-2 rounded-lg bg-gray-900 border border-gray-700 text-white text-xs uppercase font-mono tracking-widest outline-none focus:border-yellow-400">
                        <p class="text-[10px] text-gray-500 mt-1">
                            यदि कोड नहीं है, तो कोई बात नहीं - हमारे एग्जीक्यूटिव आपको फ्री में जनरेट करवा देंगे।
                        </p>
                    </div>
                </div>

                <!-- SUBMIT BUTTON -->
                <div class="pt-4 flex flex-col-reverse sm:flex-row items-center justify-between gap-4">
                    <button type="button" onclick="goToStep(2)" class="w-full sm:w-auto px-5 py-3 rounded-xl font-bold text-sm bg-gray-800 hover:bg-gray-700 text-gray-300 flex items-center justify-center gap-2 transition">
                        <i data-lucide="arrow-left" class="w-4 h-4"></i>
                        <span>वापस जाएं (Back)</span>
                    </button>

                    <button type="submit" id="btnSubmitForm" class="w-full sm:w-auto px-8 py-4 rounded-xl font-black text-base bg-gradient-to-r from-yellow-400 via-amber-500 to-yellow-500 hover:from-yellow-300 hover:to-amber-400 text-black flex items-center justify-center gap-2 shadow-neon-gold hover:scale-102 transition duration-200 cursor-pointer">
                        <span>डिटेल्स शेयर करें और सिम पोर्ट बुक करें</span>
                        <i data-lucide="send" class="w-4 h-4"></i>
                    </button>
                </div>
            </form>
        </div>

        <!-- ============================================================= -->
        <!-- STEP 4: SUCCESS CONFIRMATION SCREEN (सफलतापूर्वक सबमिट) -->
        <!-- ============================================================= -->
        <div id="step4Panel" class="step-panel hidden bg-gray-900/95 border-2 border-emerald-500/50 rounded-3xl p-5 sm:p-8 backdrop-blur-2xl shadow-2xl text-center space-y-6">
            
            <!-- Confetti & Success Banner -->
            <div class="space-y-3">
                <div class="w-16 h-16 sm:w-20 sm:h-20 mx-auto rounded-full bg-emerald-500/20 border-2 border-emerald-400 flex items-center justify-center text-emerald-400 shadow-lg shadow-emerald-500/30 animate-bounce">
                    <i data-lucide="check-check" class="w-9 h-9 sm:w-11 sm:h-11 text-emerald-400"></i>
                </div>

                <div class="inline-flex items-center gap-2 bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 text-xs font-black px-3.5 py-1 rounded-full uppercase tracking-wider">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span> अनुरोध दर्ज हो गया • 100% Free WhatsApp Send Ready
                </div>

                <h2 class="text-2xl sm:text-3xl md:text-4xl font-black text-white">
                    शानदार! आपकी सिम पोर्टिंग रिक्वेस्ट तैयार है 🎉
                </h2>
                <p class="text-xs sm:text-sm text-gray-300 max-w-lg mx-auto">
                    नीचे आपका ऑफिशियल <strong class="text-yellow-400">VIP पोर्टिंग पास</strong> व <strong class="text-emerald-400">व्हाट्सएप मैसेज</strong> तैयार है। 1-क्लिक करके एजेंट को सेंड करें और 15-30 मिनट में घर बैठे सिम पाएं!
                </p>
            </div>

            <!-- VIP DIGITAL MNP BOARDING PASS / TICKET -->
            <div class="max-w-xl mx-auto bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950 border-2 border-yellow-500/50 rounded-3xl p-5 sm:p-6 text-left space-y-4 text-xs shadow-2xl relative overflow-hidden">
                <!-- Glowing accent line -->
                <div class="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-yellow-400 via-emerald-400 to-blue-500"></div>

                <!-- Ticket Header -->
                <div class="flex items-center justify-between pb-3 border-b border-gray-800">
                    <div>
                        <span class="text-[10px] uppercase font-black tracking-widest text-yellow-400">OFFICIAL MNP BOARDING PASS</span>
                        <div id="resBookingId" class="font-mono font-black text-white text-base tracking-wider mt-0.5">MNP-XXXXXX</div>
                    </div>
                    <div class="text-right">
                        <span class="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">Status</span>
                        <div class="text-emerald-400 font-extrabold flex items-center gap-1.5 justify-end mt-0.5">
                            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> Verified Lead
                        </div>
                    </div>
                </div>

                <!-- Route Banner -->
                <div class="bg-gray-950 border border-gray-800 p-3 rounded-2xl flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <span class="text-gray-400 text-[11px]">Old SIM:</span>
                        <span id="resOldOpName" class="font-black text-white text-sm bg-gray-800 px-2.5 py-1 rounded-lg">Jio</span>
                    </div>
                    <div class="flex flex-col items-center">
                        <span class="text-[10px] text-yellow-400 font-bold uppercase tracking-wider">Switching To</span>
                        <i data-lucide="arrow-right" class="w-5 h-5 text-yellow-400 animate-pulse"></i>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-gray-400 text-[11px]">New 5G:</span>
                        <span id="resNewOpName" class="font-black text-emerald-400 text-sm bg-emerald-950/80 border border-emerald-500/40 px-2.5 py-1 rounded-lg">Airtel 5G</span>
                    </div>
                </div>

                <!-- Customer Details Grid -->
                <div class="grid grid-cols-2 gap-3 pt-1 text-gray-300">
                    <div class="p-2.5 bg-gray-900/60 rounded-xl border border-gray-800">
                        <span class="text-gray-400 block text-[10px] uppercase font-bold">👤 ग्राहक का नाम</span>
                        <strong id="resCustomerName" class="text-white text-sm font-bold block mt-0.5">राहुल शर्मा</strong>
                    </div>
                    <div class="p-2.5 bg-gray-900/60 rounded-xl border border-gray-800">
                        <span class="text-gray-400 block text-[10px] uppercase font-bold">📱 पोर्ट करने वाला नंबर</span>
                        <strong id="resPhoneNumber" class="text-emerald-400 font-mono text-sm font-bold block mt-0.5">+91 98765 43210</strong>
                    </div>
                    <div class="p-2.5 bg-gray-900/60 rounded-xl border border-gray-800">
                        <span class="text-gray-400 block text-[10px] uppercase font-bold">🛵 डिलीवरी मोड</span>
                        <span id="resDeliveryType" class="text-yellow-300 font-bold block mt-0.5">Free Doorstep Delivery</span>
                    </div>
                    <div class="p-2.5 bg-gray-900/60 rounded-xl border border-gray-800">
                        <span class="text-gray-400 block text-[10px] uppercase font-bold">⏰ पसंदीदा समय</span>
                        <span id="resPreferredTime" class="text-white font-bold block mt-0.5">⚡ ASAP (15-30 मिनट में)</span>
                    </div>
                </div>

                <!-- Live Address & GPS Badge -->
                <div class="p-3 bg-gray-900/60 rounded-xl border border-gray-800">
                    <span class="text-gray-400 block text-[10px] uppercase font-bold mb-1">🏠 डिलीवरी का पूरा पता (Verified Address)</span>
                    <p id="resFullAddress" class="text-gray-100 text-xs font-semibold leading-relaxed"></p>
                    <div id="resGpsWrap" class="hidden mt-2.5">
                        <a id="resGpsMapLink" href="#" target="_blank" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600/30 hover:bg-blue-600/50 text-blue-300 border border-blue-500/50 font-bold text-[11px] transition">
                            <i data-lucide="map-pin" class="w-3.5 h-3.5 text-blue-400"></i>
                            <span>गूगल मैप्स पर सटीक डिलीवरी लोकेशन देखें ↗</span>
                        </a>
                    </div>
                </div>

                <!-- Barcode Simulation Mockup -->
                <div class="pt-3 border-t border-dashed border-gray-800 flex items-center justify-between">
                    <div class="flex items-center gap-1 opacity-70">
                        <span class="w-1 h-6 bg-white inline-block"></span>
                        <span class="w-2 h-6 bg-white inline-block"></span>
                        <span class="w-0.5 h-6 bg-white inline-block"></span>
                        <span class="w-1.5 h-6 bg-white inline-block"></span>
                        <span class="w-0.5 h-6 bg-white inline-block"></span>
                        <span class="w-2 h-6 bg-white inline-block"></span>
                        <span class="w-1 h-6 bg-white inline-block"></span>
                        <span class="w-2.5 h-6 bg-white inline-block"></span>
                        <span class="w-1 h-6 bg-white inline-block"></span>
                    </div>
                    <span class="text-[10px] font-mono text-gray-500">SIM MNP GROUP • 2026 OFFICIAL</span>
                </div>
            </div> <!-- Closes VIP DIGITAL MNP BOARDING PASS -->

            <!-- WHATSAPP MESSAGE LIVE PREVIEW CHAT BUBBLE (CRITICAL FEATURE) -->
            <div class="max-w-xl mx-auto rounded-3xl bg-gradient-to-b from-gray-950 to-gray-900 border-2 border-emerald-500/40 p-4 sm:p-5 text-left shadow-2xl">
                <div class="flex items-center justify-between pb-3 mb-3 border-b border-gray-800">
                    <div class="flex items-center gap-2">
                        <div class="w-8 h-8 rounded-full bg-[#25D366]/20 border border-[#25D366]/40 flex items-center justify-center text-[#25D366]">
                            <i data-lucide="message-circle" class="w-5 h-5"></i>
                        </div>
                        <div>
                            <h4 class="text-xs sm:text-sm font-black text-white flex items-center gap-1.5">
                                व्हाट्सएप मैसेज प्रीव्यू (WhatsApp Live Message)
                            </h4>
                            <span class="text-[10px] text-emerald-400 font-semibold">100% Free • Direct to SIM Porter (+91 8115361348)</span>
                        </div>
                    </div>
                    <button type="button" onclick="copyLeadDetails()" class="px-2.5 py-1 rounded-lg bg-gray-800 hover:bg-gray-700 text-yellow-400 text-[11px] font-bold border border-gray-700 transition flex items-center gap-1 cursor-pointer">
                        <i data-lucide="copy" class="w-3 h-3"></i>
                        <span>Copy</span>
                    </button>
                </div>

                <!-- Styled WhatsApp Message Card -->
                <div class="relative bg-[#0d1418] border border-emerald-500/20 rounded-2xl p-3 sm:p-4 text-xs font-mono leading-relaxed text-gray-100 shadow-inner">
                    <pre id="resWaPreviewText" class="font-sans whitespace-pre-wrap select-all text-xs leading-relaxed text-gray-100 max-h-72 overflow-y-auto pr-1">लोड हो रहा है...</pre>
                </div>
                <p class="text-[10px] text-gray-400 mt-2 text-center">
                    💡 <b>नोट:</b> नीचे दिए गए हरे बटन पर क्लिक करते ही यह मैसेज सीधे सिम पोर्टर के व्हाट्सएप पर ओपन हो जाएगा।
                </p>
            </div>

            <!-- ACTION BUTTONS: WHATSAPP, COPY, CALL, RESET -->
            <div class="max-w-xl mx-auto flex flex-col sm:flex-row items-stretch justify-center gap-3 pt-2">
                <!-- 1. WhatsApp Button -->
                <a id="btnShareWhatsApp" href="#" target="_blank" class="flex-1 px-6 py-4 rounded-2xl font-black text-sm bg-gradient-to-r from-emerald-500 via-green-500 to-emerald-600 hover:from-emerald-400 hover:to-green-400 text-white flex items-center justify-center gap-2.5 shadow-xl shadow-emerald-950 hover:scale-102 transition duration-200 cursor-pointer border border-emerald-400/40">
                    <i data-lucide="message-circle" class="w-5 h-5 text-white animate-bounce"></i>
                    <span>व्हाट्सएप पर तुरंत भेजें (100% Free) 🚀</span>
                </a>

                <!-- 2. Call Porter Button -->
                <a id="btnCallAgent" href="tel:+918115361348" class="px-5 py-3.5 rounded-2xl font-bold text-xs bg-blue-600/30 hover:bg-blue-600/50 text-blue-300 border border-blue-500/40 flex items-center justify-center gap-2 transition cursor-pointer">
                    <i data-lucide="phone-call" class="w-4 h-4 text-blue-400"></i>
                    <span>कॉल करें</span>
                </a>

                <!-- 3. Copy Button -->
                <button type="button" id="btnCopySummary" onclick="copyLeadDetails()" class="px-5 py-3.5 rounded-2xl font-bold text-xs bg-gray-800 hover:bg-gray-700 text-yellow-400 border border-yellow-500/30 flex items-center justify-center gap-2 transition cursor-pointer">
                    <i data-lucide="copy" class="w-4 h-4"></i>
                    <span>कॉपी करें</span>
                </button>

                <!-- 4. Reset Button -->
                <button onclick="resetPortal()" class="px-4 py-3.5 rounded-2xl font-bold text-xs bg-gray-900 hover:bg-gray-800 text-gray-400 border border-gray-800 flex items-center justify-center gap-1.5 transition cursor-pointer">
                    <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i>
                    <span>नया सिम</span>
                </button>
            </div>

            <!-- MNP QUICK SMS INFO BOX -->
            <div class="max-w-xl mx-auto text-left bg-blue-950/30 border border-blue-900/40 rounded-2xl p-4 mt-4">
                <div class="flex items-start gap-3">
                    <div class="p-2 rounded-lg bg-blue-500/20 text-blue-400 shrink-0">
                        <i data-lucide="info" class="w-4 h-4"></i>
                    </div>
                    <div>
                        <h4 class="text-xs font-bold text-white">पोर्टिंग कोड (UPC) कैसे प्राप्त करें?</h4>
                        <p class="text-[11px] text-gray-300 mt-1 leading-relaxed">
                            अपने फोन के मैसेज में जाएं और टाइप करें: <code class="bg-black/60 px-1.5 py-0.5 rounded text-yellow-300 font-mono font-bold">PORT &lt;10 अंकों का नंबर&gt;</code> और इसे <code class="bg-black/60 px-1.5 py-0.5 rounded text-emerald-400 font-mono font-bold">1900</code> पर SMS कर दें। वापस में आपको 8 अंकों का UPC कोड मिलेगा। अगर न मिले, तो डिलीवरी एजेंट आपकी पूरी मदद करेगा।
                        </p>
                    </div>
                </div>
            </div>

        </div>

    </main>

    <!-- ADMIN / LEADS MODAL -->
    <div id="leadsModal" class="hidden fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-gray-900 border border-gray-800 rounded-3xl max-w-2xl w-full max-h-[85vh] flex flex-col overflow-hidden shadow-2xl">
            <div class="p-4 sm:p-5 border-b border-gray-800 flex items-center justify-between bg-gray-950">
                <div class="flex items-center gap-2">
                    <i data-lucide="database" class="w-5 h-5 text-yellow-400"></i>
                    <h3 class="font-black text-white text-base">पोर्टिंग अनुरोध रिकॉर्ड्स (Live Submitted Leads)</h3>
                </div>
                <button onclick="toggleLeadsModal()" class="text-gray-400 hover:text-white p-1 rounded-lg">
                    <i data-lucide="x" class="w-5 h-5"></i>
                </button>
            </div>
            
            <div id="leadsContainer" class="p-4 sm:p-6 overflow-y-auto flex-1 space-y-3">
                <div class="text-center text-gray-500 py-8">लोड हो रहा है...</div>
            </div>

            <div class="p-4 border-t border-gray-800 bg-gray-950 flex items-center justify-between text-xs text-gray-400">
                <span>Stored in <code class="text-yellow-400">leads.json</code></span>
                <button onclick="refreshLeads()" class="text-yellow-400 hover:underline flex items-center gap-1">
                    <i data-lucide="refresh-cw" class="w-3 h-3"></i> Refresh Data
                </button>
            </div>
    <!-- PORTER / OWNER SETTINGS MODAL -->
    <div id="settingsModal" class="hidden fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-gray-900 border border-yellow-500/30 rounded-3xl max-w-lg w-full overflow-hidden shadow-2xl">
            <div class="p-4 sm:p-5 border-b border-gray-800 flex items-center justify-between bg-gray-950">
                <div class="flex items-center gap-2">
                    <i data-lucide="settings" class="w-5 h-5 text-yellow-400"></i>
                    <h3 class="font-black text-white text-base">पोर्टर सेटिंग्स (Porter WhatsApp & Alerts)</h3>
                </div>
                <button onclick="toggleSettingsModal()" class="text-gray-400 hover:text-white p-1 rounded-lg">
                    <i data-lucide="x" class="w-5 h-5"></i>
                </button>
            </div>
            
            <form onsubmit="savePorterSettings(event)" class="p-4 sm:p-6 space-y-4 text-xs">
                <div>
                    <label class="block font-bold text-gray-200 mb-1">
                        पोर्टर का WhatsApp नंबर *
                    </label>
                    <div class="relative">
                        <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-emerald-400 font-bold">
                            +91
                        </div>
                        <input type="tel" id="cfgOwnerWhatsapp" maxlength="10" required placeholder="9876543210" class="w-full pl-12 pr-4 py-2.5 rounded-xl bg-gray-950 border border-gray-700 text-white font-mono font-bold text-sm focus:border-yellow-400 outline-none">
                    </div>
                    <p class="text-[11px] text-gray-400 mt-1">
                        👉 जब भी कोई कस्टमर "व्हाट्सएप पर डिटेल्स शेयर करें" दबाएगा, सीधे इसी नंबर पर उसका फॉर्म मैसेज आएगा (100% Free)।
                    </p>
                </div>

                <div>
                    <label class="block font-bold text-gray-200 mb-1">
                        पोर्टर / दुकान का नाम
                    </label>
                    <input type="text" id="cfgOwnerName" placeholder="SIM Port Center" class="w-full px-3 py-2 rounded-xl bg-gray-950 border border-gray-700 text-white focus:border-yellow-400 outline-none">
                </div>

                <!-- TELEGRAM (OPTIONAL FREE AUTO-ALERTS) -->
                <div class="p-3 bg-gray-950 border border-gray-800 rounded-xl space-y-2">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-white flex items-center gap-1.5">
                            <i data-lucide="send" class="w-3.5 h-3.5 text-blue-400"></i>
                            Telegram Instant Alerts (वैकल्पिक - 100% Free)
                        </span>
                        <span class="text-[10px] text-blue-400 font-semibold bg-blue-950 px-2 py-0.5 rounded">Auto Phone Ring</span>
                    </div>
                    <input type="text" id="cfgTelegramToken" placeholder="Telegram Bot Token (Optional)" class="w-full px-3 py-2 rounded-lg bg-gray-900 border border-gray-700 text-white font-mono text-[11px] focus:border-blue-400 outline-none">
                    <input type="text" id="cfgTelegramChatId" placeholder="Telegram Chat ID (Optional)" class="w-full px-3 py-2 rounded-lg bg-gray-900 border border-gray-700 text-white font-mono text-[11px] focus:border-blue-400 outline-none">
                    <p class="text-[10px] text-gray-500">
                        BotFather से बना बॉट टोकन डालने पर हर लीड आपके फोन पर टेलीग्राम घंटी बजाकर आएगी।
                    </p>
                </div>

                <div class="pt-2 flex items-center justify-between">
                    <span id="cfgSaveStatus" class="text-[11px] text-emerald-400 font-bold hidden">
                        ✅ सेटिंग्स सेव हो गईं!
                    </span>
                    <button type="submit" class="ml-auto px-5 py-2.5 rounded-xl font-bold bg-yellow-400 text-black hover:bg-yellow-300 transition shadow-neon-gold">
                        सेव करें (Save Settings)
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- FOOTER -->
    <footer class="border-t border-gray-900 bg-gray-950 py-6 px-4 text-center text-xs text-gray-500">
        <div class="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
            <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
                <span>SIM MNP Group • 100% Free Doorstep Activation</span>
            </div>
            <p>सही नेटवर्क, सही फैसला | All Operator Trademarks Belong to Respective Companies</p>
        </div>
    </footer>

    <!-- JAVASCRIPT LOGIC -->
    <script>
        // State variables
        let currentOperator = null;
        let targetOperator = null;
        let currentStep = 1;

        const OPERATOR_COLORS = {
            'Jio': { bg: '#0a38d1', text: '#ffffff', label: 'Reliance Jio' },
            'Airtel': { bg: '#ed1b24', text: '#ffffff', label: 'Bharti Airtel' },
            'Vi': { bg: '#c40d2e', text: '#ffffff', label: 'Vodafone Idea' },
            'BSNL': { bg: '#FFD700', text: '#002B49', label: 'BSNL' }
        };

        // Initialize Lucide Icons
        document.addEventListener('DOMContentLoaded', () => {
            lucide.createIcons();
        });

        // 1. SELECT CURRENT OPERATOR
        function selectCurrentOperator(op) {
            currentOperator = op;
            
            // Clear selections
            ['Jio', 'Airtel', 'Vi', 'BSNL'].forEach(name => {
                const card = document.getElementById(`card-current-${name}`);
                if (card) {
                    card.classList.remove('selected', 'border-yellow-400', 'bg-yellow-400/10', 'shadow-neon-gold');
                    card.querySelector('.checkmark-indicator').classList.remove('text-yellow-400', 'border-yellow-400');
                    card.querySelector('.checkmark-indicator').classList.add('text-transparent');
                }
            });

            // Mark active
            const activeCard = document.getElementById(`card-current-${op}`);
            if (activeCard) {
                activeCard.classList.add('selected', 'border-yellow-400', 'bg-yellow-400/10', 'shadow-neon-gold');
                const check = activeCard.querySelector('.checkmark-indicator');
                check.classList.remove('text-transparent');
                check.classList.add('text-yellow-400', 'border-yellow-400');
            }

            // Update bottom preview
            const badge = document.getElementById('currentSelectedBadge');
            const text = document.getElementById('currentSelectedText');
            const inst = document.getElementById('currentInstructionText');
            badge.classList.remove('hidden');
            badge.classList.add('flex');
            text.textContent = OPERATOR_COLORS[op].label;
            inst.textContent = '✅ ऑपरेटर चुना गया! अब "अगला" बटन दबाएं।';

            // Enable Next Button
            const nextBtn = document.getElementById('btnNextToStep2');
            nextBtn.disabled = false;
            nextBtn.classList.remove('bg-gray-800', 'text-gray-500', 'cursor-not-allowed');
            nextBtn.classList.add('bg-yellow-400', 'text-black', 'hover:bg-yellow-300', 'shadow-neon-gold', 'cursor-pointer');

            // Trigger small haptic celebration
            playSelectionSound();
        }

        function validateAndGoToStep2() {
            if (!currentOperator) return;
            setupStep2();
            goToStep(2);
        }

        // 2. SETUP STEP 2
        function setupStep2() {
            document.getElementById('badgeCurrentSimName').textContent = OPERATOR_COLORS[currentOperator].label;

            // Adjust target cards: disable current operator
            ['Jio', 'Airtel', 'Vi', 'BSNL'].forEach(name => {
                const card = document.getElementById(`card-target-${name}`);
                if (!card) return;

                if (name === currentOperator) {
                    // Disable card
                    card.classList.add('opacity-40', 'pointer-events-none', 'grayscale');
                    card.classList.remove('hover:border-blue-500', 'hover:border-red-500', 'hover:border-yellow-500', 'hover:border-yellow-400');
                } else {
                    card.classList.remove('opacity-40', 'pointer-events-none', 'grayscale');
                }
            });

            // Clear previous target selection if same as current
            if (targetOperator === currentOperator) {
                targetOperator = null;
                const nextBtn = document.getElementById('btnNextToStep3');
                nextBtn.disabled = true;
                nextBtn.classList.add('bg-gray-800', 'text-gray-500', 'cursor-not-allowed');
                nextBtn.classList.remove('bg-emerald-400', 'text-black', 'shadow-neon-green');
            }
        }

        function selectTargetOperator(op) {
            if (op === currentOperator) return;
            targetOperator = op;

            ['Jio', 'Airtel', 'Vi', 'BSNL'].forEach(name => {
                const card = document.getElementById(`card-target-${name}`);
                if (card) {
                    card.classList.remove('border-emerald-400', 'bg-emerald-950/30', 'shadow-neon-green');
                    const chk = card.querySelector('.target-check');
                    if (chk) {
                        chk.classList.remove('text-emerald-400', 'border-emerald-400');
                        chk.classList.add('text-transparent');
                    }
                }
            });

            const activeCard = document.getElementById(`card-target-${op}`);
            if (activeCard) {
                activeCard.classList.add('border-emerald-400', 'bg-emerald-950/30', 'shadow-neon-green');
                const chk = activeCard.querySelector('.target-check');
                if (chk) {
                    chk.classList.remove('text-transparent');
                    chk.classList.add('text-emerald-400', 'border-emerald-400');
                }
            }

            const nextBtn = document.getElementById('btnNextToStep3');
            nextBtn.disabled = false;
            nextBtn.classList.remove('bg-gray-800', 'text-gray-500', 'cursor-not-allowed');
            nextBtn.classList.add('bg-emerald-400', 'text-black', 'hover:bg-emerald-300', 'shadow-neon-green', 'cursor-pointer');

            playSelectionSound();
        }

        function validateAndGoToStep3() {
            if (!targetOperator) return;
            setupStep3();
            goToStep(3);
        }

        // 3. SETUP STEP 3
        function setupStep3() {
            const oldConf = OPERATOR_COLORS[currentOperator];
            const newConf = OPERATOR_COLORS[targetOperator];

            const oldIcon = document.getElementById('summaryOldIcon');
            oldIcon.style.backgroundColor = oldConf.bg;
            oldIcon.style.color = oldConf.text;
            oldIcon.textContent = currentOperator;
            document.getElementById('summaryOldName').textContent = oldConf.label;

            const newIcon = document.getElementById('summaryNewIcon');
            newIcon.style.backgroundColor = newConf.bg;
            newIcon.style.color = newConf.text;
            newIcon.textContent = targetOperator;
            document.getElementById('summaryNewName').textContent = newConf.label;
        }

        function copySameAsPhone() {
            const phone = document.getElementById('inputPhoneNumber').value;
            if (phone) {
                document.getElementById('inputWhatsApp').value = phone;
            }
        }

        function toggleUpcBox() {
            const box = document.getElementById('upcInputBox');
            const btn = document.getElementById('upcToggleBtn');
            if (box.classList.contains('hidden')) {
                box.classList.remove('hidden');
                btn.textContent = '[-] छुपाएं';
            } else {
                box.classList.add('hidden');
                btn.textContent = '[+] कोड डालें';
            }
        }

        // STEP NAVIGATION LOGIC
        function goToStep(step) {
            if (step === 2 && !currentOperator) {
                alert('कृपया पहले अपनी वर्तमान सिम कंपनी चुनें!');
                return;
            }
            if (step === 3 && (!currentOperator || !targetOperator)) {
                alert('कृपया पहले दोनों ऑपरेटर चुनें!');
                return;
            }

            currentStep = step;

            // Panels visibility
            document.getElementById('step1Panel').classList.add('hidden');
            document.getElementById('step2Panel').classList.add('hidden');
            document.getElementById('step3Panel').classList.add('hidden');
            document.getElementById('step4Panel').classList.add('hidden');

            const activePanel = document.getElementById(`step${step}Panel`);
            if (activePanel) {
                activePanel.classList.remove('hidden');
            }

            // On Step 4, hide heroSection so the VIP card is directly visible at the top
            const hero = document.getElementById('heroSection');
            if (hero) {
                if (step === 4) {
                    hero.classList.add('hidden');
                } else {
                    hero.classList.remove('hidden');
                }
            }

            // Progress bar
            const pb = document.getElementById('progressBar');
            if (step === 1) pb.style.width = '0%';
            else if (step === 2) pb.style.width = '33%';
            else if (step === 3) pb.style.width = '66%';
            else if (step === 4) pb.style.width = '100%';

            // Indicators
            for (let i = 1; i <= 4; i++) {
                const dot = document.getElementById(`stepDot${i}`);
                const label = document.getElementById(`stepLabel${i}`);

                if (i <= step) {
                    dot.classList.remove('bg-gray-800', 'text-gray-400', 'border-gray-700');
                    dot.classList.add('bg-yellow-400', 'text-black', 'shadow-neon-gold');
                    label.classList.remove('text-gray-500');
                    label.classList.add('text-yellow-400', 'font-bold');
                } else {
                    dot.classList.add('bg-gray-800', 'text-gray-400', 'border-gray-700');
                    dot.classList.remove('bg-yellow-400', 'text-black', 'shadow-neon-gold');
                    label.classList.add('text-gray-500');
                    label.classList.remove('text-yellow-400', 'font-bold');
                }
            }

            // Smoothly scroll to active panel
            if (activePanel) {
                setTimeout(() => {
                    activePanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 60);
            }
            lucide.createIcons();
        }

        // FORM SUBMISSION (POST TO BACKEND)
        async function handleFormSubmit(e) {
            e.preventDefault();

            const phone = document.getElementById('inputPhoneNumber').value.trim();
            const fullName = document.getElementById('inputFullName').value.trim();
            const whatsapp = document.getElementById('inputWhatsApp').value.trim() || phone;
            
            const house = (document.getElementById('inputHouseStreet')?.value || '').trim();
            const cityPin = (document.getElementById('inputCityPincode')?.value || '').trim();
            const location = [house, cityPin].filter(Boolean).join(', ') || 'पता उपलब्ध नहीं';

            const gpsCoords = document.getElementById('hiddenGpsLocation')?.value?.trim() || '';
            const preferredTime = document.getElementById('selectPreferredTime').value;
            const ekycReady = document.getElementById('chkAadhaarReady').checked;
            const deliveryMethod = document.querySelector('input[name="deliveryMethod"]:checked').value;
            const upcCode = document.getElementById('inputUpcCode')?.value?.trim() || '';

            if (!/^[6-9]\d{9}$/.test(phone)) {
                alert('कृपया एक वैध 10-अंकों का भारतीय मोबाइल नंबर दर्ज करें (शुरुआत 6, 7, 8 या 9 से)।');
                return;
            }

            const btn = document.getElementById('btnSubmitForm');
            const originalContent = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<span class="animate-spin inline-block mr-2">⏳</span> सुरक्षित दर्ज हो रहा है...';

            let gpsMapUrl = gpsCoords ? `https://www.google.com/maps?q=${gpsCoords}` : "";

            try {
                const payload = {
                    current_operator: currentOperator,
                    target_operator: targetOperator,
                    phone_number: phone,
                    full_name: fullName,
                    whatsapp_number: whatsapp,
                    city_pincode: location,
                    gps_location: gpsMapUrl,
                    preferred_time: preferredTime,
                    ekyc_ready: ekycReady,
                    delivery_type: deliveryMethod,
                    upc_status: upcCode ? "Provided" : "Needs Guidance",
                    upc_code: upcCode
                };

                let leadId = `MNP-${Date.now().toString().slice(-6)}`;
                let ownerPhone = "918115361348";

                try {
                    const res = await fetch('/api/port-request', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    const data = await res.json();
                    if (data && data.success) {
                        leadId = data.lead.id;
                        ownerPhone = data.owner_whatsapp || ownerPhone;
                    }
                } catch(fetchErr) {
                    console.log('Backend request note:', fetchErr);
                }

                // Format Ultra-VIP WhatsApp Message with bold, bullets, emojis, and dividers
                let gpsSnippet = gpsMapUrl ? `\n📍 *गूगल मैप्स लाइव लोकेशन:* ${gpsMapUrl}` : "";
                const nowTime = new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });

                const vipMessage = 
`━━━━━━━━━━━━━━━━━━━━━━━
⚡ *SIM MNP GROUP • नया पोर्टिंग अनुरोध* ⚡
━━━━━━━━━━━━━━━━━━━━━━━
🆔 *ऑर्डर रेफरेंस:* #${leadId}
📅 *दिनांक व समय:* ${nowTime}
━━━━━━━━━━━━━━━━━━━━━━━
👤 *ग्राहक विवरण (Customer Details):*
• *नाम:* *${fullName}*
• *पोर्ट करने वाला नंबर:* *+91 ${phone}*
• *व्हाट्सएप नंबर:* +91 ${whatsapp}
• *बायोमेट्रिक eKYC:* ${ekycReady ? '✅ आधार कार्ड व फोन तैयार है' : '⚠️ मार्गदर्शन चाहिए'}

🔄 *पोर्टिंग रूट (Port Route):*
• *मौजूदा सिम (Old):* *${currentOperator}*
• *नया नेटवर्क (New):* *${targetOperator} 5G (Welcome Pack)*

🏠 *सिम डिलीवरी का पता (Doorstep Delivery):*
• *मकान / गली / लैंडमार्क:* *${house || 'उपलब्ध नहीं'}*
• *शहर व पिन कोड:* *${cityPin || 'उपलब्ध नहीं'}*
• *डिलीवरी मोड:* ${deliveryMethod}
• *पसंदीदा डिलीवरी समय:* *${preferredTime}*${gpsSnippet}

🔑 *पोर्टिंग कोड (UPC Code):*
• *UPC स्टेटस:* ${upcCode ? `*${upcCode.toUpperCase()}*` : '⏳ एग्जीक्यूटिव द्वारा 1900 पर जनरेट करवाएं'}
━━━━━━━━━━━━━━━━━━━━━━━
🤝 _"सही नेटवर्क • सही फैसला"_
🚀 _प्रिय एजेंट, कृपया तुरंत ग्राहक से संपर्क कर फ्री सिम डिलीवरी और बायोमेट्रिक एक्टिवेशन पूरा करें!_
━━━━━━━━━━━━━━━━━━━━━━━`;

                // Populate Step 4 elements
                document.getElementById('resBookingId').textContent = leadId;
                document.getElementById('resOldOpName').textContent = currentOperator;
                document.getElementById('resNewOpName').textContent = `${targetOperator} 5G`;
                document.getElementById('resPhoneNumber').textContent = `+91 ${phone}`;
                document.getElementById('resCustomerName').textContent = fullName;
                document.getElementById('resDeliveryType').textContent = deliveryMethod;
                document.getElementById('resPreferredTime').textContent = preferredTime;
                document.getElementById('resFullAddress').textContent = location;

                const gpsWrap = document.getElementById('resGpsWrap');
                if (gpsMapUrl) {
                    gpsWrap.classList.remove('hidden');
                    document.getElementById('resGpsMapLink').href = gpsMapUrl;
                } else {
                    gpsWrap.classList.add('hidden');
                }

                // CRITICAL: Populate WhatsApp Message Live Preview Text
                const waPreviewEl = document.getElementById('resWaPreviewText');
                if (waPreviewEl) {
                    waPreviewEl.textContent = vipMessage;
                }

                // Setup WhatsApp Share Link
                const waUrl = `https://wa.me/${ownerPhone}?text=${encodeURIComponent(vipMessage)}`;
                document.getElementById('btnShareWhatsApp').href = waUrl;

                // Setup Call Agent Link
                const callAgent = document.getElementById('btnCallAgent');
                if (callAgent) {
                    callAgent.href = `tel:+${ownerPhone}`;
                }

                window.currentLeadFormattedText = vipMessage;

                // Fire celebratory confetti!
                fireConfetti();

                // Smoothly switch to Step 4
                goToStep(4);

            } catch (err) {
                console.error(err);
                alert('त्रुटि हुई। कृपया पुनः प्रयास करें।');
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalContent;
            }
        }

        // CONFETTI CELEBRATION
        function fireConfetti() {
            confetti({
                particleCount: 100,
                spread: 70,
                origin: { y: 0.6 },
                colors: ['#FFD700', '#0a38d1', '#ed1b24', '#10B981']
            });
            setTimeout(() => {
                confetti({
                    particleCount: 50,
                    angle: 60,
                    spread: 55,
                    origin: { x: 0 }
                });
                confetti({
                    particleCount: 50,
                    angle: 120,
                    spread: 55,
                    origin: { x: 1 }
                });
            }, 250);
        }

        // RESET PORTAL
        function resetPortal() {
            currentOperator = null;
            targetOperator = null;
            document.getElementById('portForm').reset();
            document.getElementById('currentSelectedBadge').classList.add('hidden');
            goToStep(1);
        }

        // AUDIO EFFECT
        function playSelectionSound() {
            try {
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
                osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.1); // A5
                gain.gain.setValueAtTime(0.08, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.12);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start();
                osc.stop(ctx.currentTime + 0.13);
            } catch (e) {}
        }

        // LEADS MODAL
        async function toggleLeadsModal() {
            const modal = document.getElementById('leadsModal');
            if (modal.classList.contains('hidden')) {
                modal.classList.remove('hidden');
                await refreshLeads();
            } else {
                modal.classList.add('hidden');
            }
        }

        // REAL-TIME GPS AUTO-DETECTION & REVERSE GEOCODING
        async function detectLiveLocation() {
            const btnText = document.getElementById('gpsBtnText');
            const spinner = document.getElementById('gpsSpinner');
            const badge = document.getElementById('gpsStatusBadge');
            const statusMsg = document.getElementById('gpsStatusMessage');
            const mapLink = document.getElementById('gpsMapLink');
            const hiddenGps = document.getElementById('hiddenGpsLocation');
            const houseInput = document.getElementById('inputHouseStreet');
            const cityPinInput = document.getElementById('inputCityPincode');

            if (!navigator.geolocation) {
                alert('आपके ब्राउज़र में GPS / Geolocation सपोर्ट नहीं है। कृपया हाथ से पता लिखें।');
                return;
            }

            spinner.classList.remove('hidden');
            btnText.textContent = 'लोकेशन खोजी जा रही है...';

            navigator.geolocation.getCurrentPosition(
                async (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    const accuracy = Math.round(position.coords.accuracy || 10);
                    
                    const gpsStr = `${lat.toFixed(6)},${lon.toFixed(6)}`;
                    if (hiddenGps) hiddenGps.value = gpsStr;
                    if (mapLink) mapLink.href = `https://www.google.com/maps?q=${lat},${lon}`;
                    if (badge) badge.classList.remove('hidden');

                    let detectedCityStatePin = '';
                    let detectedLocality = '';

                    // 1. Try BigDataCloud reverse geocoding
                    try {
                        const bdcRes = await fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=en`);
                        if (bdcRes.ok) {
                            const bdc = await bdcRes.json();
                            const locality = bdc.locality || bdc.city || '';
                            const district = bdc.principalSubdivision || '';
                            const postcode = bdc.postcode || '';
                            detectedLocality = locality || district;
                            if (locality || district || postcode) {
                                const parts = [locality, district, postcode ? `पिन: ${postcode}` : ''].filter(Boolean);
                                detectedCityStatePin = parts.join(', ');
                            }
                        }
                    } catch (e) {
                        console.log('BigDataCloud error, trying Nominatim', e);
                    }

                    // 2. Fallback to Nominatim
                    if (!detectedCityStatePin) {
                        try {
                            const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=16&addressdetails=1`, {
                                headers: { 'Accept-Language': 'hi,en' }
                            });
                            if (response.ok) {
                                const data = await response.json();
                                if (data && data.address) {
                                    const a = data.address;
                                    const roadArea = a.neighbourhood || a.suburb || a.road || a.residential || '';
                                    const city = a.city || a.town || a.village || a.county || a.state_district || '';
                                    const state = a.state || '';
                                    const pin = a.postcode || '';
                                    detectedLocality = roadArea || city;
                                    const parts = [roadArea, city, state, pin ? `पिन: ${pin}` : ''].filter(Boolean);
                                    detectedCityStatePin = parts.join(', ');
                                }
                            }
                        } catch (err) {
                            console.log('Nominatim error', err);
                        }
                    }

                    if (!detectedCityStatePin) {
                        detectedCityStatePin = `GPS लोकेशन: ${gpsStr}`;
                    }

                    if (cityPinInput) {
                        cityPinInput.value = detectedCityStatePin;
                    }

                    if (accuracy > 500) {
                        if (statusMsg) {
                            statusMsg.innerHTML = `<span class="text-amber-300 font-bold">⚠️ वाई-फाई/नेटवर्क से इलाका डिटेक्ट हुआ (${detectedLocality || 'शहर'})</span><br><span class="text-gray-300 text-[10px]">सटीक डिलीवरी हेतु कृपया ऊपर <b>मकान नंबर व गली</b> अवश्य टाइप करें!</span>`;
                        }
                    } else {
                        if (statusMsg) {
                            statusMsg.innerHTML = `<span class="text-emerald-300 font-bold">🎯 सटीक GPS लोकेशन डिटेक्टेड (${detectedLocality || 'सटीकता ~' + accuracy + 'm'})</span>`;
                        }
                    }

                    spinner.classList.add('hidden');
                    btnText.textContent = '✅ लोकेशन डिटेक्टेड';

                    if (houseInput && !houseInput.value.trim()) {
                        houseInput.focus();
                    }
                },
                (error) => {
                    spinner.classList.add('hidden');
                    btnText.textContent = '📍 Auto-Detect City & GPS';
                    let errMsg = 'लोकेशन डिटेक्ट नहीं हो पाई। ';
                    if (error.code === 1) errMsg += 'कृपया ब्राउज़र में Location Permission Allow करें।';
                    else if (error.code === 2) errMsg += 'GPS सिग्नल नहीं मिला।';
                    else if (error.code === 3) errMsg += 'टाइमआउट हो गया।';
                    alert(errMsg);
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
            );
        }

        // COPY FORMATTED DETAILS
        function copyLeadDetails() {
            if (window.currentLeadFormattedText) {
                navigator.clipboard.writeText(window.currentLeadFormattedText);
                const btn = document.getElementById('btnCopySummary');
                const oldHtml = btn.innerHTML;
                btn.innerHTML = '<span class="text-emerald-400">✅ कॉपी हो गया!</span>';
                setTimeout(() => { btn.innerHTML = oldHtml; }, 2000);
            }
        }

        async function refreshLeads() {
            const container = document.getElementById('leadsContainer');
            container.innerHTML = '<div class="text-center text-gray-400 py-6">लोड हो रहा है...</div>';
            try {
                const res = await fetch('/api/leads');
                const data = await res.json();
                if (data.leads && data.leads.length > 0) {
                    container.innerHTML = data.leads.map(lead => {
                        const mapsBtn = lead.gps_location ? `
                            <a href="${lead.gps_location}" target="_blank" class="px-2.5 py-1.5 rounded-lg bg-indigo-900/60 hover:bg-indigo-800 text-indigo-300 font-bold border border-indigo-500/40 flex items-center gap-1 text-[11px] transition">
                                <span>🗺️ Google Maps</span>
                            </a>
                        ` : '';

                        return `
                        <div class="bg-gray-950 border border-gray-800 hover:border-yellow-500/50 rounded-2xl p-4 text-xs transition space-y-3 shadow-lg">
                            <div class="flex items-center justify-between font-bold">
                                <span class="text-yellow-400 font-mono bg-yellow-400/10 border border-yellow-400/20 px-2.5 py-0.5 rounded">${lead.id}</span>
                                <span class="text-gray-400 text-[11px]">${lead.created_at}</span>
                            </div>
                            <div class="grid grid-cols-2 gap-2 text-gray-300">
                                <div><span class="text-gray-500">ग्राहक:</span> <strong class="text-white text-sm">${lead.full_name}</strong></div>
                                <div><span class="text-gray-500">नंबर:</span> <strong class="text-emerald-400 font-mono text-sm">${lead.phone_number}</strong></div>
                                <div><span class="text-gray-500">पोर्ट रूट:</span> <strong class="text-blue-400 font-bold">${lead.current_operator}</strong> ➔ <strong class="text-green-400 font-bold">${lead.target_operator}</strong></div>
                                <div><span class="text-gray-500">पसंदीदा समय:</span> <span class="text-white font-semibold">${lead.preferred_time || 'ASAP'}</span></div>
                                <div class="col-span-2"><span class="text-gray-500">डिलीवरी पता:</span> <span class="text-gray-200 font-medium">${lead.city_pincode}</span></div>
                                <div><span class="text-gray-500">UPC कोड:</span> <span class="font-mono text-yellow-300 font-bold">${lead.upc_code || 'मदद चाहिए'}</span></div>
                                <div><span class="text-gray-500">eKYC:</span> <span class="text-emerald-300 font-semibold">${lead.ekyc_ready ? '✅ आधार तैयार' : '⚠️ पेंडिंग'}</span></div>
                            </div>
                            
                            <!-- QUICK ACTION BUTTONS FOR SIM PORTER -->
                            <div class="pt-2 border-t border-gray-900 flex flex-wrap items-center justify-between gap-2">
                                <span class="bg-emerald-500/20 text-emerald-300 px-2.5 py-1 rounded font-semibold text-[11px]">${lead.status || 'New Lead'}</span>
                                <div class="flex items-center gap-1.5">
                                    ${mapsBtn}
                                    <a href="tel:${lead.phone_number}" class="px-2.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold flex items-center gap-1 text-[11px] transition">
                                        <span>📞 कॉल</span>
                                    </a>
                                    <a href="https://wa.me/91${lead.whatsapp_number || lead.phone_number}?text=${encodeURIComponent('नमस्ते ' + lead.full_name + ' जी! मैं SIM MNP Group से बोल रहा हूँ, आपके सिम पोर्टिंग (' + lead.current_operator + ' से ' + lead.target_operator + ') के संबंध में। क्या मैं अभी आपकी सिम डिलीवरी रवाना कर दूँ?')}" target="_blank" class="px-2.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold flex items-center gap-1 text-[11px] transition">
                                        <span>💬 WhatsApp</span>
                                    </a>
                                </div>
                            </div>
                        </div>
                    `;}).join('');
                } else {
                    container.innerHTML = '<div class="text-center text-gray-500 py-8">अभी तक कोई पोर्टिंग अनुरोध दर्ज नहीं हुआ है।</div>';
                }
            } catch (err) {
                container.innerHTML = '<div class="text-center text-red-400 py-6">डेटा लोड करने में विफल।</div>';
            }
        }

        async function toggleSettingsModal() {
            const modal = document.getElementById('settingsModal');
            if (modal.classList.contains('hidden')) {
                modal.classList.remove('hidden');
                // Load existing config
                try {
                    const res = await fetch('/api/config');
                    const d = await res.json();
                    if (d.success) {
                        let phone = d.owner_whatsapp || '';
                        if (phone.startsWith('91') && phone.length === 12) phone = phone.substring(2);
                        document.getElementById('cfgOwnerWhatsapp').value = phone;
                        document.getElementById('cfgOwnerName').value = d.owner_name || '';
                    }
                } catch(e) {}
            } else {
                modal.classList.add('hidden');
            }
        }

        async function savePorterSettings(e) {
            e.preventDefault();
            const phone = document.getElementById('cfgOwnerWhatsapp').value.trim();
            const name = document.getElementById('cfgOwnerName').value.trim();
            const token = document.getElementById('cfgTelegramToken').value.trim();
            const chatId = document.getElementById('cfgTelegramChatId').value.trim();

            const status = document.getElementById('cfgSaveStatus');
            try {
                const res = await fetch('/api/config/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        owner_whatsapp: phone,
                        owner_name: name,
                        telegram_bot_token: token,
                        telegram_chat_id: chatId
                    })
                });
                const d = await res.json();
                if (d.success) {
                    status.classList.remove('hidden');
                    setTimeout(() => {
                        status.classList.add('hidden');
                        toggleSettingsModal();
                    }, 1200);
                }
            } catch(e) {
                alert('सेटिंग्स सेव करने में त्रुटि!');
            }
        }
    </script>
</body>
</html>
'''

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print(f"==================================================")
    print(f"🚀 SIM MNP PORTAL RUNNING")
    print(f"👉 OPEN IN BROWSER: http://localhost:{port} or http://127.0.0.1:{port}")
    print(f"==================================================")

    # Automatically launch default browser when running locally / as EXE
    import webbrowser
    import threading
    def open_browser():
        try:
            webbrowser.open(f"http://localhost:{port}")
        except Exception:
            pass

    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(1.2, open_browser).start()

    app.run(host="0.0.0.0", port=port, debug=False)
