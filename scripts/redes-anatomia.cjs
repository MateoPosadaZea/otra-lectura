// Escena «anatomia» de scripts/redes.cjs: un objeto que se desarma en piezas
// numeradas, con líneas punteadas hacia cada nombre y una pieza resaltada con
// una luz roja suave. Primero aparece armado, luego se abre como un
// despiece de manual, se nombran las piezas una a una y al final se enciende
// la que importa. Dibujos a tinta con aguadas de acuarela, en la paleta del
// periódico. Cada dibujo devuelve sus piezas (de arriba abajo) y el fondo.

function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

const ms = (x) => Math.round(x);
const dib = (t, dur = 700) => `style="animation: dibuja ${ms(dur)}ms var(--trazo) ${ms(t)}ms both"`;
const aparece = (t, dur = 600) => `style="animation: aparece ${ms(dur)}ms var(--suave) ${ms(t)}ms both"`;

// Tejas en hileras de medias lunas, recortadas por el tejado.
function tejas(x0, x1, y0, y1, paso = 24) {
  let d = "";
  for (let y = y0; y <= y1; y += paso) {
    d += `M${x0} ${y}`;
    for (let x = x0; x < x1; x += 22) d += ` q11 13 22 0`;
  }
  return d;
}

const DIBUJOS = {
  // La gotera: tejado, entretecho, la gota y el cielo raso manchado,
  // sobre la sala donde alguien se sienta a leer. Luz desde la izquierda:
  // el lado derecho de cada pieza lleva una segunda aguada, más oscura.
  gotera(id, t) {
    const piezas = [
      {
        cy: 92, y: 104, junta: 102, ancla: [492, 118],
        aguada: `<path class="ac-1" d="M486 160 L660 34 L834 160 Z"/>
          <path class="ac-2" d="M660 34 L834 160 H700 Z"/>
          <rect class="ac-3" x="744" y="52" width="34" height="62"/><rect class="ac-2" x="738" y="46" width="46" height="12"/>
          <path class="ac-3" d="M476 160 H844 L836 172 H484 Z"/>`,
        trazo: `<path class="tr an-tr" pathLength="1" d="M744 108 V58 M778 58 V96 M738 46 H784 V58 H738 Z"/>
          <path class="tr an-tr" pathLength="1" d="M474 162 L660 30 L846 162"/>
          <path class="tr an-tr" pathLength="1" d="M484 172 H836 L846 162 H474 Z"/>`,
        extra: `<g clip-path="url(#tej-${id})"><path class="an-fino" d="${tejas(470, 850, 58, 158)}"/>
          <path class="an-fino an-sombra" d="${tejas(470, 850, 70, 158, 48)}"/></g>
          <path class="an-fino" d="M660 30 V160"/>`,
      },
      {
        cy: 252, y: 276, junta: 40, ancla: [500, 250],
        aguada: `<rect class="ac-1" x="500" y="222" width="320" height="46"/>
          <path class="ac-2" d="M500 268 H820 L812 280 H508 Z"/>
          <rect class="ac-3" x="548" y="280" width="224" height="22"/>`,
        trazo: `<path class="tr an-tr" pathLength="1" d="M500 222 H820 V268 H500 Z"/>
          <path class="tr an-tr" pathLength="1" d="M500 268 L508 280 H812 L820 268"/>
          <path class="tr an-tr" pathLength="1" d="M548 280 V302 H772 V280"/>`,
        extra: `<path class="an-fino" d="M540 222 V268 M580 222 V268 M620 222 V268 M660 222 V268 M700 222 V268 M740 222 V268 M780 222 V268"/>
          <path class="an-fino an-veta" d="M510 236 q14 -6 26 0 M552 250 q12 6 24 0 M594 238 q14 -6 22 0 M634 252 q12 6 22 0 M676 236 q14 -6 22 0 M716 250 q12 6 22 0 M758 240 q14 -6 22 0 M560 291 q30 -6 60 0 M650 293 q40 6 80 0"/>
          <g class="an-clavo"><circle cx="520" cy="230" r="2.6"/><circle cx="800" cy="230" r="2.6"/><circle cx="520" cy="260" r="2.6"/><circle cx="800" cy="260" r="2.6"/></g>`,
      },
      {
        cy: 404, y: 440, junta: -50, ancla: [618, 414], destaca: true,
        luz: "M660 346 C640 378 620 398 620 420 A40 40 0 0 0 700 420 C700 398 680 378 660 346 Z",
        aguada: `<path class="ac-1" d="M660 346 C640 378 620 398 620 420 A40 40 0 0 0 700 420 C700 398 680 378 660 346 Z"/>
          <path class="ac-2" d="M660 346 C680 378 700 398 700 420 A40 40 0 0 1 664 460 C686 440 690 400 660 346 Z"/>`,
        trazo: `<path class="tr an-tr" pathLength="1" d="M660 346 C640 378 620 398 620 420 A40 40 0 0 0 700 420 C700 398 680 378 660 346 Z"/>`,
        extra: `<path class="an-brillo" d="M638 418 Q638 400 648 388"/><circle class="an-brillo-p" cx="640" cy="432" r="3.5"/>`,
      },
      {
        cy: 546, y: 604, junta: -212, ancla: [478, 548], mancha: true,
        aguada: `<path class="ac-1" d="M510 520 H810 L844 572 H476 Z"/>
          <path class="ac-2" d="M476 572 H844 V586 H476 Z"/>`,
        trazo: `<path class="tr an-tr" pathLength="1" d="M510 520 H810 L844 572 H476 Z"/>
          <path class="tr an-tr" pathLength="1" d="M476 572 V586 H844 V572"/>`,
        extra: `<path class="an-fino" d="M560 520 L548 572 M610 520 L604 572 M710 520 L716 572 M760 520 L772 572"/>`,
      },
    ];
    // La sala: el piso, la poltrona, la mesa con el libro y
    // la lámpara de pie con su luz.
    const P = 800;
    const fondo = `
      <path class="tr an-tr" pathLength="1" d="M0 ${P} H900" ${dib(t + 200, 1100)}/>
      <g filter="url(#acu-${id})" ${aparece(t + 500, 700)}>
        <path class="ac-2" d="M606 ${P} V${P - 56} Q606 ${P - 84} 636 ${P - 84} H694 Q722 ${P - 84} 722 ${P - 56} V${P} Z"/>
        <path class="ac-3" d="M598 ${P - 44} H730 V${P - 26} H598 Z"/>
        <path class="ac-1" d="M744 ${P - 50} H800 V${P - 44} H744 Z"/><path class="ac-3" d="M752 ${P - 58} H788 V${P - 50} H752 Z"/>
      </g>
      <path class="tr an-tr" pathLength="1" d="M596 ${P} V${P - 44} Q596 ${P - 62} 612 ${P - 62} M732 ${P} V${P - 44} Q732 ${P - 62} 716 ${P - 62} M598 ${P - 44} H730 M598 ${P - 26} H730 M614 ${P - 62} V${P - 82} Q614 ${P - 98} 634 ${P - 98} H694 Q714 ${P - 98} 714 ${P - 82} V${P - 62}" ${dib(t + 500, 1100)}/>
      <path class="tr an-tr" pathLength="1" d="M772 ${P} V${P - 44} M744 ${P - 50} H800 M752 ${P - 58} H788 V${P - 50} M752 ${P - 58} V${P - 50}" ${dib(t + 650, 800)}/>
      <path class="tr an-tr" pathLength="1" d="M838 ${P} V${P - 96} M818 ${P} H858 M820 ${P - 96} H856 L846 ${P - 124} H830 Z" ${dib(t + 750, 900)}/>`;
    const defs = `<clipPath id="tej-${id}"><path d="M486 160 L660 34 L834 160 Z"/></clipPath>
      <linearGradient id="gp-${id}" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>
      <mask id="piso-${id}"><rect x="0" y="${P - 110}" width="900" height="110" fill="url(#gp-${id})"/></mask>
      <radialGradient id="lg-${id}"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>
      <mask id="luz-${id}"><circle r="70" fill="url(#lg-${id})"/></mask>`;
    return { piezas, fondo, defs };
  },
};

