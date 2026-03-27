import json
import requests
from bs4 import BeautifulSoup
import datetime
import sys
import time

print(f"🚀 เริ่มต้นการทำงานของหุ่นยนต์ดึงราคา วันที่: {datetime.datetime.now()}")

# 1. โหลดข้อมูลเดิมจากไฟล์ prices.json
try:
    with open('prices.json', 'r', encoding='utf-8') as f:
        appData = json.load(f)
    print("✅ โหลดไฟล์ prices.json สำเร็จ")
except FileNotFoundError:
    print("❌ ไม่พบไฟล์ prices.json โปรดตรวจสอบว่ามีไฟล์นี้อยู่ในระบบ")
    sys.exit(1)

# ==========================================
# 2. ฟังก์ชันดึงราคาของแต่ละห้าง (Web Scrapers)
# ==========================================

# --- ฟังก์ชัน Big C ---
def get_bigc_price(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        ld_json_tags = soup.find_all('script', type='application/ld+json')
        for tag in ld_json_tags:
            if tag.string:
                try:
                    data = json.loads(tag.string)
                    if isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'Product' and 'offers' in item:
                                return float(item['offers']['price'])
                    elif data.get('@type') == 'Product' and 'offers' in data:
                        return float(data['offers']['price'])
                except:
                    pass
        
        script_tag = soup.find('script', id='__NEXT_DATA__')
        if script_tag:
            data = json.loads(script_tag.string)
            product_data = data.get('props', {}).get('pageProps', {}).get('initialState', {}).get('product', {})
            promo_price = product_data.get('special_price') or product_data.get('specialPrice')
            normal_price = product_data.get('price')
            
            if promo_price and float(promo_price) > 0: return float(promo_price)
            elif normal_price: return float(normal_price)
    except Exception as e:
        print(f"  ❌ Big C Error: {e}")
    return None

# --- ฟังก์ชัน Lotus ---
def get_lotus_price(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        # หมายเหตุ: อาจต้องปรับแก้ class ตามโครงสร้างจริงของ Lotus
        price_tag = soup.find('span', class_='price-value') 
        if price_tag:
            return float(price_tag.text.replace('฿', '').replace(',', '').strip())
    except Exception as e:
        print(f"  ❌ Lotus Error: {e}")
    return None

# --- ฟังก์ชัน 7-Eleven ---
def get_seven_price(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        # หมายเหตุ: อาจต้องปรับแก้ class ตามโครงสร้างจริงของ 7-11
        price_tag = soup.find('div', class_='price') 
        if price_tag:
            return float(price_tag.text.replace('฿', '').replace(',', '').strip())
    except Exception as e:
        print(f"  ❌ 7-Eleven Error: {e}")
    return None

# --- ฟังก์ชัน CJ ---
def get_cj_price(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        # หมายเหตุ: อาจต้องปรับแก้ class ตามโครงสร้างจริงของ CJ
        price_tag = soup.find('span', class_='sale-price') 
        if price_tag:
            return float(price_tag.text.replace('฿', '').replace(',', '').strip())
    except Exception as e:
        print(f"  ❌ CJ Error: {e}")
    return None

# ==========================================
# 3. พื้นที่ใส่ลิงก์สินค้า (นำลิงก์มาใส่ใน "")
# ==========================================
product_urls = {
    1: { # ทิพรสน้ำปลาขวดเพท 700cc
        "bigc": "https://www.bigc.co.th/product/tiparos-fish-sauce-pet-bottle-700-ml.593",
        "lotus": "",
        "seven": "",
        "cj": ""
    },
    2: { # เมกาเชฟน้ำปลา 500cc
        "bigc": "",
        "lotus": "",
        "seven": "",
        "cj": ""
    },
    3: { # ปลาหมึกน้ำปลาแท้ขวดเพทฉลากเหลือง 700ml
        "bigc": "",
        "lotus": "",
        "seven": "",
        "cj": ""
    },
    4: { # ปลาหมึกน้ำปลาแท้ขวดเพทฉลากเขียว 700ml
        "bigc": "",
        "lotus": "",
        "seven": "",
        "cj": ""
    },
    5: { # แม่ครัวฉลากทองซอสหอย 300cc
        "bigc": "",
        "lotus": "",
        "seven": "",
        "cj": ""
    },
    6: { # แม่ครัวฉลากทองซอสหอย 600cc
        "bigc": "",
        "lotus": "",
        "seven": "",
        "cj": ""
    },
    7: { # ภูเขาทองซอสปรุงรสฝาเขียวเพท 1L
        "bigc": "",
        "lotus": "",
        "seven": "",
        "cj": ""
    },
    8: { # แม็กกี้ซอสปรุงรส 680cc
        "bigc": "",
        "lotus": "",
        "seven": "",
        "cj": ""
    },
    9: { # แม็กกี้ซอสปรุงอาหารสูตรเข้มเข้าเนื้อ 680cc
        "bigc": "",
        "lotus": "",
        "seven": "",
        "cj": ""
    },
    10: { # เด็กสมบูรณ์ซอสหอยนางรมสูตรเข้มข้น 800g
        "bigc": "",
        "lotus": "",
        "seven": "",
        "cj": ""
    },
    11: { # เด็กสมบูรณ์ซีอิ๊วขาวสูตร1 700cc
        "bigc": "",
        "lotus": "",
        "seven": "",
        "cj": ""
    },
    12: { # เด็กสมบูรณ์ซีอิ๊วขาวสูตร1 1000cc
        "bigc": "",
        "lotus": "",
        "seven": "",
        "cj": ""
    }
}

# ==========================================
# 4. เริ่มขั้นตอนวิ่งตรวจเช็คและอัปเดตราคา
# ==========================================
updates_made = False

for item in appData:
    item_id = item.get('id')
    
    if item_id in product_urls:
        urls = product_urls[item_id]
        print(f"\n📦 กำลังเช็คราคา: {item['name']}")
        
        # --- ตรวจสอบ Big C ---
        if urls.get("bigc"):
            new_price = get_bigc_price(urls["bigc"])
            if new_price is not None and float(item.get('bigc', 0)) != new_price:
                print(f"  -> 📉 อัปเดต Big C เป็น: {new_price} บาท (เดิม {item.get('bigc')})")
                item['bigc'] = new_price
                updates_made = True
            elif new_price is not None:
                print(f"  -> ➖ Big C ราคาคงเดิม: {new_price} บาท")

        # --- ตรวจสอบ Lotus ---
        if urls.get("lotus"):
            new_price = get_lotus_price(urls["lotus"])
            if new_price is not None and float(item.get('lotus', 0)) != new_price:
                print(f"  -> 📉 อัปเดต Lotus เป็น: {new_price} บาท (เดิม {item.get('lotus')})")
                item['lotus'] = new_price
                updates_made = True
            elif new_price is not None:
                print(f"  -> ➖ Lotus ราคาคงเดิม: {new_price} บาท")

        # --- ตรวจสอบ 7-Eleven ---
        if urls.get("seven"):
            new_price = get_seven_price(urls["seven"])
            if new_price is not None and float(item.get('seven', 0)) != new_price:
                print(f"  -> 📉 อัปเดต 7-Eleven เป็น: {new_price} บาท (เดิม {item.get('seven')})")
                item['seven'] = new_price
                updates_made = True
            elif new_price is not None:
                print(f"  -> ➖ 7-Eleven ราคาคงเดิม: {new_price} บาท")

        # --- ตรวจสอบ CJ ---
        if urls.get("cj"):
            new_price = get_cj_price(urls["cj"])
            if new_price is not None and float(item.get('cj', 0)) != new_price:
                print(f"  -> 📉 อัปเดต CJ เป็น: {new_price} บาท (เดิม {item.get('cj')})")
                item['cj'] = new_price
                updates_made = True
            elif new_price is not None:
                print(f"  -> ➖ CJ ราคาคงเดิม: {new_price} บาท")
        
        # หน่วงเวลา 2 วินาที ป้องกันโดนบล็อก
        time.sleep(2)

# ==========================================
# 5. บันทึกข้อมูลกลับลงไฟล์ prices.json
# ==========================================
if updates_made:
    with open('prices.json', 'w', encoding='utf-8') as f:
        json.dump(appData, f, ensure_ascii=False, indent=4)
    print("\n💾 บันทึกการเปลี่ยนแปลงราคาลง prices.json สำเร็จ!")
else:
    print("\n✅ ตรวจสอบเสร็จสิ้น ไม่มีราคาเปลี่ยนแปลง ไม่ต้องเซฟไฟล์ใหม่")

print("🎉 หุ่นยนต์ทำงานเสร็จสิ้นสมบูรณ์!")
