import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ph, bpy

ph.load("Store", "StoreTable")
src = [o for o in bpy.data.objects if o.type == 'MESH']
o = ph.part("PH_Table", src, ph.turn(0))
ph.finish("PH_Table", o)
