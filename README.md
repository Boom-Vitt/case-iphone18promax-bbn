# BBN CASE — iPhone 18 leather preorder

หน้าร้านภาษาไทยสำหรับเคสหนัง 12 ดีไซน์ iPhone 18 Pro / Pro Max ราคาเริ่มต้น 1,090 บาท ส่งฟรี พร้อมรับสลิปและหลังบ้านอนุมัติการโอน โค้ดใช้ Node.js 24 และ SQLite ในตัว ไม่มี runtime npm dependencies

## เริ่มใช้งาน

```sh
cp .env.example .env
# ตั้ง ADMIN_USERNAME, ADMIN_PASSWORD, PUBLIC_ORIGIN และ PORT ใน .env
npm start
```

เปิด URL ตาม `PUBLIC_ORIGIN` และ `/admin` สำหรับหลังบ้าน บัญชีที่ตั้งในเครื่องเจ้าของร้านอยู่ใน `.env` ซึ่งไม่ถูกส่งขึ้น GitHub ก่อนเปิดร้านให้กรอกพร้อมเพย์ ชื่อผู้รับเงิน กำหนดจัดส่ง และช่องทางติดต่อในหลังบ้าน แล้วเปิดสวิตช์รับพรีออร์เดอร์ ร้านเริ่มต้นในโหมดปิดรับเงิน

ลูกค้าเลือกแบบ/รุ่น → โอนตามยอด → แนบ JPG, PNG หรือ PDF ไม่เกิน 8 MB → ได้เลขออเดอร์และรหัสติดตาม ผู้ดูแลตรวจสลิปแล้วอนุมัติหรือไม่อนุมัติพร้อมเหตุผล มีสรุปความต้องการตามแบบและรุ่น

## ข้อมูลและ Google Sheets

- ออเดอร์บันทึกลง `data/store.sqlite` ทันที สลิปอยู่ `data/slips/` และเปิดดูได้เมื่อ admin login
- ต่อ Google ด้วย [ขั้นตอน Apps Script](google-apps-script/README.md) เพื่อส่งข้อมูลไปชีตและสลิปไปโฟลเดอร์ส่วนตัวใน Drive
- หาก Google ใช้งานไม่ได้ ข้อมูลยังอยู่ในร้านและรอส่งซ้ำทุก 30 วินาที ต้องให้ server ทำงานอยู่
- สถานะอนุมัติแก้ผ่านหลังบ้านเท่านั้น ชีตเป็นสำเนาสำหรับดู/วิเคราะห์ การแก้ชีตไม่ย้อนกลับมาร้าน
- ไม่ส่งรหัสติดตามลูกค้าไปชีต เก็บ session และรหัสติดตามเป็น hash ในฐานข้อมูล
- สำรองฐานข้อมูลพร้อมสลิปด้วยกัน ใช้ SQLite backup หรือหยุด server ก่อนคัดลอกทั้ง `data/`

## นำขึ้นใช้งานจริง

GitHub เป็นที่เก็บโค้ด เว็บนี้ต้องมี Node server และดิสก์ถาวร **GitHub Pages รันระบบรับออเดอร์นี้ไม่ได้** ใช้ instance เดียว ตั้ง `HOST=0.0.0.0`, `PUBLIC_ORIGIN=https://โดเมนจริง`, `COOKIE_SECURE=true` และ `DATA_DIR` ชี้ persistent volume ให้ HTTPS reverse proxy ส่งต่อมายังพอร์ต Node

ใช้รหัส admin ที่เดายากก่อนเปิดออนไลน์ อย่าส่ง `.env`, `data/`, สลิป หรือ credentials ขึ้น repository ปุ่มอนุมัติเป็นการยืนยันโดยคน ระบบไม่ได้ตรวจธนาคารอัตโนมัติ ภาพสินค้าเป็น AI concept ไม่ใช่การยืนยันความพอดีของสินค้าจริง

## Blender และภาพ

ดู [Blender MCP](blender/README.md) เพื่อเชื่อมฉากในโฟลเดอร์โปรเจกต์ ภาพต้นฉบับ/รุ่นแก้ไขและ prompt อยู่ `output/leather-cases/`; เว็บใช้ภาพ v2 จาก `public/assets/` ภาพอ้างอิง Apple ใช้ศึกษารูปร่าง ไม่ใช่ภาพสินค้าเคสของร้าน

## ตรวจสอบ

```sh
npm run check
npm run blender:check
.local-tools/blender-venv/bin/python scripts/check_blender_mcp.py
```

ชุดทดสอบใช้ฐานข้อมูลและข้อมูลลูกค้าสมมติใน temporary directory ตรวจ login, CSRF, สลิปส่วนตัว/ซ้ำ, ยอดราคา, สถานะ/การชนกันของ revision, persistence และ Google retry ด้วย endpoint จำลอง ไม่มีการส่งออเดอร์ทดสอบไป Google จริง

ข้อจำกัดรุ่นเริ่มต้น: rate limit อิง IP ของ socket หากวางหลัง reverse proxy ทุกคำขออาจใช้โควตาร่วมกัน ต้องตั้ง client-IP trust เฉพาะ proxy ที่ควบคุมได้และทดสอบก่อนรับทราฟฟิกจริง
