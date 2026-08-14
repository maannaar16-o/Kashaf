# -*- coding: utf-8 -*-
"""
team_report.py — باني تقرير تركيب الفريق (`56-TEAM-00 §2` — تسعة أقسام)
=========================================================================
سند: `DEC-277` (تشغيل الميثاق) · `DEC-278` (هذا الباني)

**التقرير عرضٌ لخلايا مختومة تحت عناوين مختومة — لا سردَ فيه.** كل جملةٍ
تخرج منه موجودةٌ حرفياً في جدولٍ من `51-MATRIX-01/02/03/04` أو في نصّ
`56-TEAM-00` أو `APPENDIX-B`. **ولا نصّ رابط مؤلَّف**: القراءة السردية شأن
المدرّب لا شأن الأداة (`§4`: صفر توليد · `G4`: إنذار بنيوي لا حكم كفاءة).

والأقفال الخمسة مطبَّقة لا مذكورة:
  · صفر مقارنة تفاضلية — لا ترتيب أعضاء ولا لغة «أعلى/أضعف»
  · صفر كشف خام — لا `SP` في المتن، الرموز الوصفية وحدها
  · صفر توليد — كل خلية من الحزمة
  · قفل العرض `G4` — يُطبع نصّه في القسم التاسع
  · صفر لمس `K1`/`K3`/`K4` — المحرّك يرفض أي حقلٍ من خارج عدسات $K_2$
"""
import hashlib
import json

from team_engine import ContentPack, LENSES, run

AR_NUM = "١٢٣٤٥٦٧٨٩"
STATE_AR = {"D": "مهيمن", "M": "مساند", "L": "نقطة عمى"}   # `DEC-041`


def _cells(row):
    return "| " + " | ".join(row) + " |"


