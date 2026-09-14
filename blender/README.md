# Blender MCP สำหรับโปรเจกต์นี้

ติดตั้ง Blender, Python 3.11+, git และ uv ก่อน แล้วรันจากโฟลเดอร์โปรเจกต์:

```sh
python3 scripts/setup_blender.py
npm run blender:start
# อีก terminal
npm run blender:check
.local-tools/blender-venv/bin/python scripts/check_blender_mcp.py
```

สคริปต์ติดตั้ง [blender-mcp](https://github.com/ahujasid/blender-mcp) จาก commit `5f8ddaf6e987c4aa0c3467fcc548838b28f64477` ไว้ใน `.local-tools/` และเขียน `.codex/config.toml` ให้ตรงกับเครื่องนี้ ไม่แก้ global config หรือหน้าต่าง Blender ที่เปิดอยู่

เปิด Codex task ใหม่ในโปรเจกต์หลังติดตั้งเพื่อโหลด MCP config ใหม่ ตัวตรวจ protocol ทดสอบ initialize, tools/list และ get_scene_info ได้แยกจากการค้นพบเครื่องมือของ Codex

- `case-workspace.blend`: ไฟล์ฉากเริ่มต้นสำหรับทำงาน **ยังไม่ใช่โมเดลเคสสำหรับผลิต**
- `bootstrap.py`: ลงทะเบียน addon เฉพาะ process และตั้ง path ของโปรเจกต์
- `headless.py`: เปิดฉากใน background และประมวลผลคำสั่งบน main thread
- `headless-support.patch`: ผ่อน guard ของ upstream เฉพาะเมื่อใช้ main-thread driver นี้ เนื่องจาก Blender background ไม่มี UI event loop
- bridge ฟังเฉพาะ `127.0.0.1:9876`; ไม่เปิดพอร์ตนี้สู่อินเทอร์เน็ต
- ปิด telemetry ทั้ง MCP server และ addon และเปิด upstream safe mode
- ตั้ง `BLENDER_BIN` หาก Blender อยู่ใน path อื่น ใช้ Ctrl+C หยุด bridge

เก็บโมเดลและ renders ใหม่ใต้ `blender/`; บันทึกฉากใน Blender ก่อนปิด การปิด process ไม่ได้บันทึกงานให้อัตโนมัติ ภาพอ้างอิงอยู่ `output/leather-cases/references/`; ต้องตรวจขนาด/ช่องกล้องจากตัวเครื่องจริงก่อนใช้ผลิต

ตรวจจริงเมื่อ 2026-09-14: Blender 5.2.1 LTS, socket ตอบ path โปรเจกต์ถูกต้อง, MCP แสดง 28 tools และเรียกอ่าน scene สำเร็จ ข้อความเตือนว่าไม่มี addon ใน global addons directory เป็นผลจากการโหลดเฉพาะ process ตามที่ตั้งใจ

## โมเดลโฆษณา

ชุดโมเดลจริงที่สร้างผ่าน Blender MCP อยู่ใน [advertisement/README.md](advertisement/README.md) พร้อม .blend, GLB และภาพตัวอย่าง; การเรนเดอร์ MP4 หยุดตามคำขอให้อัปโหลดเฉพาะงานที่มี
