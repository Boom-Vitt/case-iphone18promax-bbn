"""Read-only check of the running Blender bridge and project path."""
import json
import socket
from pathlib import Path

root = Path(__file__).resolve().parents[1]
code = "import bpy; print(bpy.context.scene.get('bbn_project_root', 'UNSET'))"
with socket.create_connection(('127.0.0.1', 9876), timeout=8) as connection:
    connection.sendall(json.dumps({'type': 'execute_code', 'params': {'code': code}}).encode())
    chunks = b''
    while True:
        chunk = connection.recv(65536)
        if not chunk:
            raise RuntimeError('Blender disconnected without a response')
        chunks += chunk
        try:
            response = json.loads(chunks)
            break
        except json.JSONDecodeError:
            continue
assert response.get('status') == 'success', response
assert str(root) in json.dumps(response), 'Blender is not connected to this project'
print('PASS: Blender socket responds and references this project root')
