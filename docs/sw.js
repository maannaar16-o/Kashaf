"use strict";
/* sw.js — مولَّد بـ build_site.py (DEC-251) — لا يُحرَّر يدوياً.
 * تخزين ذرّي مُصدَّر ببصمة الموقع: إما النسخة الجديدة كاملة أو القديمة كاملة.
 * النطاق: ملفات هذا الموقع نفسها حصراً — لا يمرّر ولا يخزّن أي أصل خارجي. */
const CACHE = "kashaf-646ccc2692a110fe";
const ASSETS = ["./", "./about.html", "./assets/icons/icon-192.png", "./assets/icons/icon-512-maskable.png", "./assets/icons/icon-512.png", "./assets/site.css", "./contribute.html", "./index.html", "./kashaf.html", "./manifest.json", "./method.html", "./sample.html", "./teams.html", "./theory.html"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then((r) => r || fetch(e.request)));
});
