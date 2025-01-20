import pyodbc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# SQL Server bağlantısı
server = 'FIRATENGIN\\SQLEXPRESS'  # SQL Server instance ismi
database = 'mediamark'  # Veritabanı adı
conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'

# Bağlantıyı açma
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# ChromeDriver ayarları
driver_path = r"C:\\Users\\fengi\\Desktop\\fiyatanlik\\chromedriver.exe"
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=options)

def fetch_products_from_page(url):
    """Belirtilen URL'den ürünleri çeker ve veritabanına kaydeder."""
    driver.get(url)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "img")))
    
    urunler = driver.find_elements(By.CSS_SELECTOR, "a[data-test='mms-router-link']")
    if not urunler:
        print("Sayfada ürün bulunamadı.")
        return

    for urun in urunler:
        try:
            # Ürün URL'si
            urun_linki = urun.get_attribute("href")
            
            # Görsel URL'si
            urun_gorsel = urun.find_element(By.TAG_NAME, "img").get_attribute("src")

            # Veritabanında aynı URL'nin olup olmadığını kontrol et
            cursor.execute("SELECT COUNT(*) FROM mediamarkiphone WHERE Urunurl = ?", (urun_linki,))
            result = cursor.fetchone()
            if result and result[0] == 0:
                # Yeni ürün ekleme
                cursor.execute("""
                INSERT INTO mediamarkiphone (Urunurl, Urungorsel)
                VALUES (?, ?)
                """, (urun_linki, urun_gorsel))
                conn.commit()
                print(f"Yeni ürün kaydedildi: {urun_linki}")
            else:
                print(f"Ürün zaten mevcut: {urun_linki}")

        except Exception as e:
            print(f"Ürün işlenirken hata: {e}")

# Ana URL ve sayfa sayıları
base_url = "https://www.mediamarkt.com.tr/tr/category/iphone-644527.html?page={}"  # Sayfa numarası ekleniyor
total_pages = 3  # Toplam sayfa sayısı

try:
    for page in range(1, total_pages + 1):
        page_url = base_url.format(page)
        print(f"Sayfa çekiliyor: {page_url}")
        fetch_products_from_page(page_url)

except Exception as e:
    print(f"Hata oluştu: {e}")

finally:
    driver.quit()
    conn.close()
