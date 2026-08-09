# -*- coding: utf-8 -*-
"""
build_packs.py — مولّد `packs.js` (المرحلة ②)
=============================================
يُضمّن حزم المحتوى الخمس داخل ملف JS واحد للعمل بلا شبكة.

مبدأ حاكم: **التوليد لا النسخ اليدوي.** كل حزمة تُسلسَل بـJSON بصيغة
مقنَّنة واحدة (مفاتيح مرتَّبة · بلا مسافات)، وتُحسَب بصمتها SHA-256.
البصمة تُضمَّن في المخرج ويُعاد التحقق منها عند التحميل — فلا تنجرف
نسخة الأداة عن المصدر صامتة (ن-7 · DEC-199).

المحتوى يُنقل حرفياً: لا اختصار ولا إعادة صياغة ولا تنسيق.
"""
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))

PACKS = [
    ("USERLAYER_K2", "k2_userlayer_pack.json", "55-USER-K2-* — طبقة المستخدم (8 عدسات)"),
    ("CONTENT_K2",   "k2_contentpack.json",    "COMPOSE-{X} — معاجم التركيب الثمانية"),
    ("SECTIONS_K3",  "skill_sections.json",    "55-USER-K3-* §1 — U01/U08/U09/U10"),
    ("THREE_K3",     "three_texts.json",       "80-K3-TEXTS — النصوص الثلاثة"),
    ("CIRCLE_K3",    "circle_map_v2.json",     "79-K3-USERMAP §2 — المشترك + الخاتمات (DEC-195/ج)"),
    ("BANNER_K3",    "k3_banner.json",         "ر-4 — لافتة الثقة (TRUST_BANNER)"),
    ("TEXTLAYER_K3", "k3_textlayer.json",      "k3_content + k3_contentpack — طبقة التركيب النصّي"),
    ("G5_K3",        "k3_g5.json",             "G5 — بوابة التطهير اللغوي (§5 · DEC-137/3)"),
    ("PUR_K2",       "k2_pur.json",            "R9 — قواميس التطهير الثمانية (72 بنداً · 55-USER-K2-* §4)"),
    ("INTENSITY_K2", "k2_intensity.json",      "R1 — كتل الشدة (64 كتلة · 55-USER-INT8-*)"),
    ("LOOKALIKE_K2", "k2_lookalike.json",      "R8/R11 — مصفوفة التمييز (7 أزواج · 51-MATRIX-05)"),
    ("LOCKREG_K2",   "k2_lock_registry.json",  "DEC-229 — سجلّ الذِكر المقبول داخل حقول القفل"),
]


