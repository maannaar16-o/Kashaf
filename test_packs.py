# -*- coding: utf-8 -*-
"""
test_packs.py — انحدار طبقة الحزم المضمَّنة (المرحلة ②)
=======================================================
يفحص ثلاثة أشياء منفصلة — كل فحص يقيس شيئاً واحداً (ن-7/②):

  ح-1  سلامة البصمات: packs.js لم ينجرف عن بصمته المثبَتة
  ح-2  مطابقة المصدر: محتوى JS = محتوى بايثون عنصراً بعنصر
  ح-3  اكتمال البنية: المفاتيح المتوقَّعة موجودة وغير فارغة

سند: ن-7 (DEC-193/198) · DEC-199 (تكافؤ النسخ)
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))

SRC = {
    "USERLAYER_K2": "k2_userlayer_pack.json",
    "CONTENT_K2":   "k2_contentpack.json",
    "SECTIONS_K3":  "skill_sections.json",
    "THREE_K3":     "three_texts.json",
    "CIRCLE_K3":    "circle_map_v2.json",
}
LENSES = ["A", "R", "C", "O", "S", "E", "St", "H"]
SKILLS = ["EP", "IR", "BI", "CF", "ST"]
K3_KEYS = ["U01", "U08", "U09", "U10"]


def js_eval(code):
    r = subprocess.run(["node", "-e", code], capture_output=True, text=True, cwd=HERE)
    if r.returncode:
        return None, r.stderr.strip()
    return r.stdout.strip(), None


def main():
    errs = []

    # ── ح-1: سلامة البصمات ────────────────────────────────────────────
    out, err = js_eval(
        'const p=require("./packs.js");'
        'try{p.verifyPacks();console.log("OK")}catch(e){console.log("FAIL:"+e.message)}')
    if err or not out or not out.startswith("OK"):
        errs.append(f"ح-1 سلامة البصمات: {out or err}")
        print("❌ ح-1 سلامة البصمات")
    else:
        print("✅ ح-1 سلامة البصمات — الخمس مطابقة لبصماتها")

    # ── ح-2: مطابقة المصدر ────────────────────────────────────────────
    js_eval('const{PACKS}=require("./packs.js");'
            'require("fs").writeFileSync("/tmp/_packs.json",JSON.stringify(PACKS));')
    try:
        js = json.load(open("/tmp/_packs.json", encoding="utf-8"))
    except Exception as e:
        js = {}
        errs.append(f"ح-2: تعذّر تصدير حزم JS ({e})")
    mism = []
    for name, fn in SRC.items():
        path = os.path.join(HERE, fn)
        if not os.path.exists(path):
            mism.append(f"{name}: المصدر {fn} غائب"); continue
        py = json.load(open(path, encoding="utf-8"))
        if name not in js:
            mism.append(f"{name}: غائب في JS")
        elif py != js[name]:
            mism.append(f"{name}: المحتوى مختلف عن {fn}")
    errs += [f"ح-2 {m}" for m in mism]
    print("✅ ح-2 مطابقة المصدر — الخمس متطابقة بايثون↔JS" if not mism
          else f"❌ ح-2 مطابقة المصدر: {mism}")

    # ── ح-3: اكتمال البنية ────────────────────────────────────────────
    struct = []
    if js:
        for d in LENSES:
            if d not in js.get("USERLAYER_K2", {}):
                struct.append(f"USERLAYER_K2: العدسة {d} غائبة")
            if d not in js.get("CONTENT_K2", {}):
                struct.append(f"CONTENT_K2: المعجم {d} غائب")
        for s in SKILLS:
            sec = js.get("SECTIONS_K3", {}).get(s, {})
            for k in K3_KEYS:
                if not str(sec.get(k, "")).strip():
                    struct.append(f"SECTIONS_K3[{s}][{k}] فارغ")
            if not str(js.get("CIRCLE_K3", {}).get("tail", {}).get(s, "")).strip():
                struct.append(f"CIRCLE_K3.tail[{s}] فارغ")
        if not str(js.get("CIRCLE_K3", {}).get("shared", "")).strip():
            struct.append("CIRCLE_K3.shared فارغ")
        for k in ("covenant_opening", "out_text", "reflective_frame"):
            if not str(js.get("THREE_K3", {}).get(k, "")).strip():
                struct.append(f"THREE_K3[{k}] فارغ")
    errs += [f"ح-3 {m}" for m in struct]
    print("✅ ح-3 اكتمال البنية — 8 عدسات · 8 معاجم · 5 مهارات × 4 مفاتيح"
          if not struct else f"❌ ح-3: {struct[:3]}")

    print("-" * 76)
    print("النتيجة النهائية:", "✅ لا انحدار" if not errs else f"❌ {len(errs)} انحراف")
    for e in errs:
        print("   ·", e)
    return len(errs)


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
