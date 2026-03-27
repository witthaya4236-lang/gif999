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
    1: { # ID 1 = ทิพรสน้ำปลาขวดเพท 700cc
        "bigc": "https://www.bigc.co.th/product/tiparos-fish-sauce-pet-bottle-700-ml.593?srsltid=AfmBOoomFq0ARaVKBKJ1vxh0T621m24WtstVHGhbwUjVEIAmtJkBVnmR",
        "lotus": "https://www.lotuss.com/th/product/tiparos-fish-sauce-700ml-49301?srsltid=AfmBOoqNQGS6hjkIHFqybGePbs2rWVQmQpdbpB-T8aEauBqZDwaN8Ja2", # <-- เอาลิงก์หน้าเว็บโลตัสมาวาง
        "seven": "https://www.allonline.7eleven.co.th/p/%E0%B8%97%E0%B8%B4%E0%B8%9E%E0%B8%A3%E0%B8%AA-%E0%B8%99%E0%B9%89%E0%B8%B3%E0%B8%9B%E0%B8%A5%E0%B8%B2%E0%B9%81%E0%B8%97%E0%B9%89-700-%E0%B8%A1%E0%B8%A5/481898/?srsltid=AfmBOooHbbp5R8inDVnit2F8E60EPTwyUboUouY3_UuuqNzkfvNgTk14, # <-- เอาลิงก์หน้าเว็บเซเว่นมาวาง
        "cj": "https://www.cjexpress.co.th/product/..." # <-- เอาลิงก์หน้าเว็บ CJ มาวาง
    },
    2: { # ID 2 = เมกาเชฟน้ำปลา 500cc
        "bigc": "https://www.bigc.co.th/product/megachef-premium-fish-sauce-500-ml.1689?srsltid=AfmBOor1apNgYecIy-Jsy2bJfRNwEPtr-Fi7qM5PoAuPaWtGUIARur5I",
        "lotus": "https://www.lotuss.com/th/product/megachef-premium-fish-sauce-500ml-18011268?srsltid=AfmBOoqdWwBX1_zW7G_NvBvdQgfdWex3WS_eByeK16zGkKwjxlMhs9yg",
        "seven": "https://www.allonline.7eleven.co.th/p/%E0%B9%80%E0%B8%A1%E0%B8%81%E0%B8%B2%E0%B9%80%E0%B8%8A%E0%B8%9F-%E0%B8%99%E0%B9%89%E0%B8%B3%E0%B8%9B%E0%B8%A5%E0%B8%B2%E0%B9%81%E0%B8%97%E0%B9%89-500-%E0%B8%A1%E0%B8%A5-%E0%B9%81%E0%B8%9E%E0%B9%87%E0%B8%81-3-%E0%B8%8A%E0%B8%B4%E0%B9%89%E0%B8%99/580636/?p=0&q=%E0%B9%80%E0%B8%A1%E0%B8%81%E0%B8%B2%E0%B9%80%E0%B8%8A%E0%B8%9F%20%E0%B8%99%E0%B9%89%E0%B8%B3%E0%B8%9B%E0%B8%A5%E0%B8%B2%E0%B9%81%E0%B8%97%E0%B9%89%20500%20%E0%B8%A1%E0%B8%A5.&view=0&requestId=R7MDU6JfRkmdSfCuueV1rg&categoryId=178730951#itemId=567073_0", # <-- ถ้าร้านไหนไม่มีขาย หรือหาลิงก์ไม่เจอ ปล่อยเครื่องหมายคำพูดติดกันไว้แบบนี้ได้เลยครับ
        "cj": "https://www.cjexpress.co.th/product/..."
    },
    3: { # ID 3 = ปลาหมึกน้ำปลาแท้ขวดเพทฉลากเหลือง 700ml
        "bigc": "ลิงก์บิ๊กซี...",
        "lotus": "ลิงก์โลตัส...",
        "seven": "ลิงก์เซเว่น...",
        "cj": "ลิงก์ซีเจ..."
    },
    
    # ... สินค้า ID 4 และ 5 ...
    
    10: { # ID 10 = เด็กสมบูรณ์ซอสหอยนางรมสูตรเข้มข้น 800g
        "bigc": "ลิงก์บิ๊กซี...",
        "lotus": "ลิงก์โลตัส...",
        "seven": "ลิงก์เซเว่น...",
        "cj": "ลิงก์ซีเจ..."
    }
}
product_urls = {
    1: { # ทิพรสน้ำปลาขวดเพท 700cc
        "bigc": "https://www.bigc.co.th/product/tiparos-fish-sauce-pet-bottle-700-ml.593",
        "lotus": "",
        "seven": "https://www.allonline.7eleven.co.th/p/%E0%B8%97%E0%B8%B4%E0%B8%9E%E0%B8%A3%E0%B8%AA-%E0%B8%99%E0%B9%89%E0%B8%B3%E0%B8%9B%E0%B8%A5%E0%B8%B2%E0%B9%81%E0%B8%97%E0%B9%89-700-%E0%B8%A1%E0%B8%A5/481898/",
        "seven_pack": 2, # <-- เพิ่มคำสั่งนี้เพื่อบอกว่าขายแพ็ค 2 ชิ้น หุ่นยนต์จะเอาไปหาร 2 ให้อัตโนมัติ
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
            if new_price is not None:
                pack_size = urls.get("bigc_pack", 1) # ถ้าไม่ได้ใส่ _pack ไว้ จะหารด้วย 1 (คือราคาเดิม)
                final_price = round(new_price / pack_size, 2)
                
                if float(item.get('bigc', 0)) != final_price:
                    print(f"  -> 📉 อัปเดต Big C เป็น: {final_price} บาท (ดึงมา {new_price} หาร {pack_size})")
                    item['bigc'] = final_price
                    updates_made = True
                else:
                    print(f"  -> ➖ Big C ราคาคงเดิม: {final_price} บาท")

        # --- ตรวจสอบ Lotus ---
        if urls.get("lotus"):
            new_price = get_lotus_price(urls["lotus"])
            if new_price is not None:
                pack_size = urls.get("lotus_pack", 1)
                final_price = round(new_price / pack_size, 2)
                
                if float(item.get('lotus', 0)) != final_price:
                    print(f"  -> 📉 อัปเดต Lotus เป็น: {final_price} บาท (ดึงมา {new_price} หาร {pack_size})")
                    item['lotus'] = final_price
                    updates_made = True
                else:
                    print(f"  -> ➖ Lotus ราคาคงเดิม: {final_price} บาท")

        # --- ตรวจสอบ 7-Eleven ---
        if urls.get("seven"):
            new_price = get_seven_price(urls["seven"])
            if new_price is not None:
                pack_size = urls.get("seven_pack", 1)
                final_price = round(new_price / pack_size, 2)
                
                if float(item.get('seven', 0)) != final_price:
                    print(f"  -> 📉 อัปเดต 7-Eleven เป็น: {final_price} บาท (ดึงมา {new_price} หาร {pack_size})")
                    item['seven'] = final_price
                    updates_made = True
                else:
                    print(f"  -> ➖ 7-Eleven ราคาคงเดิม: {final_price} บาท")

        # --- ตรวจสอบ CJ ---
        if urls.get("cj"):
            new_price = get_cj_price(urls["cj"])
            if new_price is not None:
                pack_size = urls.get("cj_pack", 1)
                final_price = round(new_price / pack_size, 2)
                
                if float(item.get('cj', 0)) != final_price:
                    print(f"  -> 📉 อัปเดต CJ เป็น: {final_price} บาท (ดึงมา {new_price} หาร {pack_size})")
                    item['cj'] = final_price
                    updates_made = True
                else:
                    print(f"  -> ➖ CJ ราคาคงเดิม: {final_price} บาท")
        
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
