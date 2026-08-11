"use strict";
/*
 * app.js — تطبيق «الكشاف» v2 (DEC-251 · DEC-252)
 * =================================================
 * المرحلة ②: ملفات متعددة محلية · أرشيف تقارير · نسخة احتياطية · مشاركة كملف.
 * التخزين: IndexedDB (مخازن profiles/progress/archive) مع هجرة من مخزن v1.
 *
 * قواعد مختومة منفَّذة هنا:
 *  · تدفق DEC-035: اختيار أ/ب لكل الكتلة ثم تقييم كل جملة مفردة دون إظهار الاختيار
 *  · التقييم 1–6 بأزرار حصراً — الواجهة نقطة إنفاذ المدى
 *  · نقطة تحويل وحيدة أ/ب → "a"/"b" (زرّا الاختيار)
 *  · إجابات موسومة ببصمة بناء — تغيّر الأداة يُبطل المحفوظ (درس GAP-Q-01)
 *  · الأرشيف يحفظ النص المُسلَّم وكتلة تدقيقه حرفياً ويعرضه وحده —
 *    لا شاشة تجمع قياسين ولا قراءة لفارق زمني (DEC-244) — قيد بنيوي
 *  · لا لوحة K1/K4 (DEC-186) · أدوات التحقق الذاتي خارج الشحنة حتى اعتماد عُدّتها
 */
