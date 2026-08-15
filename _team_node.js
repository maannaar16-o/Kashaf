/**
 * _team_node.js — جانب JS في قياس تكافؤ طبقة الفريق (`DEC-289`)
 * ================================================================
 * يقرأ الحالات ويُخرج المتن وكتلة التدقيق لكل حالة — وجانبُ بايثون
 * يقابلها حرفاً بحرف. **ولا حكم هنا**: القياس في `parity_team.py`.
 */
"use strict";
const fs = require("fs");
const path = require("path");
const TEAM = require("./team_core.js");

const HERE = __dirname;
const PACK = JSON.parse(fs.readFileSync(path.join(HERE, "team_contentpack.json"), "utf8"));
const CASES = JSON.parse(fs.readFileSync(path.join(HERE, "team_cases.json"), "utf8"));

const out = { team: {}, failure: {} };

for (const name of Object.keys(CASES.team).sort()) {
  const [body, audit] = TEAM.buildReport(CASES.team[name], PACK);
  out.team[name] = { body: body, audit: audit };
}
for (const name of Object.keys(CASES.failure).sort()) {
  try {
    TEAM.run(CASES.failure[name], PACK);
    out.failure[name] = { mode: "no-error", message: "" };
  } catch (e) {
    out.failure[name] = {
      mode: e instanceof TEAM.InputContractError ? "InputContractError"
                                                 : "other:" + e.constructor.name,
      message: String(e.message),
    };
  }
}
process.stdout.write(JSON.stringify(out));
