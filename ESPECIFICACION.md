# Otra lectura — especificación técnica

Para pegar en Claude Code. Repo privado ya creado.

## Principios

- Costo fijo cero mientras se prueba el hábito.
- Contenido en markdown, siempre. El HTML se genera al desplegar.
- Vanilla HTML/CSS/JS. Sin frameworks.
- Si hay duda entre simple y elegante, simple.

## Estructura

```
/
├── ediciones/               # una edición por archivo, markdown
│   ├── 2026-09-22-radar-01.md
│   ├── 2026-09-22-radar-02.md
│   └── 2026-09-23-radar.md
├── site/                    # salida generada, lo que publica Pages
│   ├── index.html
│   └── ediciones/*.html
├── prompt.md                # especificación del formato del radar
├── build.sh                 # markdown → HTML + índice
├── deploy.sh                # build + commit + push
└── README.md
```

## Frontmatter de cada edición

```yaml
---
fecha: 2026-09-23
edicion: 3
titulo: "..."
temas: [fiscal-subsidios, clima-adaptacion]
lugares: [Colombia, Bangladés]
cruce_mattriz: []          # candidatas para la sesión de captura
seguimiento: [chaparral]   # temas retomados de ediciones previas
---
```

Los campos `temas`, `cruce_mattriz` y `seguimiento` existen para que la
automatización futura pueda leerlos sin parsear el cuerpo: sirven para
evitar repetir temas y para listar las candidatas pendientes.

## build.sh

1. Recorre `ediciones/*.md`.
2. Parsea el frontmatter y convierte el cuerpo a HTML.
3. Escribe `site/ediciones/<slug>.html` con la plantilla.
4. Genera `site/index.html`: lista cronológica inversa con fecha,
   título y temas.

Conversor: preferir algo mínimo sin dependencias pesadas. Si toca
instalar algo, que sea una sola dependencia y quede fijada en el repo.

## Plantilla del sitio

- Una columna, ancho de lectura cómodo (unos 65 caracteres).
- Tipografía del stack que ya se usa en Mattriz.
- Jerarquía clara entre el nombre de la fricción, sus subtítulos
  (qué pasó, quién lo está resolviendo, contrapeso, historia, cruce) y el
  cuerpo.
- Marcar visualmente distinto los bloques de contrapeso y los de
  "conocimiento general, no verificado".
- Responsive, modo claro y oscuro, sin JS salvo lo imprescindible.

## Despliegue

- GitHub Pages sirviendo `site/`.
- Cloudflare para DNS y certificado.
- Cloudflare Access para dejar el sitio privado para dos usuarios (es
  gratis hasta 50). Quitar esa política es lo único que hay que hacer si
  más adelante se abre al público.

## Fase 2, no construir todavía

Cuando el formato se estabilice (cuatro o cinco ediciones más):

- GitHub Action con cron semanal.
- Script que llama a la API de Anthropic con `prompt.md` más el
  frontmatter de las últimas cinco ediciones, y búsqueda web habilitada.
- Salida en markdown a `ediciones/`.
- El Action abre un pull request en lugar de publicar directo. La
  aprobación humana se queda: la verificación de fuentes es el punto
  donde más fácil se cuela un error.