def build_report(members, pack: ContentPack = None):
    pack = (pack or ContentPack()).require()
    res = run(members, content=pack)
    a, P = res["audit"], pack.raw
    L, n = [], 0

    def head(key):
        nonlocal n
        n += 1
        L.append(f"## {AR_NUM[n - 1]} · {P['heading'][str(n)]}")
        L.append("")

    # الرأس — التنبيه الإلزامي أولاً (`APPENDIX-B §4/4`)
    L += [f"> ⚠️ {P['banner']}", ""]
    for t in P["tag"]:
        L.append(f"> وسم إلزامي: [{t}]")
    L.append("")

    # ① قائمة الأعضاء
    head("1")
    L += [_cells(["العضو", "مهيمن", "مساند", "نقطة عمى"]),
          _cells([":---", ":---", ":---", ":---"])]
    for m in res["members"]:
        pr = m["profile"]
        fmt = lambda ds: " · ".join(f"{d} ({pr['band'][d]})" for d in ds) or "—"
        L += [_cells([m["code"], fmt(pr["dominant"]), fmt(pr["support"]),
                      " · ".join(pr["blind"]) or "—"])]
    L.append("")

    # ② خريطة التغطية العدسية
    head("2")
    L += [_cells(["البُعد", "مهيمن", "مساند", "المستوى"]),
          _cells([":---", ":---", ":---", ":---"])]
    for d in LENSES:
        c = a["coverage"][d]
        lvl = {"led": "مغطّى بقيادة", "support_only": "⚠️ بلا مهيمن جماعياً",
               "absent": "⚠️ غائب"}[c["level"]]
        L += [_cells([f"**{d}** {P['blind'][d]['name']}",
                      " · ".join(c["dominant"]) or "—",
                      " · ".join(c["support"]) or "—", lvl])]
    L.append("")

    # ③ العمى الجماعي المتراكم
    head("3")
    cb = a["collective_blind"]
    L += [_cells(["البُعد بلا مهيمن", "نقطة العمى الكبرى", "ما يغيب عن العدسة"]),
          _cells([":---", ":---", ":---"])]
    for d in cb["uncovered"]:
        b = P["blind"][d]
        L += [_cells([f"**{d}** {b['name']}", b["major"], b["missing"]])]
    L.append("")
    if cb["documented"]:
        L += [_cells(["تركيبة موثَّقة", "العمى الجماعي المتراكم",
                      "البُعد الغائب المطلوب", "الخطورة"]),
              _cells([":---", ":---", ":---", ":---"])]
        for c in cb["documented"]:
            L += [_cells([" + ".join(c["lenses"]), c["blind"], c["need"],
                          c["risk"]])]
        L.append("")

    # ④ مفارقة القطبية — تُعرض بحقائقها لا بحكمٍ عليها
    head("4")
    L += [_cells(["المقياس", "القيمة"]), _cells([":---", ":---"]),
          _cells(["أبعاد يقودها مهيمن", str(len([d for d in LENSES
                                                 if a["coverage"][d]["dominant"]]))]),
          _cells(["أبعاد بلا مهيمن", " · ".join(cb["uncovered"]) or "—"]),
          _cells(["أزواج قطبية بين الأعضاء", str(len(a["inter_polarity"]))]), ""]

    # ⑤ مصفوفة الأزواج
    head("5")
    L += [_cells(["الزوج", "التقاطع", "محور الصدام", "بروتوكول الاحتواء",
                  "الكيان الهجين", "العمى المشترك"]),
          _cells([":---"] * 6)]
    for pr in a["pairs"]:
        if not pr.get("dyad"):
            # الخلوّ يُعلَن بعدستيه لا بشرطةٍ صمّاء: تقاطعٌ على العدسة نفسها
            # لا خليةَ مختومةً له في `51-MATRIX-01` — **قاعدةٌ دائمة بختم
            # المالك** (`DEC-281`). ولا جملةَ ربطٍ تُكتب هنا: الرمزان
            # مختومان والباقي شرطات.
            cross = (f"{pr['lens_a']}–{pr['lens_b']}"
                     if pr.get("lens_a") and pr.get("lens_b") else "—")
            L += [_cells([f"{pr['a']} × {pr['b']}", cross, "—", "—", "—", "—"])]
            continue
        d = P["dyad"][pr["dyad"]]
        L += [_cells([f"**{pr['a']} × {pr['b']}**",
                      f"{pr['lens_a']}–{pr['lens_b']}",
                      d["clash"], d["containment"], d["hybrid"], d["blind"]])]
    L.append("")

    # ⑥ القطبية بين شخصين
    head("6")
    if a["inter_polarity"]:
        L += [_cells(["الزوج البيني", "الطرف الأول", "الطرف الثاني",
                      "محور التعامد", "فلترة الطرف الأول", "فلترة الطرف الثاني"]),
              _cells([":---"] * 6)]
        for ip in a["inter_polarity"]:
            pol = next(p for p in P["polar"] if p["code"] == ip["polar"])
            fa, fb = ((pol["filter_a"], pol["filter_b"])
                      if pol["a"] == ip["lens_a"]
                      else (pol["filter_b"], pol["filter_a"]))
            L += [_cells([f"{ip['a']} ↔ {ip['b']}",
                          f"{ip['lens_a']} ({ip['a']})",
                          f"{ip['lens_b']} ({ip['b']})", pol["axis"], fa, fb])]
    else:
        L += ["—"]
    L.append("")

    # ⑦ سلاسل الارتداد المتزامنة
    head("7")
    L += [_cells(["العضو", "العدسة", "مُطلِق الارتداد", "نمط الانهيار الداخلي"]),
          _cells([":---"] * 4)]
    for rb in a["rebound"]:
        if not rb["has_path"]:
            L += [_cells([rb["code"], "—", "—", "—"])]
            continue
        r = P["rebound"][rb["lens"]]
        L += [_cells([rb["code"], f"**{rb['lens']}** {r['name']}",
                      r["trigger"], r["pattern"]])]
    L.append("")

    # ⑧ توصية التشكيل
    head("8")
    rec = a["recommendation"]
    if rec["gap"]:
        L += [_cells(["البُعد الغائب", "نقطة العمى الكبرى", "ما يغيب عن العدسة"]),
              _cells([":---", ":---", ":---"])]
        for d in rec["gap"]:
            b = P["blind"][d]
            L += [_cells([f"**{d}** {b['name']}", b["major"], b["missing"]])]
    else:
        L += ["—"]
    L.append("")

    # ⑨ قفل العرض — نصّ الميثاق حرفياً
    head("9")
    for lock in P["lock"]:
        L.append(f"- {lock}")
    L.append("")

    body = "\n".join(L)
    out = dict(a)
    out["sections_rendered"] = n
    out["pack_sha"] = {"CONTENT_TEAM": hashlib.sha256(
        json.dumps(P, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":")).encode("utf-8")).hexdigest()[:16]}
    out["report_sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    return body, out


if __name__ == "__main__":
    demo = [{"code": "T-01", "sp": {"A": 92, "C": 78, "O": 62, "R": 40,
                                    "S": 35, "E": 30, "St": 28, "H": 25}},
            {"code": "T-02", "sp": {"E": 95, "S": 88, "R": 60, "A": 40,
                                    "O": 35, "C": 30, "St": 28, "H": 25}},
            {"code": "T-03", "sp": {"H": 90, "St": 80, "A": 60, "R": 40,
                                    "O": 35, "C": 30, "S": 28, "E": 25}}]
    txt, _a = build_report(demo)
    print(txt)
