// Piezas fijas del perfil de Instagram: foto de perfil (3 opciones) y portadas
// de historias destacadas. Salen en redes/instagram/.
// Uso: NODE_PATH=$(npm root -g) node scripts/instagram.cjs
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");
const RAIZ = path.resolve(__dirname, "..");
const SALIDA = path.join(RAIZ, "redes", "instagram");
const f = (n) => "file://" + path.join(RAIZ, "plantilla", "fuentes", n);

const base = (cuerpo, extra = "") => `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:U;src:url(${f("unifraktur.woff2")})}
@font-face{font-family:S;src:url(${f("instrument-serif.woff2")})}
@font-face{font-family:S;font-style:italic;src:url(${f("instrument-serif-italic.woff2")})}
@font-face{font-family:I;src:url(${f("inter-tight.woff2")});font-weight:100 900}
*{margin:0;box-sizing:border-box}
html,body{width:1080px;height:1080px;background:#efe7d6;color:#16130f;overflow:hidden}
body::after{content:"";position:absolute;inset:0;opacity:.5;background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 .09 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
.c{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
.p{display:inline-block;width:.2em;height:.2em;border-radius:50%;background:#a1231b;margin-left:.04em}
${extra}</style></head><body>${cuerpo}</body></html>`;

const PERFIL = {
  // Las dos palabras, una sobre otra: se lee el nombre completo.
  "perfil-a-nombre": base(`<div class="c" style="font-family:U;font-size:300px;line-height:.95"><div>Otra</div><div>Lectura<span class="p"></span></div></div>`),
  // Monograma: las iniciales en la letra del logo.
  "perfil-b-monograma": base(`<div class="c" style="font-family:U;font-size:560px;line-height:1"><div>OL<span class="p" style="width:.13em;height:.13em"></span></div></div>`),
  // Solo la O gótica con el punto rojo: el sello.
  "perfil-c-sello": base(`<div class="c" style="font-family:U;font-size:760px;line-height:1"><div style="margin-top:-40px">O<span class="p" style="width:.12em;height:.12em"></span></div></div>`),
};

// Portadas de destacadas: dibujos, no texto (Instagram ya pone el nombre debajo).
const MAPA = JSON.parse(fs.readFileSync(path.join(RAIZ, "redes", "mapas", "colombia.json"), "utf8"));
const trazo = 'fill="none" stroke="#16130f" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"';
const bog = MAPA.ciudades.bogota;
const DESTACADAS = {
  "quienes-somos": `<div class="c" style="font-family:U;font-size:640px;line-height:1"><div style="margin-top:-30px">O<span class="p" style="width:.12em;height:.12em"></span></div></div>`,
  "mapas": `<div class="c"><svg viewBox="${MAPA.viewBox}" style="height:760px"><path d="${MAPA.contorno}" fill="none" stroke="#16130f" stroke-width="10" stroke-linejoin="round"/><circle cx="${bog.x}" cy="${bog.y}" r="34" fill="#a1231b"/></svg></div>`,
  "graficos": `<div class="c"><svg viewBox="0 0 600 600" style="width:620px"><path d="M60 540 H540" ${trazo}/><rect x="100" y="380" width="100" height="160" fill="#a39c92"/><rect x="250" y="260" width="100" height="280" fill="#a39c92"/><rect x="400" y="110" width="100" height="430" fill="#a1231b"/></svg></div>`,
  "para-conversar": `<div class="c"><svg viewBox="0 0 800 720" style="width:700px"><path d="M90 120 H460 Q490 120 490 150 V330 Q490 360 460 360 H220 L150 430 L165 360 H90 Q60 360 60 330 V150 Q60 120 90 120 Z" ${trazo}/><path d="M360 400 H710 Q740 400 740 430 V590 Q740 620 710 620 H650 L670 690 L590 620 H360 Q330 620 330 590 V430 Q330 400 360 400 Z" ${trazo.replace("#16130f", "#a1231b")}/></svg></div>`,
};

(async () => {
  fs.mkdirSync(SALIDA, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1080 } });
  const foto = async (html, nombre) => {
    const archivo = path.join(SALIDA, `_${nombre}.html`);
    fs.writeFileSync(archivo, html);
    await p.goto("file://" + archivo);
    await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: path.join(SALIDA, `${nombre}.png`) });
    fs.unlinkSync(archivo);
  };
  for (const [nombre, html] of Object.entries(PERFIL)) await foto(html, nombre);
  for (const [nombre, html] of Object.entries(DESTACADAS)) await foto(base(html), `destacada-${nombre}`);
  await b.close();
  console.log("listo:", fs.readdirSync(SALIDA).join(", "));
})();
