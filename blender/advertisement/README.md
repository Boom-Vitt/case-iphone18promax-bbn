# Cognac leather case — Blender MCP assets

สร้างชิ้นงานผ่าน **official Blender MCP** `execute_blender_code` โดยใช้ MCP Python client ใน `scripts/blender_mcp_call.py` เปิด safe mode และปิด telemetry ระหว่างสร้าง/เรนเดอร์/ส่งออก

ไฟล์ที่มีในชุดนี้:

- `cognac-turntable.blend`: โมเดลเคสพร้อมตะเข็บ ขอบกล้อง เลนส์ ปุ่ม ช่องชาร์จ แสงสตูดิโอ และ typography ฉากชื่อ `BBN_Cognac_Advertisement` มีการหมุน 360° ที่ 24 fps เฟรม 1–192 (8 วินาที; keyframe ปิดวงรอบที่ 193)
- `../../public/models/cognac-case.glb`: โมเดลสำหรับโปรแกรมดู 3D, 33 nodes, วัสดุ PBR และ normal texture ลายหนัง 1024×1024 ไม่มีแอนิเมชันฝังใน GLB; หมุนดูด้วย viewer ได้
- `hero.png`: ภาพเรนเดอร์ทดลองจาก Blender
- `build_scene.py`, `refine_lighting.py`, `export_model.py`, `render_preview.py`: โค้ดที่ส่งผ่าน Blender MCP

ผู้ใช้เลือกให้อัปโหลดเฉพาะไฟล์ที่มี ณ 2026-09-14 จึงหยุดงานเรนเดอร์คลิปไว้ **ยังไม่มี MP4 สำเร็จและยังไม่ได้เชื่อม viewer เข้าหน้าร้าน** เฟรมทดลองและ log เก็บไว้เฉพาะเครื่อง

เปิดไฟล์ .blend เลือกฉาก `BBN_Cognac_Advertisement` แล้วเล่น timeline เพื่อดูการหมุน สคริปต์ `scripts/render_turntable_mcp.py` ใช้เรนเดอร์ต่อผ่าน MCP ภายหลังได้เมื่อเปิดฉากนี้ใน bridge

ตรวจแล้ว: MCP อ่านฉากเริ่มต้นสำเร็จ, สร้าง/บันทึกฉาก, เรนเดอร์ภาพทดลองและส่งออก GLB สำเร็จ; ตรวจโครงสร้าง GLB ว่ามี 33 nodes และไม่ติด default Cube ตรวจภาพเรนเดอร์ด้วยตาแล้ว โมเดลเป็นคอนเซปต์โฆษณา ใช้ขนาดประมาณ ไม่ใช่ CAD ที่ตรวจความพอดีเพื่อผลิต


## Completed premium film — 2026-09-14

New work following the user’s request to finish the model and video lives in [premium/README.md](premium/README.md): a refined editable scene and a 16-second Full HD film with four camera shots, a 360° rotation, and an original score. The earlier interrupted render described above remains a historical asset phase; the new film uses its own files and validation reports.
