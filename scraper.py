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
    """ฟังก์ชันออโต้สแกนหาตัวหาร: ค้นหาคำว่า แพ็ค 2, แพ็ก 3, x4, pack 6, 2 ขวด, 3 ขวด, 3 ชิ้น จากชื่อสินค้า"""
    if not text: return 1
    
    if re.search(r'(แพ็คคู่|แพ็กคู่|แพคคู่|ขวดคู่)', text):
        return 2
    
    match1 = re.search(r'(?:แพ็ค|แพ็ก|แพค|pack|x)\s*(?:ละ\s*)?([2-9]|[1-9]\d)(?!\d)', text, re.IGNORECASE)
    if match1:
        return int(match1.group(1))
        
    match2 = re.search(r'([2-9]|[1-9]\d)\s*(?:ขวด|ชิ้น|ถุง|กระป๋อง|กล่อง)', text)
    if match2:
        return int(match2.group(1))
        
    return 1 

# ==========================================
# 3. ฟังก์ชันดึงราคาของแต่ละห้าง
# ==========================================
def get_bigc_price(url):
    try:
        response = scraper.get(url, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_text = soup.title.text if soup.title else ""
        auto_pack = detect_pack_size(title_text)
        
        script_tag = soup.find('script', id='__NEXT_DATA__')
        if script_tag:
            data = json.loads(script_tag.string)
            product_data = data.get('props', {}).get('pageProps', {}).get('initialState', {}).get('product', {})
            promo_price = product_data.get('special_price') or product_data.get('specialPrice')
            normal_price = product_data.get('price')
            
            if promo_price and float(promo_price) > 0: return float(promo_price), auto_pack
            elif normal_price: return float(normal_price), auto_pack

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
    except Exception as e:
        print(f"  ❌ Big C Error: ไม่สามารถเจาะระบบได้หรือลิงก์มีปัญหา")
    return None, 1


def get_lotus_price(url):
    try:
        response = scraper.get(url, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_text = soup.title.text if soup.title else ""
        auto_pack = detect_pack_size(title_text)
        
        # --- ชั้นที่ 1: เจาะข้อมูลจากระบบหลังบ้าน (Next.js Data) - แม่นยำที่สุด ---
        script_tag = soup.find('script', id='__NEXT_DATA__')
        if script_tag:
            data_str = script_tag.string
            # โลตัสใช้คำว่า sellPrice สำหรับราคาโปรโมชั่น
            sell_prices = re.findall(r'"sellPrice"\s*:\s*(\d+(?:\.\d+)?)', data_str)
            if sell_prices:
                valid_prices = [float(p) for p in sell_prices if float(p) > 0]
                if valid_prices: return valid_prices[0], auto_pack

        # --- ชั้นที่ 2: สแกนหาจาก HTML Class เผื่อมีการตั้งชื่อคลาสใหม่ ---
        for class_name in ['price-value', 'current-price', 'price', 'sale-price']:
            tags = soup.find_all(class_=class_name) # ค้นหาแบบไม่จำกัด span
            for tag in tags:
                price = extract_number(tag.text)
                if price and price > 5:
                    return price, auto_pack

        # --- ชั้นที่ 3: สแกนข้อความดิบแบบตรงไปตรงมา (หารูปแบบ ฿21.00/Each) ---
        text = soup.get_text()
        matches = re.findall(r'฿\s*(\d+(?:\.\d+)?)\s*/', text)
        if matches:
            return float(matches[0]), auto_pack

        # ชั้นสำรองสุดท้าย: ดึงจาก Schema.org (ซึ่งมักจะเป็นราคาเต็ม)
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
    except Exception as e:
        print(f"  ❌ Lotus Error: ไม่สามารถดึงข้อมูลได้")
    return None, 1


def get_seven_price(url):
    try:
        response = scraper.get(url, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_text = soup.title.text if soup.title else ""
        auto_pack = detect_pack_size(title_text)
        
        for class_name in ['price', 'current-price', 'price-current']:
            tags = soup.find_all(class_=class_name)
            for tag in tags:
                price = extract_number(tag.text)
                if price and price > 5:
                    return price, auto_pack

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
        "seven_pack": 2, 
        "cj": ""
    },
    2: { # ID 2 = เมกาเชฟน้ำปลา 500cc
        "bigc": "https://www.bigc.co.th/product/megachef-premium-fish-sauce-500-ml.1689",
        "lotus": "https://www.lotuss.com/th/product/megachef-premium-fish-sauce-500ml-18011268",
        "seven": "https://www.allonline.7eleven.co.th/p/%E0%B9%80%E0%B8%A1%E0%B8%81%E0%B8%B2%E0%B9%80%E0%B8%8A%E0%B8%9F-%E0%B8%99%E0%B9%89%E0%B8%B3%E0%B8%9B%E0%B8%A5%E0%B8%B2%E0%B9%81%E0%B8%97%E0%B9%89-500-%E0%B8%A1%E0%B8%A5-%E0%B9%81%E0%B8%9E%E0%B9%87%E0%B8%81-3-%E0%B8%8A%E0%B8%B4%E0%B9%89%E0%B8%99/580636/",
        "seven_pack": 3, # บังคับหาร 3
        "cj": ""
    },
    3: { # ID 3 = ปลาหมึกน้ำปลาแท้ขวดเพทฉลากเหลือง 700ml
        "bigc": "https://www.bigc.co.th/product/squid-fish-sauce-yellow-label-700-cc.9827",
        "lotus": "https://www.lotuss.com/th/product/squid-fish-sauce-700ml-71754261",
        "seven": "https://www.allonline.7eleven.co.th/p/%E0%B8%9B%E0%B8%A5%E0%B8%B2%E0%B8%AB%E0%B8%A1%E0%B8%B6%E0%B8%81-%E0%B8%99%E0%B9%89%E0%B8%B3%E0%B8%9B%E0%B8%A5%E0%B8%B2%E0%B9%81%E0%B8%97%E0%B9%89%E0%B8%89%E0%B8%A5%E0%B8%B2%E0%B8%81%E0%B9%80%E0%B8%AB%E0%B8%A5%E0%B8%B7%E0%B8%AD%E0%B8%87-700-%E0%B8%A1%E0%B8%A5/479516/",
        "seven_pack": 2, 
        "cj": ""
    },
    4: { # ID 4 = ปลาหมึกน้ำปลาแท้ขวดเพทฉลากเขียว 700ml
        "bigc": "https://www.bigc.co.th/product/squid-s-fish-sauce-genuine-fish-sauce-700-ml.234",
        "lotus": "https://www.lotuss.com/th/product/squid-fish-sauce-700ml-7314299",
        "seven": "https://www.allonline.7eleven.co.th/p/%E0%B8%9B%E0%B8%A5%E0%B8%B2%E0%B8%AB%E0%B8%A1%E0%B8%B6%E0%B8%81-%E0%B8%99%E0%B9%89%E0%B8%B3%E0%B8%9B%E0%B8%A5%E0%B8%B2%E0%B9%81%E0%B8%97%E0%B9%89-700-%E0%B8%A1%E0%B8%A5/475234/",
        "seven_pack": 2, 
        "cj": ""
    },
    5: { # ID 5 = แม่ครัวฉลากทองซอสหอย 300cc
        "bigc": "https://www.bigc.co.th/product/maekrua-brand-yster-sauce-300.238",
        "lotus": "https://www.lotuss.com/th/product/maekrua-oyster-sauce-300ml-49611",
        "seven": "https://www.allonline.7eleven.co.th/p/%E0%B9%81%E0%B8%A1%E0%B9%88%E0%B8%84%E0%B8%A3%E0%B8%B1%E0%B8%A7-%E0%B8%8B%E0%B8%AD%E0%B8%AA%E0%B8%AB%E0%B8%AD%E0%B8%A2%E0%B8%99%E0%B8%B2%E0%B8%87%E0%B8%A3%E0%B8%A1-300-%E0%B8%A1%E0%B8%A5-%E0%B9%81%E0%B8%9E%E0%B9%87%E0%B8%81-3-%E0%B8%8A%E0%B8%B4%E0%B9%89%E0%B8%99/470680/",
        "seven_pack": 3, # บังคับหาร 3
        "cj": ""
    },
    6: { # ID 6 = แม่ครัวฉลากทองซอสหอย 600cc
        "bigc": "https://www.bigc.co.th/product/maekrua-oyster-sauce-600-ml.18138",
        "lotus": "https://www.lotuss.com/th/product/maekrua-oyster-sauce-600ml-231924",
        "seven": "https://www.allonline.7eleven.co.th/p/%E0%B9%81%E0%B8%A1%E0%B9%88%E0%B8%84%E0%B8%A3%E0%B8%B1%E0%B8%A7-%E0%B8%8B%E0%B8%AD%E0%B8%AA%E0%B8%AB%E0%B8%AD%E0%B8%A2%E0%B8%99%E0%B8%B2%E0%B8%87%E0%B8%A3%E0%B8%A1-600-%E0%B8%A1%E0%B8%A5/482795/",
        "seven_pack": 2,
        "cj": ""
    },
    7: { # ID 7 = ภูเขาทองซอสปรุงรสฝาเขียวเพท 1L
        "bigc": "https://www.bigc.co.th/product/golden-mountain-seasoning-sauce-green-980-ml.594",
        "lotus": "https://www.lotuss.com/th/product/golden-mountain-green-cap-soy-sauce-1l-49379",
        "seven": "https://www.allonline.7eleven.co.th/p/%E0%B8%A0%E0%B8%B9%E0%B9%80%E0%B8%82%E0%B8%B2%E0%B8%97%E0%B8%AD%E0%B8%87-%E0%B8%8B%E0%B8%AD%E0%B8%AA%E0%B8%9B%E0%B8%A3%E0%B8%B8%E0%B8%87%E0%B8%A3%E0%B8%AA%E0%B8%9D%E0%B8%B2%E0%B9%80%E0%B8%82%E0%B8%B5%E0%B8%A2%E0%B8%A7-1-%E0%B8%A5%E0%B8%B4%E0%B8%95%E0%B8%A3/482340/",
        "cj": ""
    },
    8: { # ID 8 = แม็กกี้ซอสปรุงรส 680cc
        "bigc": "https://www.bigc.co.th/product/maggi-seasoning-sauce-700-ml.606",
        "lotus": "https://www.lotuss.com/th/product/maggi-well-rounded-stir-fried-recipe-cooking-sauce-1-680ml-1012614",
        "seven": "https://www.allonline.7eleven.co.th/p/%E0%B9%81%E0%B8%A1%E0%B9%87%E0%B8%81%E0%B8%81%E0%B8%B5%E0%B9%89-%E0%B8%8B%E0%B8%AD%E0%B8%AA%E0%B8%9B%E0%B8%A3%E0%B8%B8%E0%B8%87%E0%B8%AD%E0%B8%B2%E0%B8%AB%E0%B8%B2%E0%B8%A3-680-%E0%B8%A1%E0%B8%A5-%E0%B9%81%E0%B8%9E%E0%B9%87%E0%B8%81-3-%E0%B8%8A%E0%B8%B4%E0%B9%89%E0%B8%99/469337/",
        "seven_pack": 3, # บังคับหาร 3
        "cj": ""
    },
    9: { # ID 9 = แม็กกี้ซอสปรุงอาหารสูตรเข้มเข้าเนื้อ 680cc
        "bigc": "https://www.bigc.co.th/product/maggi-cooking-sauce-concentrated-formula-green-cap-size-680-ml.19444",
        "lotus": "https://www.lotuss.com/th/product/maggi-intense-meat-penetration-recipe-cooking-sauce-680ml-74095846",
        "seven": "https://www.allonline.7eleven.co.th/p/%E0%B9%81%E0%B8%A1%E0%B9%87%E0%B8%81%E0%B8%81%E0%B8%B5%E0%B9%89-%E0%B8%8B%E0%B8%AD%E0%B8%AA%E0%B8%9B%E0%B8%A3%E0%B8%B8%E0%B8%87%E0%B8%A3%E0%B8%AA-%E0%B8%9D%E0%B8%B2%E0%B9%80%E0%B8%82%E0%B8%B5%E0%B8%A2%E0%B8%A7-680-%E0%B8%81%E0%B8%A3%E0%B8%B1%E0%B8%A1/521267/",
        "cj": ""
    },
    10: { # ID 10 = เด็กสมบูรณ์ซอสหอยนางรมสูตรเข้มข้น 800g
        "bigc": "https://www.bigc.co.th/product/deksomboon-oyster-sauce-concentrate-formula-800-g.875",
        "lotus": "https://www.lotuss.com/th/product/healthy-boy-brand-thick-oyster-sauce-800ml-12579246",
        "seven": "https://www.allonline.7eleven.co.th/p/%E0%B9%80%E0%B8%94%E0%B9%87%E0%B8%81%E0%B8%AA%E0%B8%A1%E0%B8%9A%E0%B8%B9%E0%B8%A3%E0%B8%93%E0%B9%8C-%E0%B8%8B%E0%B8%AD%E0%B8%AA%E0%B8%AB%E0%B8%AD%E0%B8%A2%E0%B8%99%E0%B8%B2%E0%B8%87%E0%B8%A3%E0%B8%A1%E0%B8%AA%E0%B8%B9%E0%B8%95%E0%B8%A3%E0%B9%80%E0%B8%82%E0%B9%89%E0%B8%A1%E0%B8%82%E0%B9%89%E0%B8%99-800-%E0%B8%81%E0%B8%A3%E0%B8%B1%E0%B8%A1/482342/",
        "cj": ""
    },
    11: { # ID 11 = เด็กสมบูรณ์ซีอิ๊วขาวสูตร1 700cc
        "bigc": "https://www.bigc.co.th/product/healthy-boy-brand-soy-sauce-formula-1-size-700-ml.612",
        "lotus": "https://www.lotuss.com/th/product/healthy-boy-brand-formula-1-soybean-sauce-700ml-49794",
        "seven": "https://www.allonline.7eleven.co.th/p/%E0%B9%80%E0%B8%94%E0%B9%87%E0%B8%81%E0%B8%AA%E0%B8%A1%E0%B8%9A%E0%B8%B9%E0%B8%A3%E0%B8%93%E0%B9%8C-%E0%B8%8B%E0%B8%B5%E0%B8%AD%E0%B8%B4%E0%B9%8A%E0%B8%A7%E0%B8%82%E0%B8%B2%E0%B8%A7%E0%B8%AA%E0%B8%B9%E0%B8%95%E0%B8%A31-700-%E0%B8%A1%E0%B8%A5/481336/",
        "cj": ""
    },
    12: { # ID 12 = เด็กสมบูรณ์ซีอิ๊วขาวสูตร1 1000cc
        "bigc": "https://www.bigc.co.th/product/healthy-boy-soy-sauce-formula-1-1000-ml.235",
        "lotus": "https://www.lotuss.com/th/product/healthy-boy-brand-formula-1-soybean-sauce-1000ml-20190646",
        "seven": "https://www.allonline.7eleven.co.th/p/%E0%B9%80%E0%B8%94%E0%B9%87%E0%B8%81%E0%B8%AA%E0%B8%A1%E0%B8%9A%E0%B8%B9%E0%B8%A3%E0%B8%93%E0%B9%8C-%E0%B8%8B%E0%B8%B5%E0%B8%AD%E0%B8%B4%E0%B9%8A%E0%B8%A7%E0%B8%82%E0%B8%B2%E0%B8%A7%E0%B8%AA%E0%B8%B9%E0%B8%95%E0%B8%A31-1000-%E0%B8%A1%E0%B8%A5/480988/",
        "cj": ""
    }
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
                pack_size = urls.get("bigc_pack", auto_pack)
                final_price = round(new_price / pack_size, 2)
                div_text = f" (ดึงมา {new_price} หารด้วย {pack_size})" if pack_size > 1 else ""
                
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
                div_text = f" (ดึงมา {new_price} หารด้วย {pack_size})" if pack_size > 1 else ""
                
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
                div_text = f" (ดึงมา {new_price} หารด้วย {pack_size})" if pack_size > 1 else ""
                
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
                div_text = f" (ดึงมา {new_price} หารด้วย {pack_size})" if pack_size > 1 else ""
                
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
