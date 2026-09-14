# Google Sheets / Drive sync

1. สร้างชีตส่วนตัวที่มีแท็บ `Orders` โดย import `output/orders/preorders.xlsx` ให้ header ตรงกับ `HEADERS` ใน `Code.gs`
2. สร้างโฟลเดอร์ส่วนตัวใน Drive สำหรับสลิป
3. สร้าง Apps Script project วาง `Code.gs` และตั้ง timezone `Asia/Bangkok`
4. ใน Project Settings → Script properties ใส่ `SHEET_ID`, `SLIPS_FOLDER_ID` และ `SYNC_SECRET` (random อย่างน้อย 32 ตัวอักษร)
5. Deploy → New deployment → Web app → Execute as Me → Who has access Anyone ให้เจ้าของบัญชีอนุญาต Drive/Sheets โค้ดรับเฉพาะ POST ที่มี secret ถูกต้อง; GET ไม่คืนข้อมูลออเดอร์
6. ใส่ URL `/exec` ใน `GOOGLE_SCRIPT_URL`, secret เดียวกันใน `GOOGLE_SYNC_SECRET`, ลิงก์ชีตใน `GOOGLE_SHEET_URL` ของ `.env` และ restart server
7. กดส่งข้อมูลในหลังบ้าน ดูจำนวนที่รอส่งให้เป็นศูนย์ และตรวจออเดอร์ที่ชีตจริง การใส่ค่า config ยังไม่ใช่หลักฐานว่าส่งสำเร็จ

โค้ดส่งข้อมูลจากร้านไปชีตทางเดียว ใช้เลขออเดอร์เป็น key และ revision กันซ้ำ/การอัปเดตย้อนกลับ สลิปไม่ถูกแชร์สาธารณะและลิงก์ต้องมีสิทธิ์ Drive เหมือนเดิม รายการใช้ยอดราคาขณะสั่งซื้อ สตริงที่เริ่มด้วยเครื่องหมายสูตรถูก escape ก่อนลงชีต

เก็บ secret เฉพาะ `.env` กับ Script properties ไม่ใส่ใน source code, frontend, URL หรือ GitHub หลังแก้ Apps Script ให้ deploy version ใหม่ โค้ดนี้ใช้สิทธิ์ Drive/Sheets ของเจ้าของบัญชี; จำกัดผู้แก้ไขโปรเจกต์ให้ผู้ดูแลที่เชื่อถือได้

## เมื่อออเดอร์ไม่เข้าชีต

- ค่าใน `.env` บนเครื่องไม่ถูกส่งขึ้น GitHub ตั้ง `GOOGLE_SCRIPT_URL`, `GOOGLE_SYNC_SECRET`, `GOOGLE_SHEET_URL` ใน Environment Variables ของโฮสต์จริงด้วย แล้ว restart/redeploy
- บัญชี Execute as ของ Apps Script ต้องแก้ไขชีตและโฟลเดอร์สลิปได้ หากเป็นคนละบัญชีกับเจ้าของไฟล์ ให้เจ้าของอนุญาตเฉพาะสองรายการนี้โดยตรง ไม่เปิด Anyone with the link
- `ping` ตรวจเพียง secret; ผล `ok` ไม่ได้ยืนยันสิทธิ์อ่าน/เขียนชีตและ Drive ต้องตรวจเลขออเดอร์จริงหลัง sync
- หลังบ้านแสดงข้อผิดพลาดการส่งล่าสุด ปุ่มส่งคืน HTTP 503 เมื่อไม่ตั้งการเชื่อมต่อ และ 502 เมื่อส่งไม่สำเร็จ ออเดอร์กับ revision ยังคงอยู่สำหรับส่งซ้ำ
