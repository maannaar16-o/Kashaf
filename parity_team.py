# -*- coding: utf-8 -*-
"""
parity_team.py — تكافؤ طبقة الفريق: بايثون ⇄ JS (`DEC-289`)
==============================================================
سند: `DEC-199`/`DEC-200` (التوأمة) · `DEC-278 §5` (**قاعدة القلب**: حين
     يُبنى السطح **يُقلب الحرس لا يُحذف** — من «لا سطح بلا توأم» إلى
     «التوأم مقيسٌ بتكافؤ») · `140 §5`

**وهذه بصمة تكافؤ لا انحدار** — والتسمية مقصودة: صار ثمّة طرفان يُقاس
التطابق بينهما، فحقَّ للاسم ما لم يحقّ له في `DEC-278`.

المقيس: **المتن حرفاً بحرف** · **كتلة التدقيق كاملةً** · **ورسالة كل
خرقٍ لعقد المدخل بنصّها** — فانحرافُ رسالةٍ انحرافٌ يُرصد.
"""
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import team_engine as TE
import team_report as TR

FAILS = []


def canon(o):
    return json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main():
    cases = json.load(io.open(os.path.join(HERE, "team_cases.json"), encoding="utf-8"))
    r = subprocess.run(["node", os.path.join(HERE, "_team_node.js")],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        print("❌ جانب JS أخفق:\n" + (r.stderr or r.stdout)[:600])
        return 1
    js = json.loads(r.stdout)

    print("=" * 78)
    print(f"{'الحالة':<34}{'المتن':<10}{'التدقيق':<10}الحكم")
    print("-" * 78)

    n_body = n_audit = 0
    for name in sorted(cases["team"]):
        body_py, audit_py = TR.build_report(cases["team"][name])
        side = js["team"].get(name)
        if side is None:
            print(f"{name:<34}{'—':<10}{'—':<10}❌ غائبة في JS")
            FAILS.append(name)
            continue
        ok_b = body_py == side["body"]
        ok_a = canon(audit_py) == canon(side["audit"])
        n_body += ok_b
        n_audit += ok_a
        print(f"{name:<34}{'✅' if ok_b else '❌':<10}{'✅' if ok_a else '❌':<10}"
              + ("متطابق" if ok_b and ok_a else "تباعد"))
        if not ok_b:
            for i, (x, y) in enumerate(zip(body_py.split("\n"),
                                           side["body"].split("\n"))):
                if x != y:
                    print(f"   سطر {i + 1}:\n     py: {x[:90]}\n     js: {y[:90]}")
                    break
        if not ok_a:
            for k in sorted(set(audit_py) | set(side["audit"])):
                if canon(audit_py.get(k)) != canon(side["audit"].get(k)):
                    print(f"   حقل «{k}»:\n     py: {canon(audit_py.get(k))[:90]}"
                          f"\n     js: {canon(side['audit'].get(k))[:90]}")
                    break
        if not (ok_b and ok_a):
            FAILS.append(name)

    # **ورسائل الخرق تُقاس أيضاً**: عقدٌ يوقف برسالتين مختلفتين عقدان
    print("-" * 78)
    n_msg = 0
    for name in sorted(cases["failure"]):
        try:
            TE.run(cases["failure"][name])
            mode_py, msg_py = "no-error", ""
        except TE.InputContractError as e:
            mode_py, msg_py = "InputContractError", str(e)
        except Exception as e:                        # noqa: BLE001
            mode_py, msg_py = "other:" + type(e).__name__, str(e)
        side = js["failure"].get(name, {})
        ok = mode_py == side.get("mode") and msg_py == side.get("message")
        n_msg += ok
        print(f"{name:<34}{'✅' if ok else '❌':<10}{mode_py}")
        if not ok:
            print(f"     py: {mode_py} · {msg_py[:80]}")
            print(f"     js: {side.get('mode')} · {str(side.get('message'))[:80]}")
            FAILS.append("رسالة:" + name)

    print("-" * 78)
    parts = []
    for name in sorted(cases["team"]):
        body, audit = TR.build_report(cases["team"][name])
        parts.append(name + " " + body + " " + canon(audit))
    for name in sorted(cases["failure"]):
        try:
            TE.run(cases["failure"][name])
            parts.append(name + " no-error")
        except TE.InputContractError as e:
            parts.append(name + " InputContractError " + str(e))
        except Exception as e:                        # noqa: BLE001
            parts.append(name + " other:" + type(e).__name__)
    import hashlib
    fp = hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()[:16]

    if FAILS:
        print(f"❌ تباعد — {len(FAILS)}: " + " · ".join(FAILS[:6]))
        return 1
    print(f"✅ تكافؤ تامّ — {len(cases['team'])} تركيبة · "
          f"{n_body} متناً · {n_audit} كتلة تدقيق · {n_msg} رسالة خرق · صفر تباعد")
    print(f"   بصمة تكافؤ الفريق: {fp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
