import json
import requests
from bs4 import BeautifulSoup
import datetime
import sys

print(f"🚀 เริ่มต้นการทำงานของหุ่นยนต์ดึงราคา วันที่: {datetime.datetime.now()}")

# 1. โหลดข้อมูลเดิมจากไฟล์ prices.json
try:
    with open('prices.json', 'r', encoding='utf-8') as f:
        appData = json.load(f)
    print("✅ โหลดไฟล์ prices.json สำเร็จ")
except FileNotFoundError:
    print("❌ ไม่พบไฟล์ prices.json โปรดตรวจสอบว่ามีไฟล์นี้อยู่ในระบบ")
    sys.exit(1)

# 2. ฟังก์ชันสำหรับดึงราคาจากหน้าเว็บ Big C
def get_bigc_price(url):
    # ปลอมตัวเป็นเว็บบราวเซอร์ปกติ เพื่อไม่ให้เว็บ Big C บล็อกการดึงข้อมูล
    # แนะนำให้ใช้ User-Agent ของบราวเซอร์จริง (เช่น Chrome หรือ Firefox) 
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() # ตรวจสอบว่าเว็บโหลดสำเร็จหรือไม่
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ค้นหาข้อมูลราคา (Big C มักซ่อนข้อมูลสินค้าไว้ใน Script ID '__NEXT_DATA__')
        script_tag = soup.find('script', id='__NEXT_DATA__')
        if script_tag:
            data = json.loads(script_tag.string)
            # แกะเอาตัวเลขราคาล่าสุดออกมาจากโครงสร้าง JSON ของเว็บ
            price = data['props']['pageProps']['initialState']['product']['price']
            return float(price)
        else:
            print("  ⚠️ ไม่พบแท็กข้อมูลราคาบนหน้าเว็บ")
    except Exception as e:
        print(f"  ❌ เกิดข้อผิดพลาดในการดึงข้อมูล Big C: {e}")
    return None

# ----- เพิ่มฟังก์ชันสำหรับ Lotus -----
def get_lotus_price(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        # หมายเหตุ: ต้องเปลี่ยน class นี้ให้ตรงกับโค้ดหน้าเว็บโลตัสจริง
        price_tag = soup.find('span', class_='price-value') 
        if price_tag:
            return float(price_tag.text.replace('฿', '').replace(',', '').strip())
    except Exception as e:
        print(f"  ❌ เกิดข้อผิดพลาดในการดึงข้อมูล Lotus: {e}")
    return None

# ----- เพิ่มฟังก์ชันสำหรับ 7-Eleven (AllOnline) -----
def get_seven_price(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        # หมายเหตุ: ต้องเปลี่ยน class นี้ให้ตรงกับโค้ดหน้าเว็บ 7-11 จริง
        price_tag = soup.find('div', class_='price') 
        if price_tag:
            return float(price_tag.text.replace('฿', '').replace(',', '').strip())
    except Exception as e:
        print(f"  ❌ เกิดข้อผิดพลาดในการดึงข้อมูล 7-Eleven: {e}")
    return None

# ----- เพิ่มฟังก์ชันสำหรับ CJ -----
def get_cj_price(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        # หมายเหตุ: ต้องเปลี่ยน class นี้ให้ตรงกับโค้ดหน้าเว็บ CJ จริง
        price_tag = soup.find('span', class_='sale-price') 
        if price_tag:
            return float(price_tag.text.replace('฿', '').replace(',', '').strip())
    except Exception as e:
        print(f"  ❌ เกิดข้อผิดพลาดในการดึงข้อมูล CJ: {e}")
    return None

# 3. กำหนดลิงก์สินค้า (คุณต้องเอาลิงก์จริงของทุกเจ้ามาใส่ให้ครบ)
product_urls = {
    1: { # ID 1 = ทิพรสน้ำปลาขวดเพท 700cc
        "bigc": "https://www.bigc.co.th/product/tiparos-fish-sauce-pet-bottle-700-ml.593",
        # เอาเครื่องหมาย # ออก แล้วใส่ลิงก์จริงด้านล่างนี้
        # "lotus": "https://www.lotuss.com/...",
        # "seven": "https://www.allonline.7eleven.co.th/...",
        # "cj": "https://www.cjexpress.co.th/..."
    }
}

# 4. เริ่มขั้นตอนวิ่งตรวจเช็คและอัปเดตราคา
updates_made = False

for item in appData:
    item_id = item.get('id')
    
    # ตรวจสอบว่าสินค้านี้มีลิงก์ให้หุ่นยนต์ไปดูหรือไม่
    if item_id in product_urls:
        urls = product_urls[item_id]
        print(f"กำลังเช็คราคา: {item['name']}")
        
        # --- ตรวจสอบ Big C ---
        if "bigc" in urls:
            new_price = get_bigc_price(urls["bigc"])
            if new_price is not None:
                if float(item.get('bigc', 0)) != new_price:
                    print(f"  -> 📉 อัปเดตราคา Big C เป็น: {new_price} บาท (เดิม {item.get('bigc')})")
                    item['bigc'] = new_price
                    updates_made = True
                else:
                    print(f"  -> ➖ ราคา Big C คงเดิม: {new_price} บาท")

        # --- ตรวจสอบ Lotus ---
        if "lotus" in urls:
            new_price = get_lotus_price(urls["lotus"])
            if new_price is not None:
                if float(item.get('lotus', 0)) != new_price:
                    print(f"  -> 📉 อัปเดตราคา Lotus เป็น: {new_price} บาท (เดิม {item.get('lotus')})")
                    item['lotus'] = new_price
                    updates_made = True
                else:
                    print(f"  -> ➖ ราคา Lotus คงเดิม: {new_price} บาท")

        # --- ตรวจสอบ 7-Eleven ---
        if "seven" in urls:
            new_price = get_seven_price(urls["seven"])
            if new_price is not None:
                if float(item.get('seven', 0)) != new_price:
                    print(f"  -> 📉 อัปเดตราคา 7-Eleven เป็น: {new_price} บาท (เดิม {item.get('seven')})")
                    item['seven'] = new_price
                    updates_made = True
                else:
                    print(f"  -> ➖ ราคา 7-Eleven คงเดิม: {new_price} บาท")

        # --- ตรวจสอบ CJ ---
        if "cj" in urls:
            new_price = get_cj_price(urls["cj"])
            if new_price is not None:
                if float(item.get('cj', 0)) != new_price:
                    print(f"  -> 📉 อัปเดตราคา CJ เป็น: {new_price} บาท (เดิม {item.get('cj')})")
                    item['cj'] = new_price
                    updates_made = True
                else:
                    print(f"  -> ➖ ราคา CJ คงเดิม: {new_price} บาท")

# 5. บันทึกข้อมูลที่อัปเดตแล้ว กลับลงไปทับไฟล์ prices.json ของเดิม
if updates_made:
    with open('prices.json', 'w', encoding='utf-8') as f:
        json.dump(appData, f, ensure_ascii=False, indent=4)
    print("💾 อัปเดตและบันทึกไฟล์ prices.json เสร็จสมบูรณ์แล้ว!")
else:
    print("✅ ตรวจสอบเสร็จสิ้น ไม่มีราคาเปลี่ยนแปลง ไม่ต้องเซฟไฟล์ใหม่")

print("🎉 หุ่นยนต์ทำงานเสร็จสิ้น!")
