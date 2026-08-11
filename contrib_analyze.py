# -*- coding: utf-8 -*-
"""
contrib_analyze.py — محلِّلة الإسهامات: القراءة الأولية (`DEC-254` · `CHG-072`)
================================================================================
تقرأ دفعة `contrib_pull.py` وتنتج التقرير الأولي بأربعة محاور — **تصف وترتّب
ولا تحكم**: لا عتبة تُخترع (`ن-7/④`) ولا ادّعاء صدق (`DEC-246`) ولا كشف تكرار
(قيد التجهيل مُصرَّح به).

المصادر المختومة تُستهلك قراءةً:
  · خريطة K2 والدرجات والتصنيف: `k2_engine` (score_from_raw · classify · octal_code)
  · خريطة K3: النقل مزدوج القيد في `build_site` (K3_MAP) · المعادلة: `k3_engine.compute_ss_sp`
  · أحكام K3 (الأكواد والنطاقات): `k3_engine.run`
جدار العزل (`DEC-205`): محاور K2 وK3 لا تختلط — وفهرس الجوار يُبنى لكل دائرة وحدها.

المخرجات (محلية لا تودَع): contrib_report.md (قراءة) + contrib_report.json (آلة).
كل النِسَب عشرية — **لا علامة ٪ في أي مخرج** (توكيد ذاتي قبل الكتابة).
"""
import json
import os
import statistics
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import k2_engine as E2                      # noqa: E402
import k3_engine as E3                      # noqa: E402
from build_site import K3_MAP, K3_CODE_TO_NAME  # noqa: E402
from contrib_pull import validate           # noqa: E402 — التحقق نفسه، لا ثقة بين الأداتين

K3_NAME_TO_CODE = {v: k for k, v in K3_CODE_TO_NAME.items()}
K3_ORDER = ["EP", "IR", "BI", "CF", "ST"]
K2_LADDER = ["A", "R", "C", "O", "S", "E", "St", "H"]   # سُلَّم الجانب 7أ→0أ (سجلّ 01-MASTER)

REPORT_MD = os.path.join(HERE, "contrib_report.md")
REPORT_JSON = os.path.join(HERE, "contrib_report.json")


def die(msg):
    raise SystemExit(f"❌ {msg}")


def r3(x):
    return round(x + 0.0, 3)


def load_batch(path):
    b = json.load(open(path, encoding="utf-8"))
    if b.get("schema") != "RAWAHIL-CONTRIB-BATCH-v1":
        die("الملف ليس دفعة إسهامات")
    recs = []
    for rec in b.get("records", []):
        err = validate(rec.get("payload"))
        if err:
            die(f"سجل مخالف داخل الدفعة ({rec.get('key')}): {err} — الدفعة لا تُحلَّل")
        recs.append(rec)
    return b, recs


# ═══════ الدرجات المعيارية عبر المصادر المختومة ═══════

def k2_scores(answers):
    sfr = E2.score_from_raw(answers)
    return {d: v["sp"] for d, v in sfr.items()}, {d: v["code"] for d, v in sfr.items()}


def k3_scores(answers):
    sp = {}
    for name, items in K3_MAP.items():
        x = y = 0
        for it, letter in items:
            a = answers[str(it)]
            x += a["ratingA"] if letter == "a" else a["ratingB"]
            if a["choice"] == letter:
                y += 1
        _ss, spv = E3.compute_ss_sp(x, y, 11 - y)
        sp[K3_NAME_TO_CODE[name]] = round(spv, 1)
    audit = E3.run(sp).audit
    return sp, audit["codes"], audit["bands"]


# ═══════ المحاور ═══════

