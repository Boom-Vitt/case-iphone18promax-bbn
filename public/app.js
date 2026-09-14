let catalog, filter = 'all', selected, receipt;
const $ = s => document.querySelector(s);
const money = n => new Intl.NumberFormat('th-TH', { maximumFractionDigits: 0 }).format(n) + ' บาท';
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const statuses = {pending:'รอตรวจสอบยอดโอน', approved:'อนุมัติยอดโอนแล้ว', rejected:'ไม่อนุมัติ — กรุณาติดต่อร้าน'};
async function api(path, options = {}) {
  const res = await fetch(path, {...options, headers:{'X-Requested-With':'BBN', ...options.headers}});
  const data = await res.json(); if (!res.ok) throw new Error(data.error); return data;
}
function toast(message) { $('#toast').textContent = message; $('#toast').hidden = false; setTimeout(() => $('#toast').hidden = true, 3000); }
function render() {
  const s = catalog.settings;
  $('#hero-price').textContent = s.price.toLocaleString('th-TH');
  $('#shipping-label').textContent = s.shipping ? 'ค่าส่ง ' + money(s.shipping) : 'ส่งฟรี';
  $('#store-notice').textContent = s.open ? 'เปิดรับพรีออร์เดอร์ • ' + s.shippingNote : 'กำลังเตรียมเปิดรอบพรีออร์เดอร์ — เลือกชมดีไซน์ได้ก่อน';
  $('#delivery-text').textContent = s.shippingNote || 'จะแจ้งกำหนดจัดส่งก่อนเปิดรับชำระเงิน';
  $('#contact-text').textContent = s.contact ? 'ติดต่อร้าน: ' + s.contact : '';
  $('#products').innerHTML = catalog.products.filter(p => filter === 'all' || p.collection === filter).map((p, i) => `<article class="product-card"><div class="photo-wrap"><div class="product-photo ${p.collection} ${p.position}" role="img" aria-label="${esc(p.description)}"></div><span class="product-number">${String(catalog.products.indexOf(p)+1).padStart(2,'0')}</span></div><div class="product-meta"><div><p>${esc(p.collection.toUpperCase())}</p><h3>${esc(p.name)}</h3><span>${esc(p.description)}</span></div><button class="pick" data-product="${esc(p.id)}" aria-label="เลือก ${esc(p.name)}">↗</button></div><div class="product-bottom"><b>${money(s.price)}</b><span>${s.shipping ? 'ค่าส่ง '+money(s.shipping) : 'ส่งฟรี'}</span></div></article>`).join('');
}
function total() { const s = catalog.settings; const n = Number($('#order-form [name=quantity]').value); return s.price*n+s.shipping; }
$('#products').addEventListener('click', e => {
  const button = e.target.closest('[data-product]'); if (!button) return;
  if (!catalog.settings.open) return toast('ยังไม่เปิดรับชำระเงิน กำหนดเปิดรอบจะแจ้งในหน้านี้');
  selected = catalog.products.find(p => p.id === button.dataset.product);
  $('#order-form').reset(); $('#order-form [name=product]').value = selected.id;
  $('#selected-title').textContent = selected.name; $('#order-total').textContent = money(total());
  $('#pay-number').textContent = catalog.settings.promptpay; $('#pay-recipient').textContent = catalog.settings.recipient;
  $('#checkout-shipping').textContent = 'กำหนดส่ง: ' + catalog.settings.shippingNote;
  $('#form-error').textContent = ''; $('#checkout-content').hidden = false; $('#order-success').hidden = true; $('#checkout').showModal();
});
$('.filters').addEventListener('click', e => { const b=e.target.closest('[data-filter]'); if (!b) return; filter=b.dataset.filter; document.querySelectorAll('[data-filter]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));}); render(); });
$('#order-form [name=quantity]').addEventListener('change',()=>$('#order-total').textContent=money(total()));
$('#copy-pay').addEventListener('click', async()=>{try{await navigator.clipboard.writeText(catalog.settings.promptpay);toast('คัดลอกพร้อมเพย์แล้ว');}catch{toast('กรุณาคัดลอกหมายเลขที่แสดง');}});
document.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',()=>b.closest('dialog').close()));
$('#order-form').addEventListener('submit',async e=>{
  e.preventDefault(); const button=e.target.querySelector('[type=submit]'); button.disabled=true; button.textContent='กำลังส่งข้อมูล…'; $('#form-error').textContent='';
  try { const form=new FormData(e.target); if(form.get('slip').size>8*1024*1024)throw new Error('ไฟล์ต้องไม่เกิน 8 MB'); form.set('quotedTotal',String(total()));
    receipt=await api('/api/orders',{method:'POST',body:form}); $('#checkout-content').hidden=true; $('#order-success').hidden=false; $('#success-id').textContent=receipt.id; $('#success-token').value=receipt.token;
  } catch(error){$('#form-error').textContent=error.message;} finally{button.disabled=false;button.textContent='ส่งคำสั่งจองและสลิป';}
});
$('#copy-order').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(`${receipt.id}\nรหัสติดตาม: ${receipt.token}\n${location.origin}`);toast('คัดลอกข้อมูลออเดอร์แล้ว');}catch{toast('กรุณาคัดลอกเลขออเดอร์และรหัสที่แสดง');}});
$('#track-open').addEventListener('click',()=>$('#tracking').showModal());
$('#tracking-form').addEventListener('submit',async e=>{e.preventDefault();const b=e.target.querySelector('button');b.disabled=true;try{const r=await api('/api/order-status',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(new FormData(e.target)))});$('#tracking-result').innerHTML=`<div class="payment-box"><span class="status ${r.status}">${esc(statuses[r.status])}</span><h3>${esc(r.id)}</h3><p>${esc(r.model)} · ${esc(r.product)} × ${r.quantity}</p><b>${money(r.total)}</b><p>${esc(r.note)}</p></div>`;}catch(error){$('#tracking-result').textContent=error.message;}finally{b.disabled=false;}});
api('/api/catalog').then(data=>{catalog=data;render();}).catch(()=>{$('#store-notice').textContent='โหลดข้อมูลร้านไม่สำเร็จ กรุณารีเฟรชเพื่อลองอีกครั้ง';});