// e: { dibujo, piezas: [{nombre, nota}], destacar } ; t: inicio de la figura.
// Devuelve { svg, fin } con el instante en que termina de encenderse.
function anatomia(e, t, id) {
  const d = DIBUJOS[e.dibujo || "gotera"];
  if (!d) throw new Error(`dibujo desconocido: ${e.dibujo}`);
  const { piezas, fondo, defs } = d(id, t);
  const rotulos = e.piezas || [];
  const n = piezas.length;
  const tSepara = t + 1300, tNombre = t + 2300, cada = 760;
  const tLuz = tNombre + n * cada + 200;
  const dest = e.destacar != null ? e.destacar - 1 : piezas.findIndex((p) => p.destaca);

  let s = `<defs>
    <filter id="acu-${id}" x="-10%" y="-10%" width="120%" height="120%">
      <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="3" seed="7" result="r"/>
      <feDisplacementMap in="SourceGraphic" in2="r" scale="5" xChannelSelector="R" yChannelSelector="G"/>
    </filter>
    <pattern id="trama-${id}" width="13" height="13" patternUnits="userSpaceOnUse"><circle cx="6.5" cy="6.5" r="3.1" fill="var(--rojo)"/></pattern>
    <pattern id="trama-tinta-${id}" width="12" height="12" patternUnits="userSpaceOnUse"><circle cx="6" cy="6" r="2" fill="rgba(22,19,15,.5)"/></pattern>
    <radialGradient id="luzroja-${id}"><stop offset="0" stop-color="var(--rojo)" stop-opacity=".26"/><stop offset=".55" stop-color="var(--rojo)" stop-opacity=".1"/><stop offset="1" stop-color="var(--rojo)" stop-opacity="0"/></radialGradient>
    <radialGradient id="rg-${id}"><stop offset=".25" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>
    <mask id="halo-${id}"><circle cx="0" cy="0" r="165" fill="url(#rg-${id})"/></mask>
    ${defs}
  </defs>`;
  s += fondo;

  const dy = (p) => p.y - p.cy;
  // El halo de la pieza destacada va detrás de todo.
  if (dest >= 0) {
    const p = piezas[dest];
    s += `<g transform="translate(660 ${420 + dy(p)})"><g style="animation: halo 1300ms var(--muelle) ${ms(tLuz)}ms both">
      <circle r="160" fill="url(#luzroja-${id})"/></g></g>`;
  }

  piezas.forEach((p, i) => {
    const tA = t + 250 + i * 140;
    s += `<g transform="translate(0 ${dy(p)})"><g style="animation: aparece 700ms var(--suave) ${ms(tA)}ms both">
      <g style="--dy:${p.junta}px;animation: separa 1500ms var(--muelle) ${ms(tSepara + i * 110)}ms both">
      <g style="animation: flota ${3200 + i * 500}ms ease-in-out ${ms(tSepara + 1500 + i * 300)}ms infinite alternate">
        <g filter="url(#acu-${id})" ${aparece(tA + 300, 900)}>${p.aguada}</g>
        <g ${aparece(tA + 500, 900)}>${p.extra}</g>
        ${p.luz && i === dest ? `<path class="an-rojo-f" d="${p.luz}" ${aparece(tLuz + 150, 700)}/>` : ""}
        ${p.trazo.replace(/<path /g, () => `<path ${dib(tA, 900)} `)}
        ${p.mancha ? `<g transform="translate(660 546)"><g style="animation: mancha 1800ms var(--muelle) ${ms(tLuz + 1500)}ms both">
          <g filter="url(#acu-${id})"><path class="an-mancha" d="M-60 -8 Q-54 -22 -24 -20 Q0 -28 28 -18 Q60 -18 58 2 Q64 18 34 20 Q8 26 -16 20 Q-56 22 -60 -8 Z"/>
          <path class="an-mancha-c" d="M-34 -4 Q-30 -12 -12 -11 Q4 -16 20 -9 Q36 -8 34 2 Q36 10 18 11 Q2 14 -12 10 Q-34 11 -34 -4 Z"/></g>
          <path class="an-aro" d="M-62 -8 Q-56 -24 -24 -22 Q0 -30 28 -20 Q62 -20 60 2 Q66 20 34 22 Q8 28 -16 22 Q-58 24 -62 -8 Z"/></g></g>` : ""}
      </g></g></g></g>`;
  });

  // La gota que cae hasta el cielo raso, cuando se enciende la luz.
  const gota = piezas[dest], techo = piezas.find((p) => p.mancha);
  if (gota && techo) {
    const y0 = 462 + dy(gota), y1 = 524 + dy(techo);
    s += `<g transform="translate(660 ${y0})"><g style="--caida:${y1 - y0}px;animation: cae 900ms var(--salida) ${ms(tLuz + 700)}ms both">
      <path class="an-gotita" d="M0 -16 C-6 -6 -10 0 -10 6 A10 10 0 0 0 10 6 C10 0 6 -6 0 -16 Z"/></g></g>`;
  }

  // Rótulos: número, nombre y nota, con la línea de puntos hasta la pieza.
  const puntos = (x0, x1, y, t0, clase) => {
    let o = "";
    for (let x = x0, k = 0; x < x1; x += 13, k++) o += `<circle class="${clase}" cx="${x}" cy="${y}" r="2.7" ${aparece(t0 + k * 14, 160)}/>`;
    return o;
  };
  piezas.forEach((p, i) => {
    const r = rotulos[i] || {}, tR = tNombre + i * cada;
    const [ax, ayDib] = p.ancla, ay = ayDib + dy(p), y = ay + 13;
    const nombre = r.nombre || "", ancho = 66 + nombre.length * 22 + 30;
    const rojo = i === dest;
    s += puntos(ancho, ax - 14, ay, tR, "an-punto");
    s += `<circle class="an-ojo" cx="${ax - 4}" cy="${ay}" r="7" ${aparece(tR + 420, 300)}/>`;
    s += `<g style="animation: sube 600ms var(--suave) ${ms(tR + 80)}ms both">
      <text x="0" y="${y}" class="an-num">${String(i + 1).padStart(2, "0")}</text>
      <text x="66" y="${y}" class="an-nombre">${esc(nombre)}</text></g>`;
    if (rojo) {
      s += `<g ${aparece(tLuz, 500)}><text x="0" y="${y}" class="an-num an-rojo">${String(i + 1).padStart(2, "0")}</text>
        <text x="66" y="${y}" class="an-nombre an-rojo">${esc(nombre)}</text></g>`;
      s += puntos(ancho, ax - 14, ay, tLuz, "an-punto an-punto-rojo");
      s += `<circle class="an-ojo an-ojo-rojo" cx="${ax - 4}" cy="${ay}" r="7" ${aparece(tLuz + 300, 300)}/>`;
    }
    (r.nota || "").split("\n").forEach((linea, k) => {
      s += `<text x="66" y="${y + 44 + k * 36}" class="an-nota" style="animation: sube 600ms var(--suave) ${ms(tR + 260 + k * 90)}ms both">${esc(linea)}</text>`;
    });
  });

  return { svg: `<svg class="ilus an" viewBox="0 0 900 820" preserveAspectRatio="xMidYMid meet">${s}</svg>`, fin: tLuz + 2600 };
}

