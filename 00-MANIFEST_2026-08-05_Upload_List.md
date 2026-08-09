# 00-MANIFEST_2026-08-05 — بيان الرفع · **v2.7** (`DEC-248` · `CHG-066`)

| الحقل | البيان |
| :--- | :--- |
| **آخر قرار** | **`DEC-248`** · التالي **`DEC-249`** |
| **آخر تغيير** | **`CHG-066`** |
| **البصمات الثلاث** | `2711c24d8155819b` · `36ae94bfd5a8b60f` · `6b324f996856eac3` — **ثابتة** |
| **الأدوات** | **ستّ عشرة — كلّها خضراء** |

# 1) يُستبدَل — ثلاثة عشر

`01-MASTER` (**v3.7**) · `02-MASTER` (**v4.3**) · `00-INDEX` (**v4.1**) · **`56-REPORT-ENGINE` (v1.4)** · **`k2_report.py`** · **`k3_engine.py`** · **`00-PROTOCOL` (`ن-8`)** · `k3_content.py` ·
**`engines.js`** (توقيع `run` + العزل) · **`reports.js`** (المحوّل) ·
`k2_engine.py` · `k3_engine.py` · `k2_report.py` · `k3_report.py` · `dualreport.js` · `sp_gate.py` · `sp_gate.js` · `supervisor.py`

> ⚠️ **المحرّكات وطبقة التقرير مُعدَّلة.** إن أبقيت عرف `_FIXED` فأعد التسمية **وعدّل §3.2**.

# 2) يُضاف — تسعة

`supervisor_core.js` · `build_supervisor_html.py` · `parity_supervisor.py` · `parity_messages.py` · `parity_isolation.py` · `parity_surface.py` · **`guard_interp.py`** · **`interp_registry.json`** · `test_guard_sp.py` · **`test_guard_lock.py`** · الوثائق `105`…**`120`**

# 3) مُسقَط (`CHG-054`)

`packs.js` (يُولَّد) · `Kashaf.html` · `golden_k3_PRE-DEC-215.json`

# 4) الأداتان — تعيشان في المحادثة

| الأداة | الحجم | `SHA` |
| :--- | ---: | :--- |
| `Kashaf_v2_FIXED_DEC-230-245.html` | 1,116,516 | `2b89033c5a8c082c…` |
| `Supervisor.html` | — | `031c2dc71b8e1723…` |

**تُرفعان كل جلسة.** و`Supervisor.html` **مولَّدة** بـ`build_supervisor_html.py`.

# 5) أمر الاستئناف القادم

| # | التصويب |
| :--- | :--- |
| 1 | `آخر قرار: DEC-236 · التالي DEC-237` · آخر تغيير `CHG-060` |
| 2 | **§3.2 خطوة أولى إلزامية:** `python3 build_packs.py` |
| 3 | **§3.3 تصير خمسة عشر** — بإضافة `test_guard_sp` · `parity_supervisor` · `parity_messages` · `parity_isolation` · `parity_surface` · **`guard_interp`** · `supervisor --self-test`. كلّها خضراء |
| 4 | §1 البوابة — `DEC-248` في الماسترَين · `ن-8` في `00-PROTOCOL` · الوثائق `104`…`120` في الفهرس |
| 5 | ✅ **`GAP-RETEST-01` مُغلقة** بـ`116-RETEST` — **حظر قراءة الفارق الزمني نافذ** حتى تُستوفى شروط §7 |

# 6) مفتوح — لم يرد به أمر


- `GAP-RETEST-01` — وثيقة قراءة الفارق الزمني (**بناء مُقرّ · مؤجَّل**)
- 🔒 **`GAP-A-01-BND`** — الدائرتان تتعارضان عند `SP=50.0` (عمى في $K_2$ · مساندة في $K_3$) · **مجمَّدة · تحتاج حكم المالك**
- 🟡 **`GAP-VALID-01`** — ① أداة جاهزة · ② **بروتوكول جاهز · يحتاج ميداناً** · ③ ✅ مُغلقة بالسند (`DEC-184`)
- 🔒 **`GAP-ITEM-SIDE-01`** — سُلَّم الجانب أ/ب · اختبارٌ ممكن ببيانات استجابة وحدها
- 🔒 **`GAP-ITEM-K3-01`** — لا خريطة بنود في محرّك $K_3$
- مزامنة `accepted_debts` مع `02-MASTER` **يدوية بحدّ مُعلَن** (`DEC-245`)

**[نهاية `00-MANIFEST_2026-08-05` **v1.5**]**
