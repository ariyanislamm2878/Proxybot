from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import FORCE_JOIN_LINK
import os

def force_join_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 Channel Join Koro", url=FORCE_JOIN_LINK))
    markup.add(InlineKeyboardButton("✅ Verify Join", callback_data="verify_join"))
    return markup

def main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("🛒 Shop", callback_data="shop"), InlineKeyboardButton("👛 Wallet", callback_data="wallet"))
    markup.add(InlineKeyboardButton("📦 My Orders", callback_data="orders"), InlineKeyboardButton("👥 Refer & Earn", callback_data="refer"))
    markup.add(InlineKeyboardButton("💳 Deposit", callback_data="deposit"), InlineKeyboardButton("🆘 Support", callback_data="support"))
    return markup

def shop_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("🌍 Proxy", callback_data="proxy_list"))
    markup.add(InlineKeyboardButton("🖥 Morelogin", callback_data="morelogin_list"))
    markup.add(InlineKeyboardButton("🌐 VPN", callback_data="vpn_list"))
    markup.add(InlineKeyboardButton("📧 Gmail", callback_data="gmail_list"))
    markup.add(InlineKeyboardButton("📮 Outlook", callback_data="outlook_list"))
    markup.add(InlineKeyboardButton("📬 Hotmail", callback_data="hotmail_list"))
    markup.add(InlineKeyboardButton("🎓 Edu Mail", callback_data="edumail_list"))
    markup.add(InlineKeyboardButton("🏠 Home", callback_data="home"))
    return markup

def deposit_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("📱 bKash", callback_data="bkash"), InlineKeyboardButton("📱 Nagad", callback_data="nagad"))
    markup.add(InlineKeyboardButton("🚀 Rocket", callback_data="rocket"), InlineKeyboardButton("💵 USDT", callback_data="usdt"))
    markup.add(InlineKeyboardButton("📤 Submit Payment", callback_data="submit_payment"))
    markup.add(InlineKeyboardButton("🏠 Home", callback_data="home"))
    return markup

