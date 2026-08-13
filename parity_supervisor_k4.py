# -*- coding: utf-8 -*-
"""
parity_supervisor_k4.py — تكافؤ أحكام المشرف على دائرة الإنجاز (البصمة الخامسة)
================================================================================
سند: أمر المالك «نفّذ بالترتيب الموصى به» — 2026-08-13 · `DEC-271`
     `DEC-199`/`DEC-200` (التكافؤ والتجميد) · `136 §3/④` (كتلة التدقيق)
     `DEC-267` (الحقل الإعلاني ومزامنته اليدوية) · `DEC-268` (فصل السطحين)

**لماذا أداةٌ مستقلة ولا توسيعٌ لـ`parity_supervisor.py`:** بصمة أحكام
المشرف `6b324f996856eac3` **مرجعٌ مجمَّد**؛ وضمّ حالات $K_4$ إلى مجموعتها
كان سيزيحها فيضيع المرجع بلا كسبٍ يقابله. فالسابقة المتَّبعة هي سابقة
`parity_k4.py` نفسها: **دائرةٌ جديدة ⇒ أداةٌ وبصمةٌ خاصّتان بها**.

تشغيل جانب JS يُعاد استعمالُ محمَله `_sup_node.js` كما هو — لا محمَل ثانٍ.
"""
import copy
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import k4_report as R4
import supervisor as SV


def build_payload(sp, with_crossing=True):
    """حمولة تسليم كما تُصدَّرها الأداة — والسطح العابر **مُعلَناً منفصلاً**."""
    text, audit = R4.build_report(dict(sp))
    p = {"schema": "RAWAHIL-REPORT-v1.2", "circle": "K4",
         "generated_at": "parity", "scopes": ["full"],
         "delivery": {"markdown": text}, "audit": audit}
    if with_crossing:
        xt, xa = R4.build_crossing_surface(dict(sp))
        if xt:                      # لا يُعلَن سطحٌ لم يستحقّ العرض
            p["delivery"]["markdown_crossing"] = xt
            p["audit_crossing"] = xa
    return p


