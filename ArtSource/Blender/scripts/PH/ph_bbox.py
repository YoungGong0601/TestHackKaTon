"""Models/PH 의 FBX 범위를 Unity 좌표로 JSON 에 쓴다: blender -b --factory-startup --python ph_bbox.py -- <out.json>"""
import bpy, glob, json, os, sys
out = {}
for f in sorted(glob.glob("Assets/Art3D/Models/PH/*.fbx")):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=f)
    pts = [(-p.x, p.z, -p.y) for o in bpy.data.objects if o.type == 'MESH' for p in (o.matrix_world @ v.co for v in o.data.vertices)]
    if pts:
        out[os.path.basename(f)[:-4]] = dict(mn=[min(q[i] for q in pts) for i in range(3)], mx=[max(q[i] for q in pts) for i in range(3)])
json.dump(out, open(sys.argv[sys.argv.index("--") + 1], "w"))
