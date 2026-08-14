/**
 * workshop_app.js — سطح مسار الورشة (`DEC-279`)
 * ================================================
 * **مسارٌ ثانٍ معلَنٌ شرطُه، لا نقضٌ لوعد الموقع العام** (`DEC-277 §1`):
 * التطبيق العام يبقى بقفل صفر الشبكة وبتذييله «إجاباتك لا تغادر جهازك»،
 * وهذه صفحةٌ **أخرى** تعلن من أول سطر أن نتيجتها تصل المدرّب.
 *
 * وسطحٌ نحيل بقصد: لا ملفّات ولا أرشيف ولا مرآة ولا نسخٌ احتياطية —
 * جلسةٌ مُشرَف عليها تبدأ بالإذن والرمز وتنتهي بالإرسال. والاستمرارية
 * في `sessionStorage` وحده: تنجو من تحديث الصفحة ولا تُعمِّر بعد إغلاقها.
 *
 * **والأداة نفسها**: البنود والخرائط والمحرّكات والتقارير من الحزمة عينها
 * التي يستعملها التطبيق العام — فلا أداةَ ثانية ولا خريطةَ ثانية (`م-2`).
 */
(function () {
  "use strict";

  var D = window.KashafData;
  var W = window.WorkshopData;
  var EN = window.RawahilEngines;
  var B = window.RawahilBridge;
  var PK = window.RawahilPacks;
  var DR = window.RawahilDualReport;
  var WP = window.RawahilWorkshopPayload;

  // الخرائط من المحرّك نفسه — مصدر حقيقةٍ واحد لا نسخة في هذه الطبقة
  var K2_MAP = {};
  Object.keys(EN.K2.ITEM_MAP).forEach(function (k) {
    K2_MAP[k] = { items: EN.K2.ITEM_MAP[k] };
  });
  var K2_ORDER = EN.K2.LENSES;
  var K3_MAP = D.K3_MAP;
  var K4_MAP = EN.K4.ITEM_MAP;
  var RAW_MAPS = Object.keys(EN.K2.ITEM_MAP).map(function (k) { return EN.K2.ITEM_MAP[k]; })
    .concat(Object.keys(K3_MAP).map(function (k) { return K3_MAP[k]; }));

  var KEY = "rawahil.workshop." + D.BUILD.hash;   // درس GAP-Q-01: بناءٌ آخر ⇒ إجاباتٌ تُطرح
  var root = document.getElementById("app");
  var S = { code: "", consent: false, cursor: null, answers: {}, sent: null };

  function save() {
    try {
      sessionStorage.setItem(KEY, JSON.stringify(
        { code: S.code, consent: S.consent, cursor: S.cursor, answers: S.answers }));
    } catch (e) { /* التخزين رفاهية لا شرط */ }
  }
  function load() {
    try {
      var raw = sessionStorage.getItem(KEY);
      if (!raw) return;
      var v = JSON.parse(raw);
      S.code = v.code || ""; S.consent = v.consent === true;
      S.cursor = v.cursor || null; S.answers = v.answers || {};
    } catch (e) { /* مخزَّنٌ فاسد يُتجاهل ويُبدأ من أوّله */ }
  }
  function reset() {
    try { sessionStorage.removeItem(KEY); } catch (e) {}
    S = { code: "", consent: false, cursor: null, answers: {}, sent: null };
  }

  // ── أدوات عرض ───────────────────────────────────────────────────────
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
      p.appendChild(Object.assign(el("span", g.t === "note" ? "q-note" : ""),
        { textContent: g.s }));
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

  // ── ① بوابة الإذن والرمز — لا خطوة قبلهما ──────────────────────────
  function renderGate(err) {
    var s = screen();
    s.appendChild(el("h1", "t-title small", "مسار الورشة"));
    s.appendChild(el("p", "t-sub", "جلسة تدريب مُشرَف عليها — بإذنك ورمز مشاركتك"));

    var box = el("blockquote", "covenant");
    box.appendChild(el("p", "", "«" + W.CONSENT_TEXT + "»"));
    box.appendChild(el("p", "cov-sub",
      "هذا المسار غير مسار الموقع العام: هناك لا تغادر إجاباتك جهازك، " +
      "وهنا تصل نتيجتك إلى مدرّب الورشة كاملةً بأرقامها. لا تتابع إن لم توافق."));
    s.appendChild(box);

    var howto = el("div", "howto");
    howto.appendChild(el("h2", "", "ما يصل المدرّب بالضبط"));
    var ul = el("ul", "");
    [
      "رمز مشاركتك — لا اسمك ولا بريدك ولا مُعرِّف جهازك.",
      "تقاريرك الثلاثة كاملةً مع كتل تدقيقها ودرجاتها الخام.",
      "ولا كلمة مرور ولا ما يقوم مقامها: هذه الصفحة لا تطلبها ولا تقبلها.",
    ].forEach(function (t) { ul.appendChild(el("li", "", t)); });
    howto.appendChild(ul);
    s.appendChild(howto);

    var lab = el("label", "name-label", "رمز المشاركة (مثال: ABCD-2345)");
    var inp = el("input", "name-input");
    inp.type = "text"; inp.maxLength = 9; inp.value = S.code;
    inp.setAttribute("autocomplete", "off");
    inp.oninput = function () { inp.value = inp.value.toUpperCase(); };
    lab.appendChild(inp); s.appendChild(lab);

    var row = el("label", "name-label");
    var cb = el("input", "");
    cb.type = "checkbox"; cb.checked = S.consent;
    cb.style.marginLeft = "8px";
    row.appendChild(cb);
    row.appendChild(document.createTextNode("أوافق صراحةً: " + W.CONSENT_TEXT));
    s.appendChild(row);

    if (err) s.appendChild(Object.assign(el("blockquote", "warnbox"), { textContent: err }));

    var acts = el("div", "actions");
    var go = el("button", "btn big", "ابدأ الاستبيان");
    go.onclick = function () {
      var code = inp.value.trim().toUpperCase();
      if (!W.CODE_RE_SRC || !new RegExp(W.CODE_RE_SRC).test(code)) {
        return renderGate("صيغة الرمز غير صحيحة — أربعة رموز فشرطة فأربعة.");
      }
      if (!cb.checked) return renderGate("لا استقبال بلا إذنٍ صريح — الموافقة شرط دخول.");
      S.code = code; S.consent = true;
      S.cursor = { block: 0, phase: "choice", idx: 0 };
      save(); route();
    };
    acts.appendChild(go);
    s.appendChild(acts);
    s.appendChild(el("p", "faintline",
      "الرمز يُصدره مدرّبك. ولا يُخزَّن اعتماد: لا كلمة مرور ولا تجزئتها."));
  }

  // ── ② الاختيار ثم التقييم — التسلسل المختوم في DEC-035 ─────────────
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
    var gap = firstIncomplete();
    var missing = B.missingItems(S.answers, RAW_MAPS);
    if (gap || missing.length) {
      var s = screen();
      s.appendChild(el("h2", "q-prompt", "بقيت خطوات لم تكتمل"));
      s.appendChild(el("p", "",
        "عقد المدخل يمنع توليد تقرير على إجابات ناقصة — سنعود بك إلى أول موضع متبقٍّ."));
      var go = el("button", "btn big", "أكمل من حيث توقفت");
      go.onclick = function () {
        S.cursor = gap || { block: 0, phase: "choice", idx: 0 }; save(); route();
      };
      s.appendChild(go);
      return;
    }
    S.cursor = "send"; save(); route();
  }

  // ── ③ الإرسال — نقطة الشبكة الوحيدة في هذه الصفحة ──────────────────
  function renderSend(err) {
    var s = screen();
    s.appendChild(el("h1", "t-title small", "اكتمل الاستبيان"));
    var box = el("blockquote", "covenant");
    box.appendChild(el("p", "", "«" + W.CONSENT_TEXT + "»"));
    box.appendChild(el("p", "cov-sub",
      "بالضغط على «أرسل» تصل تقاريرك الثلاثة إلى مدرّب الورشة تحت الرمز " +
      S.code + " — وحده، بلا اسمك."));
    s.appendChild(box);
    if (err) s.appendChild(Object.assign(el("blockquote", "warnbox"), { textContent: err }));
    var acts = el("div", "actions");
    var go = el("button", "btn big", "أرسل إلى مدرّب الورشة");
    go.onclick = function () { doSend(s, go); };
    acts.appendChild(go);
    s.appendChild(acts);
  }

  function doSend(s, btn) {
    btn.disabled = true;
    btn.textContent = "جارٍ التوليد والإرسال…";
    var gen, body;
    try {
      gen = DR.generate(S.answers, K2_MAP, K2_ORDER, K3_MAP, K4_MAP);
      body = WP.build(W.SCHEMA, W.CONSENT_TEXT, S.code, gen);
    } catch (e) {
      return renderSend("تعذّر توليد التقارير: " + (e && e.message ? e.message : e));
    }
    if (gen.errors && gen.errors.length && !gen.k2 && !gen.k3 && !gen.k4) {
      return renderSend("تعذّر توليد التقارير: " + gen.errors.join(" · "));
    }
    fetch("/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(function (r) {
      return r.json().then(function (j) { return { ok: r.ok, j: j }; });
    }).then(function (r) {
      if (!r.ok) return renderSend("ردّ الخادم: " + (r.j.error || "مردود بلا بيان"));
      S.sent = r.j; S.cursor = "done"; save(); route();
    }).catch(function (e) {
      renderSend("تعذّر الإرسال: " + (e && e.message ? e.message : e));
    });
  }

  function renderDone() {
    var s = screen();
    s.appendChild(el("h1", "t-title small", "وصلت نتيجتك"));
    s.appendChild(el("p", "t-sub", "الرمز " + S.code +
      " · وحكم أداة المشرف على الدوائر الثلاث: مقبول"));
    var box = el("div", "privacy");
    box.appendChild(el("p", "",
      "قراءة تقريرك تكون مع مدرّبك في الورشة. ولا يُقرأ فارقٌ بين قياسين — " +
      "هذا محظور بقرارٍ مختوم مهما تكرّر القياس."));
    s.appendChild(box);
    var acts = el("div", "actions");
    var again = el("button", "btn ghost", "إنهاء وإخلاء هذه الجلسة");
    again.onclick = function () { reset(); route(); };
    acts.appendChild(again);
    s.appendChild(acts);
  }

  // ── التوجيه ─────────────────────────────────────────────────────────
  function route() {
    if (!S.consent || !S.code) return renderGate();
    var c = S.cursor;
    if (c === "preflight") return renderPreflight();
    if (c === "send") return renderSend();
    if (c === "done") return renderDone();
    if (c && c.phase === "choice") return renderChoice();
    if (c && c.phase === "rate") return renderRate();
    S.cursor = { block: 0, phase: "choice", idx: 0 };
    return renderChoice();
  }

  // ── الإقلاع: سلامة الحزم شرطٌ لا تحذير ─────────────────────────────
  try {
    PK.verifyPacks();
  } catch (e) {
    root.textContent = "";
    root.appendChild(Object.assign(document.createElement("blockquote"), {
      className: "warnbox",
      textContent: "سلامة الحزم مخرومة — لا تشغيل: " + e.message,
    }));
    return;
  }
  load();
  route();
})();
