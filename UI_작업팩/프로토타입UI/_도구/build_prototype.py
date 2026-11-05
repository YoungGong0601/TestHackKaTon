"""kiosk-game 원본(읽기만)을 일반 script 한 장으로 합쳐 index.html을 만들고, 음식 그림을 PNG로 뽑는다.
실행: python build_prototype.py          (index.html + images/)
      python build_prototype.py --no-png (index.html만)
"""
import re, sys, base64, pathlib

SRC = pathlib.Path(r'C:\Users\lovel\Desktop\CheckFolder\kiosk-game\src')
TOOL = pathlib.Path(__file__).parent
OUT = TOOL.parent

# (모듈 이름, 파일, 추가로 내보낼 이름)
MODS = [
    ('g', 'core/g.js', []),
    ('kit', 'core/kit.js', []),
    ('data', 'kiosk/data.js', []),
    ('art', 'kiosk/art.js', []),
    ('hw', 'kiosk/hw.js', ['drawReceipt']),
    ('screens', 'kiosk/screens.js', ['SW', 'SH', 'PW', 'PH', 'BASE_BLUR']),
    ('flow', 'kiosk/flow.js', []),
]

THREE_STUB = """
const THREE = (() => {
  class V { constructor() { this.x = 0; this.y = 0; this.z = 0; } set(x, y, z) { this.x = x; this.y = y; this.z = z; return this; } }
  class Obj { constructor() { this.position = new V(); this.scale = new V(); this.rotation = new V(); this.visible = true; this.children = []; } add(c) { this.children.push(c); } }
  class Mesh extends Obj { constructor(g, m) { super(); this.geometry = g; this.material = m || { opacity: 0 }; } }
  class Plain { constructor(o) { Object.assign(this, o || {}); } }
  return { Group: Obj, Mesh, PlaneGeometry: Plain, MeshBasicMaterial: Plain, CanvasTexture: class { constructor(c) { this.image = c; } },
    AdditiveBlending: 2, SRGBColorSpace: 'srgb' };
})();
"""


def wrap(name, rel, extra):
    text = (SRC / rel).read_text(encoding='utf-8')
    if name == 'hw':  # 3D 몸체는 쓰지 않는다. 영수증 그림 함수만.
        i = text.index('/** 영수증 그림 */')
        text = "import { FONT } from '../core/kit.js';\nconst fnt = (s, w = 700) => `${w} ${s}px ${FONT}`;\n" + text[i:]
    uses = []

    def imp(m):
        names, mod = m.group(1), m.group(2)
        base = pathlib.PurePosixPath(mod).stem
        uses.append((base, [n.strip() for n in names.split(',') if n.strip()]))
        return ''
    text = re.sub(r"import\s*\{([^}]*)\}\s*from\s*'([^']+)';", imp, text)
    text = re.sub(r"import\s+\*\s+as\s+THREE\s+from\s+'three';", '', text)
    exports = list(extra)
    for m in re.finditer(r'export\s+(?:async\s+)?(?:const|let|function|class)\s+(\w+)', text):
        exports.append(m.group(1))
    text = re.sub(r'\bexport\s+(?=(?:async\s+)?(?:const|let|function|class)\b)', '', text)
    head = ''.join('const {%s} = M_%s;\n' % (', '.join(ns), b) for b, ns in uses)
    ret = 'return {%s};' % ', '.join(sorted(set(exports)))
    return 'const M_%s = (() => {\n%s%s\n%s\n})();\n' % (name, head, text, ret)


def build():
    mods = ''.join(wrap(*m) for m in MODS)
    # 전역 이름: 원본 모듈이 import로 받던 G만 전역으로 노출
    glue = (TOOL / 'prototype_glue.js').read_text(encoding='utf-8')
    glue = 'const {G} = M_g;\n' + glue
    html = (TOOL / 'prototype_template.html').read_text(encoding='utf-8')
    html = html.replace('/*MODULES*/', (THREE_STUB + mods).replace('</script>', '<\\/script>'))
    html = html.replace('/*GLUE*/', glue)
    (OUT / 'index.html').write_text(html, encoding='utf-8')
    print('index.html', len(html))


JS_EXTRACT = """() => {
  const {art, data} = window.KIOSK, out = {};
  const png = (cv) => cv.toDataURL('image/png').split(',')[1];
  const cv = (w, h, fn) => { const c = document.createElement('canvas'); c.width = w; c.height = h; fn(c.getContext('2d')); return c; };
  for (const it of data.ALL) {
    out[it.id] = png(art.foodArt(it.art));
    if (it.kind === 'burger') {
      out[it.id + '_combo'] = png(art.comboArt(it.art, 'cola', false));
      out[it.id + '_large'] = png(art.comboArt(it.art, 'cola', true));
      out[it.id + '_big'] = png(cv(1000, 860, (c) => art.burger(c, 500, 830, 840, it.art)));
    }
  }
  out['bag'] = png(cv(360, 420, (c) => art.bagArt(c, 180, 400, 300)));
  out['tray'] = png(cv(480, 380, (c) => art.trayArt(c, 240, 360, 400)));
  return out;
}"""


def extract_png():
    from playwright.sync_api import sync_playwright
    img = OUT / 'images'
    img.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto((OUT / 'index.html').as_uri())
        res = pg.evaluate(JS_EXTRACT)
        b.close()
    for k, v in res.items():
        (img / f'{k}.png').write_bytes(base64.b64decode(v))
    print('png', len(res))


if __name__ == '__main__':
    build()
    if '--no-png' not in sys.argv:
        extract_png()
