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
        if table.startswith("pg_") or table.startswith("sql_"):
            continue
        ws = wb.create_sheet(title=table[:30])
        try:
            cur.execute(f'SELECT * FROM "{table}";')
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            ws.append(cols)
            for r in rows:
                ws.append([str(x) if x is not None else None for x in r])
        except: continue
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

    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public';")
    existing = {t[0].lower(): t[0] for t in cur.fetchall()}

    restored = 0
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.values)
        if not rows or len(rows) < 2:
            continue
        headers = [str(h).strip() for h in rows[0] if h]
        # Original case table name preserve korbo
        table_original = sheet_name  # Users_Balance
        table_lower = sheet_name.lower()  # users_balance

        # 1. Original case e table create
        cols_def = ", ".join([f'"{c.lower()}" TEXT' for c in headers])
        try:
            cur.execute(f'CREATE TABLE IF NOT EXISTS "{table_original}" ({cols_def});')
            conn.commit()
        except Exception as e:
            print(f"Create {table_original} fail: {e}")
            conn.rollback()
            cur = conn.cursor()

        # 2. Lower case e o table create (bot jate 2 vabei pay)
        if table_original != table_lower:
            try:
                cur.execute(f'CREATE TABLE IF NOT EXISTS "{table_lower}" ({cols_def});')
                conn.commit()
                existing[table_lower] = table_lower
            except:
                conn.rollback()
                cur = conn.cursor()

        # Truncate both
        for tbl in [table_original, table_lower]:
            try:
                cur.execute(f'TRUNCATE TABLE "{tbl}" RESTART IDENTITY CASCADE;')
            except:
                try:
                    cur.execute(f'DELETE FROM "{tbl}";')
                except:
                    conn.rollback()
                    cur = conn.cursor()
        conn.commit()

        # Insert into both tables
        for r in rows[1:]:
            if not r or not any(v is not None and str(v) != "" for v in r):
                continue
            r = list(r)[:len(headers)] + [None]*(len(headers)-len(r))
            cols = ", ".join([f'"{c.lower()}"' for c in headers])
            ph = ", ".join(["%s"]*len(headers))
            for tbl in set([table_original, table_lower]):
                try:
                    cur.execute(f'INSERT INTO "{tbl}" ({cols}) VALUES ({ph})', r)
                except Exception as e:
                    print(f"Skip {tbl}: {e}")
                    conn.rollback()
                    cur = conn.cursor()
                    continue
            restored += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Restored {restored} rows total")
    return restored

def register_backup_handlers(bot):
    @bot.message_handler(content_types=['document'])
    def handle_restore(message):
        if message.from_user.id != ADMIN_ID:
            return
        if not message.caption or "RESTORE" not in message.caption.upper():
            return
        bot.reply_to(message, "⏳ Restoring to PostgreSQL...")
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded = bot.download_file(file_info.file_path)
            tmp_path = "/tmp/restore.xlsx"
            with open(tmp_path, 'wb') as f:
                f.write(downloaded)
            count = restore_from_xlsx(tmp_path)
            bot.reply_to(message, f"✅ Restore Successful! {count} rows restored (balance included)")
        except Exception as e:
            bot.reply_to(message, f"❌ Restore Failed: {e}")
            print(f"Restore error: {e}")
