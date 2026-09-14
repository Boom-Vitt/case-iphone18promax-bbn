"""Start a project-specific Blender background process with the MCP bridge."""
import os
import shutil
import subprocess
from pathlib import Path
root = Path(__file__).resolve().parents[1]
blender = os.environ.get('BLENDER_BIN') or shutil.which('blender') or '/Applications/Blender.app/Contents/MacOS/Blender'
if not Path(blender).exists():
    raise SystemExit('Set BLENDER_BIN to your Blender executable')
env = dict(os.environ, BLENDER_MCP_DISABLE_TELEMETRY='1')
workspace = root / 'blender/case-workspace.blend'
args = [blender, '--background']
if workspace.exists():
    args.append(str(workspace))
else:
    args.append('--factory-startup')
args += ['--python', str(root / 'blender/headless.py')]
raise SystemExit(subprocess.call(args, cwd=root, env=env))
