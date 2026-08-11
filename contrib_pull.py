# -*- coding: utf-8 -*-
"""
contrib_pull.py — ساحبة الإسهامات (`DEC-254` · `CHG-072`)
==========================================================
تفرّغ مخزن قناة الإسهام (Cloudflare KV) وتتحقق من كل سجل ضد مواصفة
`RAWAHIL-CONTRIB-v1` حرفياً. السجل المخالف يُعزل في ملف شواذ ويُبلَّغ —
لا يُصلَح صمتاً ولا يُسقَط صمتاً.

الاعتماد: متغيرات بيئة على جهاز المالك — **لا تودَع أبداً**:
  CF_API_TOKEN         مفتاح بصلاحية قراءة KV فقط
  CF_ACCOUNT_ID        معرّف الحساب
  CF_KV_NAMESPACE_ID   معرّف الـnamespace
  CF_API_BASE          (اختياري — للاختبار المحلي فقط)

الناتج: contrib_batch.json (دفعة موسومة بالبصمة) + contrib_anomalies.json إن وُجدت شواذ.
كلاهما محلي لا يودَع (البيانات الميدانية ليست وثيقة معرفة).
"""
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
BATCH = os.path.join(HERE, "contrib_batch.json")
ANOM = os.path.join(HERE, "contrib_anomalies.json")


# ── التحقق — مطابق حرفياً لمنطق المستقبِل (site/contrib-receiver/worker.js) ──
def validate(p):
    if not isinstance(p, dict) or p.get("schema") != "RAWAHIL-CONTRIB-v1":
        return "schema"
    inst = p.get("instrument")
    if not isinstance(inst, dict) or inst.get("measure") != "40-MEASURE v5.0":
        return "instrument"
    sub = p.get("submitted")
    if not isinstance(sub, str) or len(sub) != 7 or sub[4] != "-":
        return "submitted"
    a = p.get("answers")
    if not isinstance(a, dict) or len(a) != 94:
        return "answers"
    for n in range(1, 95):
        r = a.get(str(n))
        if not isinstance(r, dict):
            return f"missing:{n}"
        if r.get("choice") not in ("a", "b"):
            return f"choice:{n}"
        for k in ("ratingA", "ratingB"):
            v = r.get(k)
            if not isinstance(v, int) or isinstance(v, bool) or not (1 <= v <= 6):
                return f"{k}:{n}"
        if len(r) != 3:
            return f"extra:{n}"
    if len(p) != 4:
        return "extra-top"
    return None


def die(msg):
    raise SystemExit(f"❌ {msg}")


def token_safety_scan(token):
    """يرفض العمل لو وُجد المفتاح داخل أي ملف بالمستودع — عهد `126-HARVEST`."""
    for root, dirs, files in os.walk(HERE):
        dirs[:] = [d for d in dirs if d not in (".git", "docs", "__pycache__")]
        for fn in files:
            if not fn.endswith((".py", ".json", ".md", ".js", ".html", ".css", ".txt")):
                continue
            try:
                txt = open(os.path.join(root, fn), encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            if token in txt:
                die(f"مفتاح الوصول موجود داخل ملف بالمستودع: {fn} — أزل الملف وبدّل المفتاح فوراً")


def api(base, token, path, params=None):
    url = base + path + (("?" + urllib.parse.urlencode(params)) if params else "")
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def main():
    token = os.environ.get("CF_API_TOKEN")
    account = os.environ.get("CF_ACCOUNT_ID")
    ns = os.environ.get("CF_KV_NAMESPACE_ID")
    base = os.environ.get("CF_API_BASE", "https://api.cloudflare.com")
    if not (token and account and ns):
        die("متغيرات البيئة ناقصة — المطلوب: CF_API_TOKEN و CF_ACCOUNT_ID و CF_KV_NAMESPACE_ID")
    token_safety_scan(token)

    prefix = f"/client/v4/accounts/{account}/storage/kv/namespaces/{ns}"

    # ① جرد المفاتيح — ترقيماً بالمؤشر
    keys, cursor = [], None
    while True:
        params = {"limit": 1000}
        if cursor:
            params["cursor"] = cursor
        data = json.loads(api(base, token, prefix + "/keys", params))
        if not data.get("success"):
            die(f"واجهة المخزن رفضت جرد المفاتيح: {data.get('errors')}")
        keys += [k["name"] for k in data.get("result", [])]
        cursor = (data.get("result_info") or {}).get("cursor")
        if not cursor:
            break

    # ② سحب كل سجل والتحقق منه
    records, anomalies = [], []
    for key in keys:
        raw = api(base, token, prefix + "/values/" + urllib.parse.quote(key))
        try:
            payload = json.loads(raw)
        except ValueError:
            anomalies.append({"key": key, "error": "json", "raw": raw[:500]})
            continue
        err = validate(payload)
        if err:
            anomalies.append({"key": key, "error": err, "raw": payload})
        else:
            records.append({"key": key, "payload": payload})

    # ③ الدفعة الموسومة
    records.sort(key=lambda r: r["key"])
    body = {
        "schema": "RAWAHIL-CONTRIB-BATCH-v1",
        "pulled_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(records),
        "records": records,
    }
    canon = json.dumps(body["records"], ensure_ascii=False, sort_keys=True)
    body["fingerprint"] = hashlib.sha256(canon.encode()).hexdigest()[:16]
    with open(BATCH, "w", encoding="utf-8") as f:
        json.dump(body, f, ensure_ascii=False, indent=1)

    if anomalies:
        with open(ANOM, "w", encoding="utf-8") as f:
            json.dump(anomalies, f, ensure_ascii=False, indent=1)

    print(f"سُحب {len(keys)} مفتاحاً · سليمة {len(records)} · شواذ {len(anomalies)}"
          + (f" (معزولة في {os.path.basename(ANOM)})" if anomalies else ""))
    print(f"الدفعة: {os.path.basename(BATCH)} · البصمة {body['fingerprint']}")
    return 1 if anomalies else 0


if __name__ == "__main__":
    raise SystemExit(main())
