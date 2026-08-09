# -*- coding: utf-8 -*-
"""
parity_messages.py — تكافؤ **رسائل الاستثناءات** بين النسختين
================================================================
سند: `DEC-199` (تكافؤ النسخ) · `DEC-235` (توحيد الرسائل) · `GAP-MSG-PARITY-01`

الفراغ الذي يسدّه: `parity_py` يقارن **اسم الاستثناء وحده**
(`type(e).__name__`)، فبقي **نصّ الرسالة** خارج كل قياس. هذا الملف
يقيسه: يستثير كل مسار خطأ في الطرفين ويقارن **الاسم والنصّ معاً**.

قياسٌ واحد (`ن-7/②`): تطابق نصّ الرسالة المُصيَّرة. لا يقيس المنطق ولا
النصّ العادي — لهما مقياساهما.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import k2_engine as E2
import k3_engine as E3

SP8 = {"A": 33.3, "R": 30.3, "C": 27.3, "O": 24.2,
       "S": 21.2, "E": 18.2, "St": 15.2, "H": 12.1}

# كل مسار خطأ **محروس** يُستثار في الطرفين بالمُدخل نفسه.
# النطاق: الاستثناءات **المعلَنة** (`InputContractError` وأخواتها).
# أخطاء اللغة الأصلية من مسارات غير محروسة خارج هذا القياس — لها
# تقرير فجوة مستقلّ (`GAP-CONTRACT-01`).
TRIGGERS = [
    {"id": "k2/ssp y+z=6",  "fn": "ssp2", "args": [30, 4, 2]},
    {"id": "k2/ssp y+z=8",  "fn": "ssp2", "args": [30, 5, 3]},
    {"id": "k2/ssp y+z=0",  "fn": "ssp2", "args": [0, 0, 0]},
    {"id": "k3/ssp y+z=10", "fn": "ssp3", "args": [40, 6, 4]},
    {"id": "k3/ssp y+z=12", "fn": "ssp3", "args": [40, 7, 5]},
    # عشريات: بايثون تُصيّر 4.0 وJS تُصيّر 4 — تباعد كامن يُقاس لا يُفترض
    {"id": "k2/ssp عشري",  "fn": "ssp2", "args": [30, 4.0, 2.0]},
    {"id": "k3/ssp عشري",  "fn": "ssp3", "args": [40, 6.5, 4.0]},
    {"id": "k2/ssp سالب",  "fn": "ssp2", "args": [30, -1, 3]},
    {"id": "k2/no-input",   "fn": "run2", "sp": None, "raw": None},
    {"id": "k2/dims-few",   "fn": "run2", "sp": {"A": 33.3, "R": 30.3}},
    {"id": "k2/dims-extra", "fn": "run2",
     "sp": dict(list(SP8.items()) + [("Z", 1.0)])},
    {"id": "k2/dims-renamed", "fn": "run2",
     "sp": {k if k != "H" else "Hh": v for k, v in SP8.items()}},
    # DEC-240 — بوابة `strict` في K3 صارت متماثلة؛ تُقاس رسالتها ونوعها
    {"id": "k3/strict فراغ",  "fn": "strict3", "missing": []},
    {"id": "k3/strict واحد",  "fn": "strict3", "missing": ["covenant_opening"]},
    {"id": "k3/strict عدّة",  "fn": "strict3",
     "missing": ["covenant_opening", "circle_map_shared", "trust_banner"]},
]

def py_call(t):
    try:
        f = t["fn"]
        if f == "ssp2":
            E2.compute_ss_sp(*t["args"])
        elif f == "ssp3":
            E3.compute_ss_sp(*t["args"])
        elif f == "run2":
            E2.run(sp=t.get("sp"), raw=t.get("raw"))
        elif f == "strict3":
            # `ContentPack` حقيقية — المحرّك يستدعي أكثر من `missing()`،
            # والبديل المصطنع أعطى `AttributeError` بدل بوابة `strict`.
            import k3_content as C3, k3_contentpack as CP3
            full = CP3.build()
            ext = {k: v for k, v in full.items() if k not in t["missing"]}
            E3.run({s: 60.0 for s in E3.SKILLS},
                   content=C3.ContentPack(external=ext), strict=True)
    except Exception as e:
        return [type(e).__name__, str(e)]
    return ["<لا استثناء>", ""]


NODE = r"""
const E = require("./engines.js");
const trig = JSON.parse(process.argv[1]);
console.log(JSON.stringify(trig.map(t => {
  try {
    if (t.fn === "ssp2") E.K2.computeSsSp.apply(null, t.args);
    else if (t.fn === "ssp3") E.K3.computeSsSp.apply(null, t.args);
    else if (t.fn === "run2") E.K2.run({ sp: t.sp === undefined ? null : t.sp,
                                         raw: t.raw === undefined ? null : t.raw });
    else if (t.fn === "strict3") {
      const sp = {}; for (const s of E.K3.SKILLS) sp[s] = 60.0;
      E.K3.run(sp, null, null, { content: { missing: () => t.missing }, strict: true });
    }
  } catch (e) { return [e.name || "Error", String(e.message)]; }
  return ["<لا استثناء>", ""];
})));
"""


def main():
    p = os.path.join(HERE, "_trig.json")
    json.dump(TRIGGERS, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    r = subprocess.run(["node", "-e", NODE, json.dumps(TRIGGERS, ensure_ascii=False)],
                       capture_output=True, text=True, cwd=HERE)
    os.remove(p)
    if r.returncode != 0:
        print("❌ تعذّر تشغيل جانب JS:\n" + (r.stderr[:800] or r.stdout[:800]))
        return 1
    js = json.loads(r.stdout)

    bad_name, bad_msg, silent = [], [], []
    for t, j in zip(TRIGGERS, js):
        pn, pm = py_call(t)
        jn, jm = j
        # اتّفاق الطرفين على عدم الرفع اتّفاقٌ لا تباعد — يغطّي الفرع
        # السالب للبوابة. التباعد أن يرفع أحدهما دون الآخر.
        if pn == "<لا استثناء>" and jn == "<لا استثناء>":
            continue
        if pn == "<لا استثناء>" or jn == "<لا استثناء>":
            silent.append((t["id"], pn, jn))
            continue
        if pn != jn:
            bad_name.append((t["id"], pn, jn))
        if pm != jm:
            bad_msg.append((t["id"], pm, jm))

    print(f"مسارات خطأ مستثارة: {len(TRIGGERS)}")
    print("-" * 76)
    if silent:
        print(f"❌ مسار لم يرفع استثناءً في أحد الطرفين — {len(silent)}")
        for i, a, b in silent:
            print(f"   [{i}] بايثون={a} · JS={b}")
    if bad_name:
        print(f"❌ اسم الاستثناء متباعد — {len(bad_name)}")
        for i, a, b in bad_name:
            print(f"   [{i}]\n     بايثون: {a}\n     JS    : {b}")
    if bad_msg:
        print(f"❌ نصّ الرسالة متباعد — {len(bad_msg)}")
        for i, a, b in bad_msg:
            print(f"   [{i}]\n     بايثون: {a}\n     JS    : {b}")
    if silent or bad_name or bad_msg:
        print("\nيُجمَّد الطرفان (`DEC-200`) — لا يُرجَّح أحدهما.")
        return 1
    print(f"✅ تكافؤ تامّ — {len(TRIGGERS)} مسار · الاسم والنصّ متطابقان")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
