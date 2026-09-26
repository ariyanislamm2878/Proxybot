from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_buttons():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ Add Balance", callback_data="admin_add_balance"),
        InlineKeyboardButton("📦 All Orders", callback_data="admin_orders")
    )
    markup.add(
        InlineKeyboardButton("⏳ Pending Orders", callback_data="admin_pending"),
        InlineKeyboardButton("📦 Add Stock", callback_data="admin_add_stock")
    )
    markup.add(
        InlineKeyboardButton("📊 Stock List", callback_data="admin_stock_list"),
        InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
    )
    return markup
