"use strict";
/**
 * dualreport.js — عرض التقريرين المعزولين (المرحلة ④-ب · DEC-205)
 * ================================================================
 * تبويبان معزولان بتصديرين مستقلين. جدار العزل (§6):
 *   · لا شاشة تجمع «المتفهم E» و«الملاحظة EP»
 *   · لا سطر يربط عدسة K2 بمهارة K3 (التجميد نافذ · 00-VERTICAL-MAP §4)
 *   · لافتة ثقة EP تبقى داخل تقرير K3 ولا تمسّ يقين K2 (DEC-108)
 *   · كل تبويب يصدّر مستنده وحده — لا تصدير مشترك
 *
 * DEC-183: صفر SP% في الشاشة وفي كل تصدير.
 * DEC-186: K1/K4 لوحة داخلية موسومة [خارج نطاق التقرير — لا محرك معتمد].
 */
(function (root) {

  const { useState } = React;
  const B = root.RawahilBridge;
  const RP = root.RawahilReports;
  const EN = root.RawahilEngines;
  const PK = root.RawahilPacks;
  const SPG = root.RawahilSPGate;        // ح-4 · DEC-183 · ن-7

  // ── تحويل Markdown مبسّط للعرض ──────────────────────────────────────
  function mdToNodes(md, keyBase) {
    const out = [];
    const lines = md.split("\n");
    let tbl = null, li = null;
    const flushLi = () => {
      if (!li) return;
      out.push(React.createElement("ul", { key: `${keyBase}-u${out.length}`, className: "rw-ul" }, li));
      li = null;
    };
    const flushTbl = () => {
      if (!tbl) return;
      const [head, ...rows] = tbl;
      out.push(React.createElement("table", { key: `${keyBase}-t${out.length}`, className: "rw-tbl" },
        React.createElement("thead", null,
          React.createElement("tr", null, head.map((c, i) =>
            React.createElement("th", { key: i }, inline(c))))),
        React.createElement("tbody", null, rows.map((r, ri) =>
          React.createElement("tr", { key: ri }, r.map((c, ci) =>
            React.createElement("td", { key: ci }, inline(c))))))));
      tbl = null;
    };
    function inline(t) {
      const parts = String(t).split(/(\*\*[^*]+\*\*)/g);
      return parts.map((p, i) => p.startsWith("**") && p.endsWith("**")
        ? React.createElement("b", { key: i }, p.slice(2, -2))
        : p);
    }
    for (let i = 0; i < lines.length; i++) {
      const l = lines[i];
      if (/^\|.*\|$/.test(l.trim())) {
        const cells = l.trim().slice(1, -1).split("|").map((c) => c.trim());
        if (cells.every((c) => /^:?-{2,}:?$/.test(c))) continue;
        flushLi(); (tbl = tbl || []).push(cells);
        continue;
      }
      flushTbl();
      if (!l.trim()) { flushLi(); continue; }
      if (l.startsWith("### ")) out.push(React.createElement("h4", { key: i, className: "rw-h4" }, inline(l.slice(4))));
      else if (l.startsWith("## ")) out.push(React.createElement("h3", { key: i, className: "rw-h3" }, inline(l.slice(3))));
      else if (l.startsWith("> ")) out.push(React.createElement("blockquote", { key: i, className: "rw-q" }, inline(l.slice(2))));
      else if (l.startsWith("- ")) { (li = li || []).push(React.createElement("li", { key: i, className: "rw-li" }, inline(l.slice(2)))); continue; }
      else out.push(React.createElement("p", { key: i, className: "rw-p" }, inline(l)));
      flushLi();
    }
    flushLi(); flushTbl();
    return out;
  }

  // ── التوليد ────────────────────────────────────────────────────────
  function generate(answers, K2_MAP, K2_ORDER, K3_MAP, K4_MAP) {
    const result = { k2: null, k3: null, k4: null, crossing: null, errors: [] };
    // كل دائرة تُولَّد على حدة — فشل إحداهما لا يُسقط الأخرى (جدار العزل)
    try {
      PK.verifyPacks();
    } catch (e) {
      result.errors.push("سلامة الحزم: " + e.message);
      return result;
    }
    try {
      const sp2 = B.spK2(answers, K2_MAP, K2_ORDER);
      const [txt, audit] = RP.buildReportK2(sp2, "full");
      const [brief, bAudit] = RP.buildReportK2(sp2, "brief");   // DEC-225/و
      result.k2 = { text: txt, audit, sp: sp2, brief, briefAudit: bAudit };
    } catch (e) { result.errors.push("K2: " + e.message); }
    try {
      const sp3 = B.spK3(answers, K3_MAP);
      const [txt, audit] = RP.buildReportK3(sp3);
      result.k3 = { text: txt, audit, sp: sp3 };
    } catch (e) { result.errors.push("K3: " + e.message); }
    // K4 — `DEC-266` رفع `DEC-186` عنها بشرطه · و`DEC-270` يُسطّحها في الأداة
    try {
      const sp4 = B.spK4(answers, K4_MAP);
      const [txt, audit] = RP.buildReportK4(sp4);
      result.k4 = { text: txt, audit, sp: sp4 };
      // سطح القراءة العابرة — **مخرج مستقل** لا يُدمج في تقرير أي دائرة
      // (`133 §3/①` · `138 §2`). يُصدَر فارغاً إن لم يتحقق مشغِّل.
      const [xtxt, xaudit] = RP.buildCrossingSurface(sp4);
      result.crossing = xtxt ? { text: xtxt, audit: xaudit } : null;
    } catch (e) { result.errors.push("K4: " + e.message); }
    return result;
  }

  // ── التصدير — مستقلّ لكل تبويب ────────────────────────────────────
  function download(content, filename, mime) {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  }

  function exportMd(doc, circle, name, scope) {
    const CIRCLE_AR = { k2: "التفكير", k3: "الانفعال", k4: "الإنجاز", x: "قراءة عابرة" };
    const hdr = `# تقرير ${CIRCLE_AR[circle] || circle}` +
                (name ? ` — ${name}` : "") + (scope ? ` (${scope})` : "") + "\n\n";
    download(SPG.outputGate("\uFEFF" + hdr + doc.text, `تصدير MD · ${circle}`),
      `تقرير-${{ k2: "التفكير-K2", k3: "الانفعال-K3", k4: "الإنجاز-K4",
                  x: "قراءة-عابرة-K4" }[circle] || circle}${scope ? "-" + scope : ""}.md`,
      "text/markdown;charset=utf-8");
  }

  function exportPrint(doc, circle, name) {
    const w = window.open("", "_blank");
    if (!w) return;
    const title = `تقرير ${circle === "k2" ? "التفكير" : "الانفعال"}${name ? " — " + name : ""}`;
    const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
    w.document.write(SPG.outputGate(
      `<!doctype html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><title>${esc(title)}</title>` +
      `<style>body{font-family:system-ui,'Segoe UI',Tahoma,sans-serif;line-height:1.9;padding:28px;max-width:820px;margin:auto;color:#1a1a1a}` +
      `h1{font-size:20px}h2{font-size:17px;border-bottom:1px solid #ddd;padding-bottom:5px;margin-top:26px}` +
      `h3{font-size:15px;margin-top:18px}blockquote{border-right:3px solid #999;margin:0;padding:2px 12px;color:#444}` +
      `table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:5px 8px;font-size:13px}` +
      `@page{margin:16mm}</style></head><body>` +
      `<h1>${esc(title)}</h1>` + mdToHtml(doc.text) +
      `<\/body><\/html>`, `تصدير طباعة · ${circle}`));
    w.document.close();
    setTimeout(() => { try { w.print(); } catch (e) {} }, 350);
  }

  function mdToHtml(md) {
    const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
    const inl = (s) => esc(s).replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>");
    const out = [];
    let tbl = null, inList = false;
    const flushT = () => {
      if (!tbl) return;
      const [h, ...r] = tbl;
      out.push("<table><thead><tr>" + h.map((c) => `<th>${inl(c)}</th>`).join("") +
        "</tr></thead><tbody>" + r.map((row) =>
          "<tr>" + row.map((c) => `<td>${inl(c)}</td>`).join("") + "</tr>").join("") +
        "</tbody></table>");
      tbl = null;
    };
    const flushL = () => { if (inList) { out.push("</ul>"); inList = false; } };
    for (const l of md.split("\n")) {
      if (/^\|.*\|$/.test(l.trim())) {
        const cells = l.trim().slice(1, -1).split("|").map((c) => c.trim());
        if (cells.every((c) => /^:?-{2,}:?$/.test(c))) continue;
        flushL(); (tbl = tbl || []).push(cells); continue;
      }
      flushT();
      if (!l.trim()) { flushL(); continue; }
      if (l.startsWith("### ")) { flushL(); out.push(`<h3>${inl(l.slice(4))}</h3>`); }
      else if (l.startsWith("## ")) { flushL(); out.push(`<h2>${inl(l.slice(3))}</h2>`); }
      else if (l.startsWith("> ")) { flushL(); out.push(`<blockquote>${inl(l.slice(2))}</blockquote>`); }
      else if (l.startsWith("- ")) { if (!inList) { out.push("<ul>"); inList = true; } out.push(`<li>${inl(l.slice(2))}</li>`); }
      else { flushL(); out.push(`<p>${inl(l)}</p>`); }
    }
    flushT(); flushL();
    return out.join("\n");
  }

  /** JSON مقسَّم حقلين: التسليم للمستفيد · المراجعة لأداة المشرف لاحقاً. */
  function exportJson(doc, circle, name) {
    // DEC-231 — النطاقات مُعلَنة لا مستنتَجة من غياب حقل.
    // `null` صامت لا يُميّز «لا نطاق مختصر لهذه الدائرة» من «مفقود/تالف» —
    // وهو ما يحظره `ن-7`. فالحقول الاختيارية تُحذف، ويُعلَن ما هو متاح.
    const scopes = doc.brief ? ["full", "brief"] : ["full"];
    const payload = {
      schema: "RAWAHIL-REPORT-v1.2",
      circle: circle.toUpperCase(),
      generated_at: new Date().toISOString(),
      scopes,                                               // DEC-231
      delivery: { markdown: doc.text },
      audit: doc.audit,
    };
    if (name) payload.subject = name;
    if (doc.brief) {                                        // DEC-225/و
      payload.delivery.markdown_brief = doc.brief;
      payload.audit_brief = doc.briefAudit;
    }
    download(SPG.outputGate(JSON.stringify(payload, null, 1), `تصدير JSON · ${circle}`),
      `${circle}-تقرير-كامل.json`, "application/json;charset=utf-8");
  }

  // ── لوحة K1 الداخلية — `DEC-186` قائم عليها وحدها بعد رفعه عن K4 (`DEC-266`)
  function InternalPanel({ report }) {
    const [open, setOpen] = useState(false);
    return React.createElement("div", { className: "rw-panel" },
      React.createElement("button", { className: "rw-toggle", onClick: () => setOpen(!open) },
        (open ? "▾ " : "▸ ") + "لوحة تشخيصية داخلية — K1"),
      open && React.createElement("div", { className: "rw-panelbody" },
        React.createElement("blockquote", { className: "rw-warn" },
          "⚠️ [خارج نطاق التقرير — لا محرك معتمد]. أرقام خام للمراجعة الداخلية فقط، " +
          "لا تُقرأ كتوصيف ولا تُصدَّر إلى المستفيد."),
        React.createElement("h4", { className: "rw-h4" }, "K1 — عدّ الاختيارات"),
        React.createElement("ul", null, (report.k1 || []).map((r, i) =>
          React.createElement("li", { key: i }, `${r.name}: ${r.count}/${r.max}`))),
        React.createElement("p", { className: "rw-hint" },
          "دائرة الإنجاز (K4) خرجت من هذه اللوحة إلى تقرير معتمد — DEC-266.")));
  }

  // ── التبويبان ──────────────────────────────────────────────────────
  function DualReportView({ answers, report, name, K2_MAP, K2_ORDER, K3_MAP, K4_MAP, onRestart }) {
    const [tab, setTab] = useState("k2");
    const [brief, setBrief] = useState(false);   // DEC-225/و
    const [xopen, setXopen] = useState(false);   // سطح القراءة العابرة — مستقل
    const [gen] = useState(() => generate(answers, K2_MAP, K2_ORDER, K3_MAP, K4_MAP));

    if (gen.errors.length && !gen.k2 && !gen.k3 && !gen.k4) {
      return React.createElement("div", { className: "rw-wrap" },
        React.createElement("h2", null, "تعذّر توليد التقرير"),
        React.createElement("ul", null, gen.errors.map((e, i) =>
          React.createElement("li", { key: i }, e))),
        React.createElement("button", { className: "rw-btn", onClick: onRestart }, "العودة"));
    }

    const doc = tab === "k2" ? gen.k2 : tab === "k3" ? gen.k3 : gen.k4;
    const label = tab === "k2" ? "التفكير" : tab === "k3" ? "الانفعال" : "الإنجاز";

    return React.createElement("div", { className: "rw-wrap", dir: "rtl" },
      // شريط التبويبين — لا محتوى مشترك بينهما
      React.createElement("div", { className: "rw-tabs" },
        React.createElement("button", {
          className: "rw-tab" + (tab === "k2" ? " on" : ""), onClick: () => setTab("k2"),
        }, "تقرير التفكير (K2)"),
        React.createElement("button", {
          className: "rw-tab" + (tab === "k3" ? " on" : ""), onClick: () => setTab("k3"),
        }, "تقرير الانفعال (K3)"),
        React.createElement("button", {
          className: "rw-tab" + (tab === "k4" ? " on" : ""), onClick: () => setTab("k4"),
        }, "تقرير الإنجاز (K4)")),

      React.createElement("blockquote", { className: "rw-note" },
        "التقارير الثلاثة مستندات منفصلة يُقرأ كلٌّ منها وحده. لا يُقابَل بند من أحدها ببند من الآخر."),

      gen.errors.length ? React.createElement("blockquote", { className: "rw-warn" },
        "⚠️ " + gen.errors.join(" · ")) : null,

      // DEC-225/و — مبدّل نطاق العرض (K2 وحده؛ النطاقان لا يمسّان K3)
      tab === "k2" && doc && doc.brief ? React.createElement("div", { className: "rw-scope" },
        React.createElement("button", {
          className: "rw-toggle", onClick: () => setBrief(!brief),
        }, brief ? "▸ عرض مختصر — اضغط للكامل" : "▾ عرض كامل — اضغط للمختصر"),
        React.createElement("span", { className: "rw-hint" },
          brief ? " (المركز كتالوجاً كاملاً · R2/R3)" : " (كل العدسات · R2 مستوفى 94/94)")) : null,

      doc
        ? React.createElement("div", { className: "rw-doc", key: tab + (brief ? "-b" : "") },
            mdToNodes((tab === "k2" && brief && doc.brief) ? doc.brief : doc.text, tab))
        : React.createElement("p", { className: "rw-p" }, `تقرير ${label} غير متاح.`),

      // تصدير مستقلّ لكل تبويب
      doc && React.createElement("div", { className: "rw-actions" },
        React.createElement("div", { className: "rw-actlabel" }, `تصدير تقرير ${label} وحده:`),
        React.createElement("button", { className: "rw-btn", onClick: () => exportMd(doc, tab, name) }, "⬇ Markdown كامل"),
        tab === "k2" && doc.brief ? React.createElement("button", {
          className: "rw-btn ghost",
          onClick: () => exportMd({ text: doc.brief, audit: doc.briefAudit }, tab, name, "مختصر"),
        }, "⬇ Markdown مختصر") : null,
        React.createElement("button", { className: "rw-btn ghost", onClick: () => exportJson(doc, tab, name) }, "⬇ JSON"),
        React.createElement("button", { className: "rw-btn ghost", onClick: () => exportPrint(doc, tab, name) }, "🖨 طباعة / PDF")),

      // سطح القراءة العابرة — **مخرج مستقل**: كتلة خارج متن أي تقرير،
      // ولا تظهر إلا إن تحقق مشغِّلها من نطاقات K4 وحدها (`138 §2/①`).
      gen.crossing && React.createElement("div", { className: "rw-panel" },
        React.createElement("button", {
          className: "rw-toggle", onClick: () => setXopen(!xopen),
        }, (xopen ? "▾ " : "▸ ") + "قراءة عابرة — سطح مستقل"),
        xopen && React.createElement("div", { className: "rw-panelbody" },
          React.createElement("blockquote", { className: "rw-note" },
            "سطحٌ مستقل لا يُدمج في متن أي تقرير، ولا يحمل درجةً من دائرة أخرى."),
          React.createElement("div", { className: "rw-doc" },
            mdToNodes(gen.crossing.text, "x")),
          React.createElement("div", { className: "rw-actions" },
            React.createElement("button", {
              className: "rw-btn ghost",
              onClick: () => exportMd(gen.crossing, "x", name),
            }, "⬇ Markdown — السطح العابر")))),

      report && React.createElement(InternalPanel, { report }),

      React.createElement("div", { className: "rw-actions" },
        React.createElement("button", { className: "rw-btn ghost", onClick: onRestart }, "↺ إعادة")));
  }

  root.RawahilDualReport = { DualReportView, generate, mdToHtml, exportMd, exportJson, exportPrint };

})(typeof window !== "undefined" ? window : globalThis);
