"use strict";
/*
 * _sup_node.js — مِحمَل Node لطرف JS في parity_supervisor.py
 * أعيد بناؤه في ترحيل 2026-08-09 وضُمّ بالجرد المختوم (DEC-249 · 121-SUPNODE).
 * لا منطق هنا: يربط الوحدات بالنطاق العام كما تفعل build_supervisor_html.py
 * ثم يمرّر الحمولات إلى RawahilSupervisor.grade كما هي.
 */
const fs = require("fs");
globalThis.RawahilPacks = require("./packs.js");
require("./sp_gate.js"); // يُسند root.RawahilSPGate بنفسه
globalThis.RawahilEngines = require("./engines.js");
globalThis.RawahilReports = require("./reports.js");
const SV = require("./supervisor_core.js");

const payloads = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const out = payloads.map((p) => {
  try {
    return SV.grade(p);
  } catch (e) {
    return [[["EXC", false, `${e.name}: ${e.message}`]], ["EXC"]];
  }
});
process.stdout.write(JSON.stringify(out));
