"""Run from Blender's Python Console. All project assets stay beside this file."""
from pathlib import Path
import importlib.util
import sys
import bpy

PROJECT = Path(__file__).resolve().parents[1]
source = PROJECT / '.local-tools/blender-mcp/addon.py'
if not source.exists():
    raise RuntimeError('Run the Blender MCP setup described in blender/README.md first')
if 'bbn_blender_mcp' not in sys.modules:
    spec = importlib.util.spec_from_file_location('bbn_blender_mcp', source)
    addon = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = addon
    spec.loader.exec_module(addon)
    # No telemetry consent or external asset-service integration for this project.
    addon._telemetry_consent_enabled = lambda: False
    addon.register()
scene = bpy.context.scene
scene['bbn_project_root'] = str(PROJECT)
scene['bbn_assets_directory'] = str(PROJECT / 'blender')
scene['bbn_note'] = 'Leather-case concept workspace. Reference images are in output/leather-cases/references.'
scene.render.filepath = str(PROJECT / 'blender/renders/')
print('BBN Blender MCP connected on localhost:9876. Project:', PROJECT)
