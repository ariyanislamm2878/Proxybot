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
    restored = 0
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.values)
        if not rows or len(rows) < 2: continue
        headers = [str(h).strip() for h in rows[0] if h]
        table_original = sheet_name
        table_lower = sheet_name.lower()
        cols_def = ", ".join([f'"{c.lower()}" TEXT' for c in headers])
        for tbl in set([table_original, table_lower]):
            try:
                cur.execute(f'CREATE TABLE IF NOT EXISTS "{tbl}" ({cols_def});')
                cur.execute(f'TRUNCATE TABLE "{tbl}" RESTART IDENTITY CASCADE;')
            except:
                conn.rollback()
                cur = conn.cursor()
                try:
                    cur.execute(f'CREATE TABLE IF NOT EXISTS "{tbl}" ({cols_def});')
                    cur.execute(f'DELETE FROM "{tbl}";')
                except:
                    continue
        conn.commit()
        for r in rows[1:]:
            if not r or not any(v is not None and str(v) != "" for v in r): continue
            r = list(r)[:len(headers)] + [None]*(len(headers)-len(r))
            cols = ", ".join([f'"{c.lower()}"' for c in headers])
            ph = ", ".join(["%s"]*len(headers))
            for tbl in set([table_original, table_lower]):
                try:
                    cur.execute(f'INSERT INTO "{tbl}" ({cols}) VALUES ({ph})', r)
                except:
                    conn.rollback()
                    cur = conn.cursor()
            restored += 1
    conn.commit()
    cur.close()
    conn.close()
    return restored

def fix_balance_sync():
    conn = get_conn()
    cur = conn.cursor()
    # Sync Users_Balance -> users, users_balance
    try:
        cur.execute('TRUNCATE TABLE "users" CASCADE;')
        cur.execute('INSERT INTO "users" SELECT * FROM "Users_Balance";')
    except Exception as e:
        conn.rollback()
        cur = conn.cursor()
        try:
            cur.execute('DELETE FROM "users";')
            cur.execute('INSERT INTO "users" (user_id, balance, referred_by, referral_count, total_referral_earning) SELECT user_id::bigint, balance::int, referred_by, referral_count::int, total_referral_earning::int FROM "Users_Balance";')
        except Exception as e2:
            print(f"users sync fail: {e2}")
            conn.rollback()
    try:
        cur.execute('TRUNCATE TABLE "users_balance" CASCADE;')
        cur.execute('INSERT INTO "users_balance" SELECT * FROM "Users_Balance";')
    except:
        conn.rollback()
    try:
        cur.execute('TRUNCATE TABLE "orders" CASCADE; INSERT INTO "orders" SELECT * FROM "Orders";')
    except: conn.rollback()
    try:
        cur.execute('TRUNCATE TABLE "stock_available" CASCADE; INSERT INTO "stock_available" SELECT * FROM "Stock_Available";')
    except: conn.rollback()
    try:
        cur.execute('TRUNCATE TABLE "stock_used" CASCADE; INSERT INTO "stock_used" SELECT * FROM "Stock_Used";')
    except: conn.rollback()
    try:
        cur.execute('TRUNCATE TABLE "referrals" CASCADE; INSERT INTO "referrals" SELECT * FROM "Referrals";')
    except: conn.rollback()
    conn.commit()
    cur.execute('SELECT COUNT(*), SUM(balance::int) FROM "users";')
    count, total = cur.fetchone()
    cur.close()
    conn.close()
    return count, total

def register_backup_handlers(bot):
    @bot.message_handler(content_types=['document'])
    def handle_restore(message):
        if message.from_user.id != ADMIN_ID: return
        if not message.caption or "RESTORE" not in message.caption.upper(): return
        bot.reply_to(message, "⏳ Restoring to PostgreSQL...")
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded = bot.download_file(file_info.file_path)
            tmp_path = "/tmp/restore.xlsx"
            with open(tmp_path, 'wb') as f: f.write(downloaded)
            count = restore_from_xlsx(tmp_path)
            bot.reply_to(message, f"✅ Restore Successful! {count} rows restored")
        except Exception as e:
            bot.reply_to(message, f"❌ Restore Failed: {e}")

    @bot.message_handler(commands=['fixbalance'])
    def handle_fixbalance(message):
        if message.from_user.id != ADMIN_ID: return
        bot.reply_to(message, "⏳ Fixing balance... syncing Users_Balance -> users")
        try:
            count, total = fix_balance_sync()
            bot.reply_to(message, f"✅ Balance Fixed!\n\n👥 Users: {count}\n💰 Total Balance: {total}\n\nEbar /start diye check koro")
        except Exception as e:
            bot.reply_to(message, f"❌ Fix Failed: {e}")
