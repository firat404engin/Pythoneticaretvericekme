import pyodbc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# SQL Server bağlantısı
server = 'FIRATENGIN\\SQLEXPRESS'  # SQL Server instance ismi
database = 'trendyol'  # Veritabanı adı
conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'

# Bağlantıyı açma
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# "Stok" sütununda "Yok" olan kayıtları sil
cursor.execute("DELETE FROM TrendyolIphone WHERE Stok = 'Yok'")
conn.commit()


# ChromeDriver ayarları
driver_path = r"C:\Users\fengi\Desktop\fiyatanlik\chromedriver.exe"
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=options)

def scroll_by_steps(driver, step_size=1000, max_scrolls=10):
    current_scrolls = 0
    last_position = driver.execute_script("return window.pageYOffset;")
    
    while current_scrolls < max_scrolls:
        driver.execute_script(f"window.scrollBy(0, {step_size});")
        time.sleep(2)
        new_position = driver.execute_script("return window.pageYOffset;")
        if new_position == last_position:
            break
        last_position = new_position
        current_scrolls += 1

# Trendyol ürünlerini çekme
base_url = "https://www.trendyol.com/iphone-ios-cep-telefonlari-x-c164462"

try:
    driver.get(base_url)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "prdct-cntnr-wrppr")))
    
    scroll_by_steps(driver, step_size=1000, max_scrolls=15)
    
    urunler = driver.find_elements(By.CLASS_NAME, "p-card-chldrn-cntnr")
    if not urunler:
        print("Ürün bulunamadı.")
    
    for urun in urunler:
        try:
            urun_linki = urun.find_element(By.TAG_NAME, "a").get_attribute("href")
            urun_gorsel = urun.find_element(By.CLASS_NAME, "p-card-img").get_attribute("src")

            # Veritabanında aynı URL'nin olup olmadığını kontrol et
            cursor.execute("SELECT COUNT(*) FROM TrendyolIphone WHERE Urunurl = ?", (urun_linki,))
            result = cursor.fetchone()
            if result:
                if result[0] == 0:
                    cursor.execute("""
                    INSERT INTO TrendyolIphone (Urunurl, Urungorsel)
                    VALUES (?, ?)
                    """, (urun_linki, urun_gorsel))
                    conn.commit()
                    print(f"Yeni ürün kaydedildi: {urun_linki}")
                else:
                    print(f"Ürün zaten mevcut: {urun_linki}")
            else:
                print(f"Veritabanı sorgusunda hata oluştu.")

        except Exception as e:
            print(f"Ürün işlenirken hata: {e}")

except Exception as e:
    print(f"Hata oluştu: {e}")

finally:
    driver.quit()
    conn.close()
