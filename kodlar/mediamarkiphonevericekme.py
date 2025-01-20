import pyodbc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

# Tarih formatlama fonksiyonu
def format_date(date):
    now = datetime.now()
    delta = now - date

    if delta.days == 0:
        return f"bugün, {date.strftime('%H:%M')}"
    elif delta.days == 1:
        return f"dün, {date.strftime('%H:%M')}"
    else:
        return date.strftime('%Y-%m-%d %H:%M')

# Veritabanı bağlantısı
conn = pyodbc.connect(
    "Driver={SQL Server};"
    "Server=FIRATENGIN\\SQLEXPRESS;"
    "Database=mediamark;"
    "Trusted_Connection=yes;"
)
cursor = conn.cursor()


# ChromeDriver path ve ayarları
driver_path = r"C:\Users\fengi\Desktop\fiyatanlik\chromedriver.exe"
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=options)

# Ürün bilgilerini çek ve veritabanını güncelle
cursor.execute("SELECT Id, Urunurl FROM [dbo].[mediamarkiphone] ORDER BY Id ASC")
urunler = cursor.fetchall()

for urun in urunler:
    urun_id, urun_url = urun
    driver.get(urun_url)
    
    try:
        # Sayfadaki bilgileri çek
        marka = driver.find_element(By.CSS_SELECTOR, "img.sc-5e958866-4.eoCwQK").get_attribute("alt")
        telefonmodeli = driver.find_element(By.CSS_SELECTOR, "h1.sc-8b815c14-0.kRkMRa").text
        # Bellek kapasitesini çekme (XPath kullanarak)
        bellek_kapasitesi = driver.find_element(By.XPATH, "//td[p[contains(text(), 'Bellek Kapasitesi')]]/following-sibling::td//p").text
        renk = driver.find_element(By.CSS_SELECTOR, "span.sc-8b815c14-0.hVYfJJ.sc-a21dccc6-2.gRJbCL").text
        # Renk bilgisini ':' işaretine göre ayır ve son kısmı al
        renk_clean = renk.split(':')[-1].strip()
        # Fiyat bilgisini çeken kod
        fiyat_elementi = driver.find_element(By.CSS_SELECTOR, "span[data-test='branded-price-whole-value']")
        fiyat_text = fiyat_elementi.text.strip()  # ₺ 57.999, gibi bir metin dönecek

        # Türkçe formatı ondalık formata çevirme
        fiyat_text_clean = fiyat_text.replace("₺", "").replace(".", "").replace(",", ".").strip()
        yeni_fiyat = float(fiyat_text_clean)  # 57999.0 şeklinde bir float değer
        kampanya = driver.find_element(By.CSS_SELECTOR, "span.sc-8b815c14-0.bfuyDG").text
        satıcı = "MediaMarkt"  # Sabit bir satıcı adı; isterseniz dinamikleştirin.
        
        # Stok kontrolü
        try:
            stok_element = driver.find_element(By.CSS_SELECTOR, "span.sc-f52d4e87-0.dzLmYX").text
            stok_durumu = "Var" if "Sepete Ekle" in stok_element else "Yok"
        except:
            stok_durumu = "Yok"
        
        # Güncelleme tarihi
        guncelleme_tarihi = format_date(datetime.now())

        # Veritabanını güncelle
        try:
            cursor.execute("""
                UPDATE [dbo].[mediamarkiphone]
                SET EskiFiyat = YeniFiyat, 
                    Satici = ?, 
                    Stok = ?, 
                    GuncellemeTarihi = ?, 
                    Dikkat = ?, 
                    Kampanya = ?, 
                    YeniFiyat = ?, 
                    Hafıza = ?, 
                    Model = ?, 
                    Renk = ?, 
                    Marka = ?
                WHERE Id = ?
            """, (satıcı, stok_durumu, guncelleme_tarihi, None, kampanya, yeni_fiyat, bellek_kapasitesi, telefonmodeli, renk_clean, marka, urun_id))

            conn.commit()  # Değişiklikleri kaydet
            print(f"Ürün ID: {urun_id}, Satıcı: {satıcı}, Stok Durumu: {stok_durumu}, Renk: {renk_clean}, "
                  f"Kampanya: {kampanya}, Yeni Fiyat: {yeni_fiyat}, Güncelleme Tarihi: {guncelleme_tarihi}, "
                  f"Dahili Hafıza: {bellek_kapasitesi}, Cep Telefonu Modeli: {telefonmodeli}, Marka: {marka}")
        except Exception as e:
            print(f"Veritabanı güncellenirken hata: {e}")

    except Exception as e:
        print(f"Ürün ID: {urun_id} için işlem hatası: {e}")

# Tarayıcıyı ve veritabanı bağlantısını kapat
driver.quit()
cursor.close()
conn.close()
