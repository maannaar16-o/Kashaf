# -*- coding: utf-8 -*-
"""
parity_supervisor.py — تكافؤ نواة أداة المشرف (`DEC-199`)
===========================================================
يبني مجموعة حمولات: سليمة + كل نمط إفساد يُتصوَّر، ثم يشغّل `grade()`
في بايثون وJS ويقارن **كل درجة**: الاسم · النتيجة · نصّ التفصيل.

تباعدٌ واحد ⇒ يُجمَّد الطرفان (`DEC-200`) — لا يُرجَّح أحدهما.
"""
import copy
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import k2_report as R2
import k3_report as R3
import supervisor as SV


def build_payload(circle, sp, with_brief):
    if circle == "K2":
        text, audit = R2.build_report(sp, mode="full")
    else:
        text, audit = R3.build_report(sp)
    p = {"schema": "RAWAHIL-REPORT-v1.2", "circle": circle,
         "generated_at": "parity", "scopes": ["full"],
         "delivery": {"markdown": text}, "audit": audit}
    if with_brief and circle == "K2":
        brief, ab = R2.build_report(sp, mode="brief")
        p["scopes"] = ["full", "brief"]
        p["delivery"]["markdown_brief"] = brief
        p["audit_brief"] = ab
    return p


def corpus():
    cases = json.load(open(os.path.join(HERE, "parity_cases.json"), encoding="utf-8"))
    k2 = list(cases["k2"].values())
    k3 = list(cases["k3"].values())
    out = []

    # سليمة — عيّنات متعددة من الدائرتين
    for sp in k2[:4]:
        out.append(("k2 سليم + مختصر", build_payload("K2", sp, True)))
        out.append(("k2 سليم بلا مختصر", build_payload("K2", sp, False)))
    for sp in k3[:4]:
        out.append(("k3 سليم", build_payload("K3", sp, False)))

    base2 = build_payload("K2", k2[0], True)
    base3 = build_payload("K3", k3[0], False)

    def mut(tag, base, fn):
        p = copy.deepcopy(base)
        fn(p)
        out.append((tag, p))

    # أنماط الإفساد
    mut("متن +حرف", base2, lambda p: p["delivery"].__setitem__(
        "markdown", p["delivery"]["markdown"] + " ."))
    mut("متن +سطر فارغ (نقل)", base2, lambda p: p["delivery"].__setitem__(
        "markdown", p["delivery"]["markdown"] + "\n"))
    mut("متن +مسافة ذيلية (نقل)", base3, lambda p: p["delivery"].__setitem__(
        "markdown", p["delivery"]["markdown"].replace("\n", " \n", 1)))
    mut("متن مختلف جوهرياً", base3, lambda p: p["delivery"].__setitem__(
        "markdown", "نصّ أجنبي تماماً"))
    mut("بصمة مزوّرة", base2, lambda p: p["audit"].__setitem__(
        "report_sha256", "0000000000000000"))
    mut("حقل ملزِم ناقص", base2, lambda p: p["audit"].pop("entries_used"))
    mut("حقلان ناقصان", base3, lambda p: [p["audit"].pop("pack_sha"),
                                          p["audit"].pop("instrument_pin")])
    mut("انجراف حزمة", base2, lambda p: p["audit"]["pack_sha"].__setitem__(
        "INTENSITY_K2", "deadbeefdeadbeef"))
    mut("scopes غائبة", base2, lambda p: p.pop("scopes"))
    mut("scopes قيمة خاطئة", base2, lambda p: p.__setitem__("scopes", ["full", "wide"]))
    mut("scopes نصّ لا مصفوفة", base2, lambda p: p.__setitem__("scopes", "full"))
    mut("إعلان يخالف المحتوى", base2, lambda p: p["delivery"].pop("markdown_brief"))
    mut("مختصر بلا audit_brief", base2, lambda p: p.pop("audit_brief"))
    mut("مخطَّط مجهول", base2, lambda p: p.__setitem__("schema", "RAWAHIL-REPORT-v9"))
    mut("مخطَّط v1.1 قديم", base2, lambda p: (p.__setitem__("schema", "RAWAHIL-REPORT-v1.1"),
                                              p.pop("scopes")))
    mut("دائرة مجهولة", base2, lambda p: p.__setitem__("circle", "K7"))
    mut("audit ليس كائناً", base2, lambda p: p.__setitem__("audit", "نصّ"))
    mut("audit غائب", base3, lambda p: p.pop("audit"))
    mut("متن غائب", base2, lambda p: p["delivery"].pop("markdown"))
    mut("متن فارغ", base3, lambda p: p["delivery"].__setitem__("markdown", "   "))
    mut("تسرّب SP%", base2, lambda p: p["delivery"].__setitem__(
        "markdown", p["delivery"]["markdown"] + "\n| البُعد | SP% |"))
    mut("تسرّب نسبة مجرّدة", base3, lambda p: p["delivery"].__setitem__(
        "markdown", p["delivery"]["markdown"] + "\nالتحليلي: 73.5%"))
    mut("sp تالف", base2, lambda p: p["audit"].__setitem__("sp", {"A": "س"}))
    mut("subject حاضر", base2, lambda p: p.__setitem__("subject", "ي. م"))
    return out


def main():
    data = corpus()
    payloads = [p for _, p in data]
    tmp = os.path.join(HERE, "_parity_sup.json")
    json.dump(payloads, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)

    r = subprocess.run(["node", os.path.join(HERE, os.environ.get("SUP_NODE","_sup_node.js")), tmp],
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
            for a, b in zip(py_out + [None] * 9, js_out + [None] * 9):
                if a != b:
                    diverged.append((tag, a, b))
                    break
            else:
                diverged.append((tag, len(py_out), len(js_out)))
        # اتّفاق الحكم النهائي أيضاً
        if bool(py_err) != bool(js[1]):
            diverged.append((tag + " · الحكم", bool(py_err), bool(js[1])))
    os.remove(tmp)

    print(f"حمولات: {len(data)} · درجات مقارَنة: {n_deg}")
    print("-" * 76)
    if diverged:
        print(f"❌ تباعد — {len(diverged)} · يُجمَّد الطرفان (DEC-200)")
        for t, a, b in diverged[:10]:
            print(f"   [{t}]\n     بايثون: {a}\n     JS    : {b}")
        return 1
    key = hashlib.sha256(json.dumps(js_all, ensure_ascii=False,
                                    sort_keys=True).encode()).hexdigest()[:16]
    print(f"✅ تكافؤ تامّ — {len(data)} حمولة · {n_deg} درجة · صفر تباعد")
    print(f"   بصمة أحكام المشرف: {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
