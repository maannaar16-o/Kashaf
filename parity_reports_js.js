"use strict";
const fs = require("fs");
const R = require("./reports.js");
const cases = JSON.parse(fs.readFileSync(__dirname + "/parity_cases.json", "utf8"));
const out = { k2: {}, k3: {} };
for (const [n, sp] of Object.entries(cases.k2)) for (const m of ["full","brief"]) out.k2[`${n}:${m}`] = R.buildReportK2(sp, m)[0];
for (const [n, sp] of Object.entries(cases.k3)) out.k3[n] = R.buildReportK3(sp)[0];
process.stdout.write(JSON.stringify(out));
