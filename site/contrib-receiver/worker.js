"use strict";
/*
 * worker.js — التنفيذ المرجعي لنقطة استقبال الإسهام (DEC-253) — Cloudflare Worker
 * ================================================================================
 * غير منشور من المستودع — يُنشره مالك المشروع بحسابه ثم يفعَّل الرابط في build_site.py.
 *
 * عهود الخصوصية المنفَّذة هنا (وتُنشر في المواصفة العلنية):
 *  · لا يُخزَّن عنوان الشبكة ولا أي ترويسة تعريفية — الحمولة المتحقَّق منها وحدها
 *  · معرّف السجل عشوائي — لا اشتقاق من أي شيء يخص المُرسِل
 *  · يُقبل فقط ما يطابق RAWAHIL-CONTRIB-v1 حرفياً: 94 بنداً بمداها الصحيح
 *
 * الربط المطلوب: KV namespace باسم CONTRIB. النشر: wrangler deploy.
 */

const ALLOWED_ORIGIN = "https://maannaar16-o.github.io";

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

function bad(msg, status) {
  return new Response(JSON.stringify({ ok: false, error: msg }),
    { status: status || 400, headers: { "Content-Type": "application/json", ...corsHeaders() } });
}

function validate(p) {
  if (!p || p.schema !== "RAWAHIL-CONTRIB-v1") return "schema";
  if (!p.instrument || p.instrument.measure !== "40-MEASURE v5.0") return "instrument";
  if (typeof p.submitted !== "string" || !/^\d{4}-\d{2}$/.test(p.submitted)) return "submitted";
  const a = p.answers;
  if (!a || typeof a !== "object") return "answers";
  const keys = Object.keys(a);
  if (keys.length !== 94) return "count";
  for (let n = 1; n <= 94; n++) {
    const r = a[String(n)];
    if (!r) return "missing:" + n;
    if (r.choice !== "a" && r.choice !== "b") return "choice:" + n;
    for (const k of ["ratingA", "ratingB"]) {
      if (!Number.isInteger(r[k]) || r[k] < 1 || r[k] > 6) return k + ":" + n;
    }
    if (Object.keys(r).length !== 3) return "extra:" + n;   // لا حقول زائدة
  }
  if (Object.keys(p).length !== 4) return "extra-top";
  return null;
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS")
      return new Response(null, { status: 204, headers: corsHeaders() });
    if (request.method !== "POST") return bad("POST only", 405);

    let payload;
    try { payload = await request.json(); } catch (e) { return bad("json"); }

    const err = validate(payload);
    if (err) return bad(err, 422);

    // إعادة البناء الصريحة: يُخزَّن ما تحقَّقنا منه فقط — لا تمرير للجسم الخام
    const clean = {
      schema: payload.schema,
      instrument: {
        measure: payload.instrument.measure,
        scoring: payload.instrument.scoring,
        build: String(payload.instrument.build || "").slice(0, 16),
      },
      submitted: payload.submitted,
      answers: payload.answers,
    };
    const id = crypto.randomUUID();
    await env.CONTRIB.put("c_" + id, JSON.stringify(clean));

    return new Response(JSON.stringify({ ok: true }),
      { status: 201, headers: { "Content-Type": "application/json", ...corsHeaders() } });
  },
};
