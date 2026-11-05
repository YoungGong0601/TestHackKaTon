"""ph_spec 표로 Assets/Art3D/PH_Map.json 을 만든다: python3 ph_map.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ph_spec import ROWS, LOOKS, CLEAR

rows = []
for n, r in ROWS.items():
    if r["prefab"]:
        row = {"prefab": r["prefab"], "target": r["target"], "model": f"Models/PH/{n}.fbx"}
        if "look" in r:
            row["look"] = LOOKS.index(r["look"])
        rows.append(row)
rows += [{"prefab": p, "target": t, "model": ""} for p, t in CLEAR]
json.dump({"rows": rows}, open("Assets/Art3D/PH_Map.json", "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
print("PH_Map", len(rows), "행")
