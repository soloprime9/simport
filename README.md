# 🚀 SIM MNP Portal - Mobile Number Portability Web Portal

> **"सही नेटवर्क, सही फैसला"** — An ultra-modern, high-converting 4-step SIM Porting Web Application with circular operator branding, real-time GPS location detection, digital boarding pass, and **100% FREE direct WhatsApp dispatch to the SIM porting agent**.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-emerald.svg)](https://flask.palletsprojects.com/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v3.4-38bdf8.svg)](https://tailwindcss.com/)
[![Vercel](https://img.shields.io/badge/Deploy-Vercel-black.svg)](https://vercel.com/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20|%20Linux%20|%20macOS-lightgrey.svg)](#)

---

## ✨ Features

- 🎯 **4-Step Wizard Flow:**
  - **Step 1:** Select Current Operator (Jio, Airtel, Vi, BSNL) in circular logos.
  - **Step 2:** Select Target Operator to Switch to (Auto-disables current operator to prevent duplicate selection).
  - **Step 3:** Customer Details & Address:
    - Dedicated House / Street / Landmark input for exact doorstep delivery.
    - 📍 **Auto-Detect GPS City & Pincode** button with automatic reverse geocoding (OpenStreetMap / BigDataCloud) and laptop Wi-Fi fallback guidance.
    - Delivery time slot selection (ASAP, Morning, Afternoon, Evening).
    - Biometric Aadhaar eKYC readiness check.
    - Optional 1900 UPC code input.
  - **Step 4:** **Official VIP MNP Boarding Pass & WhatsApp Dispatch:**
    - Live Order Reference ID (`#MNP-XXXXXX`).
    - Verified Customer details and Google Maps live pinpoint link.
    - **WhatsApp Live Message Preview Box** styled like a real WhatsApp chat bubble.
    - **1-Click Free WhatsApp Button:** Dispatches the richly formatted order directly to the SIM Porter's WhatsApp without needing any paid WhatsApp Business API.
    - Direct Agent Call (`tel:+918115361348`) and One-Click Copy details buttons.

- ⚙️ **Admin & Porter Controls:**
  - Secret Leads Dashboard (`Check Requests` button) to view all submitted porting orders.
  - Settings Modal (`⚙️ Settings` button) to update Porter WhatsApp Number and Name on the fly.
  - Optional Free Telegram Bot Push Notifications for instant sound alerts on the porter's phone.

---

## 📁 Project Structure

```
simport/
├── app.py                 # Core Flask backend & embedded UI
├── index.html             # Standalone static single-page application
├── build_exe.py           # One-click PyInstaller Windows .exe compiler
├── portal_config.json     # Porter WhatsApp number and settings
├── leads.json             # Stored leads database
├── requirements.txt       # Python dependencies
├── vercel.json            # Vercel serverless configuration
├── .gitignore             # Clean Git ignore rules
├── api/
│   └── index.py           # Vercel Serverless entrypoint
└── static/
    └── brand_logo.jpg     # Circular brand logo
```

---

## 💻 Local Quickstart

### 1. Clone repository
```bash
git clone https://github.com/soloprime9/simport.git
cd simport
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run application
```bash
python app.py
```
Open **[http://localhost:5050](http://localhost:5050)** in your browser!

---

## ⚡ Deploy to Vercel (100% Free Hosting)

This repository is pre-configured with `vercel.json` and `api/index.py` for Vercel Python Serverless deployment.

### Method 1: Via Vercel Web Dashboard (Recommended)
1. Go to [vercel.com](https://vercel.com) and log in with your GitHub account.
2. Click **"Add New..."** ➔ **"Project"**.
3. Select your repository: **`soloprime9/simport`**.
4. Leave settings as default (Framework Preset: **Other**).
5. Click **"Deploy"**.
6. Within 60 seconds, your site will be live with a free `.vercel.app` URL!

### Method 2: Via Vercel CLI
```bash
npm install -g vercel
vercel
```

---

## 📦 Build Windows Standalone Executable (.EXE)

To create a single `.exe` file that runs on any Windows PC without requiring Python or terminal commands:

```bash
python build_exe.py
```

The compiled file will be generated at:
`dist/SIM_MNP_Portal.exe`

### How the EXE Works:
- Double-clicking `SIM_MNP_Portal.exe` starts the local server and **automatically opens your default web browser** to `http://localhost:5050`.
- All assets, logos, and configs are packaged inside.
- Saved orders and configurations persist in the same folder as the `.exe`.

---

## ⚙️ Configuration (`portal_config.json`)

To change the SIM Porter's WhatsApp number or business name, update `portal_config.json` or use the in-app Settings modal:

```json
{
  "owner_whatsapp": "918115361348",
  "owner_name": "Sandeep MNP Agent",
  "telegram_bot_token": "",
  "telegram_chat_id": "",
  "admin_pin": "1234"
}
```

---

## 📄 License
This project is open-source under the MIT License.
