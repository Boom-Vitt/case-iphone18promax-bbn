# BBN CASE — iPhone 18 leather preorder

หน้าร้านภาษาไทยสำหรับเคสหนัง 12 ดีไซน์ iPhone 18 Pro / Pro Max ราคาเริ่มต้น 1,090 บาท ส่งฟรี พร้อมรับสลิปและหลังบ้านอนุมัติการโอน โค้ดใช้ Node.js 24 และ SQLite ในตัว ไม่มี runtime npm dependencies

## เริ่มใช้งาน

```sh
cp .env.example .env
# ตั้ง ADMIN_USERNAME, ADMIN_PASSWORD, PUBLIC_ORIGIN และ PORT ใน .env
npm start
```

เปิด URL ตาม `PUBLIC_ORIGIN` และ `/admin` สำหรับหลังบ้าน บัญชีที่ตั้งในเครื่องเจ้าของร้านอยู่ใน `.env` ซึ่งไม่ถูกส่งขึ้น GitHub ร้านเปิดรับพรีออร์เดอร์ด้วยราคา 1,090 บาท ส่งฟรี พร้อมเพย์ตามที่ตั้งไว้ แก้ชื่อผู้รับเงิน กำหนดจัดส่ง ช่องทางติดต่อ และเปิด/ปิดร้านได้ในหลังบ้าน หากยังไม่มีวันจัดส่ง หน้าร้านจะแสดงว่ายังไม่ระบุวันจัดส่ง

สต็อกเริ่มต้น 20 ชิ้นต่อดีไซน์ รวม Pro / Pro Max ทั้ง 12 ดีไซน์ เลือกจำนวนได้ถึงสต็อกที่เหลือ (สูงสุด 20 ชิ้นต่อออเดอร์) ออเดอร์รอตรวจและอนุมัติแล้วกันสต็อก ส่วนไม่อนุมัติคืนสต็อก ฐานข้อมูลป้องกันการสั่งเกินเมื่อมีคำขอพร้อมกัน การเริ่มระบบซ้ำไม่รีเซ็ตจำนวนหรือสถานะเปิด/ปิดร้าน การอัปเดตครั้งนี้เปิดร้านที่มีอยู่หนึ่งครั้งตามคำขอเจ้าของร้าน

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

### Hostinger Node.js Web App

ตั้ง Framework เป็น Other, Node 24.x, Root `./`, Build command ไม่มี, Output directory `.` และ Entry file `app.cjs` (ห้ามปล่อย entry ว่าง เพราะแอปนี้ต้องรัน backend) ค่า environment: `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `PUBLIC_ORIGIN=https://โดเมนจริง`, `COOKIE_SECURE=true`, `HOST=0.0.0.0` โดยใช้ `PORT` ที่โฮสต์กำหนด

ตั้ง `DATA_DIR` เป็น absolute path ของโฟลเดอร์ส่วนตัวนอก `public_html` และ `hbuilds` เช่น `/home/<hosting-user>/domains/<domain>/bbn-data` เพื่อเก็บออเดอร์และสลิปข้ามการ deploy อย่าใช้ `./data` ใน build folder ของโฮสต์ ตรวจสิทธิ์เขียนและการคงอยู่จริงหลัง deploy ตั้ง Google environment แยกตามขั้นตอน Apps Script; ไม่ใส่ secrets ใน GitHub

[เอกสาร Hostinger](https://www.hostinger.com/support/how-to-deploy-a-nodejs-website-in-hostinger/) ระบุว่าแต่ละ deployment สร้าง build folder ใหม่ และ entry file ใช้เริ่มแอป ตรวจ `/api/catalog` หลัง deploy ต้องตอบ JSON ที่มี 12 products และ stock; ข้อความ build สำเร็จอย่างเดียวไม่ได้ยืนยันว่า server รัน

## Blender และภาพ

ดู [Blender MCP](blender/README.md) เพื่อเชื่อมฉากในโฟลเดอร์โปรเจกต์ ภาพต้นฉบับ/รุ่นแก้ไขและ prompt อยู่ `output/leather-cases/`; เว็บใช้ภาพ v2 จาก `public/assets/` ภาพอ้างอิง Apple ใช้ศึกษารูปร่าง ไม่ใช่ภาพสินค้าเคสของร้าน

## ตรวจสอบ

```sh
npm run check
npm run blender:check
.local-tools/blender-venv/bin/python scripts/check_blender_mcp.py
```

ชุดทดสอบใช้ฐานข้อมูลและข้อมูลลูกค้าสมมติใน temporary directory ตรวจ login, CSRF, สลิปส่วนตัว/ซ้ำ, ยอดราคา, สถานะ/การชนกันของ revision, persistence สต็อกร่วมสองรุ่น/สั่งพร้อมกัน/คืนสต็อก/ไม่เติมซ้ำหลังรีสตาร์ต และ Google retry ด้วย endpoint จำลอง ไม่มีการส่งออเดอร์ทดสอบไป Google จริง

Rate limit ใช้ IP ของ socket ตามค่าเริ่มต้น หากใช้ reverse proxy บนเครื่องเดียวกัน ให้ตั้ง `TRUST_PROXY=loopback` และให้ proxy เขียน `X-Forwarded-For` ด้วย IP ลูกค้าจริง (เช่น Nginx `proxy_set_header X-Forwarded-For $remote_addr;`) จำกัดพอร์ต Node ให้รับเฉพาะ proxy ในโหมดนี้ ไม่เชื่อ header จากการเชื่อมต่อภายนอกโดยตรง สำหรับ proxy คนละเครื่องให้คงค่า trust ว่างและเพิ่มการตรวจขอบเขต proxy ก่อน deploy
