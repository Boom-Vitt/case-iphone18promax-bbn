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
