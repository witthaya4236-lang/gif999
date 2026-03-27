import json
import cloudscraper
from bs4 import BeautifulSoup
import datetime
import sys
import time
import random
import re

print(f"🚀 เริ่มต้นการทำงานของหุ่นยนต์ดึงราคา วันที่: {datetime.datetime.now()}")

# 1. โหลดข้อมูลเดิมจากไฟล์ prices.json
try:
    with open('prices.json', 'r', encoding='utf-8') as f:
        appData = json.load(f)
    print("✅ โหลดไฟล์ prices.json สำเร็จ")
except FileNotFoundError:
    print("❌ ไม่พบไฟล์ prices.json โปรดตรวจสอบว่ามีไฟล์นี้อยู่ในระบบ")
    sys.exit(1)

# สร้างหุ่นยนต์แบบเนียนพิเศษ (Bypass Cloudflare & Bot Protection)
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

# ==========================================
# 2. ฟังก์ชันเสริมความฉลาด
# ==========================================
def extract_number(text):
    """ฟังก์ชันดึงเฉพาะตัวเลขออกจากข้อความที่ปนกัน เช่น '฿ 125 ฿ 129' -> 125.0"""
    match = re.search(r'\d+(\.\d+)?', text.replace(',', ''))
    return float(match.group()) if match else None

