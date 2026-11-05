"""합격 검사: blender -b --factory-startup --python ph_check.py -- [이름...]
Models/PH 의 FBX 를 다시 불러와 Unity 좌표 (-x, z, -y) 로 ph_spec 과 비교한다."""
import bpy, os, sys, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import k3d
from ph_spec import ROWS

AX = {"x": 0, "y": 1, "z": 2}
U = lambda p: (-p[0], p[2], -p[1])


def check(name):
    spec = ROWS[name]
    fbx = os.path.join(k3d.ART, "Models", "PH", name + ".fbx")
    if not os.path.exists(fbx):
        return ["FBX 없음"], None
    k3d.reset()
    bpy.ops.import_scene.fbx(filepath=fbx)
    bad, pts, mats = [], [], set()
    for o in bpy.data.objects:
        if o.type == 'MESH':
            pts += [U(o.matrix_world @ v.co) for v in o.data.vertices]
            mats |= {m.name for m in o.data.materials if m}
    if not pts:
        return ["메시 없음"], None
    mn = [min(p[i] for p in pts) for i in range(3)]
    mx = [max(p[i] for p in pts) for i in range(3)]
    size = [mx[i] - mn[i] for i in range(3)]
    tol = spec.get("tol", {})
    for ax, i in AX.items():
        want = spec["size"][i]
        t = tol.get(ax, 0.10)
        if want is None or t is None:
            continue
        if abs(size[i] - want) > t * want + 0.002:
            bad.append(f"{ax} 크기 {size[i]:.3f}, 기준 {want} (±{int(t * 100)}%)")
    c = [(mn[i] + mx[i]) / 2 for i in range(3)]
    if spec["pivot"] == "bottom":
        if abs(mn[1]) > 0.02:
            bad.append(f"바닥 y {mn[1]:.3f}")
        for i, ax in ((0, "x"), (2, "z")):
            if abs(c[i]) > 0.03 + 0.03 * size[i]:
                bad.append(f"{ax} 중심 {c[i]:.3f}")
    elif spec["pivot"] == "center":
        for ax, i in AX.items():
            if abs(c[i]) > 0.01 + 0.03 * size[i]:
                bad.append(f"{ax} 중심 {c[i]:.3f}")
    for ax, (a, b) in spec.get("range", {}).items():
        i = AX[ax]
        if mn[i] < a or mx[i] > b:
            bad.append(f"{ax} 범위 {mn[i]:.3f}..{mx[i]:.3f}, 기준 {a}..{b}")
    f = spec.get("front")
    if f:
        m = bpy.data.objects.get(name + "_FrontMark")
        if m is None:
            bad.append("FrontMark 없음")
        else:
            p = U(m.matrix_world.translation)
            i = AX[f[1].lower()]
            lo, hi = mn[i] + 0.3 * size[i], mx[i] - 0.3 * size[i]
            if (f[0] == "-" and p[i] > lo) or (f[0] == "+" and p[i] < hi):
                bad.append(f"앞면이 {f} 아님 (mark {p[i]:.3f}, 범위 {mn[i]:.3f}..{mx[i]:.3f})")
    dyn = [m for m in mats if m.startswith("M_Dyn")]
    if dyn:
        bad.append(f"글자 면 남음 {dyn}")
    js = os.path.splitext(fbx)[0] + ".json"
    if not os.path.exists(js):
        bad.append("JSON 없음")
    else:
        names = {d["name"] for d in json.load(open(js))["materials"]}
        for m in mats:
            if m.split(".")[0] not in names:
                bad.append(f"JSON 에 없는 머티리얼 {m}")
        for d in json.load(open(js))["materials"]:
            for rel in d.get("maps", {}).values():
                if not os.path.exists(os.path.join(k3d.ART, rel)):
                    bad.append(f"텍스처 없음 {rel}")
    return bad, [round(s, 3) for s in size]


args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
names = [n for n in ROWS if not args or any(n == a or n.startswith(a) for a in args)]
fails = 0
for n in names:
    bad, size = check(n)
    fails += bool(bad)
    print(f"PH_CHECK {'FAIL' if bad else 'PASS'} {n} {size} {bad if bad else ''}")
print(f"PH_CHECK 합계 {len(names) - fails}/{len(names)} 통과")