def corpus():
    cases = json.load(open(os.path.join(HERE, "parity_cases_k4.json"),
                           encoding="utf-8"))
    k4 = list(cases["k4"].values())
    out = []

    # ① سليمة — عيّنات متنوّعة، بسطحٍ عابر وبلا سطح
    for i, sp in enumerate(k4[:10]):
        out.append((f"k4 سليم +سطح [{i}]", build_payload(sp, True)))
        out.append((f"k4 سليم بلا سطح [{i}]", build_payload(sp, False)))

    # حالةٌ يستحقّ سطحُها العرض قطعاً (محطة في الحضور المحدود على مشغِّل)
    sp_x = dict(WM=62, TI=38, F=74, PF=44, OR=55, TM=41, PER=40)
    base_x = build_payload(sp_x, True)
    assert "markdown_crossing" in base_x["delivery"], "حالة السطح لا تُنتج سطحاً"
    base = build_payload(k4[0], False)
    out.append(("k4 سطح مستحقّ", base_x))

    def mut(tag, src, fn):
        p = copy.deepcopy(src)
        fn(p)
        out.append((tag, p))

    # ② إفساد المتن والبصمة — كأنماط $K_2$/$K_3$ نفسها
    mut("متن +حرف", base, lambda p: p["delivery"].__setitem__(
        "markdown", p["delivery"]["markdown"] + " ."))
    mut("متن +سطر فارغ (نقل)", base, lambda p: p["delivery"].__setitem__(
        "markdown", p["delivery"]["markdown"] + "\n"))
    mut("متن مختلف جوهرياً", base, lambda p: p["delivery"].__setitem__(
        "markdown", "نصّ أجنبي تماماً"))
    mut("بصمة مزوّرة", base, lambda p: p["audit"].__setitem__(
        "report_sha256", "0000000000000000"))
    mut("متن غائب", base, lambda p: p["delivery"].pop("markdown"))
    mut("متن فارغ", base, lambda p: p["delivery"].__setitem__("markdown", "   "))

    # ③ عقد كتلة التدقيق — **كل حقل من الاثنين والعشرين يُختبر غيابه**
    for k in SV.REQUIRED_AUDIT_K4:
        mut(f"حقل ناقص: {k}", base, lambda p, k=k: p["audit"].pop(k))
    mut("حقل K2 مطلوبٌ خطأً غائب", base,
        lambda p: p["audit"].__setitem__("entries_used", None))   # لا يُحاسَب في K4

    # ④ الحقل الإعلاني — انجرافه ودَين الميدان
    mut("دَين الميدان محذوف", base, lambda p: p["audit"].__setitem__(
        "open_debts", [d for d in p["audit"]["open_debts"]
                       if d != "DEBT-K4-FIELD-01"]))
    mut("دَين وهمي مضاف", base, lambda p: p["audit"]["open_debts"].append("DEBT-وهمي"))
    mut("الديون فارغة", base, lambda p: p["audit"].__setitem__("open_debts", []))

    # ⑤ إعلان نطاقٍ لا وجود له في K4
    mut("مختصر مُعلَن كذباً", base, lambda p: p.__setitem__("scopes", ["full", "brief"]))
    mut("مختصر مُعلَن ومحتواه حاضر", base, lambda p: (
        p.__setitem__("scopes", ["full", "brief"]),
        p["delivery"].__setitem__("markdown_brief", "متن مختصر مزعوم")))
    mut("scopes غائبة", base, lambda p: p.pop("scopes"))
    mut("scopes قيمة خاطئة", base, lambda p: p.__setitem__("scopes", ["full", "wide"]))

    # ⑥ السطح العابر — بصمته وقيوده وفصلُه
    mut("سطح: بصمة مزوّرة", base_x, lambda p: p["audit_crossing"].__setitem__(
        "surface_sha256", "0000000000000000"))
    mut("سطح: متن مبدَّل", base_x, lambda p: p["delivery"].__setitem__(
        "markdown_crossing", p["delivery"]["markdown_crossing"] + " ."))
    mut("سطح: قيود منجرفة", base_x, lambda p: p["audit_crossing"].__setitem__(
        "entries", ["K4-XR-99"]))
    mut("سطح: audit_crossing غائب", base_x, lambda p: p.pop("audit_crossing"))
    mut("سطح: متنه غائب", base_x, lambda p: p["delivery"].pop("markdown_crossing"))
    mut("سطح: مدموج في المتن (DEC-268)", base_x, lambda p: p["delivery"].__setitem__(
        "markdown", p["delivery"]["markdown"] + "\n"
        + p["delivery"]["markdown_crossing"]))
    mut("سطح مُعلَن لحالة لا تستحقّه", base, lambda p: (
        p["delivery"].__setitem__("markdown_crossing", base_x["delivery"]["markdown_crossing"]),
        p.__setitem__("audit_crossing", copy.deepcopy(base_x["audit_crossing"]))))

    # ⑦ انجراف الحزمة وحارسا المخرج
    mut("انجراف حزمة", base, lambda p: p["audit"]["pack_sha"].__setitem__(
        "CONTENT_K4", "deadbeefdeadbeef"))
    mut("تسرّب SP%", base, lambda p: p["delivery"].__setitem__(
        "markdown", p["delivery"]["markdown"] + "\n| المحطة | SP% |"))
    mut("تسرّب نسبة مجرّدة", base, lambda p: p["delivery"].__setitem__(
        "markdown", p["delivery"]["markdown"] + "\nالمثابرة: 41.0%"))

    # ⑧ عقد المدخل عند إعادة التوليد — من مجموعة الفشل المختومة
    for tag, sp in cases["failure"].items():
        mut(f"عقد المدخل: {tag}", base, lambda p, sp=sp: p["audit"].__setitem__(
            "sp", dict(sp)))

    # ⑨ البنية والمخطَّط
    mut("مخطَّط مجهول", base, lambda p: p.__setitem__("schema", "RAWAHIL-REPORT-v9"))
    mut("مخطَّط v1.1 قديم", base, lambda p: (
        p.__setitem__("schema", "RAWAHIL-REPORT-v1.1"), p.pop("scopes")))
    mut("دائرة مجهولة", base, lambda p: p.__setitem__("circle", "K7"))
    mut("دائرة بحرف صغير", base, lambda p: p.__setitem__("circle", "k4"))
    mut("audit ليس كائناً", base, lambda p: p.__setitem__("audit", "نصّ"))
    mut("audit غائب", base, lambda p: p.pop("audit"))
    mut("subject حاضر", base, lambda p: p.__setitem__("subject", "ي. م"))
    return out


