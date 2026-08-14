# -*- coding: utf-8 -*-
"""
team_engine.py — محرّك تركيب الفريق (`56-TEAM-00`)
====================================================
سند: `DEC-277` (تشغيل الميثاق) · `DEC-039` (اعتماد المصفوفات) ·
     `DEC-041`/`DEC-157` (عتبات المهيمن/المساند) · `DEC-040` (وسم `GAP-A-02`)

**لا يعرّف عتبةً ولا يحسب درجة.** يستقبل تقارير أفراد **معتمدة** (عقد
المدخل `56-TEAM-00 §1`) ويشتقّ منها التركيب. والعتبات تُقرأ من
`k2_engine.comp_state` — **مصدرُ حقيقةٍ واحد**، فلا رقم مكرَّر هنا.

**صفر لمس `K1`/`K3`/`K4`** (`56-TEAM-00 §4`): هذا المحرّك لا يعرف إلا
عدسات $K_2$ الثماني، ولا يستقبل حقلاً من دائرةٍ أخرى.
"""
import json
import os

import k2_engine as E2

HERE = os.path.dirname(os.path.abspath(__file__))

LENSES = list(E2.LENSES)
ENGINE_VERSION = "1.0"
SPEC_VERSION = "56-TEAM-00 v1.0"
INSTRUMENT_PIN = E2.INSTRUMENT_PIN if hasattr(E2, "INSTRUMENT_PIN") else "40 v5.0 + 41 v4.2"
MIN_MEMBERS = 2                      # `56-TEAM-00 §1` — عضوان حدّاً أدنى
FULL_MATRIX_MAX = 4                  # `§5` — حتى n=4 تُعرض كل الأزواج


class InputContractError(ValueError):
    """خرق عقد المدخل — إيقاف بلا إصلاح صامت (`56-TEAM-00 §1`)."""


class ContentPack:
    """حزمة `CONTENT_TEAM` — تُحمَّل ولا تُؤلَّف."""

    def __init__(self, raw=None):
        if raw is None:
            with open(os.path.join(HERE, "team_contentpack.json"),
                      encoding="utf-8") as fh:
                raw = json.load(fh)
        self.raw = raw

    def require(self):
        need = ("dyad", "polar", "blind", "rebound", "combo", "heading", "lock")
        missing = [k for k in need if k not in self.raw]
        if missing:
            raise InputContractError(
                f"حزمة الفريق ناقصة {missing} — لا تقرير بلا حزمة (صفر تأليف)")
        return self


def _validate(members):
    if not isinstance(members, (list, tuple)):
        raise InputContractError("قائمة الأعضاء ليست تسلسلاً")
    if len(members) < MIN_MEMBERS:
        raise InputContractError(
            f"عضوان حدّاً أدنى — وُجد {len(members)} (`56-TEAM-00 §1`)")
    codes = []
    for m in members:
        if not isinstance(m, dict) or "code" not in m or "sp" not in m:
            raise InputContractError("عضوٌ بلا `code` أو `sp`")
        code = str(m["code"]).strip()
        if not code:
            raise InputContractError("رمز عضوٍ فارغ")
        if code in codes:
            raise InputContractError(f"رمز عضوٍ مكرَّر: {code}")
        codes.append(code)
        sp = m["sp"]
        if not isinstance(sp, dict):
            raise InputContractError(f"{code}: `sp` ليس قاموساً")
        for d in LENSES:
            if d not in sp:
                raise InputContractError(f"{code}: عدسة ناقصة {d}")
            try:
                f = float(sp[d])
            except (TypeError, ValueError):
                raise InputContractError(f"{code}/{d}: قيمة غير عددية")
            # غير المنتهي يُرفض صراحةً — وإلا صُنِّف «مهيمناً» صامتاً
            # (الدرس نفسه المقيَّد في `k4_engine._validate`).
            if f != f or f in (float("inf"), float("-inf")):
                raise InputContractError(f"{code}/{d}: قيمة غير منتهية")
        extra = [k for k in sp if k not in LENSES]
        if extra:
            raise InputContractError(
                f"{code}: حقول من خارج عدسات $K_2$ — {extra} (`§4`: صفر لمس K1/K3/K4)")


def profile(sp):
    """حالة كل عدسة — **بدوالّ `k2_engine` لا بعتبةٍ تُكتب هنا**."""
    st = {d: E2.comp_state(float(sp[d])) for d in LENSES}
    return {
        "state": st,
        "band": {d: E2.octal_code(float(sp[d])) for d in LENSES},
        "dominant": [d for d in LENSES if st[d] == "D"],
        "support": [d for d in LENSES if st[d] == "M"],
        "blind": [d for d in LENSES if st[d] == "L"],
    }


