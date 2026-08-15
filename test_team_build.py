# -*- coding: utf-8 -*-
"""
test_team_build.py — حرس بناء سطح الفريق: **يُنفَّذ لا يُقرأ** (`DEC-289`)
============================================================================
سند: `DEC-269` (الدرس: تجميعٌ ينكسر صامتاً) · `DEC-278 §5` (قاعدة القلب) ·
     `DEC-277 §2` (رفع `ح-4` محصورٌ بسطح المالك)

**الحزمة المولَّدة تُشغَّل**: يُستخرج التوأم من `Team.html` نفسه ويُنفَّذ
في `node` بنافذةٍ وهمية، ويُقابَل مخرجُه بمخرج بايثون **حرفاً بحرف**.
فقراءةُ النصّ تُثبت وجودَ سطرٍ، **والتنفيذ يُثبت أنه يعمل**.

**ولا تُنشر**: فحصٌ مستقلٌّ يرفض أن تدخل `docs/` أو أن يُشار إليها منها.
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import team_report as TR

FAILS = []


def check(label, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + label + (" - " + detail if detail else ""))
    if not ok:
        FAILS.append(label)


CASE = [{"code": "T-01", "sp": {"A": 92, "C": 78, "O": 62, "R": 40,
                                "S": 35, "E": 30, "St": 28, "H": 25}},
        {"code": "T-02", "sp": {"E": 95, "S": 88, "R": 60, "A": 40,
                                "O": 35, "C": 30, "St": 28, "H": 25}},
        {"code": "T-03", "sp": {"H": 90, "St": 80, "A": 60, "R": 40,
                                "O": 35, "C": 30, "S": 28, "E": 25}}]

PROBE = r"""
"use strict";
const fs = require("fs"), vm = require("vm");
const html = fs.readFileSync(process.argv[2], "utf8");
const case_ = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));

// تُستخرج كتل النصّ البرمجي من الحزمة المولَّدة **كما هي**، ثم تُنفَّذ.
const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
const win = { console: console, JSON: JSON, Math: Math, Object: Object,
              Array: Array, String: String, Number: Number, Error: Error,
              TextEncoder: TextEncoder, Uint8Array: Uint8Array, Map: Map, Set: Set };
win.window = win; win.self = win; win.globalThis = win;
// عنصرٌ وهميٌّ يقبل ما تسنده الصفحة — فتُنفَّذ **كل** كتلة، حتى كتلة
// التطبيق. وتنفيذُ الحزمة كاملةً أقوى من انتقاء ما يُنفَّذ منها.
win.navigator = {};
win.document = { getElementById: () => ({ onclick: null, value: "", innerHTML: "" }) };
vm.createContext(win);
for (const b of blocks) vm.runInContext(b, win);
const T = win.RawahilTeam;
if (!T) { console.error("NO_TEAM"); process.exit(2); }
const [body, audit] = T.buildReport(case_, win.TEAM_PACK);
process.stdout.write(JSON.stringify({
  body: body, sections: audit.sections_rendered, sha: audit.report_sha256,
  locked: typeof win.fetch === "function",
}));
"""


def test_bundle_executes():
    import build_team_html as BT
    html = BT.build()
    io.open(BT.OUT, "w", encoding="utf-8").write(html)

    tmp = tempfile.mkdtemp(prefix="team_build_")
    try:
        probe = os.path.join(tmp, "probe.js")
        case_f = os.path.join(tmp, "case.json")
        io.open(probe, "w", encoding="utf-8").write(PROBE)
        io.open(case_f, "w", encoding="utf-8").write(
            json.dumps(CASE, ensure_ascii=False))
        r = subprocess.run(["node", probe, BT.OUT, case_f],
                           capture_output=True, text=True, cwd=HERE)
        if r.returncode != 0:
            check("1 الحزمة المولَّدة تُنفَّذ", False,
                  (r.stderr or r.stdout)[:160])
            return
        got = json.loads(r.stdout)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    body_py, audit_py = TR.build_report(CASE)
    check("1 الحزمة المولَّدة تُنفَّذ وتُخرج تقريراً",
          got["sections"] == 9, str(got["sections"]) + " قسماً")
    check("1 مخرَج الحزمة = مخرَج بايثون حرفاً بحرف",
          got["body"] == body_py and got["sha"] == audit_py["report_sha256"],
          "بصمة " + got["sha"])
    check("1 قفل صفر الشبكة مركَّبٌ وفاعل", got["locked"],
          "fetch مُستبدَلٌ برامٍ")


def test_not_published():
    docs = os.path.join(HERE, "docs")
    check("2 لا تدخل docs/", not os.path.exists(os.path.join(docs, "Team.html"))
          and not os.path.exists(os.path.join(docs, "team.html")), "")
    if os.path.isdir(docs):
        linked = [f for f in sorted(os.listdir(docs))
                  if f.endswith(".html")
                  and re.search(r"Team\.html|RawahilTeam",
                                io.open(os.path.join(docs, f), encoding="utf-8").read())]
        check("2 صفر إشارةٍ إليها من صفحةٍ منشورة", not linked, str(linked))
    r = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=HERE)
    if r.returncode == 0:
        check("2 الناتج غير متبَع", "Team.html" not in r.stdout.split("\n"), "")
    gi = io.open(os.path.join(HERE, ".gitignore"), encoding="utf-8").read()
    check("2 الإسقاط مُعلَن", "Team.html" in gi, "")


if __name__ == "__main__":
    print("=" * 76)
    test_bundle_executes()
    test_not_published()
    print("-" * 76)
    if FAILS:
        print("النتيجة النهائية: انحدار - " + str(len(FAILS)) + ": " +
              " · ".join(FAILS))
        raise SystemExit(1)
    print("النتيجة النهائية: لا انحدار")
