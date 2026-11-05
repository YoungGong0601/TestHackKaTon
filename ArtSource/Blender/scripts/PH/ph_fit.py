"""친구 프리팹 실물과 PH 모델 비교 (Blender 불필요).
python3 ph_fit.py <프리팹폴더> <bbox.json>   bbox.json 은 ph_bbox.py 가 만든다.
PH_Map.json 의 자리마다 회색 메시 범위와 모델 범위를 프리팹 좌표로 나란히 찍는다."""
import glob, re, sys, json, os

HDR = re.compile(r'^--- !u!(\d+) &(-?\d+)(?: stripped)?\s*$', re.M)
UNIT = {'10202': ((-.5, -.5, -.5), (.5, .5, .5)), '10210': ((-.5, -.5, 0), (.5, .5, 0)), '10206': ((-.5, -1, -.5), (.5, 1, .5)),
        '10207': ((-.5, -.5, -.5), (.5, .5, .5)), '10208': ((-.5, -1, -.5), (.5, 1, .5))}  # 큐브 쿼드 원기둥 구 캡슐


def vec(s, key):
    m = re.search(key + r': \{x: ([-\d.e]+), y: ([-\d.e]+), z: ([-\d.e]+)(?:, w: ([-\d.e]+))?\}', s)
    return tuple(float(x) for x in m.groups() if x is not None) if m else None


def load(path):
    t = open(path, encoding='utf-8').read()
    ms = list(HDR.finditer(t))
    docs = {m.group(2): (m.group(1), t[m.end():ms[i + 1].start() if i + 1 < len(ms) else len(t)]) for i, m in enumerate(ms)}
    names, meshes, tf = {}, {}, {}
    for k, (c, s) in docs.items():
        if c == '1':
            names[k] = re.search(r'm_Name: (.*)', s).group(1).strip()
        elif c == '33':
            g, m = re.search(r'm_GameObject: \{fileID: (-?\d+)', s), re.search(r'm_Mesh: \{fileID: (-?\d+)', s)
            if g and m and m.group(1) in UNIT:
                meshes[g.group(1)] = UNIT[m.group(1)]
        elif c in ('4', '224'):
            g, f = re.search(r'm_GameObject: \{fileID: (-?\d+)\}', s), re.search(r'm_Father: \{fileID: (-?\d+)\}', s)
            if g and f:
                ch = re.findall(r'- \{fileID: (-?\d+)\}', s.split('m_Children:')[1].split('m_Father')[0])
                tf[k] = dict(go=g.group(1), father=f.group(1), children=ch, pos=vec(s, 'm_LocalPosition') or (0, 0, 0),
                             rot=vec(s, 'm_LocalRotation') or (0, 0, 0, 1), scl=vec(s, 'm_LocalScale') or (1, 1, 1))
    return names, meshes, tf


def rotate(q, v):
    x, y, z, w = q
    tx, ty, tz = 2 * (y * v[2] - z * v[1]), 2 * (z * v[0] - x * v[2]), 2 * (x * v[1] - y * v[0])
    return v[0] + w * tx + y * tz - z * ty, v[1] + w * ty + z * tx - x * tz, v[2] + w * tz + x * ty - y * tx


def chain(tf, k):
    out = []
    while k in tf:
        out.append(tf[k])
        k = tf[k]['father']
    return out


def to_root(c, p):
    for t in c:
        p = rotate(t['rot'], tuple(p[i] * t['scl'][i] for i in range(3)))
        p = tuple(p[i] + t['pos'][i] for i in range(3))
    return p


def box(ps):
    return [min(p[i] for p in ps) for i in range(3)], [max(p[i] for p in ps) for i in range(3)]


def corners(a, b):
    return [(x, y, z) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]


def main(folder, bbox):
    rows = [r for m in sorted(glob.glob("Assets/Art3D/PH_Map*.json")) for r in json.load(open(m, encoding="utf-8"))["rows"]]
    bb = json.load(open(bbox))
    fmt = lambda v: "(" + ",".join(f"{x:.3f}" for x in v) + ")"
    for r in rows:
        if not r.get("model"):
            continue
        names, meshes, tf = load(os.path.join(folder, r["prefab"] + ".prefab"))
        paths = {k: "/".join(names[t['go']] for t in reversed(chain(tf, k)[:-1])) for k in tf}
        key = next((k for k, p in paths.items() if p == r["target"]), None) or \
            next((k for k, p in paths.items() if p.endswith("/" + r["target"])), None)
        n = os.path.basename(r["model"])[:-4]
        if key is None or n not in bb:
            print("MISSING", n, r["target"])
            continue
        gray = []

        def walk(k):
            if tf[k]['go'] in meshes:
                gray.extend(to_root(chain(tf, k), p) for p in corners(*meshes[tf[k]['go']]))
            for c in tf[k]['children']:
                if c in tf:
                    walk(c)
        walk(key)
        m = box([to_root(chain(tf, key), p) for p in corners(bb[n]['mn'], bb[n]['mx'])])
        if not gray:
            print(f"NOGRAY {n:32s} model {fmt(m[0])}..{fmt(m[1])}")
            continue
        g = box(gray)
        size = [g[1][i] - g[0][i] for i in range(3)]
        bad = [("xyz"[i] + s) for i in range(3) for s, d in (("-", m[0][i] - g[0][i]), ("+", m[1][i] - g[1][i])) if abs(d) > max(0.03, 0.08 * size[i])]
        print(f"{'DIFF' if bad else 'OK  '} {n:32s} gray {fmt(g[0])}..{fmt(g[1])} model {fmt(m[0])}..{fmt(m[1])} {' '.join(bad)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
