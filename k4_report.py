# -*- coding: utf-8 -*-
"""
k4_report.py — مُركِّب تقرير دائرة الإنجاز (K4)
================================================
عقد التقرير مختوم في `136-K4-ENGINE §3` (`DEC-266`).

قواعد العرض النافذة:
  ر-1  ترقيم المعروض فعلاً — لا يقفز عند غياب قسم شرطي
  ر-2  صفر رقم أو نسبة في أي عنوان أو متن (حارسا `ح-4`/`ح-5`)
  ر-3  التحفّظ **كتلة واحدة موحَّدة** مهما تعدّدت الصمامات (`DEC-090` قياساً)
  ر-4  المحطة الأدنى تُعرض بكامل المتعادلين — لا كسر تعادل (`DEC-150`)
  ر-5  عند `OUT` يُصدَّر **تقرير فجوة**: لا نمط ولا قراءة مسار فوق النقص

🔒 يجمّع ولا يؤلّف: كل سطر من `k4_contentpack.json` أو من المحرك.
توأمه الحرفي: `K4Report` في `reports.js`.
"""
import hashlib
import json

from k4_engine import run, band, VALVES, USER_NAME, RESERVE_CODE
from k4_content import ContentPack
from sp_gate import output_gate            # ح-4 · ح-5 · DEC-183

AR_NUM = "١٢٣٤٥٦٧٨٩"


def build_report(sp, pack: ContentPack = None):
    pack = (pack or ContentPack()).require()
    res = run(sp, content=pack)
    a = res.audit
    L, n = [], 0

    def head(key):
        """ر-1: ترقيم متسلسل للمعروض فعلاً."""
        nonlocal n
        n += 1
        L.append(f"## {AR_NUM[n - 1]} · {pack.raw['heading'][key]}")
        L.append("")

    # ⓪ إخطار الفجوة — ر-5 (قبل كل شيء، ويمنع ما بعده من قراءات المسار)
    if a["gap_report"]:
        L += ["> ⚠️ " + pack.raw["notice"]["gap"], ""]

    # ① لوحة المحطات
    head("panel")
    L += [pack.raw["notice"]["order"], ""]
    for v in VALVES:
        b = a["bands"][v]
        L += [f"### {USER_NAME[v]} — {pack.band_label(b)}", "",
              pack.valve(v, "U01"), ""]
        if b in ("core", "high"):
            L += [pack.valve(v, "U03"), ""]
        elif b == "limited":
            L += [pack.valve(v, "U04"), ""]
        # OUT: لا نص حالة — الوعاء لا يُصنَّف (ر-5)

    # ② مواضع الانقطاع
    pts = a["interruption_points"]
    if pts:
        head("interruption")
        for v in pts:
            L += [f"**{USER_NAME[v]}** — " + pack.valve(v, "U05"), ""]

    # ③ المحطة الأدنى — ر-4
    bn = a["bottleneck"]
    if bn["valves"]:
        head("bottleneck")
        if bn["tie"]:
            L += ["> " + pack.raw["notice"]["tie"], ""]
        names = "، ".join(USER_NAME[v] for v in bn["valves"])
        L += [f"**{names}** — {pack.band_label(bn['band'])}", ""]
        if all(c["reading"] == "وصف موضع" for c in a["choke_readings"]):
            L += [pack.raw["notice"]["choke_plain"], ""]

    # ④ الشبكة — القيود المفعَّلة
    if a["constraint_map"]:
        head("network")
        for c in a["constraint_map"]:
            arrow = "×" if c["mutual"] else "←"
            L += [f"- **{c['kind']}** · {USER_NAME[c['a']]} {arrow} {USER_NAME[c['b']]}"]
        L.append("")

    # ⑤ تحفّظ القراءة — ر-3: كتلة واحدة موحَّدة
    inv = {code: v for v, code in RESERVE_CODE.items()}
    if a["reading_reserve"]:
        head("reserve")
        L += [pack.reserve_opening(), ""]
        for code in a["reading_reserve"]:
            v = inv[code]
            L += [f"- **{USER_NAME[v]}** — " + pack.reserve(v)]
        L.append("")

    # ⑥ أسئلة الفرز
    if a["lookalike_flags"]:
        head("lookalike")
        L += [pack.raw["notice"]["lookalike_lead"], ""]
        for code in a["lookalike_flags"]:
            L += ["- " + pack.lookalike(code)]
        L.append("")

    # ⑦ التدريبات — لمحطات الانقطاع حصراً · والفراغ يُصرَّح لا يُملأ
    if pts:
        head("training")
        L += [pack.raw["notice"]["training_lead"], ""]
        for v in pts:
            t = pack.training(v)
            if t is None:
                L += [f"- **{USER_NAME[v]}** — " + pack.training_void(v)]
            else:
                L += [f"- **{USER_NAME[v]}** — " + t]
        L.append("")

    # ⑧ بصمة القراءة
    head("audit")
    L += ["```", json.dumps(a, ensure_ascii=False, sort_keys=True, indent=1), "```"]

    a = dict(a)
    a["sections_rendered"] = n
    _sha = lambda o: hashlib.sha256(
        json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        .encode("utf-8")).hexdigest()[:16]
    a["pack_sha"] = {"CONTENT_K4": _sha(pack.raw)}
    body = "\n".join(L)
    a["report_sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    output_gate(body, "تقرير K4")       # ح-4/ح-5 — يوقف الإصدار عند التسرّب
    return body, a


if __name__ == "__main__":
    txt, _ = build_report(dict(WM=62, TI=78, F=74, PF=38, OR=55, TM=41, PER=44))
    print(txt)
