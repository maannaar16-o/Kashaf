/**
 * _ws_lock_probe.js — يقيس القفل المضيَّق **بتشغيله** لا بقراءة نصّه
 * ====================================================================
 * سند: `DEC-279`. الحقلُ الذي يقرأ وجود رمزٍ في صفحةٍ **لا يقيس شيئاً**:
 * قفلٌ وُسِّع خطأً يُبقي رمزَه. فيُركَّب القفل على نافذةٍ وهمية وتُجرَّب
 * عليه خمس محاولات — أربعٌ يجب أن تُرفض وواحدةٌ يجب أن تمرّ.
 */
"use strict";
const fs = require("fs");
const vm = require("vm");

const src = fs.readFileSync(process.argv[2], "utf8");
let reached = null;

const win = {
  fetch: function (url, opts) { reached = { url: url, opts: opts }; return "SENT"; },
  XMLHttpRequest: function () {}, WebSocket: function () {}, EventSource: function () {},
  location: { href: "http://127.0.0.1:8787/", origin: "http://127.0.0.1:8787" },
  navigator: { sendBeacon: function () { return true; } },
  URL: URL, Object: Object, Error: Error, String: String,
};
win.window = win;
vm.createContext(win);
vm.runInContext(src, win);

function denied(fn) {
  try { fn(); return false; } catch (e) { return true; }
}

const r = {
  installed: !!(win.CPL_WORKSHOP_RUNTIME && win.CPL_WORKSHOP_RUNTIME.id === "CPL-WS-01"),
  xhr_denied: denied(function () { new win.XMLHttpRequest(); }),
  ws_denied: denied(function () { new win.WebSocket("ws://x"); }),
  es_denied: denied(function () { new win.EventSource("http://x"); }),
  beacon_denied: denied(function () { win.navigator.sendBeacon("http://x", "y"); }),
  foreign_origin_denied:
    denied(function () { win.fetch("https://evil.example/submit", { method: "POST" }); }),
  other_path_denied:
    denied(function () { win.fetch("/other", { method: "POST" }); }),
  get_denied: denied(function () { win.fetch("/submit", { method: "GET" }); }),
  no_opts_denied: denied(function () { win.fetch("/submit"); }),
};
r.submit_allowed = (win.fetch("/submit", { method: "POST", body: "{}" }) === "SENT");
r.submit_same_origin = !!(reached &&
  String(reached.url).indexOf("http://127.0.0.1:8787/submit") === 0);
process.stdout.write(JSON.stringify(r));
