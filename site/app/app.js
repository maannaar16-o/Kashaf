"use strict";
/*
 * app.js — تطبيق «الكشاف» — تدفق الاستبيان (DEC-035 · الكتل المتداخلة)
 * =====================================================================
 * آلة حالات بلا مكتبات: WELCOME → [لكل كتلة: CHOICE ثم RATE] → NAME → REPORT.
 * React لا يُستدعى إلا عند عرض التقرير (DualReportView تشترطه).
 *
 * قواعد مختومة منفَّذة هنا:
 *  · المرحلة الثانية تعرض كل جملة مفردة دون إظهار الاختيار السابق (DEC-035)
 *  · التقييم 1–6 بأزرار حصراً — الواجهة هي نقطة إنفاذ المدى
 *  · نقطة تحويل وحيدة أ/ب → "a"/"b" (زرّا الاختيار)
 *  · إجابات محفوظة ببصمة بناء — تغيّر الأداة يُبطل المحفوظ (درس GAP-Q-01)
 */
(function () {
  var D = window.KashafData;
  var EN = window.RawahilEngines;
  var B = window.RawahilBridge;
  var PK = window.RawahilPacks;

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

  var LS_KEY = "rawahil.kashaf.v1";
  var root = document.getElementById("app");

  // ── حالة التطبيق ──────────────────────────────────────────────────────
  var S = { cursor: null, answers: {}, name: "" };
  var reactRoot = null;

  function save() {
    try {
      localStorage.setItem(LS_KEY, JSON.stringify({
        v: D.BUILD.hash, cursor: S.cursor, answers: S.answers,
        savedAt: new Date().toISOString(),
      }));
    } catch (e) { /* وضع خاص أو حصة ممتلئة — يتابع بلا حفظ */ }
  }
  function loadSaved() {
    try {
      var raw = localStorage.getItem(LS_KEY);
      if (!raw) return null;
      var p = JSON.parse(raw);
      if (!p || p.v !== D.BUILD.hash) return { stale: true };
      return p;
    } catch (e) { return null; }
  }
  function clearSaved() { try { localStorage.removeItem(LS_KEY); } catch (e) {} }

  // ── أدوات ─────────────────────────────────────────────────────────────
  var AR_D = "٠١٢٣٤٥٦٧٨٩";
  function ar(n) { return String(n).replace(/\d/g, function (d) { return AR_D[+d]; }); }
  function el(tag, cls, txt) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (txt !== undefined) n.textContent = txt;
    return n;
  }
  function screen() { root.textContent = ""; var s = el("div", "scr"); root.appendChild(s); return s; }
  function sentenceNode(segs, cls) {
    var p = el("p", cls);
    segs.forEach(function (g) {
      p.appendChild(Object.assign(el("span", g.t === "note" ? "q-note" : ""), { textContent: g.s }));
    });
    return p;
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

  // ── الشاشات ───────────────────────────────────────────────────────────
  function renderWelcome(staleNotice) {
    var s = screen();
    s.appendChild(el("h1", "t-title", "الكشاف"));
    s.appendChild(el("p", "t-sub", "أداة الرواحل المسحية — قراءة بنيوية لعدساتك المعرفية وقدراتك التنظيمية"));

    var cov = el("blockquote", "covenant");
    cov.appendChild(el("p", "", "«هذا التقرير وصف لطريقة عملك، لا حكم عليك.»"));
    cov.appendChild(el("p", "cov-sub", "ما تقرأه حالة لا صفة · وترجيح لا يقين · وآخر كلمة لك أنت."));
    s.appendChild(cov);

    if (staleNotice) {
      s.appendChild(Object.assign(el("blockquote", "warnbox"), { textContent:
        "تحدّثت الأداة منذ زيارتك السابقة، فأُلغيت الإجابات المحفوظة — لا تُقرأ إجابات قديمة بخرائط جديدة. نبدأ من جديد." }));
    }

    var how = el("div", "howto");
    how.appendChild(el("h2", "", "كيف تجيب؟"));
    var ol = el("ul", "");
    [
      "٩٤ بنداً على " + ar(10) + " كتل — " + ar(TOTAL_STEPS) + " خطوة قصيرة إجمالاً.",
      "في كل كتلة تختار أولاً من كل بند الجملة (أ) أو (ب) الأكثر وصفاً لك مقارنةً بالأخرى.",
      "ثم تعود جُمل الكتلة نفسها واحدةً واحدة لتقيّم كل جملة على حدة: من ١ (لا تمثلني أبدًا) إلى ٦ (تمثلني تمامًا) — بمعزل عن اختيارك السابق.",
      "لا إجابة صحيحة وأخرى خاطئة — لا درجة أفضل، يوجد نمط مختلف.",
      "تقدّمك يُحفظ على جهازك تلقائياً وتستطيع الاستئناف لاحقاً.",
    ].forEach(function (t) { ol.appendChild(el("li", "", t)); });
    how.appendChild(ol);
    s.appendChild(how);

    s.appendChild(Object.assign(el("p", "privacy"), { textContent:
      "🔒 خصوصيتك: هذه الصفحة قائمة بذاتها ومنافذ الشبكة فيها مقفلة برمجياً — إجاباتك وتقريرك لا يغادران جهازك." }));

    var actions = el("div", "actions");
    var saved = loadSaved();
    if (saved && !saved.stale && saved.cursor) {
      var resume = el("button", "btn big", saved.cursor === "done"
        ? "إجاباتك مكتملة — اعرض تقريرك"
        : "استئناف من الكتلة " + ar((saved.cursor.block || 0) + 1));
      resume.onclick = function () {
        S.cursor = saved.cursor; S.answers = saved.answers || {};
        route();
      };
      actions.appendChild(resume);
      var restart = el("button", "btn ghost", "البدء من جديد");
      restart.onclick = function () {
        if (confirm("سيؤدي هذا إلى محو إجاباتك المحفوظة. أواصل؟")) {
          clearSaved(); S.cursor = { block: 0, phase: "choice", idx: 0 }; S.answers = {};
          save(); route();
        }
      };
      actions.appendChild(restart);
    } else {
      var start = el("button", "btn big", "ابدأ الاستبيان");
      start.onclick = function () {
        S.cursor = { block: 0, phase: "choice", idx: 0 }; S.answers = {};
        save(); route();
      };
      actions.appendChild(start);
    }
    s.appendChild(actions);
  }

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
        save(); route();
      };
      s.appendChild(btn);
    });

    if (c.idx > 0) {
      var back = el("button", "btn ghost small", "→ السابق");
      back.onclick = function () { c.idx -= 1; save(); route(); };
      s.appendChild(back);
    }
  }

  function rateSeq(bi) {
    var seq = [];
    blockItems(bi).forEach(function (n) { seq.push([n, "a"], [n, "b"]); });
    return seq;
  }

  function renderRate() {
    var c = S.cursor, seq = rateSeq(c.block), cur = seq[c.idx];
    var item = cur[0], letter = cur[1];
    var s = screen();
    progressHeader(s);
    s.appendChild(el("h2", "q-prompt", "إلى أي مدى تمثّلك هذه الجملة؟"));
    // لا يُعرض أي أثر لاختيار المرحلة الأولى (DEC-035)
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
        else if (c.block + 1 < D.BLOCKS.length) { S.cursor = { block: c.block + 1, phase: "choice", idx: 0 }; }
        else { S.cursor = "preflight"; }
        save(); route();
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
      back.onclick = function () { c.idx -= 1; save(); route(); };
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
    // فحص محلي شامل ثم فحص عقد المدخل (missingItems — بمصفوفات الأزواج الخام)
    var gap = firstIncomplete();
    var missing = B.missingItems(S.answers, RAW_MAPS);
    if (gap || missing.length) {
      var s = screen();
      s.appendChild(el("h2", "q-prompt", "بقيت خطوات لم تكتمل"));
      s.appendChild(el("p", "", "عقد المدخل يمنع توليد تقرير على إجابات ناقصة — سنعود بك إلى أول موضع متبقٍّ."));
      var go = el("button", "btn big", "أكمل من حيث توقفت");
      go.onclick = function () { S.cursor = gap || { block: 0, phase: "choice", idx: 0 }; save(); route(); };
      s.appendChild(go);
      return;
    }
    S.cursor = "name"; save(); route();
  }

  function renderName() {
    var s = screen();
    s.appendChild(el("h1", "t-title small", "اكتمل الاستبيان ✓"));
    s.appendChild(el("p", "t-sub", "خطوة أخيرة اختيارية قبل توليد تقريرَيك."));
    var lab = el("label", "name-label", "اسمك (اختياري — يظهر في ترويسة التقرير فقط ولا يُخزَّن):");
    var inp = el("input", "name-input");
    inp.type = "text"; inp.maxLength = 60; inp.value = S.name || "";
    lab.appendChild(inp); s.appendChild(lab);
    var go = el("button", "btn big", "أنشئ تقريرَيّ");
    go.onclick = function () {
      S.name = inp.value.trim();
      S.cursor = "done"; save(); route();
    };
    s.appendChild(go);
  }

  function renderReport() {
    root.textContent = "";
    var host = el("div", "");
    root.appendChild(host);
    reactRoot = ReactDOM.createRoot(host);
    reactRoot.render(React.createElement(
      window.RawahilDualReport.DualReportView,
      {
        answers: S.answers, name: S.name,
        K2_MAP: K2_MAP, K2_ORDER: K2_ORDER, K3_MAP: K3_MAP,
        // لا خاصية report — لوحة K1/K4 الداخلية لا تُعرض علناً (DEC-186)
        onRestart: function () {
          if (!confirm("سيمحو هذا إجاباتك وتقريرك من الجهاز. أواصل؟")) return;
          try { reactRoot.unmount(); } catch (e) {}
          clearSaved(); S.cursor = null; S.answers = {}; S.name = "";
          route();
        },
      }
    ));
  }

  function route() {
    var c = S.cursor;
    if (!c) return renderWelcome();
    if (c === "preflight") return renderPreflight();
    if (c === "name") return renderName();
    if (c === "done") return renderReport();
    return c.phase === "choice" ? renderChoice() : renderRate();
  }

  // ── الإقلاع — سلامة الحزم أولاً ───────────────────────────────────────
  try {
    PK.verifyPacks();
  } catch (e) {
    root.textContent = "";
    var warn = el("blockquote", "warnbox");
    warn.textContent = "⚠️ انجراف في حزم المحتوى — الأداة معطَّلة حفاظاً على سلامة القراءة. (" + e.message + ")";
    root.appendChild(warn);
    return;
  }
  var boot = loadSaved();
  renderWelcome(boot && boot.stale);
})();