const CSS = `
.esc-anatomia{justify-content:flex-start}
.an-tit{font-family:var(--tit);font-weight:var(--tw);font-size:96px;line-height:1.04;letter-spacing:-.01em}
.an-bajada{font-family:var(--sans);font-weight:500;font-size:40px;line-height:1.3;color:var(--tenue);margin-top:18px;text-wrap:balance;max-width:820px}
.an-fig{height:820px;margin-top:30px}
.an-tr{stroke-width:3.2}
.an-fino{fill:none;stroke:rgba(22,19,15,.5);stroke-width:2;stroke-linecap:round}
.an-brillo{fill:none;stroke:var(--papel);stroke-width:5;stroke-linecap:round}
.ac-1,.ac-2,.ac-3{stroke:rgba(22,19,15,.14);stroke-width:5;stroke-linejoin:round}
.ac-1{fill:rgba(22,19,15,.08)}.ac-2{fill:rgba(22,19,15,.17)}.ac-3{fill:rgba(22,19,15,.32)}
.an-sombra{stroke:rgba(22,19,15,.28);stroke-width:3}.an-veta{stroke:rgba(22,19,15,.35)}.an-clavo{fill:var(--tinta)}
.an-brillo-p{fill:var(--papel)}.an-mancha-c{fill:rgba(90,60,30,.35)}.an-aro{fill:none;stroke:rgba(90,60,30,.55);stroke-width:2.4}
.an-mancha{fill:rgba(90,60,30,.42)}
.an-gotita{fill:rgba(22,19,15,.3);stroke:var(--tinta);stroke-width:2.5}
.an-punto{fill:var(--tinta)}.an-punto-rojo{fill:var(--rojo)}.an-ojo-rojo{stroke:var(--rojo)}
.an-ojo{fill:var(--papel);stroke:var(--tinta);stroke-width:2.6}
.an text{font-family:var(--sans)}
.an-num{font-size:34px;font-weight:600;fill:var(--tenue)!important;font-variant-numeric:tabular-nums;letter-spacing:.02em}
.an-nombre{font-size:42px;font-weight:500;fill:var(--tinta)}
.an-nota{font-size:30px;font-weight:500;fill:var(--tenue)!important}
.an-rojo{fill:var(--rojo)!important}
.an-rojo-f{fill:rgba(161,35,27,.78)}
@keyframes separa{from{transform:translateY(var(--dy))}to{transform:none}}
@keyframes flota{from{transform:translateY(0)}to{transform:translateY(-7px)}}
@keyframes halo{0%{opacity:0;transform:scale(.3)}20%{opacity:1}100%{opacity:1;transform:none}}
@keyframes cae{0%{opacity:0;transform:translateY(-10px)}15%{opacity:1}85%{opacity:1}100%{opacity:0;transform:translateY(var(--caida))}}
@keyframes mancha{from{opacity:0;transform:scale(.25)}to{opacity:1;transform:none}}
`;

module.exports = { anatomia, CSS, DIBUJOS };
