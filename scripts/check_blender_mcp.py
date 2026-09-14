"""Run using .local-tools/blender-venv/bin/python; requires the local bridge."""
import asyncio
import os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    root = Path(__file__).resolve().parents[1]
    params = StdioServerParameters(command=str(root / '.local-tools/blender-venv/bin/blender-mcp'), env={
        **os.environ, 'BLENDER_HOST': '127.0.0.1', 'BLENDER_PORT': '9876',
        'BLENDER_MCP_DISABLE_TELEMETRY': '1', 'BLENDER_MCP_SAFE_MODE': '1'})
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as client:
            await client.initialize()
            tools = await client.list_tools()
            assert any(tool.name == 'get_scene_info' for tool in tools.tools)
            result = await client.call_tool('get_scene_info', {'user_prompt': 'Read the current project scene to verify Blender MCP.'})
            assert not result.isError, result
            assert 'objects' in str(result), 'Missing scene objects'
            print(f'PASS: MCP initialize, list {len(tools.tools)} tools, and get_scene_info')

asyncio.run(main())
