import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def create_backup_excel():
    from openpyxl import Workbook
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public';")
    tables = [r[0] for r in cur.fetchall()]
    wb = Workbook()
    wb.remove(wb.active)
    for table in tables:
        if table.startswith("pg_") or table.startswith("sql_"): continue
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

def get_db_file_if_sqlite(): return None

def restore_from_xlsx(file_path):
    from openpyxl import load_workbook
    conn = get_conn()
    cur = conn.cursor()
    wb = load_workbook(file_path)
    restored = 0
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.values)
        if not rows or len(rows) < 2: continue
        headers = [str(h).strip() for h in rows[0] if h]
        for tbl in set([sheet_name, sheet_name.lower()]):
            cols_def = ", ".join([f'"{c.lower()}" TEXT' for c in headers])
            try:
                cur.execute(f'CREATE TABLE IF NOT EXISTS "{tbl}" ({cols_def});')
                cur.execute(f'TRUNCATE TABLE "{tbl}" RESTART IDENTITY CASCADE;')
            except:
                conn.rollback()
                cur = conn.cursor()
        conn.commit()
        for r in rows[1:]:
            if not r or not any(v is not None and str(v) != "" for v in r): continue
            r = list(r)[:len(headers)] + [None]*(len(headers)-len(r))
            cols = ", ".join([f'"{c.lower()}"' for c in headers])
            ph = ", ".join(["%s"]*len(headers))
            for tbl in set([sheet_name, sheet_name.lower()]):
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
    # Step 1: Get all data from Users_Balance as text and clean
    cur.execute('SELECT * FROM "Users_Balance";')
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(f"Users_Balance has {len(rows)} rows, cols {cols}")

    # Find correct source - if Users_Balance empty, try users_balance or Users_Balance lowercase check
    if len(rows) < 10:
        try:
            cur.execute('SELECT * FROM "users_balance";')
            rows2 = cur.fetchall()
            if len(rows2) > len(rows):
                rows = rows2
                cols = [d[0] for d in cur.description]
                print(f"Using users_balance with {len(rows)} rows")
        except: pass

    # Now insert into users table row by row with casting
    cur.execute('DELETE FROM "users";')
    conn.commit()
    inserted = 0
    total_bal = 0
    for r in rows:
        try:
            d = dict(zip(cols, r))
            uid = int(str(d.get('user_id') or d.get('USER_ID') or 0))
            bal = int(float(str(d.get('balance') or 0)))
            ref_by = d.get('referred_by')
            ref_count = int(str(d.get('referral_count') or 0))
            ref_earn = int(str(d.get('total_referral_earning') or 0))
            # handle None string
            if ref_by in ('None', '', 'null'): ref_by = None
            else:
                try: ref_by = int(ref_by) if ref_by else None
                except: ref_by = None
            cur.execute('INSERT INTO "users" (user_id, balance, referred_by, referral_count, total_referral_earning) VALUES (%s,%s,%s,%s,%s)', (uid, bal, ref_by, ref_count, ref_earn))
            inserted += 1
            total_bal += bal
        except Exception as e:
            print(f"skip row {r}: {e}")
            conn.rollback()
            cur = conn.cursor()
            continue
    conn.commit()

    # Also sync to lower tables
    try:
        cur.execute('DELETE FROM "users_balance";')
        cur.execute('INSERT INTO "users_balance" SELECT * FROM "users";')
        conn.commit()
    except:
        conn.rollback()

    try:
        cur.execute('DELETE FROM "orders"; INSERT INTO "orders" SELECT * FROM "Orders";')
        cur.execute('DELETE FROM "stock_available"; INSERT INTO "stock_available" SELECT * FROM "Stock_Available";')
        cur.execute('DELETE FROM "stock_used"; INSERT INTO "stock_used" SELECT * FROM "Stock_Used";')
        cur.execute('DELETE FROM "referrals"; INSERT INTO "referrals" SELECT * FROM "Referrals";')
        conn.commit()
    except:
        conn.rollback()

    cur.close()
    conn.close()
    return inserted, total_bal

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
            bot.reply_to(message, f"✅ Restore Successful! {count} rows restored\n\nEbar /fixbalance dao")
        except Exception as e:
            bot.reply_to(message, f"❌ Restore Failed: {e}")

    @bot.message_handler(commands=['fixbalance'])
    def handle_fixbalance(message):
        if message.from_user.id != ADMIN_ID: return
        bot.reply_to(message, "⏳ Fixing balance... syncing 254 users -> users table")
        try:
            count, total = fix_balance_sync()
            bot.reply_to(message, f"✅ Balance Fixed!\n\n👥 Users: {count}\n💰 Total Balance: {total}\n\nEbar /start diye check koro")
        except Exception as e:
            bot.reply_to(message, f"❌ Fix Failed: {e}")
            print(e)
