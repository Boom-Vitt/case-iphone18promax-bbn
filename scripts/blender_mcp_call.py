"""Call the installed official Blender MCP over MCP stdio, keeping safe mode on."""
import asyncio
import json
import os
import sys
from datetime import timedelta
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
USER_PROMPT = 'ใช้ตัวของ Blender MCP ในการสร้างตัว 3D โมเดลที่สามารถหมุนโชว์ได้เป็นโฆษณา ย้ำว่าใช้ตัวของ Blender MCP'

async def main():
    script = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
    params = StdioServerParameters(command=str(ROOT / '.local-tools/blender-venv/bin/blender-mcp'), env={
        **os.environ, 'BLENDER_HOST': '127.0.0.1', 'BLENDER_PORT': '9876',
        'BLENDER_MCP_DISABLE_TELEMETRY': '1', 'BLENDER_MCP_SAFE_MODE': '1'})
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=210)) as client:
            await client.initialize()
            if script:
                result = await client.call_tool('execute_blender_code', {'code': script.read_text(), 'user_prompt': USER_PROMPT})
            else:
                result = await client.call_tool('get_scene_info', {'user_prompt': USER_PROMPT})
            content = '\n'.join(item.text for item in result.content if item.type == 'text')
            print(content)
            if result.isError or 'Rejected by safe mode' in content or 'Error executing code' in content:
                raise SystemExit(1)

if __name__ == '__main__':
    asyncio.run(main())
