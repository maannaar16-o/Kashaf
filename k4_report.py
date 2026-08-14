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


def fill_pair(tpl, a, b):
    """تعبئة قالب الطرفين — **صريحة عمداً** (`ن-8`): البديل يشمل **كل**
    المواضع. الاتّكال على `replace` الضمني أنتج تباعداً حقيقياً — فـJS
    يبدّل أول موضع فقط وبايثون يبدّل الكلّ (رُصد ببناء `DEC-268`)."""
    return tpl.replace("{أ}", a).replace("{ب}", b)


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

    # ⓪ وسم الاشتقاق للقارئ — `DEC-283`: **مرّةً واحدة في الصدر**، وقبل
    # إخطار الفجوة لأنه يصف التقرير كلّه ولا يحمل قراءةً يسبقها `ر-5`.
    L += ["> " + pack.raw["notice"]["derivation"], ""]

    # ⓪ إخطار الفجوة — ر-5 (يمنع ما بعده من قراءات المسار)
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

    # ② مواضع الانقطاع — مُثرىً بالسطح المركَّب (`138 §3/②`)
    pts = a["interruption_points"]
    C = pack.raw["composed"]
    if pts:
        head("interruption")
        if len(pts) > 1:
            L += [C["interruption_multi"], ""]
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
        L += [C["bottleneck_meaning"], ""]
        if bn["tie"]:
            L += [C["bottleneck_tie"], ""]
        if all(c["reading"] == "وصف موضع" for c in a["choke_readings"]):
            L += [pack.raw["notice"]["choke_plain"], ""]

    # ④ الشبكة والأنماط — مُثرىً بالسطح المركَّب (`138 §3/②-③`)
    if a["constraint_map"] or a["patterns_recognized"]:
        head("network")
        if a["constraint_map"]:
            L += [C["network_lead"], ""]
            for c in a["constraint_map"]:
                arrow = "×" if c["mutual"] else "←"
                L += [f"- **{c['kind']}** · {USER_NAME[c['a']]} {arrow} {USER_NAME[c['b']]}"]
                L += ["  " + fill_pair(pack.composed_kind(c["kind"]),
                                       USER_NAME[c["a"]], USER_NAME[c["b"]])]
            L += ["", C["network_limit"], ""]
        # الأنماط داخل القسم نفسه — لا قسم ثالث (`138 §3/③`)
        if a["patterns_recognized"]:
            for code in a["patterns_recognized"]:
                L += ["- " + pack.composed_pattern(code)]
            L += ["", C["pattern_limit"], ""]

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


# --------------------------------------------------------------------------- #
# سطح القراءة العابرة — **مخرج مستقل** (`138 §2` · `133 §3/①`)
# --------------------------------------------------------------------------- #
# مشغِّله نطاقات $K_4$ وحدها — لا يدخله رقم ولا نطاق من دائرة أخرى (العزل مصان).
CROSSING_TRIGGERS = [
    ("K4-XR-02", ("TI",)),
    ("K4-XR-05", ("TI",)),
    ("K4-XR-06", ("TI",)),
    ("K4-XR-04", ("PER",)),
    ("K4-XR-08", ("OR", "TM", "PF")),
]


def crossing_entries(sp):
    """القيود المستحقة للعرض — و`K4-XR-03` يتصدَّر متى ظهر السطح."""
    out = []
    for code, valves in CROSSING_TRIGGERS:
        if any(band(sp[v]) == "limited" for v in valves):
            out.append(code)
    return (["K4-XR-03"] + out) if out else []


def build_crossing_surface(sp, pack: ContentPack = None):
    """يُصدَر **مستقلاً** — ولا يُستدعى من `build_report` أبداً."""
    pack = (pack or ContentPack()).require()
    codes = crossing_entries(sp)
    if not codes:
        return "", {"surface": "crossing", "entries": [], "rendered": False}
    cr = pack.raw["crossing"]
    L = [f"# {cr['heading']}", "", cr["lead"], ""]
    for code in codes:
        L += ["- " + pack.crossing(code)]
    L += ["", cr["closing"]]
    body = "\n".join(L)
    output_gate(body, "سطح القراءة العابرة K4")
    audit = {"surface": "crossing", "entries": codes, "rendered": True,
             "spec_version": "138-K4-SURFACES v1.0"}
    audit["surface_sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    return body, audit


if __name__ == "__main__":
    txt, _ = build_report(dict(WM=62, TI=78, F=74, PF=38, OR=55, TM=41, PER=44))
    print(txt)