def _rank(sp, codes):
    """ترتيب بالـSP تنازلياً · وكسر التعادل بترتيب `41 §5.2` (`DEF-K2-04`)."""
    return sorted(codes, key=lambda d: (-float(sp[d]), LENSES.index(d)))


def coverage(mem):
    """§2 — خريطة التغطية العدسية: من يقود كل عدسة، وأيّها بلا قائد."""
    out = {}
    for d in LENSES:
        dom = [m["code"] for m in mem if d in m["profile"]["dominant"]]
        sup = [m["code"] for m in mem if d in m["profile"]["support"]]
        out[d] = {"dominant": dom, "support": sup,
                  "level": "led" if dom else ("support_only" if sup else "absent")}
    return out


def collective_blind(mem, pack):
    """§3 — العمى المشترك بين الأبعاد المهيمنة **جميعاً** (`51-MATRIX-04 §2`)."""
    dom = sorted({d for m in mem for d in m["profile"]["dominant"]},
                 key=LENSES.index)
    uncovered = [d for d in LENSES
                 if not any(d in m["profile"]["dominant"] for m in mem)]
    # التركيبة الموثَّقة تنطبق بشرطين معاً: أبعادها **مهيمنة في الفريق**،
    # و**البُعد الذي تطلبه غائبٌ فعلاً**. والاكتفاء بالشرط الأول يُطابق
    # ستّ تركيبات على فريقٍ واسع الهيمنة فيصير الاستدعاء ضجيجاً لا قراءة —
    # والتشغيل المعتمد `56-TEAM-P001` يستدعي **واحدة** تطابق فجوته.
    matched = []
    for c in pack.raw["combo"]:
        if not set(c["lenses"]).issubset(set(dom)):
            continue
        need = [d for d in LENSES if f"${d}$" in c["need"]]
        # **كل** ما تطلبه التركيبة غائبٌ فعلاً — لا بعضُه: **الاحتواء
        # التام** (`DEC-282` · `56-TEAM-00 §7/②`). والتقاطع الجزئي يستدعي
        # ثلاث تركيبات على حالة `56-TEAM-P001` بينما التشغيل المعتمد يستدعي
        # **واحدة**؛ وبالاحتواء التام يُستعاد مخرجه. **ختمها المالك.**
        if need and set(need) <= set(uncovered):
            matched.append(dict(c, need_codes=need))
    return {"team_dominant": dom, "uncovered": uncovered, "documented": matched}


def polar_pairs(pack):
    return [(p["a"], p["b"], p["code"]) for p in pack.raw["polar"]]


def inter_polarity(mem, pack):
    """§6 — القطبية بين شخصين (`56-TEAM-00 §3`): كلٌّ **مهيمنٌ** في طرفٍ
    من زوجٍ قطبي، والآخر في الطرف المقابل."""
    out = []
    for i in range(len(mem)):
        for j in range(i + 1, len(mem)):
            a, b = mem[i], mem[j]
            for x, y, code in polar_pairs(pack):
                for p, q in ((x, y), (y, x)):
                    if p in a["profile"]["dominant"] and q in b["profile"]["dominant"]:
                        out.append({"a": a["code"], "b": b["code"],
                                    "lens_a": p, "lens_b": q, "polar": code})
    return out


def _dyad_key(x, y, pack):
    return f"{x}–{y}" if f"{x}–{y}" in pack.raw["dyad"] else f"{y}–{x}"


def pair_matrix(mem, pack):
    """§5 — لكل عضوين تقاطعٌ واحد.

    **قاعدةٌ مختومة** (`DEC-282` · `56-TEAM-00 §7/①`): **يُقدَّم الزوج
    القطبي إن وُجد بين مهيمنَيهما، وإلا فأعلى مهيمنٍ لكلٍّ** — والترتيب
    بالـ`SP` تنازلياً وكسرُ التعادل بترتيب `41 §5.2` (`_rank`).

    قُرئت من التشغيل التجريبي المعتمد `56-TEAM-P001` (ثلاثة صفوف متسقة)
    ورُفعت قراءةً في `DEC-278 §4`، ثم **ختمها المالك**.
    """
    out = []
    polars = polar_pairs(pack)
    for i in range(len(mem)):
        for j in range(i + 1, len(mem)):
            a, b = mem[i], mem[j]
            da = _rank(a["sp"], a["profile"]["dominant"])
            db = _rank(b["sp"], b["profile"]["dominant"])
            if not da or not db:
                out.append({"a": a["code"], "b": b["code"], "cross": None,
                            "reason": "no_dominant"})
                continue
            pick = None
            for x, y, code in polars:
                if x in da and y in db:
                    pick = (x, y, code)
                elif y in da and x in db:
                    pick = (y, x, code)
                if pick:
                    break
            lx, ly, pcode = pick if pick else (da[0], db[0], None)
            # **تقاطعٌ على العدسة نفسها لا خليةَ مختومةً له**: `51-MATRIX-01`
            # جدولُ ثمانيةٍ وعشرين زوجاً **متمايزة** (`C(8,2)`)، والميثاق
            # `§2/5` يقول «بين كل عضوين **متقاطعين**». فلا تُخترع خلية ولا
            # يُنتقى بديلٌ بقاعدةٍ بلا سند — **يُعلَن الخلوّ**.
            # **قاعدةٌ دائمة بختم المالك** (`DEC-281`, `GAP-TEAM-02` مُغلقة):
            # والعدستان تُعرضان كما هما فيرى القارئ **سبب** الخلوّ بلا
            # جملةٍ مؤلَّفة.
            if lx == ly:
                out.append({"a": a["code"], "b": b["code"], "lens_a": lx,
                            "lens_b": ly, "dyad": None, "polar": pcode,
                            "by": "same_lens", "reason": "same_lens"})
                continue
            key = _dyad_key(lx, ly, pack)
            out.append({"a": a["code"], "b": b["code"], "lens_a": lx,
                        "lens_b": ly, "dyad": key, "polar": pcode,
                        "by": "polar" if pick else "top_dominant"})
    return out


