"""Keep Blender's project bridge alive without changing an open UI session."""
from pathlib import Path
import os
import runpy
import time
import bpy

root = Path(__file__).resolve().parents[1]
os.environ['BBN_MAIN_THREAD_DRIVER'] = '1'
runpy.run_path(str(root / 'blender/bootstrap.py'), run_name='__main__')
scene = bpy.context.scene
workspace = root / 'blender/case-workspace.blend'
if not workspace.exists():
    bpy.ops.wm.save_as_mainfile(filepath=str(workspace))
server = bpy.types.blendermcp_server
if not server.running:
    raise RuntimeError('MCP bridge could not start; check localhost:9876')
try:
    while server.running:
        server._drain_command_queue()
        time.sleep(0.02)
finally:
    server.stop()
