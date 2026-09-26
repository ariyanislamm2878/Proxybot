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
        if table.lower() != table: continue
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
        tbl = sheet_name.lower()
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
    try:
        cur.execute('SELECT * FROM "users_balance" LIMIT 1;')
        src = "users_balance"
    except:
        conn.rollback()
        cur = conn.cursor()
        src = "users_balance"
        cur.execute('SELECT * FROM "users" LIMIT 1;')
        # if users_balance empty, copy from users
        return 0,0
    cur.execute(f'SELECT * FROM "{src}";')
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    cur.execute('DELETE FROM "users";')
    conn.commit()
    inserted = 0
    total_bal = 0
    for r in rows:
        try:
            d = dict(zip(cols, r))
            def parse_int(v, default=0):
                if v is None or v == '' or str(v).lower() == 'none': return default
                try: return int(float(str(v)))
                except: return default
            def parse_float(v, default=0):
                if v is None or v == '' or str(v).lower() == 'none': return default
                try: return float(str(v))
                except: return default
            def parse_bigint(v):
                if v is None or str(v).lower() in ('none','','null'): return None
                try: return int(float(str(v)))
                except: return None
            uid = parse_int(d.get('user_id'))
            if uid == 0: continue
            bal = parse_int(d.get('balance'))
            ref_by = parse_bigint(d.get('referred_by'))
            ref_count = parse_int(d.get('referral_count'))
            ref_earn = parse_float(d.get('total_referral_earning'))
            cur.execute('INSERT INTO "users" (user_id, balance, referred_by, referral_count, total_referral_earning) VALUES (%s,%s,%s,%s,%s)', (uid, bal, ref_by, ref_count, ref_earn))
            inserted += 1
            total_bal += bal
        except:
            conn.rollback()
            cur = conn.cursor()
            continue
    conn.commit()
    cur.close()
    conn.close()
    return inserted, total_bal

def register_backup_handlers(bot):
    @bot.message_handler(content_types=['document'])
    def handle_restore(message):
        if message.from_user.id != ADMIN_ID: return
        if not message.caption or "RESTORE" not in message.caption.upper(): return
        bot.reply_to(message, "⏳ Restoring (lowercase only)...")
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded = bot.download_file(file_info.file_path)
            tmp_path = "/tmp/restore.xlsx"
            with open(tmp_path, 'wb') as f: f.write(downloaded)
            count = restore_from_xlsx(tmp_path)
            bot.reply_to(message, f"✅ Restore Successful! {count} rows\nEbar /fixbalance dao")
        except Exception as e:
            bot.reply_to(message, f"❌ Restore Failed: {e}")

    @bot.message_handler(commands=['fixbalance','clearstock','checkstatus'])
    def handle_checkstatus(message):
        if message.from_user.id != ADMIN_ID: return
        try:
            conn = get_conn()
            cur = conn.cursor()
            msg = "📊 Current Status:\n"
            for tbl in ['orders','stock_available','users','users_balance']:
                try:
                    cur.execute(f'SELECT COUNT(*) FROM "{tbl}";')
                    cnt = cur.fetchone()[0]
                    msg += f"{tbl}: {cnt}\n"
                except:
                    conn.rollback()
                    cur = conn.cursor()
            try:
                cur.execute(f"SELECT COUNT(*) FROM \"orders\" WHERE LOWER(status) = 'pending';")
                pend = cur.fetchone()[0]
                msg += f"\n⏳ Pending orders: {pend}\n"
                if pend > 0:
                    cur.execute(f'SELECT id, user_id, product, status FROM "orders" WHERE LOWER(status) = \'pending\' ORDER BY id DESC LIMIT 5;')
                    for oid, uid, prod, st in cur.fetchall():
                        msg += f"#{oid} UID:{uid} {prod[:20]} - {st}\n"
            except:
                conn.rollback()
            bot.reply_to(message, msg[:4000])
            cur.close()
            conn.close()
        except Exception as e:
            bot.reply_to(message, f"Failed: {e}")

    @bot.message_handler(commands=['fixduplicates','pendinglist'])
    def handle_pendinglist(message):
        if message.from_user.id != ADMIN_ID: return
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id, user_id, product, price, status FROM \"orders\" WHERE LOWER(status) LIKE 'pend%' ORDER BY id DESC LIMIT 20;")
            rows = cur.fetchall()
            if not rows:
                bot.reply_to(message, "✅ Kono pending order nai! Sob approved.\n\nUser er taka katle o refund dite chaile /refund command use koro.")
            else:
                msg = f"⏳ {len(rows)} ta pending order ache:\n\n"
                for oid, uid, prod, price, st in rows:
                    msg += f"ID:{oid} | UID:{uid} | {prod[:25]} | {price}৳ | {st}\n"
                msg += "\nAdmin panel e na asle, tomar main bot er pending button er code e 'orders' table (choto hater) use korte hobe, 'Orders' na."
                bot.reply_to(message, msg[:4000])
            cur.close()
            conn.close()
        except Exception as e:
            bot.reply_to(message, f"pendinglist failed: {e}")

    @bot.message_handler(commands=['refund'])
    def handle_refund(message):
        if message.from_user.id != ADMIN_ID: return
        try:
            parts = message.text.split()
            if len(parts) < 2:
                bot.reply_to(message, "Use: /refund <order_id>")
                return
            oid = int(parts[1])
            conn = get_conn()
            cur = conn.cursor()
            cur.execute('SELECT user_id, price, status FROM "orders" WHERE id=%s;', (oid,))
            row = cur.fetchone()
            if not row:
                bot.reply_to(message, f"Order {oid} not found")
                return
            uid, price, st = row
            cur.execute('SELECT balance FROM "users" WHERE user_id=%s;', (uid,))
            bal_row = cur.fetchone()
            if bal_row:
                new_bal = int(bal_row[0]) + int(price)
                cur.execute('UPDATE "users" SET balance=%s WHERE user_id=%s;', (new_bal, uid))
                cur.execute('UPDATE "users_balance" SET balance=%s WHERE user_id=%s;', (new_bal, uid))
            cur.execute('UPDATE "orders" SET status=%s WHERE id=%s;', ('refunded', oid))
            conn.commit()
            bot.reply_to(message, f"✅ Order {oid} refunded! User {uid} ke {price}৳ back deya holo.")
            cur.close()
            conn.close()
        except Exception as e:
            bot.reply_to(message, f"Refund failed: {e}")