def product_menu(category):
    markup = InlineKeyboardMarkup()

    if category == "proxy":
        markup.add(InlineKeyboardButton("Owl Proxy 200MB 12 BDT", callback_data="select_qty|proxy|Owl Proxy 200MB|12"))
        markup.add(InlineKeyboardButton("ABC Proxy SUB 1 GB 250 BDT", callback_data="select_qty|proxy|ABC Proxy SUB 1 GB|250"))
        markup.add(InlineKeyboardButton("Dataimpluse SUB Proxy 1 GB 150 BDT", callback_data="select_qty|proxy|Dataimpluse Proxy SUB 1 GB|150"))
        markup.add(InlineKeyboardButton("Rapid Proxy SUB 1 GB 130 BDT", callback_data="select_qty|proxy|Rapid Proxy SUB 1 GB|130"))
        markup.add(InlineKeyboardButton("Rapid Proxy 200 MB 35 BDT", callback_data="select_qty|proxy|Rapid Proxy 200 MB|35"))
        markup.add(InlineKeyboardButton("Rocket Proxy SUB 1 GB 160 BDT", callback_data="select_qty|proxy|Rocket Proxy SUB 1 GB|160"))
        markup.add(InlineKeyboardButton("711 Proxy SUB 1 GB 115 BDT", callback_data="select_qty|proxy|711 Proxy SUB 1 GB|115"))
        markup.add(InlineKeyboardButton("CLI proxy SUB 1 GB 115 BDT", callback_data="select_qty|proxy|CLI Proxy SUB 1 GB|115"))
        markup.add(InlineKeyboardButton("MASH Proxy SUB 1 GB 130 BDT", callback_data="select_qty|proxy|MASH Proxy SUB 1 GB|130"))
        markup.add(InlineKeyboardButton("9 Proxy SUB 1 GB 130 BDT", callback_data="select_qty|proxy|9 Proxy SUB 1 GB|130"))
        markup.add(InlineKeyboardButton("9 Proxy 200 MB 35 BDT", callback_data="select_qty|proxy|9 Proxy 200 MB|35"))
        markup.add(InlineKeyboardButton("H143 Proxy Data user 100 MB 8 BDT", callback_data="select_qty|proxy|H143 Proxy mobile user 100 MB|8"))
        markup.add(InlineKeyboardButton("H143 Proxy Data user 200 MB 15 BDT", callback_data="select_qty|proxy|H143 Proxy mobile user 200 MB|15"))
        markup.add(InlineKeyboardButton("H143 Proxy Data user 500 MB 30 BDT", callback_data="select_qty|proxy|H143 Proxy mobile user 500 MB|30"))
        markup.add(InlineKeyboardButton("H143 Proxy Data user 1 GB 50 BDT", callback_data="select_qty|proxy|H143 Proxy mobile user 1 GB|50"))
        markup.add(InlineKeyboardButton("NOVA PROXY 200 MB 12 BDT", callback_data="select_qty|proxy|NOVA PROXY 200 MB|12"))
    elif category == "morelogin":
        markup.add(InlineKeyboardButton("Morelogin 100 Minutes 30 BDT", callback_data="select_qty|morelogin|Morelogin 100 Minutes|30"))
    elif category == "vpn":
        markup.add(InlineKeyboardButton("Comet VPN 3 Days 1GB 25 BDT", callback_data="select_qty|vpn|Comet VPN 3 Days 1GB|25"))
        markup.add(InlineKeyboardButton("Nord VPN 7 Days 25 BDT", callback_data="select_qty|vpn|Nord VPN 7 Days|25"))
        markup.add(InlineKeyboardButton("HMA VPN 7 Days 25 BDT", callback_data="select_qty|vpn|HMA VPN 7 Days|25"))
        markup.add(InlineKeyboardButton("Surfshark 7 Days 25 BDT", callback_data="select_qty|vpn|Surfshark 7 Days|25"))
        markup.add(InlineKeyboardButton("Hotspot Shield 7 Days 25 BDT", callback_data="select_qty|vpn|Hotspot Shield 7 Days|25"))
        markup.add(InlineKeyboardButton("Cyber Ghost 7 Days 25 BDT", callback_data="select_qty|vpn|Cyber Ghost 7 Days|25"))
        markup.add(InlineKeyboardButton("Avast 7 Days 25 BDT", callback_data="select_qty|vpn|Avast 7 Days|25"))
        markup.add(InlineKeyboardButton("IP Vanish 7 Days 25 BDT", callback_data="select_qty|vpn|IP Vanish 7 Days|25"))
        markup.add(InlineKeyboardButton("PIA 7 Days 25 BDT", callback_data="select_qty|vpn|PIA 7 Days|25"))
        markup.add(InlineKeyboardButton("Pure 7 Days 25 BDT", callback_data="select_qty|vpn|Pure 7 Days|25"))
        markup.add(InlineKeyboardButton("Potato 7 Days 25 BDT", callback_data="select_qty|vpn|Potato 7 Days|25"))
        markup.add(InlineKeyboardButton("Sky 7 Days 25 BDT", callback_data="select_qty|vpn|Sky 7 Days|25"))
        markup.add(InlineKeyboardButton("Turbo 7 Days 25 BDT", callback_data="select_qty|vpn|Turbo 7 Days|25"))
        markup.add(InlineKeyboardButton("HMA 1 Month 56 BDT", callback_data="select_qty|vpn|HMA 1 Month|56"))
        markup.add(InlineKeyboardButton("Nord 1 Month 150 BDT", callback_data="select_qty|vpn|Nord 1 Month|150"))
        markup.add(InlineKeyboardButton("Proton 1 Month 150 BDT", callback_data="select_qty|vpn|Proton 1 Month|150"))
        markup.add(InlineKeyboardButton("Express 1 Month 75 BDT", callback_data="select_qty|vpn|Express 1 Month|75"))
        markup.add(InlineKeyboardButton("Mysterium 1 Month 1875 BDT", callback_data="select_qty|vpn|Mysterium 1 Month|1875"))
        markup.add(InlineKeyboardButton("MYSTERIUM DARK 1 Month 740 BDT", callback_data="select_qty|vpn|MYSTERIUM DARK 1 Month|740"))
    elif category == "gmail":
        markup.add(InlineKeyboardButton("Gmail.com 40 BDT", callback_data="select_qty|gmail|Gmail.com 40|40"))
    elif category == "outlook":
        markup.add(InlineKeyboardButton("Outlook.com 1 BDT", callback_data="select_qty|outlook|Outlook.com|1"))
        markup.add(InlineKeyboardButton("Outlook.fr 1 BDT", callback_data="select_qty|outlook|Outlook.fr|1"))
        markup.add(InlineKeyboardButton("Outlook.cl 1 BDT", callback_data="select_qty|outlook|Outlook.cl|1"))
        markup.add(InlineKeyboardButton("Outlook.cz 1 BDT", callback_data="select_qty|outlook|Outlook.cz|1"))
        markup.add(InlineKeyboardButton("Outlook.at 1 BDT", callback_data="select_qty|outlook|Outlook.at|1"))
        markup.add(InlineKeyboardButton("Outlook.sa 1 BDT", callback_data="select_qty|outlook|Outlook.sa|1"))
        markup.add(InlineKeyboardButton("Outlook.jp 1 BDT", callback_data="select_qty|outlook|Outlook.jp|1"))
        markup.add(InlineKeyboardButton("Outlook.de 1 BDT", callback_data="select_qty|outlook|Outlook.de|1"))
        markup.add(InlineKeyboardButton("Outlook.in 1 BDT", callback_data="select_qty|outlook|Outlook.in|1"))
        markup.add(InlineKeyboardButton("Outlook.it 1 BDT", callback_data="select_qty|outlook|Outlook.it|1"))
        markup.add(InlineKeyboardButton("Outlook.kr 1 BDT", callback_data="select_qty|outlook|Outlook.kr|1"))
        markup.add(InlineKeyboardButton("Outlook.lv 1 BDT", callback_data="select_qty|outlook|Outlook.lv|1"))
        markup.add(InlineKeyboardButton("Outlook.my 1 BDT", callback_data="select_qty|outlook|Outlook.my|1"))
        markup.add(InlineKeyboardButton("Outlook.pt 1 BDT", callback_data="select_qty|outlook|Outlook.pt|1"))
        markup.add(InlineKeyboardButton("Outlook.ph 1 BDT", callback_data="select_qty|outlook|Outlook.ph|1"))
        markup.add(InlineKeyboardButton("Outlook.ie 1 BDT", callback_data="select_qty|outlook|Outlook.ie|1"))
        markup.add(InlineKeyboardButton("Outlook.sk 1 BDT", callback_data="select_qty|outlook|Outlook.sk|1"))
        markup.add(InlineKeyboardButton("Outlook.dk 1 BDT", callback_data="select_qty|outlook|Outlook.dk|1"))
        markup.add(InlineKeyboardButton("Outlook.es 1 BDT", callback_data="select_qty|outlook|Outlook.es|1"))
        markup.add(InlineKeyboardButton("Outlook.be 1 BDT", callback_data="select_qty|outlook|Outlook.be|1"))
        markup.add(InlineKeyboardButton("Outlook.hu 1 BDT", callback_data="select_qty|outlook|Outlook.hu|1"))
        markup.add(InlineKeyboardButton("Outlook.sg 1 BDT", callback_data="select_qty|outlook|Outlook.sg|1"))
    elif category == "hotmail":
        markup.add(InlineKeyboardButton("Hotmail Fresh 1 BDT", callback_data="select_qty|hotmail|Hotmail Fresh|1"))
    elif category == "edumail":
        markup.add(InlineKeyboardButton("Edu Gmail Live 10 Minute 0.30 BDT", callback_data="select_qty|edumail|Edu Gmail Live 10 Minute|0.30"))
        markup.add(InlineKeyboardButton("Edu Live 12 hour Vietnam name 0.70 BDT", callback_data="select_qty|edumail|Edu Live 12 hour Vietnam name|0.70"))
        markup.add(InlineKeyboardButton("Edu Gmail Live 12-48 Hours 0.80 BDT", callback_data="select_qty|edumail|Edu Gmail Live 12-48 Hours|0.80"))
        markup.add(InlineKeyboardButton("Edu Gmail 3 day Access 2.60 BDT", callback_data="select_qty|edumail|Edu Gmail 3 day Access|2.60"))

    markup.add(InlineKeyboardButton("⬅ Back", callback_data="shop"))
    markup.add(InlineKeyboardButton("🏠 Home", callback_data="home"))
    return markup

def quantity_menu(category, name, price, qty):
    total = float(price) * int(qty)
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(
        InlineKeyboardButton("➖", callback_data=f"qty_minus|{category}|{name}|{price}|{qty}"),
        InlineKeyboardButton(f"{qty} pcs", callback_data="noop"),
        InlineKeyboardButton("➕", callback_data=f"qty_plus|{category}|{name}|{price}|{qty}")
    )
    markup.add(InlineKeyboardButton("✏ Custom Quantity", callback_data=f"custom_qty|{category}|{name}|{price}"))
    markup.add(InlineKeyboardButton(f"🛒 Buy - {total} BDT", callback_data=f"buy|{category}|{name}|{price}|{qty}"))
    markup.add(InlineKeyboardButton("⬅ Back", callback_data=f"{category}_list"))
    markup.add(InlineKeyboardButton("🏠 Home", callback_data="home"))
    return markup
