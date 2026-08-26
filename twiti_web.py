# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════╗
║   💜 تويتي — المحفظة السودانية العصرية 💜   ║
║   النسخة النهائية الجاهزة للنشر 🚀          ║
╚══════════════════════════════════════╝
"""

import hashlib
import os
import random
import re
import sqlite3
from datetime import datetime
from flask import (Flask, session, redirect, url_for,
                   request, render_template_string)

# ══════════════ الإعدادات ══════════════
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24).hex())

DB_FILE = "twiti.db"
CURRENCY = "ج.س"
FEE_RATE = 0.01            # عمولة السحب/التحويل 1%
SAVINGS_RATE = 0.07        # فائدة التوفير 7%

SUPPORT_WHATSAPP = "249904648008"
SUPPORT_FACEBOOK = "https://www.facebook.com/Tweete2"
SUPPORT_TELEGRAM = "https://t.me/mohammed200"


# ══════════════ قاعدة البيانات ══════════════
def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS accounts(
        phone TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        balance REAL DEFAULT 0,
        savings REAL DEFAULT 0,
        account_number TEXT UNIQUE,
        card_number TEXT,
        is_admin INTEGER DEFAULT 0,
        points REAL DEFAULT 0,
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT, tx_type TEXT, amount REAL,
        details TEXT, balance_after REAL, created_at TEXT
    );
    """)
    conn.commit()


def hash_password(p):
    salt = os.urandom(16).hex()
    h = hashlib.pbkdf2_hmac("sha256", p.encode(), salt.encode(), 100_000)
    return f"{salt}${h.hex()}"


def verify_password(p, stored):
    try:
        salt, h = stored.split("$")
        check = hashlib.pbkdf2_hmac("sha256", p.encode(), salt.encode(), 100_000)
        return check.hex() == h
    except Exception:
        return False


def record_tx(phone, tx_type, amount, details="", bal=0):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    c = db()
    c.execute("""INSERT INTO transactions(phone,tx_type,amount,details,balance_after,created_at)
                 VALUES(?,?,?,?,?,?)""", (phone, tx_type, amount, details, bal, now))
    c.commit()


def current_user():
    phone = session.get("phone")
    if not phone:
        return None
    row = db().execute("SELECT * FROM accounts WHERE phone=?", (phone,)).fetchone()
    return dict(row) if row else None


def set_msg(msg, typ="err"):
    session["msg"], session["typ"] = msg, typ