def canon_json(obj):
    """تسلسل مقنَّن — مطابق لقواعد 87-PARITY §4 (فرز بنقطة الترميز · بلا فراغ)."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main():
    src_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    out_path = os.path.join(HERE, "packs.js")

    blobs, manifest, total = [], {}, 0
    for name, fn, desc in PACKS:
        path = os.path.join(src_dir, fn)
        with open(path, encoding="utf-8") as fh:
            obj = json.load(fh)
        text = canon_json(obj)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        manifest[name] = {"file": fn, "sha256": digest, "bytes": len(text.encode("utf-8"))}
        total += len(text.encode("utf-8"))
        # يُضمَّن كسلسلة JSON ثم يُحلَّل — يحفظ التطابق الحرفي ويُبقي البصمة قابلة للتحقق
        blobs.append(f'  {name}: {json.dumps(text, ensure_ascii=False)},')
        print(f"  {name:<14} {fn:<26} {len(text.encode('utf-8')):>7} بايت  {digest[:16]}")

    body = "\n".join(blobs)
    man = json.dumps({k: v["sha256"] for k, v in manifest.items()},
                     ensure_ascii=False, sort_keys=True, indent=2)

    js = f'''"use strict";
/**
 * packs.js — حزم المحتوى المضمَّنة (المرحلة ② · مولَّد آلياً)
 * ==========================================================
 * ⚠️ لا يُحرَّر يدوياً. يُعاد توليده بـ`build_packs.py`.
 * المحتوى منقول حرفياً من حزم خط الأساس — بلا اختصار ولا إعادة صياغة.
 *
 * كل حزمة مسلسلة بصيغة مقنَّنة (مفاتيح مرتَّبة · بلا مسافات) وبصمتها
 * SHA-256 مثبَتة أدناه. `verifyPacks()` يُعيد التحقق عند التحميل ويوقف
 * الإصدار عند أي انجراف (ن-7).
 *
 * الحجم الكلي: {total} بايت
 */

const _RAW = {{
{body}
}};

const PACK_SHA = {man};

const PACK_SOURCE = {json.dumps({k: v["file"] for k, v in manifest.items()}, ensure_ascii=False, sort_keys=True, indent=2)};

/** SHA-256 متزامن — تنفيذ مستقلّ ليعمل بلا شبكة وبلا اعتماد على WebCrypto. */
function _sha256(str) {{
  const K = [
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
  let H = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
  // UTF-8
  const bytes = [];
  for (let i = 0; i < str.length; i++) {{
    let c = str.codePointAt(i);
    if (c > 0xffff) i++;
    if (c < 0x80) bytes.push(c);
    else if (c < 0x800) bytes.push(0xc0 | (c >> 6), 0x80 | (c & 63));
    else if (c < 0x10000) bytes.push(0xe0 | (c >> 12), 0x80 | ((c >> 6) & 63), 0x80 | (c & 63));
    else bytes.push(0xf0 | (c >> 18), 0x80 | ((c >> 12) & 63), 0x80 | ((c >> 6) & 63), 0x80 | (c & 63));
  }}
  const bitLen = bytes.length * 8;
  bytes.push(0x80);
  while (bytes.length % 64 !== 56) bytes.push(0);
  for (let i = 7; i >= 0; i--) bytes.push((bitLen / Math.pow(2, i * 8)) & 0xff);
  const rotr = (x, n) => (x >>> n) | (x << (32 - n));
  for (let off = 0; off < bytes.length; off += 64) {{
    const w = new Array(64);
    for (let i = 0; i < 16; i++) {{
      w[i] = (bytes[off+i*4] << 24) | (bytes[off+i*4+1] << 16) | (bytes[off+i*4+2] << 8) | bytes[off+i*4+3];
    }}
    for (let i = 16; i < 64; i++) {{
      const s0 = rotr(w[i-15],7) ^ rotr(w[i-15],18) ^ (w[i-15] >>> 3);
      const s1 = rotr(w[i-2],17) ^ rotr(w[i-2],19) ^ (w[i-2] >>> 10);
      w[i] = (w[i-16] + s0 + w[i-7] + s1) | 0;
    }}
    let [a,b,c,d,e,f,g,h] = H;
    for (let i = 0; i < 64; i++) {{
      const S1 = rotr(e,6) ^ rotr(e,11) ^ rotr(e,25);
      const ch = (e & f) ^ (~e & g);
      const t1 = (h + S1 + ch + K[i] + w[i]) | 0;
      const S0 = rotr(a,2) ^ rotr(a,13) ^ rotr(a,22);
      const mj = (a & b) ^ (a & c) ^ (b & c);
      const t2 = (S0 + mj) | 0;
      h=g; g=f; f=e; e=(d+t1)|0; d=c; c=b; b=a; a=(t1+t2)|0;
    }}
    H = H.map((v, i) => (v + [a,b,c,d,e,f,g,h][i]) | 0);
  }}
  return H.map((v) => (v >>> 0).toString(16).padStart(8, "0")).join("");
}}

class PackIntegrityError extends Error {{
  constructor(m) {{ super(m); this.name = "PackIntegrityError"; }}
}}

/** يوقف الإصدار عند انجراف أي حزمة عن بصمتها (ن-7). */
function verifyPacks() {{
  const bad = [];
  for (const name of Object.keys(PACK_SHA)) {{
    if (!(name in _RAW)) {{ bad.push(`${{name}}: الحزمة غائبة`); continue; }}
    const got = _sha256(_RAW[name]);
    if (got !== PACK_SHA[name]) {{
      bad.push(`${{name}} (${{PACK_SOURCE[name]}}): البصمة ${{got.slice(0,16)}} ≠ ${{PACK_SHA[name].slice(0,16)}}`);
    }}
  }}
  if (bad.length) throw new PackIntegrityError("انجراف حزمة — يُوقَف الإصدار:\\n- " + bad.join("\\n- "));
  return true;
}}

const PACKS = {{}};
for (const k of Object.keys(_RAW)) PACKS[k] = JSON.parse(_RAW[k]);

if (typeof module !== "undefined") {{
  module.exports = {{ PACKS, PACK_SHA, PACK_SOURCE, verifyPacks, _sha256, PackIntegrityError }};
}}
'''
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(js)
    print(f"\n✅ packs.js — {total} بايت محتوى · {os.path.getsize(out_path)} بايت الملف")
    json.dump(manifest, open(os.path.join(HERE, "packs_manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
