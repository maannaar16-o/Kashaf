"use strict";
/*
 * build_checks.js — فحوصات جانب JS لبناء الموقع (يشغّلها build_site.py)
 * =====================================================================
 * يتلقى ملف JSON: { K2_EXPECT, K3_MAP, BLOCKS } ويتحقق من:
 *  ① K2_EXPECT (منقول من 41 §5.2) == K2.ITEM_MAP في المحرك — تطابقاً عميقاً
 *  ② مسار الإجابات الحتمية: sp عبر الجسر == إعادة الحساب عبر المحرك (K2 وK3)
 *  ③ missingItems: فارغة على المكتمل · الاتحاد الكامل على الفارغ
 *  ④ سلامة الحزم وتوليد التقريرين واجتياز حارسَي المخرج
 * أي إخفاق ⇒ خروج بغير صفر ⇒ يفشل البناء كله.
 */
const fs = require("fs");
const path = require("path");
const HERE = path.dirname(__dirname); // site/
const ROOT = path.dirname(HERE);      // repo root

const { K2, K3 } = require(path.join(ROOT, "engines.js"));
const PK = require(path.join(ROOT, "packs.js"));
require(path.join(ROOT, "sp_gate.js"));
const SPG = globalThis.RawahilSPGate;
const RP = require(path.join(ROOT, "reports.js"));
const B = require(path.join(ROOT, "bridge.js"));

const cfg = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const { K2_EXPECT, K3_MAP, BLOCKS } = cfg;

function fail(msg) { console.error("❌ " + msg); process.exit(1); }
function deepEq(a, b) { return JSON.stringify(a) === JSON.stringify(b); }

// ① خريطة K2 المتوقعة (من الوثيقة) تطابق خريطة المحرك حرفياً
if (!deepEq(K2_EXPECT, K2.ITEM_MAP)) fail("K2_EXPECT (41 §5.2) لا يطابق K2.ITEM_MAP في المحرك");
if (!deepEq(Object.keys(K2.ITEM_MAP).sort(), [...K2.LENSES].sort())) fail("مفاتيح ITEM_MAP لا تطابق LENSES");

// ② الإجابات الحتمية: لكل بند 1..94 اختيار "a" · تقييم أ=6 · تقييم ب=1
const answers = {};
for (let n = 1; n <= 94; n++) answers[n] = { choice: "a", ratingA: 6, ratingB: 1 };

const K2_MAP_ADAPTED = Object.fromEntries(
  Object.entries(K2.ITEM_MAP).map(([k, v]) => [k, { items: v }]));
const spViaBridge = B.spK2(answers, K2_MAP_ADAPTED, K2.LENSES);

// إعادة الحساب من المحرك مباشرة — نفس معادلة الوعاء SS = x − 2z + y
function handSp(items, maxRaw) {
  let x = 0, y = 0;
  for (const [item, letter] of items) {
    const a = answers[item];
    x += letter === "a" ? a.ratingA : a.ratingB;
    if (a.choice === letter) y += 1;
  }
  const z = items.length - y;
  return (x - 2 * z + y) / maxRaw * 100.0;
}
for (const k of K2.LENSES) {
  const h = handSp(K2.ITEM_MAP[k], 42);
  if (Math.abs(spViaBridge[k] - h) !== 0) fail(`K2/${k}: جسر=${spViaBridge[k]} ≠ يدوي=${h}`);
}
// والمحرك نفسه عبر scoreFromRaw — طريق ثالث مستقل
// (يعيد {x,y,z,ss,sp,code} لكل عدسة، وsp فيه مقرَّبة لمنزلة واحدة تصريحاً)
const spViaEngine = K2.scoreFromRaw(answers);
for (const k of K2.LENSES) {
  const rounded = Math.round(spViaBridge[k] * 10) / 10;
  if (rounded !== spViaEngine[k].sp) fail(`K2/${k}: جسر=${rounded} ≠ scoreFromRaw=${spViaEngine[k].sp}`);
}

