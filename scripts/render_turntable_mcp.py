"""Render the ad via official Blender MCP in short, resumable batches."""
import asyncio
import os
from datetime import timedelta
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from blender_mcp_call import ROOT, USER_PROMPT

async def main():
    frames=ROOT/'blender/advertisement/frames'
    frames.mkdir(exist_ok=True)
    params=StdioServerParameters(command=str(ROOT/'.local-tools/blender-venv/bin/blender-mcp'),env={**os.environ,'BLENDER_HOST':'127.0.0.1','BLENDER_PORT':'9876','BLENDER_MCP_DISABLE_TELEMETRY':'1','BLENDER_MCP_SAFE_MODE':'1'})
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write,read_timeout_seconds=timedelta(seconds=210)) as client:
            await client.initialize()
            for start in range(1,193,8):
                pending=[f for f in range(start,min(start+8,193)) if not (frames/f'{f:04d}.png').exists()]
                if not pending:continue
                code=f'''import bpy
scene=bpy.context.scene
assert scene.name == 'BBN_Cognac_Advertisement'
scene.render.resolution_percentage=100
scene.cycles.samples=32
for frame in {pending!r}:
    scene.frame_set(frame)
    scene.render.filepath={str(frames)!r}+'/'+str(frame).zfill(4)+'.png'
    bpy.ops.render.render(write_still=True)
print('Rendered frames', {pending!r})
'''
                result=await client.call_tool('execute_blender_code',{'code':code,'user_prompt':USER_PROMPT})
                text='\n'.join(item.text for item in result.content if item.type=='text')
                if result.isError or 'Error executing' in text or 'Rejected' in text:raise RuntimeError(text)
                assert all((frames/f'{f:04d}.png').exists() for f in pending),text
                print(f'Rendered {pending[0]}–{pending[-1]} / 192',flush=True)
            result=await client.call_tool('execute_blender_code',{'code':"import bpy\nbpy.context.scene.frame_set(1)\nbpy.context.scene.render.filepath="+repr(str(ROOT/'blender/advertisement/hero.png'))+"\nbpy.ops.render.render(write_still=True)\nbpy.ops.wm.save_as_mainfile(filepath="+repr(str(ROOT/'blender/advertisement/cognac-turntable.blend'))+")",'user_prompt':USER_PROMPT})
            assert not result.isError

asyncio.run(main())