def axis1_side(recs):
    """ميل الجانب (أ) — GAP-ITEM-SIDE-01."""
    n = len(recs)
    per_item = []
    for item in range(1, 95):
        n_a = sum(1 for r in recs if r["payload"]["answers"][str(item)]["choice"] == "a")
        rate = n_a / n
        per_item.append({"item": item, "n_a": n_a, "rate": r3(rate), "dev": r3(rate - 0.5)})
    ranked = sorted(per_item, key=lambda x: -abs(x["dev"]))
    # سُلَّم A→H: تأييد جانب البُعد (اختيار حرف البُعد في خاناته السبع)
    ladder = []
    for pos, d in enumerate(K2_LADDER, start=1):
        slots = E2.K2_ITEM_MAP[d]
        tot = hits = 0
        for it, letter in slots:
            for r in recs:
                tot += 1
                if r["payload"]["answers"][str(it)]["choice"] == letter:
                    hits += 1
        a_slots = sum(1 for _it, letter in slots if letter == "a")
        ladder.append({"dim": d, "pos": pos, "a_slots": a_slots,
                       "endorse": r3(hits / tot)})
    overall = r3(sum(x["rate"] for x in per_item) / 94)
    return {"per_item": per_item, "ranked": ranked, "ladder": ladder, "overall_a": overall}


def axis2_scale(recs):
    """سلوك سُلَّم التقييم ١–٦ لكل جملة من الـ188."""
    out = []
    for item in range(1, 95):
        for letter, key in (("a", "ratingA"), ("b", "ratingB")):
            vals = [r["payload"]["answers"][str(item)][key] for r in recs]
            dist = {str(v): vals.count(v) for v in range(1, 7)}
            var = statistics.pvariance(vals) if len(vals) > 1 else 0.0
            out.append({
                "sentence": f"{item}{'أ' if letter == 'a' else 'ب'}",
                "dist": dist, "mean": r3(statistics.fmean(vals)),
                "var": r3(var),
                "at_floor": r3(vals.count(1) / len(vals)),
                "at_ceiling": r3(vals.count(6) / len(vals)),
            })
    low_var = sorted(out, key=lambda s: s["var"])[:20]
    extreme = sorted(out, key=lambda s: -max(s["at_floor"], s["at_ceiling"]))[:20]
    return {"sentences": out, "low_var_top20": low_var, "extreme_top20": extreme}


def quartiles(vals):
    q = statistics.quantiles(vals, n=4) if len(vals) >= 2 else [vals[0]] * 3
    return {"min": r3(min(vals)), "q1": r3(q[0]), "median": r3(q[1]),
            "q3": r3(q[2]), "max": r3(max(vals))}


def axis3_distributions(recs):
    """توزيعات الدرجات المعيارية — كل دائرة وحدها (DEC-205)."""
    k2_sp_all, k2_codes_all, centers = {d: [] for d in K2_LADDER}, {d: [] for d in K2_LADDER}, []
    k3_sp_all, k3_bands_all = {s: [] for s in K3_ORDER}, {s: [] for s in K3_ORDER}
    for r in recs:
        ans = r["payload"]["answers"]
        sp2, codes2 = k2_scores(ans)
        centers.append(E2.classify(sp2).center)
        for d in K2_LADDER:
            k2_sp_all[d].append(sp2[d])
            k2_codes_all[d].append(codes2[d])
        sp3, codes3, bands3 = k3_scores(ans)
        for s in K3_ORDER:
            k3_sp_all[s].append(sp3[s])
            k3_bands_all[s].append(bands3[s])
    return {
        "k2": {
            "lens_quartiles": {d: quartiles(k2_sp_all[d]) for d in K2_LADDER},
            "center_dist": {c: centers.count(c) for c in K2_LADDER if centers.count(c)},
            "code_dist": {d: {c: k2_codes_all[d].count(c) for c in sorted(set(k2_codes_all[d]))}
                          for d in K2_LADDER},
        },
        "k3": {
            "skill_quartiles": {s: quartiles(k3_sp_all[s]) for s in K3_ORDER},
            "band_dist": {s: {b: k3_bands_all[s].count(b) for b in sorted(set(k3_bands_all[s]))}
                          for s in K3_ORDER},
        },
    }


