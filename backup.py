import os
import psycopg2
from openpyxl import Workbook, load_workbook

DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def create_backup_excel():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public';")
    tables = [r[0] for r in cur.fetchall()]
    wb = Workbook()
    wb.remove(wb.active)
    for table in tables:
        ws = wb.create_sheet(title=table[:30])
        cur.execute(f'SELECT * FROM "{table}";')
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        ws.append(cols)
        for r in rows:
            ws.append(list(r))
    path = "/tmp/ProxyStore_Backup.xlsx"
    wb.save(path)
    cur.close()
    conn.close()
    return open(path, 'rb')

def get_db_file_if_sqlite():
    return None

def restore_from_xlsx(file_path):
    conn = get_conn()
    cur = conn.cursor()
    wb = load_workbook(file_path)
    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        rows = list(sheet.values)
        if not rows or len(rows) < 2: continue
        headers = [str(h).lower() for h in rows[0]]
        cur.execute(f'TRUNCATE TABLE "{sheet_name}" RESTART IDENTITY CASCADE;')
        for r in rows[1:]:
            if not any(r): continue
            cols = ", ".join([f'"{c}"' for c in headers])
            ph = ", ".join(["%s"]*len(headers))
            try:
                cur.execute(f'INSERT INTO "{sheet_name}" ({cols}) VALUES ({ph})', r)
            except: continue
    conn.commit()
    cur.close()
    conn.close()

def register_backup_handlers(bot):
    @bot.message_handler(content_types=['document'])
    def handle_restore(message):
        if message.from_user.id!= ADMIN_ID: return
        if not message.caption or "RESTORE" not in message.caption.upper(): return
        bot.reply_to(message, "⏳ Restoring to PostgreSQL...")
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        tmp_path = "/tmp/restore.xlsx"
        with open(tmp_path, 'wb') as f:
            f.write(downloaded)
        try:
            restore_from_xlsx(tmp_path)
            bot.reply_to(message, "✅ Restore Successful! All balances restored.")
        except Exception as e:
            bot.reply_to(message, f"❌ Restore Failed: {e}")