def rebound(mem, pack):
    """§7 — مسار الارتداد لكل عضوٍ عن عدسته المهيمنة الأعلى (`51-MATRIX-03`)."""
    # **كل** عدسةٍ مهيمنة لكل عضو — لا اختيار واحدةٍ منها (`DEC-282` ·
    # `56-TEAM-00 §7/③`). والتشغيل المعتمد `56-TEAM-P001` يعرض لـ`T-01`
    # عدسته الثانية (`C`) لا الأولى (`A`)، فلا قاعدة اختيارٍ تُستخرج منه؛
    # والعرض الكامل **يُغني عن قاعدةٍ تُخترع** ويشمل ما عرضه (`م-8`).
    # **ختمها المالك.**
    out = []
    for m in mem:
        dom = _rank(m["sp"], m["profile"]["dominant"])
        if not dom:
            out.append({"code": m["code"], "lens": None, "has_path": False})
            continue
        for d in dom:
            out.append({"code": m["code"], "lens": d, "has_path": True})
    return out


def recommendation(cov):
    """§8 — العدسة الغائبة المطلوب استقطابها: بلا مهيمنٍ أصلاً أوّلاً."""
    absent = [d for d in LENSES if cov[d]["level"] == "absent"]
    support_only = [d for d in LENSES if cov[d]["level"] == "support_only"]
    return {"absent": absent, "support_only": support_only,
            "gap": absent + support_only}


def run(members, content=None):
    """التركيب الكامل — مخرجه بنيةٌ يقرؤها `team_report`."""
    pack = (content or ContentPack()).require()
    _validate(members)
    mem = []
    for m in members:
        sp = {d: float(m["sp"][d]) for d in LENSES}
        mem.append({"code": str(m["code"]).strip(), "sp": sp,
                    "profile": profile(sp)})
    cov = coverage(mem)
    n = len(mem)
    audit = {
        "engine_version": ENGINE_VERSION, "spec_version": SPEC_VERSION,
        "instrument_pin": INSTRUMENT_PIN,
        "n_members": n, "members": [m["code"] for m in mem],
        "band": {m["code"]: m["profile"]["band"] for m in mem},
        "state": {m["code"]: m["profile"]["state"] for m in mem},
        "coverage": cov,
        "collective_blind": collective_blind(mem, pack),
        "pairs": pair_matrix(mem, pack),
        "inter_polarity": inter_polarity(mem, pack),
        "rebound": rebound(mem, pack),
        "recommendation": recommendation(cov),
        "full_matrix": n <= FULL_MATRIX_MAX,
        "unification_tag": "GAP-A-01/GAP-A-02 — توحيد تشغيلي مؤقت (DEC-040/041)",
        "accepted_debts": ["GAP-A-01", "GAP-A-02"],
        "open_debts": ["GAP-K2-TEAMBLIND-01"],
    }
    return {"members": mem, "audit": audit, "pack": pack}


if __name__ == "__main__":
    import sys as _s
    demo = [{"code": "T-01", "sp": {"A": 92, "C": 78, "O": 62, "R": 40,
                                    "S": 35, "E": 30, "St": 28, "H": 25}},
            {"code": "T-02", "sp": {"E": 95, "S": 88, "R": 60, "A": 40,
                                    "O": 35, "C": 30, "St": 28, "H": 25}},
            {"code": "T-03", "sp": {"H": 90, "St": 80, "A": 60, "R": 40,
                                    "O": 35, "C": 30, "S": 28, "E": 25}}]
    a = run(demo)["audit"]
    print(json.dumps({k: a[k] for k in ("coverage", "pairs", "inter_polarity",
                                        "recommendation")},
                     ensure_ascii=False, indent=1)[:1400])
