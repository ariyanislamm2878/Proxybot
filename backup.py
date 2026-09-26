import os
from openpyxl import load_workbook
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

def restore_from_xlsx(file_path):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    wb = load_workbook(file_path)
    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        rows = list(sheet.values)
        if not rows or len(rows) < 2:
            continue
        headers = [str(h).lower() for h in rows[0]]
        cur.execute(f'TRUNCATE TABLE "{sheet_name}" RESTART IDENTITY CASCADE;')
        for r in rows[1:]:
            if not any(r):
                continue
            cols = ", ".join([f'"{c}"' for c in headers])
            ph = ", ".join(["%s"]*len(headers))
            try:
                cur.execute(f'INSERT INTO "{sheet_name}" ({cols}) VALUES ({ph})', r)
            except Exception as e:
                print(f"Skip row in {sheet_name}: {e}")
                continue
    conn.commit()
    cur.close()
    conn.close()
    return len(wb.sheetnames)

def register_backup_handlers(bot):
    @bot.message_handler(content_types=['document'])
    def handle_restore(message):
        if message.from_user.id!= ADMIN_ID:
            return
        if not message.caption or "RESTORE" not in message.caption.upper():
            return
        bot.reply_to(message, "⏳ Restoring to PostgreSQL...")
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        tmp_path = "/tmp/restore.xlsx"
        with open(tmp_path, 'wb') as f:
            f.write(downloaded)
        try:
            tables = restore_from_xlsx(tmp_path)
            bot.reply_to(message, f"✅ Restore Successful! {tables} tables restored")
        except Exception as e:
            bot.reply_to(message, f"❌ Restore Failed: {e}")
