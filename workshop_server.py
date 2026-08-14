# -*- coding: utf-8 -*-
"""
workshop_server.py — خادم استقبال الورشة (`DEC-279`)
======================================================
`stdlib` وحدها · **صفر اعتمادية** كبقية المشروع. مساران لا ثالث لهما:

  * `GET  /`        → صفحة الورشة (`Workshop.html` المولَّدة)
  * `POST /submit`  → `workshop_store.accept` — يقبل أو يردّ بحكمه

**وما عداهما `404`**: لا خدمةَ ملفّاتٍ ولا فهرسةَ مجلَّد ولا مسارٌ يُشتقّ
من الطلب — فصنفُ «اجتياز المسار» ساقطٌ بالبناء لا بالتنقية.

**والربط `127.0.0.1` افتراضاً**: فتحُه على الشبكة **اختيارٌ صريح** بعَلَمٍ
مكتوب (`--host`)، ويُطبع عنده تنبيهٌ بما يعنيه. فالمالك يفتح ما يفتح
عالماً بأنه فتحه (`م-4`).

**ولا اعتماد يُطلب ولا يُقبل** (`DEC-277 §4`): الرمز يُصدره المالك، وبوابةُ
القبول هي أداةُ المشرف لا كلمةُ مرور.
"""
import io
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import workshop_store as WS

PAGE = os.path.join(HERE, "Workshop.html")
MAX_BODY = 4 * 1024 * 1024          # حدٌّ معلَن — حمولةٌ أكبر تُردّ لا تُقرأ


def _page():
    if not os.path.isfile(PAGE):
        return None
    return io.open(PAGE, encoding="utf-8").read().encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "RawahilWorkshop/1.0"
    protocol_version = "HTTP/1.1"

    # ── أدوات الردّ ──────────────────────────────────────────────────
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        # الصفحة لا تحمّل شيئاً من الخارج — والسياسة تقول ذلك للمتصفح أيضاً
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; script-src 'unsafe-inline'; "
                         "style-src 'unsafe-inline'; connect-src 'self'")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _404(self):
        self._json(404, {"error": "مسار غير معروف — للخادم مساران لا ثالث"})

    # ── المساران ────────────────────────────────────────────────────
    def do_GET(self):                                    # noqa: N802
        if self.path.split("?")[0] not in ("/", "/index.html"):
            return self._404()
        body = _page()
        if body is None:
            return self._json(503, {"error": "Workshop.html غير مبنيّة — "
                                             "شغّل build_workshop_html.py"})
        self._send(200, body, "text/html; charset=utf-8")

    def do_POST(self):                                   # noqa: N802
        if self.path.split("?")[0] != "/submit":
            return self._404()
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._json(400, {"error": "طول الحمولة غير مقروء"})
        if length <= 0:
            return self._json(400, {"error": "حمولة فارغة"})
        if length > MAX_BODY:
            return self._json(413, {"error": "حمولة تتجاوز الحدّ المعلَن"})
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            return self._json(400, {"error": "حمولة ليست JSON صالحاً: " + str(e)[:80]})
        try:
            result = WS.accept(payload)
        except WS.WorkshopError as e:
            # يُردّ بحكمه ولا يُخزَّن — والردّ يقول السبب لا يُخفيه
            self.log_message("مردود: %s", str(e)[:120])
            return self._json(400, {"error": str(e)})
        self.log_message("مقبول: %s", result["code"])
        self._json(200, {"ok": True, "code": result["code"],
                         "record_sha": result["record_sha"]})

    def log_message(self, fmt, *args):
        # سجلٌّ بلا حمولة: لا تمرّ نصوص التقارير في سجلّ الطرفية
        sys.stderr.write("· " + (fmt % args) + "\n")


def serve(host="127.0.0.1", port=8787):
    httpd = ThreadingHTTPServer((host, port), Handler)
    return httpd


def main(argv):
    host, port = "127.0.0.1", 8787
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--help"):
            print(__doc__.strip())
            print("\n  python3 workshop_server.py [--port 8787] [--host 0.0.0.0]")
            return 2
        if a == "--port":
            i += 1; port = int(argv[i])
        elif a == "--host":
            i += 1; host = argv[i]
        else:
            print("❌ خيار غير معروف: " + a); return 2
        i += 1

    if not os.path.isfile(PAGE):
        print("❌ Workshop.html غائبة — شغّل: python3 build_workshop_html.py")
        return 1
    if host not in ("127.0.0.1", "localhost", "::1"):
        print("⚠️  الخادم مفتوحٌ على الشبكة (" + host + ") — كلُّ من يبلغه "
              "يستطيع الإرسال إليه.\n"
              "   وبوابة القبول تبقى أداة المشرف والرمز المُصدَر، "
              "لا كلمةَ مرور.")
    httpd = serve(host, port)
    print(f"✅ مسار الورشة يعمل: http://{host}:{port}/")
    print(f"   المخزن: {os.path.basename(WS.STORE_DIR)}/ — خارج المستودع (DEC-277)")
    print("   الإيقاف: Ctrl+C")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n· أوقِف.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
