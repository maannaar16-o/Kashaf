/**
 * ws_payload.js — باني حمولة الورشة (`DEC-279`)
 * ================================================
 * **وحدةٌ نقية بلا مستند ولا نافذة** — تُحمَّل في المتصفح وفي `node` معاً،
 * فتُختبر الحمولة **بتنفيذها** لا بقراءة نصّها (درس `DEC-269`/`test_supervisor_build`).
 *
 * ولا تعرف مخطَّطاً ولا نصَّ إذن: يُمرَّران إليها من `workshop_store.py`
 * عبر البناء — **مصدر حقيقةٍ واحد** (`م-2`)، فلا نسخة ثانية لنصٍّ حاكم.
 */
(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) module.exports = factory();
  else root.RawahilWorkshopPayload = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  /**
   * يبني الحمولة من مخرَج `RawahilDualReport.generate` حرفياً.
   * لا يقرأ اسماً ولا أي حقلٍ خارج الرمز والإذن والتقارير — **صفر اعتماد**
   * (`DEC-277 §4`): لا كلمة مرور ولا تجزئتها، فالمخزن يعرف الرمز وحده.
   */
  function build(schema, consentText, code, gen) {
    if (!schema || !consentText) throw new Error("مخطَّط أو نصّ إذنٍ غائب");
    if (!gen) throw new Error("لا مخرَج توليد");
    var reports = {};
    if (gen.k2) reports.K2 = { markdown: gen.k2.text, audit: gen.k2.audit };
    if (gen.k3) reports.K3 = { markdown: gen.k3.text, audit: gen.k3.audit };
    if (gen.k4) {
      reports.K4 = { markdown: gen.k4.text, audit: gen.k4.audit };
      // السطح العابر **مخرجٌ مستقل** لا يُدمج في متن أي دائرة (`133 §3/①`)
      if (gen.crossing) {
        reports.K4.crossing = {
          markdown: gen.crossing.text, audit: gen.crossing.audit,
        };
      }
    }
    if (!Object.keys(reports).length) throw new Error("لا تقرير مولَّد — لا إرسال");
    return {
      schema: schema,
      code: String(code || "").trim().toUpperCase(),
      consent: { text: consentText, accepted: true },
      reports: reports,
    };
  }

  return { build: build };
});
