# app.py
from flask import Flask, request, jsonify, render_template_string
import json, datetime, os

app = Flask(__name__)
DATA_FILE = "captured.json"

VICTIM_PAGE = """
<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>توعية أمنية</title>
<style>
body{font-family:Arial;background:#0f172a;color:#e2e8f0;padding:20px;max-width:600px;margin:auto}
.card{background:#1e293b;padding:20px;border-radius:10px;margin:10px 0}
h1{color:#38bdf8;text-align:center}
.btn{width:100%;padding:15px;background:#2563eb;color:#fff;border:none;
border-radius:8px;font-size:16px;cursor:pointer;margin:15px 0}
.btn.gps{background:#dc2626;font-size:14px;padding:10px}
.notice{background:#422006;color:#fde68a;padding:12px;border-radius:8px;font-size:13px}
</style></head><body>
<h1>🕵️ ماذا يعرف عنك هذا الرابط؟</h1>
<div class="notice">⚠️ تجربة تعليمية. عند الضغط، ستُرسل معلومات جهازك
إلى شاشة المحاضرة لعرضها. لا تُدخل بيانات حساسة.</div>
<button class="btn" onclick="scanAll()">🔍 افحص كل شيء</button>
<div id="out"></div>
<script>
async function scanAll(){
  const out = document.getElementById('out');
  out.innerHTML = '<div class="card">⏳ جاري الفحص الشامل...</div>';
  const data = {};

  // معلومات أساسية
  data.userAgent = navigator.userAgent;
  data.platform = navigator.platform;
  data.language = navigator.language;
  data.languages = (navigator.languages||[]).join(', ');
  data.cores = navigator.hardwareConcurrency;
  data.memory = navigator.deviceMemory;
  data.screen = screen.width + 'x' + screen.height;
  data.pixelRatio = devicePixelRatio;
  data.colorDepth = screen.colorDepth;
  data.touchPoints = navigator.maxTouchPoints;
  data.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  data.localTime = new Date().toLocaleString('ar');
  data.online = navigator.onLine;
  data.connection = navigator.connection?.effectiveType;
  data.downlink = navigator.connection?.downlink;
  data.rtt = navigator.connection?.rtt;

  // بصمة Canvas
  try {
    const cv = document.createElement('canvas');
    const ctx = cv.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);
    ctx.fillStyle = '#069';
    ctx.fillText('توعية', 2, 15);
    data.canvasFingerprint = cv.toDataURL().slice(-50);
  } catch(e) { data.canvasFingerprint = 'محجوب'; }

  // بصمة الصوت
  try {
    const AC = window.OfflineAudioContext || window.webkitOfflineAudioContext;
    if (AC) {
      const ctx = new AC(1, 44100, 44100);
      const osc = ctx.createOscillator();
      osc.type = 'triangle';
      osc.frequency.value = 10000;
      const comp = ctx.createDynamicsCompressor();
      osc.connect(comp); comp.connect(ctx.destination);
      osc.start(0);
      const buf = await ctx.startRendering();
      const d = buf.getChannelData(0);
      let sum = 0;
      for (let i = 0; i < d.length; i += 100) sum += Math.abs(d[i]);
      data.audioFingerprint = sum.toFixed(6);
    }
  } catch(e) { data.audioFingerprint = 'محجوب'; }

  // IP والموقع التقريبي
  try {
    const r = await fetch('https://ipwho.is/');
    const d = await r.json();
    if (d.success) {
      data.ipCountry = d.country;
      data.ipCity = d.city;
      data.ipRegion = d.region;
      data.ipISP = d.connection?.isp;
      data.ipLat = d.latitude;
      data.ipLon = d.longitude;
      data.ipIsVPN = /vpn|hosting|proxy/i.test(d.connection?.isp||'') ? 'احتمال' : 'لا';
    }
  } catch(e) {}

  out.innerHTML = '<div class="card">✅ تم جمع ' + Object.keys(data).length + ' إشارة. جاري الإرسال...</div>';

  await fetch('/capture', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  });

  out.innerHTML = `
    <div class="card" style="border-right:4px solid #22c55e">
      ✅ تم إرسال ${Object.keys(data).length} إشارة إلى شاشة المحاضرة.
    </div>
    <div class="card" style="border-right:4px solid #dc2626">
      <h3 style="color:#f87171">🔓 هل تسمح بالموقع الدقيق؟</h3>
      <p style="font-size:13px;color:#fbbf24">هذا اختياري. اضغط "سماح" لترى ماذا يحدث.</p>
      <button class="btn gps" onclick="askGPS()">جرّب السماح بالموقع الدقيق</button>
      <div id="gpsOut"></div>
    </div>`;
}

async function askGPS(){
  const o = document.getElementById('gpsOut');
  if(!navigator.geolocation){ o.innerHTML = '<p style="color:#f87171">غير مدعوم</p>'; return; }
  o.innerHTML = '<p style="color:#fbbf24">⏳ يطلب المتصفح إذنك...</p>';
  navigator.geolocation.getCurrentPosition(
    async (p) => {
      await fetch('/capture', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          gps_lat: p.coords.latitude,
          gps_lon: p.coords.longitude,
          gps_accuracy: p.coords.accuracy,
          gps_timestamp: new Date().toISOString()
        })
      });
      o.innerHTML = `<div style="background:#450a0a;padding:10px;border-radius:6px">
        <b style="color:#f87171">🔴 أعطيت الإذن!</b><br>
        خط العرض: ${p.coords.latitude.toFixed(6)}<br>
        خط الطول: ${p.coords.longitude.toFixed(6)}<br>
        الدقة: ± ${p.coords.accuracy.toFixed(0)} متر</div>`;
    },
    (e) => {
      o.innerHTML = `<div style="background:#14532d;padding:10px;border-radius:6px">
        <b style="color:#4ade80">✅ رفضت الإذن — أحسنت!</b><br>
        الموقع لا يعرف سوى مدينتك التقريبية.</div>`;
    }
  );
}
</script></body></html>
"""