def axis4_neighbors(recs):
    """مخزون الملفات القريبة — فهرس جوار لكل دائرة وحدها (تجهيز مادة 120 §2)."""
    ids = [r["key"][:12] for r in recs]
    vecs2, vecs3 = [], []
    for r in recs:
        ans = r["payload"]["answers"]
        sp2, _ = k2_scores(ans)
        vecs2.append([sp2[d] for d in K2_LADDER])
        sp3, _c, _b = k3_scores(ans)
        vecs3.append([sp3[s] for s in K3_ORDER])

    def index(vecs):
        out = {}
        for i in range(len(vecs)):
            dists = []
            for j in range(len(vecs)):
                if i == j:
                    continue
                d = sum((a - b) ** 2 for a, b in zip(vecs[i], vecs[j])) ** 0.5
                dists.append((r3(d), ids[j]))
            dists.sort()
            out[ids[i]] = [{"id": nid, "dist": dv} for dv, nid in dists[:3]]
        return out
    return {"k2": index(vecs2), "k3": index(vecs3)}


# ═══════ التقرير ═══════

DISCLAIMER = """> **حدود هذه القراءة — تُقرأ قبل أي رقم:** هذا وصفٌ وترتيب، لا حكم. لا عتبة
> فاصلة هنا — أي حدّ يُراد استعماله يُقترح ثم **يُختم قراراً** قبل أول استعمال
> (`ن-7/④`). لا ادّعاء صدق ولا استدلال عليه (`DEC-246`). التجهيل يمنع كشف
> إسهام الشخص الواحد مرتين — **قيد مُصرَّح به**. والعدد الصغير ليس دليلاً."""


