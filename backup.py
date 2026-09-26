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
        except Exception as e:
            print(f"Backup skip {table}: {e}")
            continue
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

    # Postgres er sob table er list (lowercase map)
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public';")
    existing_tables = {t[0].lower(): t[0] for t in cur.fetchall()}

    restored_count = 0
    for sheet_name in wb.sheetnames:
        real_table = existing_tables.get(sheet_name.lower())
        if not real_table:
            print(f"Table not found for sheet {sheet_name}, skipping")
            continue

        sheet = wb[sheet_name]
        rows = list(sheet.values)
        if not rows or len(rows) < 2:
            continue

        headers = [str(h).lower() for h in rows[0]]

        # Table khali koro
        cur.execute(f'TRUNCATE TABLE "{real_table}" RESTART IDENTITY CASCADE;')

        # Insert
        for r in rows[1:]:
            if not any(v is not None and str(v) != "" for v in r):
                continue
            # row length header er soman koro
            r = list(r)[:len(headers)] + [None]*(len(headers)-len(r))
            cols = ", ".join([f'"{c}"' for c in headers])
            ph = ", ".join(["%s"]*len(headers))
            try:
                cur.execute(f'INSERT INTO "{real_table}" ({cols}) VALUES ({ph})', r)
                restored_count += 1
            except Exception as e:
                print(f"Skip row in {real_table}: {e}")
                conn.rollback()
                cur = conn.cursor()
                continue

    conn.commit()
    cur.close()
    conn.close()
    return restored_count

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
            bot.reply_to(message, f"✅ Restore Successful! {count} rows restored to PostgreSQL")
        except Exception as e:
            bot.reply_to(message, f"❌ Restore Failed: {e}")
            print(f"Restore error: {e}")