def main():
    data = corpus()
    payloads = [p for _, p in data]
    tmp = os.path.join(HERE, "_parity_sup_k4.json")
    json.dump(payloads, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)

    r = subprocess.run(["node", os.path.join(HERE, "_sup_node.js"), tmp],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        print("❌ تعذّر تشغيل جانب JS:\n" + (r.stderr[:900] or r.stdout[:900]))
        return 1
    js_all = json.loads(r.stdout)

    diverged, n_deg = [], 0
    for (tag, p), js in zip(data, js_all):
        try:
            py_out, py_err = SV.grade(p)
        except Exception as e:
            py_out, py_err = [["EXC", False, f"{type(e).__name__}: {e}"]], ["EXC"]
        js_out = [tuple(x) for x in js[0]]
        py_out = [tuple(x) for x in py_out]
        n_deg += len(py_out)
        if py_out != js_out:
            for a, b in zip(py_out + [None] * 14, js_out + [None] * 14):
                if a != b:
                    diverged.append((tag, a, b))
                    break
            else:
                diverged.append((tag, len(py_out), len(js_out)))
        if bool(py_err) != bool(js[1]):
            diverged.append((tag + " · الحكم", bool(py_err), bool(js[1])))
    os.remove(tmp)

    # فحصٌ يقيس ما يعلنه: السليم **يُقبل**، والمُفسَد **يُرصد**. وقائمة
    # «المقبول بمسوّغه» **مُعلَنة صريحة** — فأربع حمولاتٍ فيها ليست إفساداً:
    #   · `entries_used` غائبة — حقلُ $K_2$، وعقد $K_4$ لا يطلبها (`136 §3/④`)
    #   · مخطَّط `v1.1` — مدعوم، والدرجة ② لا تُحاسَب عليه (`DEC-231`)
    #   · دائرة بحرف صغير — `upper()` تسوّيها، فليست حالة رفض
    #   · `subject` حاضر — حقل تعريفٍ مباح لا يُدقَّق
    # وبلا هذا الإعلان يصير الفحص نفسه **حقلاً لا يفحص**: يعدّ الصحيحَ خطأً.
    EXPECTED_PASS = {"حقل K2 مطلوبٌ خطأً غائب", "مخطَّط v1.1 قديم",
                     "دائرة بحرف صغير", "subject حاضر"}
    blind = []
    for tag, p in data:
        _, errs = SV.grade(p)
        healthy = (tag.startswith("k4 سليم") or tag == "k4 سطح مستحقّ"
                   or tag in EXPECTED_PASS)
        if healthy and errs:
            blind.append(f"سليمٌ رُفض: {tag} — {errs[0]}")
        if not healthy and not errs:
            blind.append(f"مُفسَدٌ مرّ: {tag}")

    print(f"حمولات: {len(data)} · درجات مقارَنة: {n_deg}")
    print("-" * 76)
    if diverged:
        print(f"❌ تباعد — {len(diverged)} · يُجمَّد الطرفان (DEC-200)")
        for t, a, b in diverged[:10]:
            print(f"   [{t}]\n     بايثون: {a}\n     JS    : {b}")
        return 1
    if blind:
        print(f"❌ الأداة عمياء في {len(blind)} موضعاً — الدرجة لا تقيس ما تعلنه")
        for b in blind[:10]:
            print("   " + b)
        return 1
    key = hashlib.sha256(json.dumps(js_all, ensure_ascii=False,
                                    sort_keys=True).encode()).hexdigest()[:16]
    print(f"✅ تكافؤ تامّ — {len(data)} حمولة · {n_deg} درجة · صفر تباعد")
    print(f"   وكل إفسادٍ مرصود · وكل سليمٍ مقبول — {len(data)} حكماً")
    print(f"   بصمة أحكام المشرف على K4: {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
