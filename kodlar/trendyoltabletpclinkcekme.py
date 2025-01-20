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

# ChromeDriver ayarları
driver_path = r"C:\Users\fengi\Desktop\fiyatanlik\chromedriver.exe"
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=options)

# "Stok" sütununda "Yok" olan kayıtları sil
cursor.execute("DELETE FROM TrendyolTablet WHERE Stok = 'Yok'")
conn.commit()

# URL başlangıcı
base_url = "https://www.trendyol.com/tablet-x-c103665?pi={page}"
max_page = 15  # Sabit sayfa sayısı
page = 1

try:
    # Sayfaları dolaşmaya başla
    while page <= max_page:
        # Her sayfa için URL'yi oluştur
        url = base_url.format(page=page)
        print(f"Sayfa: {page}, URL: {url}")
        
        # Sayfayı aç
        driver.get(url)
        
        # Sayfanın yüklenmesini bekle
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "prdct-cntnr-wrppr")))
        except Exception as e:
            print("Sayfa yüklenemedi veya son sayfaya ulaşıldı. İşlem tamamlandı.")
            break
        
        # Ürün bağlantılarını bul
        urunler = driver.find_elements(By.CLASS_NAME, "p-card-chldrn-cntnr")
        if not urunler:
            print("Daha fazla ürün bulunamadı, işlem tamamlandı.")
            break
        
       # Ürün bağlantılarını ve görsel URL'lerini kaydet
        for urun in urunler:
            try:
                urun_linki = urun.find_element(By.TAG_NAME, "a").get_attribute("href")
                urun_gorsel = urun.find_element(By.CLASS_NAME, "p-card-img").get_attribute("src")
                
                # Veritabanında aynı URL'nin olup olmadığını kontrol et
                cursor.execute("SELECT COUNT(*) FROM TrendyolTablet WHERE Urunurl = ?", (urun_linki,))
                result = cursor.fetchone()
                
                if result and result[0] == 0:  # URL yoksa ekle
                    cursor.execute("""
                    INSERT INTO TrendyolTablet (Urunurl, Urungorsel)
                    VALUES (?, ?)
                    """, (urun_linki, urun_gorsel))
                    conn.commit()
                    print(f"Ürün kaydedildi: {urun_linki}, Görsel URL: {urun_gorsel}")
                else:
                    print(f"Ürün zaten mevcut: {urun_linki}")
            except Exception as e:
                print(f"Ürün işlenirken hata: {e}")

        # Sonraki sayfaya geç
        page += 1
        time.sleep(2)  # Trendyol'un bot korumasını tetiklememek için bekleme süresi

except Exception as e:
    print(f"Hata oluştu: {e}")

finally:
    # Bağlantıları kapatma
    driver.quit()
    conn.close()
