# -*- coding: utf-8 -*-
"""
build_team_pack.py — استخراج حزمة محتوى تقرير الفريق **بصفر تأليف**
====================================================================
سند: `DEC-277` (تشغيل `56-TEAM-00`) · `DEC-039` (اعتماد المصفوفات السبع)

**لا يكتب هذا المولّد جملةً واحدة.** يفكّ الجداول المختومة ويعيد صفّها:
  · `51-MATRIX-01 §2`  → 28 زوجاً (صدام · احتواء · كيان هجين · عمى مشترك)
  · `51-MATRIX-02 §1.1` → الأزواج القطبية الخمسة
  · `51-MATRIX-04 §1`  → نقطة العمى الكبرى لكل بُعد وما يغيب عن عدسته
  · `51-MATRIX-03 §1`  → مصفوفة الارتداد الداخلي تحت الضغط
  · `56-TEAM-00 §2/§4` → عناوين الأقسام التسعة وأقفال العرض

والضمانة ليست هنا بل في `test_report_team.py`: **كل نصّ في الحزمة يُطابَق
حرفياً بمصدره** — فنصٌّ بلا مصدر يوقف الإصدار.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "team_contentpack.json")

SRC = {
    "dyad":    "51-MATRIX-01_Full_Dyadic.md",
    "polar":   "51-MATRIX-02_Polar_Pairs.md",
    "blind":   "51-MATRIX-04_Shared_Blindspots.md",
    "rebound": "51-MATRIX-03_Fallback_Map.md",
    "charter": "56-TEAM-00_Team_Composition_Protocol_Charter.md",
    "leader":  "56-REPORT-ENGINE-APPENDIX-B_Leader_Mode_Conversion_Rule.md",
}
LENSES = ["A", "R", "C", "O", "S", "E", "St", "H"]


def read(name):
    return io.open(os.path.join(HERE, name), encoding="utf-8").read()


def cell(x):
    return x.strip()


def dyads(text):
    rows = re.findall(
        r"^\| (\d{2}) \| \*\*([A-Za-z]+)–([A-Za-z]+)\*\* \| ([^|]*) \| ([^|]*) \| "
        r"([^|]*) \| ([^|]*) \| ([^|]*) \|$", text, re.M)
    out = {}
    for num, a, b, polar, clash, contain, hybrid, blind in rows:
        out[f"{a}–{b}"] = {"n": num, "polar": cell(polar), "clash": cell(clash),
                           "containment": cell(contain), "hybrid": cell(hybrid),
                           "blind": cell(blind)}
    if len(out) != 28:
        sys.exit(f"❌ أزواج `51-MATRIX-01`: {len(out)} بدل 28")
    return out


def polars(text):
    rows = re.findall(
        r"^\| (P\d) \| \*\*([A-Za-z]+) ↔ ([A-Za-z]+)\*\* \| ([^|]*) \| ([^|]*) \| "
        r"([^|]*) \| ([^|]*) \|$", text, re.M)
    out = [{"code": c, "a": a, "b": b, "axis": cell(ax),
            "filter_a": cell(f1), "filter_b": cell(f2)}
           for c, a, b, ax, f1, f2, _src in rows]
    if len(out) != 5:
        sys.exit(f"❌ أزواج قطبية: {len(out)} بدل 5")
    return out


def blinds(text):
    rows = re.findall(r"^\| \*\*([A-Za-z]+)\*\* (\S+) \| ([^|]*) \| ([^|]*) \|$",
                      text, re.M)
    out = {c: {"name": cell(n), "major": cell(mj), "missing": cell(ms)}
           for c, n, mj, ms in rows if c in LENSES}
    if len(out) != 8:
        sys.exit(f"❌ نقاط عمى: {len(out)} بدل 8")
    return out


def rebounds(text):
    rows = re.findall(r"^\| \*\*([A-Za-z]+)\*\* (\S+) \| ([^|]*) \| ([^|]*) \| ([^|]*) \|$",
                      text, re.M)
    out = {c: {"name": cell(n), "trigger": cell(tr), "pattern": cell(pt)}
           for c, n, tr, pt, _fast in rows if c in LENSES}
    if len(out) != 8:
        sys.exit(f"❌ مسارات ارتداد: {len(out)} بدل 8")
    return out


def combos(text):
    """`51-MATRIX-04 §2.1` — ستّ تركيبات موثّقة عالية الخطورة.
    قاعدة الحساب في `§2`: عمى الفريق = **المشترك بين أبعاده المهيمنة جميعاً**؛
    وهذه الستّ **حالاتٌ موصوفة نصّاً** تُستدعى حرفياً عند انطباقها."""
    sec = re.search(r"^## 2\.1 .*?(?=^\*\*\[مشتق\]|^## |\Z)", text, re.M | re.S)
    if not sec:
        sys.exit("❌ `51-MATRIX-04 §2.1` غير موجود")
    rows = re.findall(r"^\| \*\*([^*]+)\*\* \(([^)]*)\) \| ([^|]*) \| ([^|]*) \| ([^|]*) \|$",
                      sec.group(0), re.M)
    out = []
    for lenses, name, blind, need, risk in rows:
        codes = [c.strip() for c in lenses.split("+")]
        out.append({"lenses": codes, "name": cell(name), "blind": cell(blind),
                    "need": cell(need), "risk": cell(risk)})
    if len(out) != 6:
        sys.exit(f"❌ تركيبات الخطورة: {len(out)} بدل 6")
    return out


def banner(text):
    """`APPENDIX-B §4/4` — التنبيه الإلزامي في رأس كل تقرير قائد.
    يُفكّ من عمود «البديل المعتمد» حرفياً — لا يُعاد صوغه."""
    m = re.search(r'تنبيه إلزامي في رأس كل تقرير قائد: "([^"]+)"', text)
    if not m:
        sys.exit("❌ التنبيه الإلزامي غير موجود في `APPENDIX-B §4`")
    return m.group(1)


def charter_bits(text):
    """العناوين التسعة من `§2` والأقفال من `§4` — تُقرأ ولا تُصاغ."""
    heads = re.findall(r"^\| (\d) \| ([^|]+) \| [^|]* \| [^|]* \|$", text, re.M)
    heading = {n: cell(h).replace("**", "") for n, h in heads}
    if len(heading) != 9:
        sys.exit(f"❌ عناوين الأقسام: {len(heading)} بدل 9")
    # الأقفال: **من جدول `§4` وحده** — لا من أي جدولٍ آخر في الميثاق.
    # أول صياغة التقطت ثلاثة أقفال من خمسة لأنها اشترطت شكل العمود الثاني،
    # فقُصر الفكّ على القسم نفسه: الحدّ يُعرَّف بموضعه لا بشكله.
    sec = re.search(r"^# القسم 4:.*?(?=^# القسم |\Z)", text, re.M | re.S)
    if not sec:
        sys.exit("❌ القسم 4 من الميثاق غير موجود")
    locks = [cell(a) for a, _b in
             re.findall(r"^\| ([^|]+) \| ([^|]+) \|$", sec.group(0), re.M)]
    locks = [l for l in locks if l and l != "القفل" and not l.startswith(":---")]
    if len(locks) != 5:
        sys.exit(f"❌ أقفال `56-TEAM-00 §4`: {len(locks)} بدل 5")
    return heading, locks


def main():
    d = dyads(read(SRC["dyad"]))
    p = polars(read(SRC["polar"]))
    b = blinds(read(SRC["blind"]))
    r = rebounds(read(SRC["rebound"]))
    c = combos(read(SRC["blind"]))
    heading, locks = charter_bits(read(SRC["charter"]))
    bn = banner(read(SRC["leader"]))
    pack = {
        "_meta": {
            "pack": "CONTENT_TEAM", "version": "1.0", "sealed_by": "DEC-278",
            "rule": ("صفر تأليف — كل نص هنا مفكوكٌ حرفياً من جدولٍ مختوم. "
                     "الفحص آلي في test_report_team.py: أي نص لا يوجد حرفياً "
                     "في مصدره يوقف الإصدار."),
            "sources": SRC,
            "approval": "DEC-039 — اعتماد حزمة المصفوفات السبع M-00…M-06",
        },
        "dyad": d, "polar": p, "blind": b, "rebound": r, "combo": c,
        "heading": heading, "lock": locks, "banner": bn,
        # الوسمان الإجرائيان الملازمان لكل مخرج (`DEC-040`/`DEC-041` ·
        # `51-MATRIX-06 §15` · `DEC-219`) — بصيغتهما في `k2_report` حرفياً،
        # فلا صيغة ثانية لوسمٍ واحد.
        "tag": ["توحيد تشغيلي مؤقت — GAP-A-01 — قابل للترقية",
                "توحيد تشغيلي مؤقت — GAP-A-02 — قابل للمراجعة"],
    }
    io.open(OUT, "w", encoding="utf-8").write(
        json.dumps(pack, ensure_ascii=False, sort_keys=True, indent=1) + "\n")
    print(f"✅ team_contentpack.json — {len(d)} زوجاً · {len(p)} قطبياً · "
          f"{len(b)} عمى · {len(r)} ارتداداً · {len(c)} تركيبة · {len(heading)} عنواناً · "
          f"{len(locks)} قفلاً · {os.path.getsize(OUT)} بايت")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