def detect_pack_size(text):
    """ฟังก์ชันออโต้สแกนหาตัวหาร: ค้นหาคำว่า แพ็ค 2, แพ็ก 3, x4, pack 6 จากชื่อสินค้า"""
    if not text: return 1
    match = re.search(r'(?:แพ็ค|แพ็ก|แพค|pack|x)\s*(?:ละ\s*)?([2-9]|[1-9]\d)(?!\d)', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 1 # ถ้าไม่เจอคำว่าแพ็ค ให้หาร 1 (ราคาปกติ)

# ==========================================
# 3. ฟังก์ชันดึงราคาของแต่ละห้าง
# ==========================================
def get_bigc_price(url):
    try:
        response = scraper.get(url, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # อ่านชื่อสินค้าเพื่อหาว่าเป็นแพ็คหรือไม่
        title_text = soup.title.text if soup.title else ""
        auto_pack = detect_pack_size(title_text)
        
        # 1. หาราคาจาก Schema
        ld_json_tags = soup.find_all('script', type='application/ld+json')
        for tag in ld_json_tags:
            if tag.string:
                try:
                    data = json.loads(tag.string)
                    if isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'Product' and 'offers' in item:
                                return float(item['offers']['price']), auto_pack
                    elif data.get('@type') == 'Product' and 'offers' in data:
                        return float(data['offers']['price']), auto_pack
                except:
                    pass
        
        # 2. หาราคาจากโครงสร้างเว็บ React
        script_tag = soup.find('script', id='__NEXT_DATA__')
        if script_tag:
            data = json.loads(script_tag.string)
            product_data = data.get('props', {}).get('pageProps', {}).get('initialState', {}).get('product', {})
            promo_price = product_data.get('special_price') or product_data.get('specialPrice')
            normal_price = product_data.get('price')
            
            if promo_price and float(promo_price) > 0: return float(promo_price), auto_pack
            elif normal_price: return float(normal_price), auto_pack
    except Exception as e:
        print(f"  ❌ Big C Error: ไม่สามารถเจาะระบบได้หรือลิงก์มีปัญหา")
    return None, 1

def get_lotus_price(url):
    try:
        response = scraper.get(url, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_text = soup.title.text if soup.title else ""
        auto_pack = detect_pack_size(title_text)
        
        price_tag = soup.find('span', class_='price-value') 
        if price_tag:
            return extract_number(price_tag.text), auto_pack
    except Exception as e:
        print(f"  ❌ Lotus Error: ไม่สามารถดึงข้อมูลได้")
    return None, 1

def get_seven_price(url):
    try:
        response = scraper.get(url, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_text = soup.title.text if soup.title else ""
        auto_pack = detect_pack_size(title_text)
        
        # ดึงจาก Schema.org ก่อน
        ld_json_tags = soup.find_all('script', type='application/ld+json')
        for tag in ld_json_tags:
            if tag.string:
                try:
                    data = json.loads(tag.string)
                    if isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'Product' and 'offers' in item:
                                return float(item['offers']['price']), auto_pack
                    elif data.get('@type') == 'Product' and 'offers' in data:
                        return float(data['offers']['price']), auto_pack
                except:
                    pass
                    
        # ถ้าหาจาก Schema ไม่เจอ ให้ไปดูป้ายราคา HTML
        for class_name in ['price', 'current-price', 'price-current']:
            price_tag = soup.find(class_=class_name)
            if price_tag:
                price = extract_number(price_tag.text)
                if price: return price, auto_pack
    except Exception as e:
        print(f"  ❌ 7-Eleven Error: ไม่สามารถดึงข้อมูลได้")
    return None, 1

def get_cj_price(url):
    try:
        response = scraper.get(url, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_text = soup.title.text if soup.title else ""
        auto_pack = detect_pack_size(title_text)
        
        price_tag = soup.find('span', class_='sale-price') 
        if price_tag:
            return extract_number(price_tag.text), auto_pack
    except Exception as e:
        print(f"  ❌ CJ Error: ไม่สามารถดึงข้อมูลได้")
    return None, 1

# ==========================================
# 4. พื้นที่ใส่ลิงก์สินค้า
# ==========================================
product_urls = {
    1: { # ID 1 = ทิพรสน้ำปลาขวดเพท 700cc
        "bigc": "https://www.bigc.co.th/product/tiparos-fish-sauce-pet-bottle-700-ml.593",
        "lotus": "https://www.lotuss.com/th/product/tiparos-fish-sauce-700ml-49301",
        "seven": "https://www.allonline.7eleven.co.th/p/%E0%B8%97%E0%B8%B4%E0%B8%9E%E0%B8%A3%E0%B8%AA-%E0%B8%99%E0%B9%89%E0%B8%B3%E0%B8%9B%E0%B8%A5%E0%B8%B2%E0%B9%81%E0%B8%97%E0%B9%89-700-%E0%B8%A1%E0%B8%A5/481898/",
        "cj": ""
    },
    2: { # ID 2 = เมกาเชฟน้ำปลา 500cc
        "bigc": "https://www.bigc.co.th/product/megachef-premium-fish-sauce-500-ml.1689",
        "lotus": "https://www.lotuss.com/th/product/megachef-premium-fish-sauce-500ml-18011268",
        "seven": "https://www.allonline.7eleven.co.th/p/%E0%B9%80%E0%B8%A1%E0%B8%81%E0%B8%B2%E0%B9%80%E0%B8%8A%E0%B8%9F-%E0%B8%99%E0%B9%89%E0%B8%B3%E0%B8%9B%E0%B8%A5%E0%B8%B2%E0%B9%81%E0%B8%97%E0%B9%89-500-%E0%B8%A1%E0%B8%A5-%E0%B9%81%E0%B8%9E%E0%B9%87%E0%B8%81-3-%E0%B8%8A%E0%B8%B4%E0%B9%89%E0%B8%99/580636/",
        "cj": ""
    },
    3: { "bigc": "", "lotus": "", "seven": "", "cj": "" },
    4: { "bigc": "", "lotus": "", "seven": "", "cj": "" },
    5: { "bigc": "", "lotus": "", "seven": "", "cj": "" },
    10: { "bigc": "", "lotus": "", "seven": "", "cj": "" }
}

# ==========================================
# 5. เริ่มขั้นตอนวิ่งตรวจเช็คและอัปเดตราคา
# ==========================================
updates_made = False

for item in appData:
    item_id = item.get('id')
    
    if item_id in product_urls:
        urls = product_urls[item_id]
        print(f"\n📦 กำลังเช็คราคา: {item['name']}")
        
        # --- Big C ---
        if urls.get("bigc"):
            new_price, auto_pack = get_bigc_price(urls["bigc"])
            if new_price is not None:
                pack_size = urls.get("bigc_pack", auto_pack) # ใช้ manual ก่อน ถ้าไม่มีใช้ออโต้
                final_price = round(new_price / pack_size, 2)
                div_text = f" (ดึงมา {new_price} หารด้วยออโต้แพ็ค {pack_size})" if pack_size > 1 else ""
                
                if float(item.get('bigc', 0)) != final_price:
                    print(f"  -> 📉 อัปเดต Big C เป็น: {final_price} บาท{div_text}")
                    item['bigc'] = final_price
                    updates_made = True
                else:
                    print(f"  -> ➖ Big C ราคาคงเดิม: {final_price} บาท{div_text}")

        # --- Lotus ---
        if urls.get("lotus"):
            new_price, auto_pack = get_lotus_price(urls["lotus"])
            if new_price is not None:
                pack_size = urls.get("lotus_pack", auto_pack)
                final_price = round(new_price / pack_size, 2)
                div_text = f" (ดึงมา {new_price} หารด้วยออโต้แพ็ค {pack_size})" if pack_size > 1 else ""
                
                if float(item.get('lotus', 0)) != final_price:
                    print(f"  -> 📉 อัปเดต Lotus เป็น: {final_price} บาท{div_text}")
                    item['lotus'] = final_price
                    updates_made = True
                else:
                    print(f"  -> ➖ Lotus ราคาคงเดิม: {final_price} บาท{div_text}")

        # --- 7-Eleven ---
        if urls.get("seven"):
            new_price, auto_pack = get_seven_price(urls["seven"])
            if new_price is not None:
                pack_size = urls.get("seven_pack", auto_pack)
                final_price = round(new_price / pack_size, 2)
                div_text = f" (ดึงมา {new_price} หารด้วยออโต้แพ็ค {pack_size})" if pack_size > 1 else ""
                
                if float(item.get('seven', 0)) != final_price:
                    print(f"  -> 📉 อัปเดต 7-Eleven เป็น: {final_price} บาท{div_text}")
                    item['seven'] = final_price
                    updates_made = True
                else:
                    print(f"  -> ➖ 7-Eleven ราคาคงเดิม: {final_price} บาท{div_text}")

        # --- CJ ---
        if urls.get("cj"):
            new_price, auto_pack = get_cj_price(urls["cj"])
            if new_price is not None:
                pack_size = urls.get("cj_pack", auto_pack)
                final_price = round(new_price / pack_size, 2)
                div_text = f" (ดึงมา {new_price} หารด้วยออโต้แพ็ค {pack_size})" if pack_size > 1 else ""
                
                if float(item.get('cj', 0)) != final_price:
                    print(f"  -> 📉 อัปเดต CJ เป็น: {final_price} บาท{div_text}")
                    item['cj'] = final_price
                    updates_made = True
                else:
                    print(f"  -> ➖ CJ ราคาคงเดิม: {final_price} บาท{div_text}")
        
        # หน่วงเวลา 3-5 วินาที เพื่อไม่ให้เว็บปลายทางสงสัย
        time.sleep(random.uniform(3, 5))

# ==========================================
# 6. บันทึกข้อมูลกลับลงไฟล์ prices.json
# ==========================================
if updates_made:
    with open('prices.json', 'w', encoding='utf-8') as f:
        json.dump(appData, f, ensure_ascii=False, indent=4)
    print("\n💾 บันทึกการเปลี่ยนแปลงราคาลง prices.json สำเร็จ!")
else:
    print("\n✅ ตรวจสอบเสร็จสิ้น ไม่มีราคาเปลี่ยนแปลง ไม่ต้องเซฟไฟล์ใหม่")

print("🎉 หุ่นยนต์ทำงานเสร็จสิ้นสมบูรณ์!")
