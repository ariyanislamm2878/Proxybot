from bot import bot
from handler import register_handlers
from backup import create_backup_excel, get_db_file_if_sqlite
from config import ADMIN_ID
import threading
import time
import os

register_handlers(bot)

@bot.message_handler(commands=["backup"])
def backup_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Access Denied")
        return
    bot.reply_to(message, "⏳ Backup create hocche...")
    try:
        excel_file = create_backup_excel()
        if excel_file:
            bot.send_document(ADMIN_ID, excel_file, caption=f"FULL BACKUP Time: {excel_file.name}")
        db_file = get_db_file_if_sqlite()
        if db_file:
            with open(db_file, 'rb') as f:
                bot.send_document(ADMIN_ID, f, caption="proxystore.db")
        bot.send_message(ADMIN_ID, "Backup Done!")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Backup error: {e}")

# ===== AUTO RESTORE ON START IF BACKUP FILE EXISTS =====
def try_auto_restore():
    try:
        files = [f for f in os.listdir(".") if f.startswith("ProxyStore_Backup") and f.endswith(".xlsx")]
        if files and os.environ.get("RESTORE", "false").lower() == "true":
            print(f"🔄 Restoring from {files[0]}...")
            from restore import restore_backup
            restore_backup(files[0])
            print("✅ Restore complete!")
            # Send confirmation to admin
            bot.send_message(ADMIN_ID, f"✅ Restore Done from {files[0]} - All balances restored!")
    except Exception as e:
        print(f"Restore error: {e}")

# Run restore before bot starts
try_auto_restore()

def auto_backup_loop():
    while True:
        try:
            time.sleep(12 * 60 * 60)
            print("Auto backup running...")
            excel_file = create_backup_excel()
            if excel_file:
                bot.send_document(ADMIN_ID, excel_file, caption=f"AUTO BACKUP 12h - {excel_file.name}")
        except Exception as e:
            print(f"Auto backup error: {e}")
            time.sleep(60)

backup_thread = threading.Thread(target=auto_backup_loop, daemon=True)
backup_thread.start()

print("✅ ProxyStore BOT Started with Backup System")
bot.infinity_polling(timeout=30, skip_pending=True)