# ══════════════ التصميم العصري 💜 ══════════════
BASE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#6b21a8">
<title>تويتي 💜</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI', Tahoma, sans-serif; }
  body {
    min-height:100vh;
    background: linear-gradient(135deg, #1a0533 0%, #3b0764 50%, #6b21a8 100%);
    display:flex; justify-content:center; align-items:center; padding:20px;
  }
  .card {
    background:rgba(255,255,255,.08); backdrop-filter:blur(20px);
    border:1px solid rgba(255,255,255,.15); border-radius:25px;
    padding:35px; width:100%; max-width:430px;
    box-shadow:0 25px 60px rgba(0,0,0,.4); color:#fff;
    animation:fadeUp .5s ease; margin-bottom:60px;
  }
  @keyframes fadeUp { from{opacity:0; transform:translateY(25px)} to{opacity:1; transform:none} }
  .logo { text-align:center; font-size:2rem; font-weight:bold; margin-bottom:5px; }
  .logo span { background:linear-gradient(90deg,#c084fc,#f0abfc);
               -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
  .sub { text-align:center; color:#d8b4fe; font-size:.85rem; margin-bottom:25px; }
  input, select {
    width:100%; padding:14px 18px; margin:8px 0; border-radius:14px;
    border:1px solid rgba(255,255,255,.2); background:rgba(255,255,255,.1);
    color:#fff; font-size:1rem; outline:none; transition:.3s;
  }
  input::placeholder { color:#c4b5fd; }
  input:focus { border-color:#c084fc; box-shadow:0 0 0 3px rgba(192,132,252,.25); }
  option { color:#000; }
  .btn {
    width:100%; padding:14px; margin-top:12px; border:none; border-radius:14px;
    background:linear-gradient(90deg,#9333ea,#c026d3); color:#fff; font-size:1.05rem;
    font-weight:bold; cursor:pointer; transition:.3s;
  }
  .btn:hover { transform:translateY(-2px); box-shadow:0 10px 25px rgba(147,51,234,.5); }
  .btn.small { padding:10px; font-size:.85rem; }
  .grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; margin-top:18px; }
  .action {
    background:rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.15);
    border-radius:16px; padding:16px 6px; text-align:center; cursor:pointer;
    transition:.3s; color:#fff; text-decoration:none; font-size:.78rem;
  }
  .action:hover { background:rgba(192,132,252,.25); transform:translateY(-3px); }
  .action .ic { font-size:1.5rem; display:block; margin-bottom:5px; }
  .balance-box {
    background:linear-gradient(135deg,#7e22ce,#a21caf);
    border-radius:20px; padding:22px; text-align:center; margin-bottom:20px;
    box-shadow:inset 0 2px 10px rgba(255,255,255,.15);
  }
  .balance-box .amount { font-size:2.1rem; font-weight:bold; }
  .msg { padding:12px; border-radius:12px; margin:10px 0; font-size:.9rem; }
  .ok  { background:rgba(34,197,94,.2); border:1px solid #22c55e; color:#bbf7d0; }
  .err { background:rgba(239,68,68,.2); border:1px solid #ef4444; color:#fecaca; }
  table { width:100%; border-collapse:collapse; font-size:.82rem; }
  td,th { padding:9px 6px; border-bottom:1px solid rgba(255,255,255,.1); text-align:right; }
  th { color:#c084fc; }
  .in  { color:#4ade80; } .out { color:#f87171; }
  a.link { color:#d8b4fe; display:block; text-align:center; margin-top:15px;
           text-decoration:none; font-size:.9rem; }
  a.link:hover { color:#fff; }
  .header { display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; }
  .header b { font-size:1.1rem; }
  .logout { color:#f0abfc; text-decoration:none; font-size:.85rem; }

  /* ═══ أزرار الدعم العائمة 💬💙💜 ═══ */
  .float-btn {
    position: fixed; left: 22px; width: 54px; height: 54px;
    border-radius: 50%; display: flex !important;
    justify-content: center; align-items: center;
    z-index: 999; transition: all .3s ease;
    box-shadow: 0 6px 20px rgba(0,0,0,.35);
  }
  .whatsapp {
    bottom: 150px;
    background: linear-gradient(135deg, #25d366, #128c7e);
    animation: waPulse 2s infinite;
  }
  .whatsapp:hover { transform: scale(1.12) rotate(-6deg);
                    box-shadow: 0 10px 28px rgba(37,211,102,.65); }
  .facebook {
    bottom: 88px;
    background: linear-gradient(135deg, #1877f2, #0b5fce);
    animation: fbPulse 2.5s infinite;
  }
  .facebook:hover { transform: scale(1.12) rotate(6deg);
                    box-shadow: 0 10px 28px rgba(24,119,242,.65); }
  .telegram {
    bottom: 26px;
    background: linear-gradient(135deg, #2aabee, #229ed9);
    animation: tgPulse 2.2s infinite;
  }
  .telegram:hover { transform: scale(1.12) rotate(-6deg);
                    box-shadow: 0 10px 28px rgba(42,171,238,.65); }
  @keyframes waPulse {
    0%   { box-shadow: 0 0 0 0 rgba(37,211,102,.55); }
    70%  { box-shadow: 0 0 0 15px rgba(37,211,102,0); }
    100% { box-shadow: 0 0 0 0 rgba(37,211,102,0); }
  }
  @keyframes fbPulse {
    0%   { box-shadow: 0 0 0 0 rgba(24,119,242,.55); }
    70%  { box-shadow: 0 0 0 15px rgba(24,119,242,0); }
    100% { box-shadow: 0 0 0 0 rgba(24,119,242,0); }
  }
  @keyframes tgPulse {
    0%   { box-shadow: 0 0 0 0 rgba(42,171,238,.55); }
    70%  { box-shadow: 0 0 0 15px rgba(42,171,238,0); }
    100% { box-shadow: 0 0 0 0 rgba(42,171,238,0); }
  }
  .float-btn::after {
    position: absolute; left: 66px; white-space: nowrap;
    background: rgba(0,0,0,.78); color: #fff;
    padding: 6px 14px; border-radius: 10px; font-size: .8rem;
    opacity: 0; pointer-events: none; transition: opacity .3s;
  }
  .whatsapp::after { content: "دعم واتساب"; }
  .facebook::after { content: "صفحتنا على فيسبوك"; }
  .telegram::after { content: "قناة تيليجرام"; }
  .float-btn:hover::after { opacity: 1; }
</style>
</head>
<body>
<div class="card">{{ inner }}</div>

<!-- ═══ أزرار الدعم الثلاثة ═══ -->
<a href="https://wa.me/{{ wa }}?text=%D9%85%D8%B1%D8%AD%D8%A8%D8%A7%20%D8%A3%D8%B1%D9%8A%D8%AF%20%D8%A7%D9%84%D9%85%D8%B3%D8%A7%D8%B9%D8%AF%D8%A9%20%D9%81%D9%8A%20%D9%85%D8%AD%D9%81%D8%B8%D8%A9%20%D8%AA%D9%88%D9%8A%D8%AA%D9%8A"
   target="_blank" class="float-btn whatsapp" title="دعم واتساب">
  <svg width="28" height="28" viewBox="0 0 24 24" fill="#fff"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
</a>
<a href="{{ fb }}" target="_blank" class="float-btn facebook" title="فيسبوك">
  <svg width="28" height="28" viewBox="0 0 24 24" fill="#fff"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
</a>
<a href="{{ tg }}" target="_blank" class="float-btn telegram" title="تيليجرام">
  <svg width="28" height="28" viewBox="0 0 24 24" fill="#fff"><path d="M11.944 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0012 0a12 12 0 00-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 01.171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>
</a>
</body>
</html>
"""


def page(inner):
    return render_template_string(BASE, inner=inner,
                                  wa=SUPPORT_WHATSAPP,
                                  fb=SUPPORT_FACEBOOK,
                                  tg=SUPPORT_TELEGRAM)


def flash_msg():
    msg = session.pop("msg", None)
    typ = session.pop("typ", None)
    if msg:
        cls = "ok" if typ == "ok" else "err"
        return f'<div class="msg {cls}">{msg}</div>'
    return ""


# ══════════════ المسارات ══════════════

@app.route("/")
def home():
    if current_user():
        return redirect(url_for("dashboard"))
    return page(f"""
      <div class="logo"><span>💜 تويتي</span></div>
      <div class="sub">محفظتك السودانية العصرية 🇸🇩</div>
      {flash_msg()}
      <a href="{url_for('login')}"><button class="btn">🔓 تسجيل الدخول</button></a>
      <a href="{url_for('register')}"><button class="btn" style="background:rgba(255,255,255,.15)">📝 فتح حساب جديد</button></a>
      <a href="{url_for('support')}"><button class="btn" style="background:linear-gradient(90deg,#25d366,#128c7e)">💬 الدعم الفني</button></a>
    """)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        phone = request.form["phone"].strip()
        pwd = request.form["pwd"].strip()
        if not re.fullmatch(r"09\d{8}", phone):
            set_msg("رقم الهاتف يجب أن يبدأ بـ 09 ويتكون من 10 خانات")
            return redirect(url_for("register"))
        if len(pwd) < 4:
            set_msg("الرقم السري قصير جداً (4 خانات على الأقل)")
            return redirect(url_for("register"))
        conn = db()
        if conn.execute("SELECT 1 FROM accounts WHERE phone=?", (phone,)).fetchone():
            set_msg("هذا الرقم مسجل مسبقاً!")
            return redirect(url_for("register"))
        acc_num = f"TWT-{random.randint(100000,999999)}"
        card = "4" + "".join(random.choices("0123456789", k=15))
        now = datetime.now().strftime("%Y-%m-%d")
        conn.execute("INSERT INTO accounts VALUES(?,?,?,?,?,?,?,?,?,?)",
                     (phone, name, hash_password(pwd), 0, 0, acc_num, card, 0, 0, now))
        conn.commit()
        record_tx(phone, "فتح حساب 🎉", 0, "", 0)
        set_msg(f"🎉 أهلاً بك يا {name}! رقم حسابك {acc_num} — سجّل دخولك الآن", "ok")
        return redirect(url_for("login"))
    return page(f"""
      <div class="logo">📝</div><div class="sub">فتح حساب جديد في تويتي</div>
      {flash_msg()}
      <form method="post">
        <input name="name" placeholder="👤 الاسم الكامل" required>
        <input name="phone" placeholder="📱 الهاتف (09xxxxxxxx)" required>
        <input name="pwd" type="password" placeholder="🔐 الرقم السري (4+ خانات)" required>
        <button class="btn">إنشاء الحساب ✨</button>
      </form>
      <a class="link" href="{url_for('home')}">→ رجوع للرئيسية</a>
    """)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form["phone"].strip()
        pwd = request.form["pwd"].strip()
        row = db().execute("SELECT * FROM accounts WHERE phone=?", (phone,)).fetchone()
        if row and verify_password(pwd, row["password_hash"]):
            session["phone"] = phone
            return redirect(url_for("dashboard"))
        set_msg("بيانات الدخول غير صحيحة!")
        return redirect(url_for("login"))
    return page(f"""
      <div class="logo">🔓</div><div class="sub">تسجيل الدخول إلى تويتي</div>
      {flash_msg()}
      <form method="post">
        <input name="phone" placeholder="📱 الهاتف" required>
        <input name="pwd" type="password" placeholder="🔐 الرقم السري" required>
        <button class="btn">دخول 💜</button>
      </form>
      <a class="link" href="{url_for('register')}">ليس لديك حساب؟ أنشئ واحداً الآن</a>
    """)


@app.route("/dashboard")
def dashboard():
    u = current_user()
    if not u:
        return redirect(url_for("login"))
    actions = [
        ("⬇️", "إيداع", "deposit"), ("⬆️", "سحب", "withdraw"),
        ("💸", "تحويل", "transfer"), ("🐖", "التوفير", "savings"),
        ("📜", "كشف الحساب", "history"), ("💬", "الدعم", "support"),
        ("⚙️", "الإعدادات", "settings"), ("🚪", "خروج", "logout"),
    ]
    acts = "".join(
        f'<a class="action" href="{url_for(r)}"><span class="ic">{i}</span>{t}</a>'
        for i, t, r in actions)
    return page(f"""
      <div class="header"><b>👋 {u['full_name']}</b>
        <a class="logout" href="{url_for('logout')}">خروج ←</a></div>
      {flash_msg()}
      <div class="balance-box">
        <div style="color:#e9d5ff;font-size:.85rem">💰 الرصيد المتوفر</div>
        <div class="amount">{u['balance']:,.0f} {CURRENCY}</div>
        <div style="color:#f0abfc;font-size:.8rem;margin-top:5px">
          🏦 {u['account_number']} | ⭐ {u['points']:.0f} نقطة
        </div>
      </div>
      <div class="grid">{acts}</div>
    """)


@app.route("/deposit", methods=["GET", "POST"])
def deposit():
    u = current_user()
    if not u:
        return redirect(url_for("login"))
    if request.method == "POST":
        try:
            amt = float(request.form.get("amount") or 0)
        except ValueError:
            amt = 0
        if amt > 0:
            nb = u["balance"] + amt
            c = db()
            c.execute("UPDATE accounts SET balance=? WHERE phone=?", (nb, u["phone"]))
            c.commit()
            record_tx(u["phone"], "إيداع ⬇️", amt, "", nb)
            set_msg(f"✅ تم إيداع {amt:,.0f} {CURRENCY}", "ok")
        else:
            set_msg("مبلغ غير صالح")
        return redirect(url_for("dashboard"))
    return _money_page("⬇️ إيداع أموال")


@app.route("/withdraw", methods=["GET", "POST"])
def withdraw():
    u = current_user()
    if not u:
        return redirect(url_for("login"))
    if request.method == "POST":
        try:
            amt = float(request.form.get("amount") or 0)
        except ValueError:
            amt = 0
        fee = amt * FEE_RATE
        total = amt + fee
        if amt <= 0:
            set_msg("مبلغ غير صالح")
        elif total > u["balance"]:
            set_msg(f"❌ الرصيد غير كافٍ (تحتاج {total:,.0f} مع العمولة)")
        else:
            nb = u["balance"] - total
            c = db()
            c.execute("UPDATE accounts SET balance=? WHERE phone=?", (nb, u["phone"]))
            c.commit()
            record_tx(u["phone"], "سحب ⬆️", amt, f"عمولة {fee:.0f}", nb)
            set_msg(f"✅ تم السحب — رصيدك الآن {nb:,.0f} {CURRENCY}", "ok")
        return redirect(url_for("dashboard"))
    return _money_page("⬆️ سحب أموال")


@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    u = current_user()
    if not u:
        return redirect(url_for("login"))
    if request.method == "POST":
        to_phone = request.form.get("to", "").strip()
        try:
            amt = float(request.form.get("amount") or 0)
        except ValueError:
            amt = 0
        fee = amt * FEE_RATE
        conn = db()
        other = conn.execute("SELECT * FROM accounts WHERE phone=?",
                             (to_phone,)).fetchone()
        if not other:
            set_msg("المستلم غير مسجل في تويتي!")
        elif to_phone == u["phone"]:
            set_msg("لا يمكنك التحويل لنفسك!")
        elif amt <= 0 or amt + fee > u["balance"]:
            set_msg("مبلغ غير صالح أو رصيد غير كافٍ")
        else:
            sb = u["balance"] - amt - fee
            rb = dict(other)["balance"] + amt
            c = db()
            c.execute("UPDATE accounts SET balance=?, points=points+? WHERE phone=?",
                      (sb, amt / 100, u["phone"]))
            c.execute("UPDATE accounts SET balance=? WHERE phone=?", (rb, to_phone))
            c.commit()
            record_tx(u["phone"], "تحويل صادر 📤", amt,
                      f"إلى {other['full_name']}", sb)
            record_tx(to_phone, "تحويل وارد 📥", amt,
                      f"من {u['full_name']}", rb)
            set_msg(f"💸 حُوّل {amt:,.0f} {CURRENCY} إلى {other['full_name']} — ربحت نقاطاً ⭐", "ok")
        return redirect(url_for("dashboard"))
    return page(f"""
      <div class="header"><b>💸 تحويل أموال</b><a class="logout" href="{url_for('dashboard')}">رجوع ←</a></div>
      {flash_msg()}
      <form method="post">
        <input name="to" placeholder="📱 هاتف المستلم" required>
        <input name="amount" type="number" step="any" placeholder="💵 المبلغ" required>
        <button class="btn">إرسال الآن 🚀</button>
      </form>
      <p style="text-align:center;color:#d8b4fe;font-size:.78rem;margin-top:10px">
        العمولة 1% | اربح نقاطاً مع كل تحويل! ⭐
      </p>
    """)


@app.route("/savings", methods=["GET", "POST"])
def savings():
    u = current_user()
    if not u:
        return redirect(url_for("login"))
    if request.method == "POST":
        mode = request.form.get("mode")
        try:
            amt = float(request.form.get("amount") or 0)
        except ValueError:
            amt = 0
        c = db()
        if mode == "save" and 0 < amt <= u["balance"]:
            c.execute("UPDATE accounts SET balance=?, savings=? WHERE phone=?",
                      (u["balance"] - amt, u["savings"] + amt, u["phone"]))
            c.commit()
            record_tx(u["phone"], "إدخار 🐖", amt, "", u["balance"] - amt)
            set_msg(f"🐷 أدرت {amt:,.0f} {CURRENCY} في التوفير", "ok")
        elif mode == "take" and 0 < amt <= u["savings"]:
            c.execute("UPDATE accounts SET balance=?, savings=? WHERE phone=?",
                      (u["balance"] + amt, u["savings"] - amt, u["phone"]))
            c.commit()
            record_tx(u["phone"], "سحب من التوفير 💰", amt, "", u["balance"] + amt)
            set_msg(f"رُجّع {amt:,.0f} {CURRENCY} لمحفظتك", "ok")
        else:
            set_msg("مبلغ غير صالح")
        return redirect(url_for("savings"))
    return page(f"""
      <div class="header"><b>🐖 حساب التوفير</b><a class="logout" href="{url_for('dashboard')}">رجوع ←</a></div>
      {flash_msg()}
      <div class="balance-box" style="background:linear-gradient(135deg,#b45309,#d97706)">
        <div style="color:#fef3c7;font-size:.85rem">مدخراتك — فائدة سنوية {SAVINGS_RATE*100:.0f}%</div>
        <div class="amount">{u['savings']:,.0f} {CURRENCY}</div>
      </div>
      <form method="post">
        <input name="amount" type="number" step="any" placeholder="💵 المبلغ" required>
        <div class="grid">
          <button class="btn small" name="mode" value="save">إدخ 🐷</button>
          <button class="btn small" name="mode" value="take"
                  style="background:linear-gradient(90deg,#be185d,#db2777)">سحب 💸</button>
        </div>
      </form>
    """)


@app.route("/history")
def history():
    u = current_user()
    if not u:
        return redirect(url_for("login"))
    rows = db().execute(
        "SELECT * FROM transactions WHERE phone=? ORDER BY id DESC LIMIT 30",
        (u["phone"],)).fetchall()
    incoming = {"إيداع ⬇️", "تحويل وارد 📥", "سحب من التوفير 💰"}
    trs = ""
    for r in rows:
        cls = "in" if r["tx_type"] in incoming else "out"
        sign = "+" if r["tx_type"] in incoming else "−"
        trs += (f"<tr><td>{r['created_at']}</td><td>{r['tx_type']}</td>"
                f"<td class='{cls}'>{sign}{r['amount']:,.0f}</td>"
                f"<td style='color:#c4b5fd'>{r['balance_after']:,.0f}</td></tr>")
    if not trs:
        trs = "<tr><td colspan='4' style='text-align:center;color:#c4b5fd'>لا توجد عمليات بعد</td></tr>"
    return page(f"""
      <div class="header"><b>📜 كشف الحساب</b><a class="logout" href="{url_for('dashboard')}">رجوع ←</a></div>
      {flash_msg()}
      <table><tr><th>الوقت</th><th>العملية</th><th>المبلغ</th><th>الرصيد</th></tr>{trs}</table>
    """)

@app.route("/settings")
def settings():
    u = current_user()
    if not u:
        return redirect(url_for("login"))
    return page(f"""
      <div class="header"><b>⚙️ الإعدادات وتفاصيل الحساب</b>
        <a class="logout" href="{url_for('dashboard')}">رجوع ←</a></div>
      {flash_msg()}
      <div class="balance-box" style="background:linear-gradient(135deg,#334155,#475569)">
        <div style="color:#e2e8f0;font-size:.85rem">💳 بطاقتك البنكية</div>
        <div style="font-size:1.15rem;font-weight:bold;letter-spacing:3px;margin-top:8px">
          {u['card_number'][:4]} **** **** {u['card_number'][-4:]}
        </div>
      </div>
      <p style="color:#e9d5ff;font-size:.9rem;line-height:2.2;margin-bottom:10px">
        👤 الاسم: <b>{u['full_name']}</b><br>
        📱 الهاتف: <b>{u['phone']}</b><br>
        🏦 رقم الحساب: <b>{u['account_number']}</b><br>
        📅 عضو منذ: <b>{u['created_at']}</b><br>
        ⭐ نقاطك: <b>{u['points']:.0f} نقطة</b>
      </p>
      <a href="{url_for('change_password')}"><button class="btn small">🔑 تغيير الرقم السري</button></a>
    """)


@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    u = current_user()
    if not u:
        return redirect(url_for("login"))
    if request.method == "POST":
        old = request.form.get("old", "").strip()
        new = request.form.get("new", "").strip()
        if not verify_password(old, u["password_hash"]):
            set_msg("الرقم السري القديم غير صحيح!")
        elif len(new) < 4:
            set_msg("الرقم الجديد قصير (4 خانات على الأقل)")
        else:
            c = db()
            c.execute("UPDATE accounts SET password_hash=? WHERE phone=?",
                      (hash_password(new), u["phone"]))
            c.commit()
            set_msg("✅ تم تغيير الرقم السري بنجاح", "ok")
            return redirect(url_for("settings"))
        return redirect(url_for("change_password"))
    return page(f"""
      <div class="header"><b>🔑 تغيير الرقم السري</b>
        <a class="logout" href="{url_for('settings')}">رجوع ←</a></div>
      {flash_msg()}
      <form method="post">
        <input name="old" type="password" placeholder="🔐 الرقم السري القديم" required>
        <input name="new" type="password" placeholder="🔐 الرقم السري الجديد" required>
        <button class="btn">حفظ التغيير ✅</button>
      </form>
    """)


@app.route("/support")
def support():
    return page(f"""
      <div class="header"><b>💬 الدعم الفني</b>
        <a class="logout" href="{url_for('home')}">رجوع ←</a></div>
      {flash_msg()}
      <div class="balance-box" style="background:linear-gradient(135deg,#16a34a,#0369a1)">
        <div style="font-size:.85rem;color:#dcfce7">فريق تويتي في خدمتك 24/7</div>
        <div style="font-size:1.2rem;margin-top:8px">📞 +249 90 464 8008</div>
      </div>
      <div class="grid" style="grid-template-columns:1fr 1fr">
        <a href="https://wa.me/{SUPPORT_WHATSAPP}" target="_blank" style="text-decoration:none">
          <button class="btn small" style="background:linear-gradient(90deg,#25d366,#128c7e)">💬 واتساب</button></a>
        <a href="{SUPPORT_FACEBOOK}" target="_blank" style="text-decoration:none">
          <button class="btn small" style="background:linear-gradient(90deg,#1877f2,#0b5fce)">💙 فيسبوك</button></a

> ⚠️ The connection to the model was interrupted. Reply **continue** to pick up from here.




# ══════════════ التشغيل ══════════════
if __name__ == "__main__":
    init_db()
    print("💜 تويتي يعمل الآن")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
