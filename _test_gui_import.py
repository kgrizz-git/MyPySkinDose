from mypyskindose.gui.app import run_gui
from mypyskindose.gui.helpers import get_example_rdsr_files, get_human_mesh_names
print("run_gui:", run_gui)
print("example files:", [p.name for p in get_example_rdsr_files()])
print("human meshes:", get_human_mesh_names())
print("ALL OK")