const spK3ViaBridge = B.spK3(answers, K3_MAP);
for (const [name, items] of Object.entries(K3_MAP)) {
  const code = B.K3_NAME_TO_CODE[name];
  if (!code) fail(`اسم مهارة K3 غير معرّف في الجسر: ${name}`);
  const h = handSp(items, 66);
  if (Math.abs(spK3ViaBridge[code] - h) !== 0) fail(`K3/${code}: جسر=${spK3ViaBridge[code]} ≠ يدوي=${h}`);
}

// ③ missingItems — الشكل الخام (مصفوفات أزواج) لا الشكل المهيّأ
const RAW_MAPS = [...Object.values(K2.ITEM_MAP), ...Object.values(K3_MAP)];
const allItems = [...new Set(RAW_MAPS.flat().map(([n]) => n))].sort((a, b) => a - b);
const missAll = B.missingItems({}, RAW_MAPS);
if (!deepEq(missAll, allItems)) fail("missingItems({}) لا يعيد اتحاد بنود K2∪K3 كاملاً");
if (B.missingItems(answers, RAW_MAPS).length !== 0) fail("missingItems على المكتمل ليست فارغة");

// ④ الحزم والتقريران وحارسا المخرج
PK.verifyPacks();
const [txt2] = RP.buildReportK2(spViaBridge, "full");
const [txt2b] = RP.buildReportK2(spViaBridge, "brief");
const [txt3] = RP.buildReportK3(spK3ViaBridge);
SPG.outputGate(txt2, "فحص البناء · K2 كامل");
SPG.outputGate(txt2b, "فحص البناء · K2 مختصر");
SPG.outputGate(txt3, "فحص البناء · K3");

// ⑤ جدول الكتل: 10 كتل [4×10 + 6×9] متصلة على 1..94 = 282 خطوة
if (BLOCKS.length !== 10) fail("عدد الكتل ≠ 10");
let expectStart = 1, steps = 0;
BLOCKS.forEach(([a, b], i) => {
  if (a !== expectStart) fail(`الكتلة ${i + 1} لا تبدأ من ${expectStart}`);
  const n = b - a + 1;
  if (n !== (i < 4 ? 10 : 9)) fail(`حجم الكتلة ${i + 1} = ${n}`);
  steps += 3 * n; expectStart = b + 1;
});
if (expectStart !== 95) fail("الكتل لا تنتهي عند 94");
if (steps !== 282) fail(`الخطوات = ${steps} ≠ 282 (CHG-021)`);

// ⑥ عُدّة المرآة (DEC-255/256): بنية نصوص الحزم كما تتوقعها الواجهة
const TXT = PK.PACKS.TEXTLAYER_K3;
if (!deepEq(Object.keys(TXT.VERIFY_QUESTIONS).sort(), ["BI", "CF", "IR", "ST"]))
  fail("VERIFY_QUESTIONS: المفاتيح ليست BI/CF/IR/ST");
const sepRows = TXT.SEPARATION_QS.split("\n").filter((l) => {
  const t = l.trim();
  if (!/^\|.*\|$/.test(t)) return false;
  const c = t.slice(1, -1).split("|").map((x) => x.trim());
  return c.length === 3 && !/^:?-+:?$/.test(c[0]) && c[0] !== "السلوك الشائع";
});
if (sepRows.length !== 8) fail(`SEPARATION_QS: صفوف الفصل = ${sepRows.length} ≠ 8`);
if (!TXT.VERIFY_BLOCK || !TXT.VERIFY_CLOSING) fail("نصوص كتلة التحقق ناقصة");

console.log("OK — فحوصات JS كلها مجتازة · K2 ثلاثي المسار · K3 مزدوج · التقريران يجتازان الحارسين · بنية عُدّة المرآة سليمة");