DASHBOARD = """
<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8">
<title>لوحة التحكم</title><meta http-equiv="refresh" content="3">
<style>
body{font-family:Arial;background:#0f172a;color:#e2e8f0;padding:20px;max-width:900px;margin:auto}
h1{color:#38bdf8}
.entry{background:#1e293b;padding:20px;border-radius:10px;margin:15px 0;border-right:4px solid #38bdf8}
.row{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #334155}
.label{color:#94a3b8}.value{font-family:monospace;font-size:13px;direction:ltr;text-align:right}
.clear{background:#dc2626;color:white;padding:10px 20px;border:none;border-radius:6px;cursor:pointer}
</style></head><body>
<h1>📊 ما وصل من الأجهزة</h1>
<p style="color:#94a3b8">تحديث تلقائي كل 3 ثوانٍ</p>
<form method="POST" action="/clear" style="margin:10px 0">
<button class="clear" type="submit">🗑️ حذف كل البيانات</button>
</form>
{% for e in entries %}
<div class="entry"><h3>{{ e.timestamp }}</h3>
{% for k,v in e.items() %}{% if k != 'timestamp' %}
<div class="row"><span class="label">{{ k }}</span><span class="value">{{ v }}</span></div>
{% endif %}{% endfor %}</div>
{% else %}<div class="entry">لا توجد بيانات بعد.</div>{% endfor %}
</body></html>
"""

@app.route("/")
def victim(): return render_template_string(VICTIM_PAGE)

@app.route("/capture", methods=["POST"])
def capture():
    data = request.get_json()
    data["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data["ip_address"] = request.remote_addr
    existing = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
    existing.append(data)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})

@app.route("/dashboard")
def dashboard():
    entries = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            entries = json.load(f)[::-1]
    return render_template_string(DASHBOARD, entries=entries)

@app.route("/clear", methods=["POST"])
def clear():
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    return dashboard()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
  Flask==3.0.0
gunicorn==21.2.0
web: gunicorn app:app
