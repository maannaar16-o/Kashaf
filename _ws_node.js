/**
 * _ws_node.js — يبني حمولة الورشة **بجانب JS** ليحكمها جانب بايثون
 * ==================================================================
 * سند: `DEC-279`. الغرض برهانٌ طرفيّ: التقارير تُولَّد بالتوأم `JS`
 * (وهو ما يعمل فعلاً في صفحة الورشة)، وتُصاغ الحمولة بالوحدة التي
 * تُحمَّل في تلك الصفحة نفسها — ثم يحكمها `workshop_store` في بايثون.
 * فإن قبِلها، فالسطح والمخزن متّفقان **بالتنفيذ** لا بالقراءة.
 */
"use strict";
const fs = require("fs");
const RP = require("./reports.js");
const WP = require("./site/workshop/ws_payload.js");

const cfg = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));

const [t2, a2] = RP.buildReportK2(cfg.sp2, "full");
const [t3, a3] = RP.buildReportK3(cfg.sp3);
const [t4, a4] = RP.buildReportK4(cfg.sp4);
const [xt, xa] = RP.buildCrossingSurface(cfg.sp4);

const gen = {
  k2: { text: t2, audit: a2 },
  k3: { text: t3, audit: a3 },
  k4: { text: t4, audit: a4 },
  crossing: xt ? { text: xt, audit: xa } : null,
  errors: [],
};

const payload = WP.build(cfg.schema, cfg.consent, cfg.code, gen);
process.stdout.write(JSON.stringify(payload));
