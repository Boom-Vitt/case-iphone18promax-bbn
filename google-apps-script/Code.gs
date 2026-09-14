/** Private Google Sheets/Drive bridge. Configure Script Properties, then deploy as a web app. */
const HEADERS = ['เลขออเดอร์','วันที่จอง','แบบเคส','รุ่น','จำนวน','ราคาต่อชิ้น','ค่าส่ง','ยอดรวม','ชื่อผู้รับ','เบอร์โทร','ที่อยู่','รหัสไปรษณีย์','สถานะ','หมายเหตุ','แก้ไขล่าสุด','ผู้ตรวจ','สลิปใน Drive','เวอร์ชัน'];
function doGet() { return output({ok:true,service:'BBN order sync'}); }
function output(value) { return ContentService.createTextOutput(JSON.stringify(value)).setMimeType(ContentService.MimeType.JSON); }
function safeCell(value) { const s=String(value==null?'':value); return /^[=+@\-\t\r]/.test(s) ? "'"+s : s; }
function doPost(e) {
  let lock;
  try {
    const properties=PropertiesService.getScriptProperties();
    const secret=properties.getProperty('SYNC_SECRET');
    if(!secret || secret.length<32) return output({ok:false,error:'not_configured'});
    const data=JSON.parse(e.postData.contents);
    if(data.secret!==secret) return output({ok:false,error:'unauthorized'});
    if(data.action==='ping') return output({ok:true});
    const o=data.order;
    if(data.action!=='upsert'||!o||!/^BBN-[A-F0-9]{12}$/.test(o.id)||!['pending','approved','rejected'].includes(o.status)||!Number.isInteger(o.revision)||o.revision<1) return output({ok:false,error:'invalid_order'});
    lock=LockService.getScriptLock(); lock.waitLock(25000);
    const sheet=SpreadsheetApp.openById(properties.getProperty('SHEET_ID')).getSheetByName('Orders');
    if(!sheet) throw new Error('Missing Orders sheet');
    if(sheet.getRange(1,1).getValue()!==HEADERS[0]) throw new Error('Unexpected schema');
    const last=sheet.getLastRow();
    const found=last>1?sheet.getRange(2,1,last-1,1).createTextFinder(o.id).matchEntireCell(true).useRegularExpression(false).findNext():null;
    const row=found?found.getRow():Math.max(2,last+1);
    let driveUrl=found?String(sheet.getRange(row,17).getValue()):'';
    if(found && Number(sheet.getRange(row,18).getValue())>=o.revision) return output({ok:true,driveUrl});
    if(!driveUrl){
      if(!data.slip||!['image/png','image/jpeg','application/pdf'].includes(data.slip.type)||data.slip.base64.length>12*1024*1024)throw new Error('Missing valid slip');
      const folder=DriveApp.getFolderById(properties.getProperty('SLIPS_FOLDER_ID'));
      const ext={'image/png':'png','image/jpeg':'jpg','application/pdf':'pdf'}[data.slip.type];
      const filename=o.id+'.'+ext, existing=folder.getFilesByName(filename);
      const file=existing.hasNext()?existing.next():folder.createFile(Utilities.newBlob(Utilities.base64Decode(data.slip.base64),data.slip.type,filename));
      // Inherit only the private folder's access. Never enable link sharing.
      driveUrl=file.getUrl();
    }
    const status={pending:'รอตรวจสอบ',approved:'อนุมัติแล้ว',rejected:'ไม่อนุมัติ'}[o.status];
    const values=[o.id,o.created,o.product,o.model,o.quantity,o.unit_price,o.shipping,o.total,o.name,o.phone,o.address,o.postal,status,o.note,o.updated,o.reviewed_by,driveUrl,o.revision];
    sheet.getRange(row,10).setNumberFormat('@'); sheet.getRange(row,12).setNumberFormat('@');
    sheet.getRange(row,1,1,18).setValues([values.map(v=>typeof v==='number'?v:safeCell(v))]);
    SpreadsheetApp.flush();
    return output({ok:true,driveUrl});
  } catch(error) { return output({ok:false,error:'sync_failed'}); }
  finally { if(lock && lock.hasLock())lock.releaseLock(); }
}