def fmt_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join([":---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(out)


def build_md(batch, recs, a1, a2, a3, a4):
    n = len(recs)
    months = {}
    for r in recs:
        m = r["payload"]["submitted"]
        months[m] = months.get(m, 0) + 1
    L = []
    L.append("# القراءة الأولية لإسهامات «الكشاف» — دفعة "
             + batch.get("fingerprint", "؟"))
    L.append("")
    L.append(f"**حجم العينة: {n} إسهاماً** · سُحبت {batch.get('pulled_at', '؟')} · "
             "المواصفة `RAWAHIL-CONTRIB-v1` · كل النِسَب عشرية")
    L.append("")
    L.append(DISCLAIMER)
    L.append("")
    L.append("## الجرد")
    L.append(fmt_table(["الشهر", "إسهامات"], sorted(months.items())))
    L.append("")
    L.append("## المحور ① — ميل الجانب (أ) — بيانات `GAP-ITEM-SIDE-01`")
    L.append(f"متوسط اختيار (أ) عبر البنود كلها: **{a1['overall_a']}** (المرجع البنيوي 0.5).")
    L.append("")
    L.append("### سُلَّم الجانب A→H — تأييد جانب البُعد في خاناته السبع")
    L.append(fmt_table(["البُعد", "موضعه", "خانات (أ)", "نسبة تأييد جانبه"],
                       [(x["dim"], x["pos"], x["a_slots"], x["endorse"]) for x in a1["ladder"]]))
    L.append("")
    L.append("### البنود مرتبة بانحرافها عن 0.5 (الأعلى عشرون)")
    L.append(fmt_table(["البند", "اختاروا (أ)", "النسبة", "الانحراف"],
                       [(x["item"], x["n_a"], x["rate"], x["dev"]) for x in a1["ranked"][:20]]))
    L.append("")
    L.append("*(الجدول البندي الكامل — 94 بنداً — في ملف الآلة.)*")
    L.append("")
    L.append("## المحور ② — سلوك سُلَّم التقييم (١–٦)")
    L.append("### الجمل الأدنى تبايناً (مادة مراجعة — وصف لا وسم)")
    L.append(fmt_table(["الجملة", "المتوسط", "التباين", "عند الأرضية", "عند السقف"],
                       [(s["sentence"], s["mean"], s["var"], s["at_floor"], s["at_ceiling"])
                        for s in a2["low_var_top20"]]))
    L.append("")
    L.append("### الجمل الأشد التصاقاً بطرف")
    L.append(fmt_table(["الجملة", "المتوسط", "عند الأرضية", "عند السقف"],
                       [(s["sentence"], s["mean"], s["at_floor"], s["at_ceiling"])
                        for s in a2["extreme_top20"]]))
    L.append("")
    L.append("## المحور ③ — توزيعات الدرجة المعيارية (وصف لا معايير — `DEBT-K3-NORM-01` قائم)")
    L.append("### دائرة التفكير K2 — أرباع الدرجة لكل عدسة")
    L.append(fmt_table(["العدسة", "أدنى", "ر1", "الوسيط", "ر3", "أقصى"],
                       [(d, q["min"], q["q1"], q["median"], q["q3"], q["max"])
                        for d, q in a3["k2"]["lens_quartiles"].items()]))
    L.append("")
    L.append("### توزيع المراكز الظاهرة في العينة")
    L.append(fmt_table(["المركز", "عدد الملفات"], sorted(a3["k2"]["center_dist"].items())))
    L.append("")
    L.append("### دائرة الانفعال K3 — أرباع الدرجة لكل قدرة")
    L.append(fmt_table(["القدرة", "أدنى", "ر1", "الوسيط", "ر3", "أقصى"],
                       [(s, q["min"], q["q1"], q["median"], q["q3"], q["max"])
                        for s, q in a3["k3"]["skill_quartiles"].items()]))
    L.append("")
    L.append("### توزيع نطاقات K3")
    L.append(fmt_table(["القدرة", "النطاقات (عدّاً)"],
                       [(s, " · ".join(f"{b}:{c}" for b, c in bd.items()))
                        for s, bd in a3["k3"]["band_dist"].items()]))
    L.append("")
    L.append("## المحور ④ — مخزون الملفات القريبة (تجهيز مادة `120-VALID-STEPS §2` — لا تنفيذ)")
    L.append("فهرس الجوار الكامل (أقرب ثلاثة لكل ملف، لكل دائرة وحدها) في ملف الآلة. "
             "عيّنة أول خمسة ملفات — دائرة التفكير:")
    sample_rows = [(rid, " · ".join(f"{nb['id']}({nb['dist']})" for nb in nbs))
                   for rid, nbs in list(a4["k2"].items())[:5]]
    L.append(fmt_table(["الملف", "أقرب جيرانه (المسافة)"], sample_rows))
    L.append("")
    L.append("---")
    L.append("**ذيل — ما ينتظر ختمك لا اجتهاد الأداة:** حدّ «الميل» الفاصل في المحور ① · "
             "معايير إدراج جملة في «مادة المراجعة» بالمحور ② · أي استعمال معياري للمحور ③.")
    L.append("")
    L.append(f"*(وُلّد {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}Z — "
             "أداة وصفية؛ الحكم للمالك.)*")
    return "\n".join(L)


def analyze(batch, recs):
    a1 = axis1_side(recs)
    a2 = axis2_scale(recs)
    a3 = axis3_distributions(recs)
    a4 = axis4_neighbors(recs)
    md = build_md(batch, recs, a1, a2, a3, a4)
    machine = {"batch_fingerprint": batch.get("fingerprint"), "n": len(recs),
               "axis1": a1, "axis2": a2, "axis3": a3, "axis4": a4}
    # توكيد ذاتي: لا علامة نسبة في أي مخرج
    if "%" in md or "%" in json.dumps(machine, ensure_ascii=False):
        die("علامة ٪ تسربت إلى مخرج — خرق نظافة العرض")
    return md, machine


# ═══════ الاختبار الذاتي — عيّنة معلومة النتائج سلفاً ═══════

def self_test():
    def rec(key, choice, ra, rb):
        return {"key": key, "payload": {
            "schema": "RAWAHIL-CONTRIB-v1",
            "instrument": {"measure": "40-MEASURE v5.0", "scoring": "41 v4.2", "build": "t"},
            "submitted": "2026-08",
            "answers": {str(n): {"choice": choice, "ratingA": ra, "ratingB": rb}
                        for n in range(1, 95)},
        }}
    recs = [rec("c_t1", "a", 6, 1), rec("c_t2", "a", 6, 1),
            rec("c_t3", "a", 2, 5), rec("c_t4", "b", 1, 1)]
    for r in recs:
        assert validate(r["payload"]) is None, "عينة الاختبار نفسها مخالفة"
    batch = {"schema": "RAWAHIL-CONTRIB-BATCH-v1", "fingerprint": "selftest",
             "pulled_at": "test", "records": recs}
    md, m = analyze(batch, recs)

    ok = True
    def chk(label, cond):
        nonlocal ok
        print(("✅" if cond else "❌"), label)
        ok = ok and cond

    # ① نسبة (أ) = 3/4 لكل بند · السُلَّم: A تأييده = نسبة اختيار a (0.75)، H = 0.25
    chk("محور①: نسبة (أ) 0.75 لكل بند",
        all(x["rate"] == 0.75 for x in m["axis1"]["per_item"]))
    lad = {x["dim"]: x for x in m["axis1"]["ladder"]}
    chk("محور①: سُلَّم A=0.75 (7 خانات أ) وH=0.25 (0 خانات أ)",
        lad["A"]["a_slots"] == 7 and lad["A"]["endorse"] == 0.75
        and lad["H"]["a_slots"] == 0 and lad["H"]["endorse"] == 0.25)
    # ② جملة 1أ: القيم [6,6,2,1] → متوسط 3.75 · أرضية 0.25 · سقف 0.5
    s1a = next(s for s in m["axis2"]["sentences"] if s["sentence"] == "1أ")
    chk("محور②: توزيع 1أ معلوم (متوسط 3.75 · أرضية 0.25 · سقف 0.5)",
        s1a["mean"] == 3.75 and s1a["at_floor"] == 0.25 and s1a["at_ceiling"] == 0.5)
    # ③ درجات السجل الأول تطابق المحرك المختوم مباشرة (وقيمة A اليدوية 116.7)
    sp2, _ = k2_scores(recs[0]["payload"]["answers"])
    chk("محور③: درجة A للسجل الأول = 116.7 (يدوي مقابل محرك)",
        sp2["A"] == 116.7)
    chk("محور③: توزيع المراكز يحصي 4 ملفات",
        sum(m["axis3"]["k2"]["center_dist"].values()) == 4)
    # ④ التوأمان c_t1/c_t2 أقرب جارين بمسافة 0 — في الدائرتين
    chk("محور④: التوأمان مسافتهما 0 في K2 وK3",
        m["axis4"]["k2"]["c_t1"][0] == {"id": "c_t2", "dist": 0.0}
        and m["axis4"]["k3"]["c_t1"][0] == {"id": "c_t2", "dist": 0.0})
    chk("التقرير يحمل الحدود المعلنة", "لا حكم" in md and "قيد مُصرَّح به" in md)
    print("✅ الاختبار الذاتي مجتاز" if ok else "❌ الاختبار الذاتي ساقط")
    return 0 if ok else 1


def main():
    if "--self-test" in sys.argv:
        return self_test()
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "contrib_batch.json")
    if not os.path.isfile(path):
        die(f"الدفعة غير موجودة: {path} — شغّل contrib_pull.py أولاً")
    batch, recs = load_batch(path)
    if not recs:
        die("الدفعة فارغة — لا شيء يُحلَّل")
    md, machine = analyze(batch, recs)
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(machine, f, ensure_ascii=False, indent=1)
    print(f"حُلّلت {len(recs)} إسهاماً · التقرير: {os.path.basename(REPORT_MD)} "
          f"+ {os.path.basename(REPORT_JSON)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
