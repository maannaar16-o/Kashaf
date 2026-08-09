"use strict";
/**
 * bridge.js — جسر الأداة ← المحرّكين (المرحلة ④-ب)
 * =================================================
 * يحوّل `answers` من الاستبيان إلى `sp` بالصيغة التي يقبلها المحرّكان.
 *
 * 🔒 لا يُعيد حساباً ولا يُعرّف مصفوفة: مصفوفات البنود تُقرأ من
 *    `K2_MAP`/`K3_MAP` القائمتين في الأداة — وقد فُحصتا مقابل
 *    `41-Raw_Measure v4.2 §5.2/§5.3` فطابقتا 1:1.
 *
 * جدار العزل (§6): تقريران منفصلان لا يتقاطعان. لا دالة هنا
 * تُمرّر قيمة من K2 إلى K3 أو العكس (DEC-205).
 */
(function (root) {

  // §5.3 — ربط اسم المهارة العربي في الأداة بكود المحرك
  const K3_NAME_TO_CODE = {
    "قوة الملاحظة": "EP",       // K3-EP · قوة الملاحظة الانفعالية
    "التحكم الانفعالي": "IR",   // K3-IR · التحكم الانفعالي الداخلي
    "كبح جماح النفس": "BI",     // K3-BI · كبح جماح النفس الميكانيكي
    "المرونة": "CF",            // K3-CF · المرونة الانفعالية والتكيف
    "تحمل الضغوط": "ST",        // K3-ST · تحمل الضغوط والإنقاذ العصبي
  };

  class BridgeContractError extends Error {
    constructor(m) { super(m); this.name = "BridgeContractError"; }
  }

  /** SS = x − 2z + y — نفس معادلة `calcVessel` (41 §3). */
  function vessel(answers, items) {
    let x = 0, y = 0;
    for (const [item, letter] of items) {
      const a = answers[item];
      if (!a) throw new BridgeContractError(`البند ${item} متروك — عقد المدخل يمنع الإكمال (41 §7)`);
      x += (letter === "a") ? a.ratingA : a.ratingB;
      if (a.choice === letter) y += 1;
    }
    const z = items.length - y;
    return { x, y, z, ss: x - 2 * z + y, n: items.length };
  }

  /** sp لـK2 — ثمانية أبعاد · MAX_RAW = 42. */
  function spK2(answers, K2_MAP, K2_ORDER) {
    const sp = {};
    for (const k of K2_ORDER) {
      const v = vessel(answers, K2_MAP[k].items);
      if (v.n !== 7) throw new BridgeContractError(`K2/${k}: ${v.n} بنداً بدل 7`);
      sp[k] = v.ss / 42 * 100.0;
    }
    return sp;
  }

  /** sp لـK3 — خمس مهارات · MAX_RAW = 66. */
  function spK3(answers, K3_MAP) {
    const sp = {};
    for (const [name, items] of Object.entries(K3_MAP)) {
      const code = K3_NAME_TO_CODE[name];
      if (!code) throw new BridgeContractError(`مهارة K3 غير معرَّفة: «${name}»`);
      const v = vessel(answers, items);
      if (v.n !== 11) throw new BridgeContractError(`K3/${code}: ${v.n} بنداً بدل 11`);
      sp[code] = v.ss / 66 * 100.0;
    }
    const missing = ["EP", "IR", "BI", "CF", "ST"].filter((s) => !(s in sp));
    if (missing.length) throw new BridgeContractError(`مهارات K3 ناقصة: ${missing}`);
    return sp;
  }

  /** فحص اكتمال الاستبيان قبل أي توليد — لا تقرير على إجابات ناقصة. */
  function missingItems(answers, maps) {
    const need = new Set();
    for (const m of maps) for (const [it] of m) need.add(it);
    return Array.from(need).filter((it) => !answers[it]).sort((a, b) => a - b);
  }

  root.RawahilBridge = {
    K3_NAME_TO_CODE, vessel, spK2, spK3, missingItems, BridgeContractError,
  };

})(typeof window !== "undefined" ? window : globalThis);

if (typeof module !== "undefined") module.exports = (typeof window !== "undefined" ? window : globalThis).RawahilBridge;