(function () {
  var D = window.KashafData;
  var EN = window.RawahilEngines;
  var B = window.RawahilBridge;
  var PK = window.RawahilPacks;
  var DR = window.RawahilDualReport;

  // ── الخرائط — K2 من المحرك مباشرة (مصدر الحقيقة الواحد) ──────────────
  var K2_MAP = {};
  Object.keys(EN.K2.ITEM_MAP).forEach(function (k) {
    K2_MAP[k] = { items: EN.K2.ITEM_MAP[k] };
  });
  var K2_ORDER = EN.K2.LENSES;
  var K3_MAP = D.K3_MAP;
  // missingItems تستقبل مصفوفات الأزواج الخام لا الشكل المهيّأ
  var RAW_MAPS = Object.keys(EN.K2.ITEM_MAP).map(function (k) { return EN.K2.ITEM_MAP[k]; })
    .concat(Object.keys(K3_MAP).map(function (k) { return K3_MAP[k]; }));

  var LEGACY_KEY = "rawahil.kashaf.v1";
  var root = document.getElementById("app");

  // ── IndexedDB — مساعد موعود صغير ─────────────────────────────────────
  var db = null;
  function openDb() {
    return new Promise(function (res, rej) {
      var r = indexedDB.open("rawahil-kashaf", 1);
      r.onupgradeneeded = function () {
        var d = r.result;
        d.createObjectStore("profiles", { keyPath: "id" });
        d.createObjectStore("progress", { keyPath: "profileId" });
        d.createObjectStore("archive", { keyPath: "id" })
          .createIndex("byProfile", "profileId", { unique: false });
      };
      r.onsuccess = function () { res(r.result); };
      r.onerror = function () { rej(r.error); };
    });
  }
  function op(store, mode, fn) {
    return new Promise(function (res, rej) {
      var t = db.transaction(store, mode);
      var out = fn(t.objectStore(store));
      t.oncomplete = function () { res(out && "result" in out ? out.result : undefined); };
      t.onerror = function () { rej(t.error); };
    });
  }
  function getAll(store) { return op(store, "readonly", function (s) { return s.getAll(); }); }
  function get(store, key) { return op(store, "readonly", function (s) { return s.get(key); }); }
  function put(store, val) { return op(store, "readwrite", function (s) { return s.put(val); }); }
  function del(store, key) { return op(store, "readwrite", function (s) { return s.delete(key); }); }
  function archiveOf(pid) {
    return op("archive", "readonly", function (s) { return s.index("byProfile").getAll(pid); });
  }
  function newId(prefix) {
    return prefix + "_" + Date.now().toString(36) + "_" +
      Math.random().toString(36).slice(2, 8);
  }

  // ── حالة التشغيل ──────────────────────────────────────────────────────
  var S = { profile: null, cursor: null, answers: {}, name: "" };
  var reactRoot = null;

  function saveProgress() {
    if (!S.profile) return;
    put("progress", {
      profileId: S.profile.id, v: D.BUILD.hash, cursor: S.cursor,
      answers: S.answers, savedAt: new Date().toISOString(),
    });
  }
  function clearProgress() { if (S.profile) del("progress", S.profile.id); }

  // ── أدوات عرض ─────────────────────────────────────────────────────────
  var AR_D = "٠١٢٣٤٥٦٧٨٩";
  function ar(n) { return String(n).replace(/\d/g, function (d) { return AR_D[+d]; }); }
  function arDate(iso) {
    var d = new Date(iso);
    return ar(d.getFullYear()) + "/" + ar(d.getMonth() + 1) + "/" + ar(d.getDate()) +
      " · " + ar(d.getHours()) + ":" + ar(String(d.getMinutes()).padStart(2, "0"));
  }
  function el(tag, cls, txt) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (txt !== undefined) n.textContent = txt;
    return n;
  }
  function screen() { unmountReact(); root.textContent = ""; var s = el("div", "scr"); root.appendChild(s); return s; }
  function unmountReact() {
    if (reactRoot) { try { reactRoot.unmount(); } catch (e) {} reactRoot = null; }
  }
  function sentenceNode(segs, cls) {
    var p = el("p", cls);
    segs.forEach(function (g) {
      p.appendChild(Object.assign(el("span", g.t === "note" ? "q-note" : ""), { textContent: g.s }));
    });
    return p;
  }
  function download(content, filename, mime) {
    var blob = new Blob([content], { type: mime });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  }

  function blockItems(bi) {
    var r = D.BLOCKS[bi], out = [];
    for (var n = r[0]; n <= r[1]; n++) out.push(n);
    return out;
  }
  var TOTAL_STEPS = 0;
  D.BLOCKS.forEach(function (r) { TOTAL_STEPS += 3 * (r[1] - r[0] + 1); });

  function stepNumber() {
    var c = S.cursor, done = 0;
    for (var i = 0; i < c.block; i++) done += 3 * (D.BLOCKS[i][1] - D.BLOCKS[i][0] + 1);
    var n = blockItems(c.block).length;
    done += (c.phase === "choice") ? c.idx : n + c.idx;
    return done + 1;
  }

  function progressHeader(box) {
    var c = S.cursor;
    var h = el("div", "prog");
    h.appendChild(el("div", "prog-line",
      "الكتلة " + ar(c.block + 1) + " من " + ar(D.BLOCKS.length) +
      " · " + (c.phase === "choice" ? "المرحلة الأولى — الاختيار" : "المرحلة الثانية — التقييم") +
      " · الخطوة " + ar(stepNumber()) + " من " + ar(TOTAL_STEPS)));
    var bar = el("div", "prog-bar"), fill = el("div", "prog-fill");
    fill.style.width = ((stepNumber() - 1) / TOTAL_STEPS * 100).toFixed(2) + "%";
    bar.appendChild(fill); h.appendChild(bar); box.appendChild(h);
  }

  // ═══════════════ الشاشات ═══════════════

  // ── البوابة: الملفات ──
  function renderHome(notice) {
    unmountReact();
    Promise.all([getAll("profiles"), getAll("progress"), getAll("archive")]).then(function (r) {
      var profiles = r[0].sort(function (a, b) { return a.createdAt < b.createdAt ? -1 : 1; });
      var progress = {}, counts = {};
      r[1].forEach(function (p) { progress[p.profileId] = p; });
      r[2].forEach(function (a) { counts[a.profileId] = (counts[a.profileId] || 0) + 1; });

      var s = screen();
      s.appendChild(el("h1", "t-title", "الكشاف"));
      s.appendChild(el("p", "t-sub", "أداة الرواحل المسحية — كل شيء على جهازك، ولا شيء يغادره"));
      if (notice) s.appendChild(Object.assign(el("blockquote", "warnbox"), { textContent: notice }));

      var cov = el("blockquote", "covenant");
      cov.appendChild(el("p", "", "«هذا التقرير وصف لطريقة عملك، لا حكم عليك.»"));
      cov.appendChild(el("p", "cov-sub", "ما تقرأه حالة لا صفة · وترجيح لا يقين · وآخر كلمة لك أنت."));
      s.appendChild(cov);

      if (profiles.length) {
        s.appendChild(el("h2", "sec-h", "ملفات هذا الجهاز"));
        var list = el("div", "home-list");
        profiles.forEach(function (p) {
          var card = el("button", "profile-card");
          card.appendChild(el("span", "p-alias", p.alias));
          var pr = progress[p.id];
          var bits = [];
          if (pr && pr.cursor && pr.cursor !== "done" && pr.v === D.BUILD.hash)
            bits.push("استبيان جارٍ — الكتلة " + ar((pr.cursor.block || 0) + 1));
          if (counts[p.id]) bits.push("تقارير محفوظة: " + ar(counts[p.id]));
          card.appendChild(el("span", "p-state", bits.join(" · ") || "لم يبدأ بعد"));
          card.onclick = function () { S.profile = p; renderProfile(); };
          list.appendChild(card);
        });
        s.appendChild(list);
      }

      var form = el("div", "newp");
      var inp = el("input", "name-input");
      inp.type = "text"; inp.maxLength = 40;
      inp.placeholder = profiles.length ? "اسم ملف جديد (لشخص آخر مثلاً)…" : "اسمك أو اسم مستعار…";
      var btn = el("button", "btn big", profiles.length ? "＋ إنشاء ملف جديد" : "أنشئ ملفك وابدأ");
      btn.onclick = function () {
        var alias = inp.value.trim() || "ملفي";
        var p = { id: newId("p"), alias: alias, createdAt: new Date().toISOString() };
        put("profiles", p).then(function () { S.profile = p; renderProfile(); });
      };
      form.appendChild(inp); form.appendChild(btn);
      s.appendChild(form);

      var tools = el("div", "actions");
      var exp = el("button", "btn ghost", "⬇ نسخة احتياطية لكل الجهاز");
      exp.onclick = exportBackup;
      tools.appendChild(exp);
      var impLab = el("label", "btn ghost", "⬆ استيراد نسخة احتياطية");
      var impInp = el("input", "");
      impInp.type = "file"; impInp.accept = "application/json"; impInp.style.display = "none";
      impInp.addEventListener("change", function () {
        if (impInp.files[0]) importBackup(impInp.files[0]);
      });
      impLab.appendChild(impInp);
      tools.appendChild(impLab);
      s.appendChild(tools);
      s.appendChild(el("p", "privacy",
        "🔒 لا خادم ولا حساب ولا تتبع — النسخة الاحتياطية ملف واحد بيدك، وهي درعك أمام حذف النظام للتخزين الخامل."));
    });
  }

  // ── ملف واحد ──
  function renderProfile() {
    var p = S.profile;
    Promise.all([get("progress", p.id), archiveOf(p.id)]).then(function (r) {
      var pr = r[0];
      var reports = r[1].sort(function (a, b) { return a.createdAt < b.createdAt ? 1 : -1; });
      var s = screen();
      var backRow = el("div", "toprow");
      var back = el("button", "btn ghost small", "→ كل الملفات");
      back.onclick = function () { S.profile = null; renderHome(); };
      backRow.appendChild(back);
      s.appendChild(backRow);
      s.appendChild(el("h1", "t-title small", p.alias));

      var acts = el("div", "actions");
      if (pr && pr.cursor && pr.cursor !== "done" && pr.v === D.BUILD.hash) {
        var resume = el("button", "btn big", "استئناف الاستبيان — الكتلة " + ar((pr.cursor.block || 0) + 1));
        resume.onclick = function () {
          S.cursor = pr.cursor; S.answers = pr.answers || {}; route();
        };
        acts.appendChild(resume);
        var restart = el("button", "btn ghost", "البدء من جديد");
        restart.onclick = function () {
          if (confirm("سيمحو هذا تقدمك الجاري (لا يمسّ التقارير المحفوظة). أواصل؟"))
            renderIntro(true);
        };
        acts.appendChild(restart);
      } else {
        if (pr && pr.cursor && pr.cursor !== "done" && pr.v !== D.BUILD.hash)
          s.appendChild(Object.assign(el("blockquote", "warnbox"), { textContent:
            "تحدّثت الأداة منذ آخر تقدم محفوظ، فأُلغي — لا تُقرأ إجابات قديمة بخرائط جديدة." }));
        var start = el("button", "btn big", reports.length ? "استبيان جديد" : "ابدأ الاستبيان");
        start.onclick = function () { renderIntro(true); };
        acts.appendChild(start);
      }
      s.appendChild(acts);

      if (reports.length) {
        s.appendChild(el("h2", "sec-h", "التقارير المحفوظة"));
        s.appendChild(el("p", "faintline",
          "كل تقرير سِجلٌّ يُقرأ وحده — لا يُعرض قياسان معاً ولا يُقرأ فارق بينهما."));
        var list = el("div", "home-list");
        reports.forEach(function (rec, i) {
          var row = el("button", "arch-item");
          row.appendChild(el("span", "p-alias", "تقرير " + arDate(rec.createdAt)));
          row.appendChild(el("span", "p-state",
            (rec.name ? rec.name + " · " : "") + (i === 0 ? "الأحدث" : "سِجلّ سابق")));
          row.onclick = function () { renderArchived(rec, i === 0); };
          list.appendChild(row);
        });
        s.appendChild(list);
      }

      // إسهام من الأرشيف: أحدث سجلّ يحمل إجاباته (سجلات ما قبل DEC-253 لا تحملها)
      var contribSrc = reports.find(function (r2) { return r2.answers; });
      if (contribSrc && !p.contribDismissed) {
        s.appendChild(contribCard(contribSrc.answers, p));
      }

      var danger = el("div", "actions");
      var delBtn = el("button", "btn ghost small danger", "حذف هذا الملف نهائياً");
      delBtn.onclick = function () {
        if (!confirm("سيمحو هذا الملف وتقدمه وكل تقاريره من الجهاز نهائياً. أواصل؟")) return;
        Promise.all([del("profiles", p.id), del("progress", p.id)]).then(function () {
          return archiveOf(p.id);
        }).then(function (recs) {
          return Promise.all(recs.map(function (r2) { return del("archive", r2.id); }));
        }).then(function () { S.profile = null; renderHome(); });
      };
      danger.appendChild(delBtn);
      s.appendChild(danger);
    });
  }

  // ── مقدمة الاستبيان (العهد والتعليمات) ──
  function renderIntro(fresh) {
    var s = screen();
    s.appendChild(el("h1", "t-title small", "قبل أن تبدأ"));
    var cov = el("blockquote", "covenant");
    cov.appendChild(el("p", "", "«هذا التقرير وصف لطريقة عملك، لا حكم عليك.»"));
    cov.appendChild(el("p", "cov-sub", "ما تقرأه حالة لا صفة · وترجيح لا يقين · وآخر كلمة لك أنت."));
    s.appendChild(cov);
    var how = el("div", "howto");
    how.appendChild(el("h2", "", "كيف تجيب؟"));
    var ol = el("ul", "");
    [
      "٩٤ بنداً على " + ar(10) + " كتل — " + ar(TOTAL_STEPS) + " خطوة قصيرة إجمالاً.",
      "في كل كتلة تختار أولاً من كل بند الجملة (أ) أو (ب) الأكثر وصفاً لك مقارنةً بالأخرى.",
      "ثم تعود جُمل الكتلة نفسها واحدةً واحدة لتقيّم كل جملة على حدة: من ١ (لا تمثلني أبدًا) إلى ٦ (تمثلني تمامًا) — بمعزل عن اختيارك السابق.",
      "لا إجابة صحيحة وأخرى خاطئة — لا درجة أفضل، يوجد نمط مختلف.",
      "تقدّمك يُحفظ في ملف «" + S.profile.alias + "» على هذا الجهاز تلقائياً.",
    ].forEach(function (t) { ol.appendChild(el("li", "", t)); });
    how.appendChild(ol);
    s.appendChild(how);
    var acts = el("div", "actions");
    var go = el("button", "btn big", "ابدأ");
    go.onclick = function () {
      S.cursor = { block: 0, phase: "choice", idx: 0 };
      if (fresh) S.answers = {};
      saveProgress(); route();
    };
    acts.appendChild(go);
    var back = el("button", "btn ghost", "رجوع");
    back.onclick = renderProfile;
    acts.appendChild(back);
    s.appendChild(acts);
  }

  // ── الاختيار ──
  function renderChoice() {
    var c = S.cursor, items = blockItems(c.block), item = items[c.idx];
    var s = screen();
    progressHeader(s);
    s.appendChild(el("h2", "q-prompt", "أي الجملتين أكثر وصفاً لك مقارنةً بالأخرى؟"));
    s.appendChild(el("p", "q-num", "البند " + ar(item)));
    var prev = (S.answers[item] || {}).choice;
    ["a", "b"].forEach(function (letter) {
      var btn = el("button", "choice-btn" + (prev === letter ? " picked" : ""));
      btn.appendChild(el("span", "choice-tag", letter === "a" ? "أ" : "ب"));
      btn.appendChild(sentenceNode(D.ITEMS[item][letter], "choice-text"));
      btn.onclick = function () {
        S.answers[item] = S.answers[item] || {};
        S.answers[item].choice = letter;          // نقطة التحويل الوحيدة أ/ب → a/b
        if (c.idx + 1 < items.length) c.idx += 1;
        else { c.phase = "rate"; c.idx = 0; }
        saveProgress(); route();
      };
      s.appendChild(btn);
    });
    if (c.idx > 0) {
      var back = el("button", "btn ghost small", "→ السابق");
      back.onclick = function () { c.idx -= 1; saveProgress(); route(); };
      s.appendChild(back);
    }
  }

  function rateSeq(bi) {
    var seq = [];
    blockItems(bi).forEach(function (n) { seq.push([n, "a"], [n, "b"]); });
    return seq;
  }

  // ── التقييم — جملة مفردة بلا أثر للاختيار (DEC-035) ──
  function renderRate() {
    var c = S.cursor, seq = rateSeq(c.block), cur = seq[c.idx];
    var item = cur[0], letter = cur[1];
    var s = screen();
    progressHeader(s);
    s.appendChild(el("h2", "q-prompt", "إلى أي مدى تمثّلك هذه الجملة؟"));
    var card = el("div", "rate-card");
    card.appendChild(sentenceNode(D.ITEMS[item][letter], "rate-text"));
    s.appendChild(card);
    var key = letter === "a" ? "ratingA" : "ratingB";
    var prev = (S.answers[item] || {})[key];
    var scale = el("div", "scale");
    for (var v = 1; v <= 6; v++) (function (val) {
      var b = el("button", "scale-btn" + (prev === val ? " picked" : ""), ar(val));
      b.onclick = function () {
        S.answers[item] = S.answers[item] || {};
        S.answers[item][key] = val;
        if (c.idx + 1 < seq.length) c.idx += 1;
        else if (c.block + 1 < D.BLOCKS.length) S.cursor = { block: c.block + 1, phase: "choice", idx: 0 };
        else S.cursor = "preflight";
        saveProgress(); route();
      };
      scale.appendChild(b);
    })(v);
    s.appendChild(scale);
    var lbl = el("div", "scale-labels");
    lbl.appendChild(el("span", "", "١ = لا تمثلني أبدًا"));
    lbl.appendChild(el("span", "", "٦ = تمثلني تمامًا"));
    s.appendChild(lbl);
    if (c.idx > 0) {
      var back = el("button", "btn ghost small", "→ السابق");
      back.onclick = function () { c.idx -= 1; saveProgress(); route(); };
      s.appendChild(back);
    }
  }

  function firstIncomplete() {
    for (var bi = 0; bi < D.BLOCKS.length; bi++) {
      var items = blockItems(bi);
      for (var i = 0; i < items.length; i++) {
        var a = S.answers[items[i]];
        if (!a || (a.choice !== "a" && a.choice !== "b")) return { block: bi, phase: "choice", idx: i };
      }
      var seq = rateSeq(bi);
      for (var j = 0; j < seq.length; j++) {
        var an = S.answers[seq[j][0]] || {};
        var val = seq[j][1] === "a" ? an.ratingA : an.ratingB;
        if (!(val >= 1 && val <= 6)) return { block: bi, phase: "rate", idx: j };
      }
    }
    return null;
  }

  function renderPreflight() {
    var gap = firstIncomplete();
    var missing = B.missingItems(S.answers, RAW_MAPS);
    if (gap || missing.length) {
      var s = screen();
      s.appendChild(el("h2", "q-prompt", "بقيت خطوات لم تكتمل"));
      s.appendChild(el("p", "", "عقد المدخل يمنع توليد تقرير على إجابات ناقصة — سنعود بك إلى أول موضع متبقٍّ."));
      var go = el("button", "btn big", "أكمل من حيث توقفت");
      go.onclick = function () { S.cursor = gap || { block: 0, phase: "choice", idx: 0 }; saveProgress(); route(); };
      s.appendChild(go);
      return;
    }
    S.cursor = "name"; saveProgress(); route();
  }

  function renderName() {
    var s = screen();
    s.appendChild(el("h1", "t-title small", "اكتمل الاستبيان ✓"));
    s.appendChild(el("p", "t-sub", "سيُولَّد تقريراك ويُحفظان في ملف «" + S.profile.alias + "» على هذا الجهاز."));
    var lab = el("label", "name-label", "الاسم في ترويسة التقرير (اختياري):");
    var inp = el("input", "name-input");
    inp.type = "text"; inp.maxLength = 60; inp.value = S.name || S.profile.alias || "";
    lab.appendChild(inp); s.appendChild(lab);
    var go = el("button", "btn big", "أنشئ تقريرَيّ");
    go.onclick = function () {
      S.name = inp.value.trim();
      // التوليد ثم الأرشفة: النص المُسلَّم وكتلة تدقيقه يُحفظان حرفياً (عقد إعادة التوليد)
      var gen = DR.generate(S.answers, K2_MAP, K2_ORDER, K3_MAP);
      if (!gen.k2 && !gen.k3) {
        var s2 = screen();
        s2.appendChild(el("h2", "q-prompt", "تعذّر توليد التقرير"));
        gen.errors.forEach(function (e2) {
          s2.appendChild(Object.assign(el("blockquote", "warnbox"), { textContent: e2 }));
        });
        var back = el("button", "btn ghost", "رجوع للملف");
        back.onclick = renderProfile;
        s2.appendChild(back);
        return;
      }
      var rec = {
        id: newId("r"), profileId: S.profile.id, name: S.name,
        createdAt: new Date().toISOString(), buildHash: D.BUILD.hash,
        k2: gen.k2, k3: gen.k3, errors: gen.errors,
        answers: S.answers,   // تبقى محلية — وتتيح الإسهام الطوعي لاحقاً (DEC-253)
      };
      put("archive", rec).then(function () {
        S.cursor = "done"; saveProgress(); route();
      });
    };
    s.appendChild(go);
  }

  // ── الإسهام الطوعي المجهّل (DEC-253) ─────────────────────────────────
  // بانٍ نقي: يستقبل الإجابات وحدها ولا يقرأ أي حقل هوية — يفحصه البناء آلياً.
  function contribPayload(answers) {
    return {
      schema: "RAWAHIL-CONTRIB-v1",
      instrument: { measure: "40-MEASURE v5.0", scoring: "41 v4.2", build: D.BUILD.hash },
      submitted: new Date().toISOString().slice(0, 7),   // سنة-شهر فقط — لا طابع دقيق
      answers: answers,
    };
  }

  var CONTRIB_TEXT =
    "ما يُرسَل بالضبط: إجاباتك الـ٩٤ (الاختيار والتقييمان لكل بند) وإصدار الأداة وشهر الإسهام — " +
    "لا اسمك، ولا اسم ملفك، ولا بريدك، ولا مُعرِّف جهازك. " +
    "الإسهام يخدم اختبار صدق الأداة ميدانياً، وهو اختياري بالكامل ورفضه لا يؤثر في شيء.";

  function startContribution(answers) {
    try {
      sessionStorage.setItem("rawahil.contrib.pending",
        JSON.stringify(contribPayload(answers)));
      location.href = "contribute.html";
    } catch (e) {
      alert("تعذّر تجهيز الإسهام: " + e);
    }
  }

  function contribCard(answers, profile) {
    var box = el("div", "contrib-card");
    box.appendChild(el("h3", "contrib-h", "إسهام اختياري — مجهّل تماماً"));
    box.appendChild(el("p", "contrib-p", CONTRIB_TEXT));
    var acts = el("div", "actions tight");
    var go = el("button", "btn", "أطّلع قبل أن أقرر");
    go.onclick = function () { startContribution(answers); };
    acts.appendChild(go);
    var no = el("button", "btn ghost", "لا، شكراً");
    no.onclick = function () {
      // الإزالة بعد اكتمال الحفظ — إبحار فوري لا يجهض المعاملة
      if (profile) {
        profile.contribDismissed = true;
        put("profiles", profile).then(function () { box.remove(); });
      } else box.remove();
    };
    acts.appendChild(no);
    box.appendChild(acts);
    return box;
  }

  // ── التقرير الطازج — DualReportView كما هي ──
  function renderReport() {
    root.textContent = "";
    var host = el("div", "");
    root.appendChild(host);
    reactRoot = ReactDOM.createRoot(host);
    reactRoot.render(React.createElement(
      DR.DualReportView,
      {
        answers: S.answers, name: S.name,
        K2_MAP: K2_MAP, K2_ORDER: K2_ORDER, K3_MAP: K3_MAP,
        // لا خاصية report — لوحة K1/K4 لا تُعرض علناً (DEC-186)
        onRestart: function () {
          // التقرير محفوظ في الأرشيف — الخروج لا يفقد شيئاً
          unmountReact();
          clearProgress(); S.cursor = null; S.answers = {}; S.name = "";
          renderProfile();
        },
      }
    ));
    // بطاقة الإسهام خارج شجرة React المختومة — أسفل التقرير
    if (S.profile && !S.profile.contribDismissed) {
      var ans = S.answers;
      root.appendChild(contribCard(ans, S.profile));
    }
  }

  // ── عارض الأرشيف — النص المحفوظ حرفياً، سِجلّ يُقرأ وحده ──
  function renderArchived(rec, isLatest) {
    var s = screen();
    var backRow = el("div", "toprow");
    var back = el("button", "btn ghost small", "→ ملف " + S.profile.alias);
    back.onclick = renderProfile;
    backRow.appendChild(back);
    s.appendChild(backRow);
    s.appendChild(el("h1", "t-title small", "تقرير " + arDate(rec.createdAt)));
    if (!isLatest) {
      s.appendChild(Object.assign(el("blockquote", "warnbox"), { textContent:
        "سِجلٌّ سابق — يُقرأ وحده. تسجيل القياسات مباح، وقراءة الفارق بين قياسين محظورة حتى تُبنى قواعدها." }));
    }
    var tabs = el("div", "rw-tabs");
    var body = el("div", "rw-doc");
    var actions = el("div", "rw-actions");
    var current = rec.k2 ? "k2" : "k3";
    var brief = false;

    function renderBody() {
      var doc = rec[current];
      body.innerHTML = doc
        ? DR.mdToHtml(current === "k2" && brief && doc.brief ? doc.brief : doc.text)
        : "<p class='rw-p'>هذا الجانب غير متاح في هذا السجلّ.</p>";
      renderActions();
    }
    function tabBtn(key, label) {
      var b = el("button", "rw-tab" + (current === key ? " on" : ""), label);
      b.onclick = function () {
        current = key;
        Array.prototype.forEach.call(tabs.children, function (c2) { c2.classList.remove("on"); });
        b.classList.add("on");
        renderBody();
      };
      return b;
    }
    tabs.appendChild(tabBtn("k2", "تقرير التفكير (K2)"));
    tabs.appendChild(tabBtn("k3", "تقرير الانفعال (K3)"));
    s.appendChild(tabs);
    s.appendChild(Object.assign(el("blockquote", "rw-note"), { textContent:
      "التقريران مستندان منفصلان يُقرأ كلٌّ منهما وحده. لا يُقابَل بند من أحدهما ببند من الآخر." }));
    s.appendChild(body);
    s.appendChild(actions);

    function renderActions() {
      actions.textContent = "";
      var doc = rec[current];
      if (!doc) return;
      if (current === "k2" && doc.brief) {
        var t = el("button", "rw-toggle", brief ? "▸ عرض مختصر — اضغط للكامل" : "▾ عرض كامل — اضغط للمختصر");
        t.onclick = function () { brief = !brief; renderBody(); };
        actions.appendChild(t);
      }
      var md = el("button", "rw-btn", "⬇ Markdown");
      md.onclick = function () { DR.exportMd(doc, current, rec.name); };
      actions.appendChild(md);
      var js = el("button", "rw-btn ghost", "⬇ JSON (بكتلة التدقيق)");
      js.onclick = function () { DR.exportJson(doc, current, rec.name); };
      actions.appendChild(js);
      var pr = el("button", "rw-btn ghost", "🖨 طباعة / PDF");
      pr.onclick = function () { DR.exportPrint(doc, current, rec.name); };
      actions.appendChild(pr);
      var sh = el("button", "rw-btn ghost", "↗ مشاركة كملف");
      sh.onclick = function () { shareDoc(doc, current, rec.name); };
      actions.appendChild(sh);
    }
    renderBody();
  }

  function shareDoc(doc, circle, name) {
    var hdr = "# تقرير " + (circle === "k2" ? "التفكير" : "الانفعال") +
      (name ? " — " + name : "") + "\n\n";
    var content = "﻿" + hdr + doc.text;
    var fname = "تقرير-" + (circle === "k2" ? "التفكير-K2" : "الانفعال-K3") + ".md";
    try {
      var file = new File([content], fname, { type: "text/markdown" });
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        navigator.share({ files: [file], title: fname }).catch(function () {});
        return;
      }
    } catch (e) { /* متصفح بلا Web Share — ننزل الملف */ }
    download(content, fname, "text/markdown;charset=utf-8");
  }

  // ── النسخة الاحتياطية ──
  function exportBackup() {
    Promise.all([getAll("profiles"), getAll("progress"), getAll("archive")]).then(function (r) {
      var payload = {
        schema: "RAWAHIL-KASHAF-BACKUP-v1",
        exportedAt: new Date().toISOString(),
        buildHash: D.BUILD.hash,
        profiles: r[0], progress: r[1], archive: r[2],
      };
      var d = new Date();
      download(JSON.stringify(payload), "kashaf-backup-" +
        d.getFullYear() + String(d.getMonth() + 1).padStart(2, "0") +
        String(d.getDate()).padStart(2, "0") + ".json", "application/json;charset=utf-8");
    });
  }

  function importBackup(file) {
    var reader = new FileReader();
    reader.onload = function () {
      var p;
      try { p = JSON.parse(reader.result); } catch (e) { p = null; }
      if (!p || p.schema !== "RAWAHIL-KASHAF-BACKUP-v1" ||
          !Array.isArray(p.profiles) || !Array.isArray(p.archive)) {
        renderHome("الملف ليس نسخة احتياطية صالحة من «الكشاف».");
        return;
      }
      if (!confirm("سيستبدل الاستيراد كلَّ بيانات هذا الجهاز بمحتوى النسخة (" +
                   p.profiles.length + " ملفات، " + p.archive.length + " تقارير). أواصل؟")) return;
      op("profiles", "readwrite", function (s) { s.clear(); })
        .then(function () { return op("progress", "readwrite", function (s) { s.clear(); }); })
        .then(function () { return op("archive", "readwrite", function (s) { s.clear(); }); })
        .then(function () {
          return Promise.all(
            p.profiles.map(function (x) { return put("profiles", x); })
              .concat((p.progress || []).map(function (x) { return put("progress", x); }))
              .concat(p.archive.map(function (x) { return put("archive", x); })));
        })
        .then(function () { S.profile = null; renderHome("استُوردت النسخة الاحتياطية بنجاح."); });
    };
    reader.readAsText(file);
  }

  // ── هجرة مخزن v1 (localStorage) ──
  function migrateLegacy() {
    var raw = null;
    try { raw = localStorage.getItem(LEGACY_KEY); } catch (e) {}
    if (!raw) return Promise.resolve(null);
    var payload = null;
    try { payload = JSON.parse(raw); } catch (e) {}
    try { localStorage.removeItem(LEGACY_KEY); } catch (e) {}
    if (!payload || payload.v !== D.BUILD.hash || !payload.cursor) {
      return Promise.resolve(payload ? "أُلغي تقدم قديم محفوظ بنسخة أقدم من الأداة." : null);
    }
    var p = { id: newId("p"), alias: "ملفي", createdAt: new Date().toISOString() };
    return put("profiles", p).then(function () {
      return put("progress", {
        profileId: p.id, v: payload.v, cursor: payload.cursor,
        answers: payload.answers || {}, savedAt: new Date().toISOString(),
      });
    }).then(function () { return "نُقل تقدمك المحفوظ إلى ملف «ملفي» — افتحه للمتابعة."; });
  }

  function route() {
    var c = S.cursor;
    if (!c) return S.profile ? renderProfile() : renderHome();
    if (c === "preflight") return renderPreflight();
    if (c === "name") return renderName();
    if (c === "done") return renderReport();
    return c.phase === "choice" ? renderChoice() : renderRate();
  }

  // ── الإقلاع — سلامة الحزم ثم القاعدة ثم الهجرة ────────────────────────
  try {
    PK.verifyPacks();
  } catch (e) {
    var warn = el("blockquote", "warnbox");
    warn.textContent = "⚠️ انجراف في حزم المحتوى — الأداة معطَّلة حفاظاً على سلامة القراءة. (" + e.message + ")";
    root.textContent = ""; root.appendChild(warn);
    return;
  }
  openDb().then(function (d) {
    db = d;
    return migrateLegacy();
  }).then(function (notice) {
    renderHome(notice);
  }).catch(function (e) {
    // بيئة بلا IndexedDB — نادرة؛ نوضح بدل أن نفشل صامتين
    var warn = el("blockquote", "warnbox");
    warn.textContent = "تعذّر فتح مخزن الجهاز (" + e + ") — تصفّح خاص؟ الأداة تحتاج تخزيناً محلياً للملفات والأرشيف.";
    root.textContent = ""; root.appendChild(warn);
  });
})();
