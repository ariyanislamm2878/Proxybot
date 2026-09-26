from bot import bot
from handler import register_handlers
from backup import create_backup_excel, get_db_file_if_sqlite, register_backup_handlers, restore_from_xlsx
from config import ADMIN_ID
import threading, time, os

register_handlers(bot)
register_backup_handlers(bot) # <-- EITA ADD KORO

@bot.message_handler(commands=["backup"])
def backup_command(message):
    if message.from_user.id!= ADMIN_ID:
        bot.reply_to(message, "❌ Access Denied")
        return
    bot.reply_to(message, "⏳ Backup create hocche...")
    try:
        excel_file = create_backup_excel()
        if excel_file:
            bot.send_document(ADMIN_ID, excel_file, caption=f"FULL BACKUP")
        bot.send_message(ADMIN_ID, "Backup Done!")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Backup error: {e}")

def try_auto_restore():
    try:
        files = [f for f in os.listdir(".") if f.startswith("ProxyStore_Backup") and f.endswith(".xlsx")]
        if not files:
            files = [f for f in os.listdir("/tmp") if f.startswith("ProxyStore_Backup") and f.endswith(".xlsx")]
            files = ["/tmp/"+f for f in os.listdir("/tmp") if f.startswith("ProxyStore_Backup") and f.endswith(".xlsx")]
        if files and os.environ.get("RESTORE", "false").lower() == "true":
            print(f"🔄 Restoring from {files[0]}...")
            restore_from_xlsx(files[0])
            print("✅ Restore complete!")
            bot.send_message(ADMIN_ID, f"✅ Restore Done from {files[0]}")
    except Exception as e:
        print(f"Restore error: {e}")

try_auto_restore()

print("✅ ProxyStore BOT Started with Backup System")
bot.infinity_polling(timeout=30, skip_pending=True)
