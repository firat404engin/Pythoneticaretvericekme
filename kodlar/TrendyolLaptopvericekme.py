import pyodbc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

# SQL Server bağlantısı için doğru bağlantı dizesi
server = 'FIRATENGIN\\SQLEXPRESS'  # SQL Server instance ismi
database = 'trendyol'  # Veritabanı adı
conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'

# Bağlantıyı açma
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# ChromeDriver path ve ayarları
driver_path = r"C:\Users\fengi\Desktop\fiyatanlik\chromedriver.exe"
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=options)

# TrendyolLaptop tablosundaki URL'leri çek
cursor.execute("SELECT Id, Urunurl FROM [dbo].[TrendyolLaptop]")
urunler = cursor.fetchall()
def format_date(date):
    now = datetime.now()
    delta = now - date

    if delta.days == 0:
        return f"bugün, {date.strftime('%H:%M')}"
    elif delta.days == 1:
        return f"dün, {date.strftime('%H:%M')}"
    else:
        return date.strftime('%Y-%m-%d %H:%M')


for urun in urunler:
    urun_id = urun[0]
    urun_url = urun[1]
    
    try:
              # Ürün URL'sine git
        driver.get(urun_url)
     
      
     # Sayfanın tamamen yüklenmesini bekle
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        # Marka
        brand_element = driver.find_element(By.CSS_SELECTOR, ".product-brand-name-with-link")
        brand = brand_element.text
        
        # Satıcı ismini çek
        try:
            satıcı = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "seller-name-text"))
            ).text
        except Exception as e:
            satıcı = "Satıcı bulunamadı"
            print(f"Satıcı ismi alınamadı: {e}")

         # Kampanya bilgisini çek
        try:
            kampanya_element = driver.find_element(By.CLASS_NAME, "banner-content")
            kampanya = kampanya_element.text
        except Exception as e:
            kampanya = "Kampanya bilgisi bulunamadı"
            print(f"Kampanya bilgisi alınamadı: {e}")
        
        YeniFiyat = None

        try:
            # Fiyat bilgisini 'prc-dsc' sınıfından çekmeye çalış
            fiyat_element = driver.find_element(By.CLASS_NAME, "prc-dsc")
            fiyat_text = fiyat_element.text
            YeniFiyat = float(fiyat_text.replace(".", "").replace(",", ".").replace(" TL", ""))
        except Exception as e:
            # Eğer prc-dsc sınıfından fiyat alınamazsa, campaign-price sınıfından fiyat alınmaya çalışılacak
            try:
                fiyat_element_campaign = driver.find_element(By.CLASS_NAME, "campaign-price")
                fiyat_text_campaign = fiyat_element_campaign.text
                YeniFiyat = float(fiyat_text_campaign.replace(".", "").replace(",", ".").replace(" TL", ""))
            except Exception as campaign_exception:
                # Eğer her iki sınıftan da fiyat alınamazsa, hata mesajı yazdırılır
                print(f"Fiyat bilgisi alınamadı (her iki sınıftan): {campaign_exception}")
                print(f"Orijinal hata: {e}")
        # Model
        model_element = driver.find_element(By.CSS_SELECTOR, "h1.pr-new-br span")
        model = model_element.text
        
         # Dikkat alanını çek
        try:
            dikkat_element = driver.find_elements(By.CLASS_NAME, "stock-warning-badge-text")
            dikkat = dikkat_element[0].text if dikkat_element else None
        except Exception as e:
            dikkat = None
            print(f"Dikkat alanı alınamadı: {e}")
        
            screen_size = None
        try:
              screen_size = driver.find_element(By.XPATH, "//li[contains(@class, 'attribute-item') and contains(., 'Ekran Boyutu')]//div[contains(@class, 'attr-name-w')]").text
        except:
              screen_size = None  
        # Detaylar
        details = driver.find_elements(By.CSS_SELECTOR, "li.detail-attr-item")
        specs = {}
        for detail in details:
            try:
                key = detail.find_element(By.CSS_SELECTOR, ".attr-key-name-w").text
                value = detail.find_element(By.CSS_SELECTOR, ".attr-value-name-w").text
                specs[key] = value
            except:
                continue
        
        # Veritabanı sütunlarını doldur
        ram = specs.get("Ram (Sistem Belleği)", None)
        storage = specs.get("SSD Kapasitesi", None)
        cpu_type = specs.get("İşlemci Tipi", None)
        cpu_model = specs.get("İşlemci Modeli", None)
        cpu_gen = specs.get("İşlemci Nesli", None)
        gpu = specs.get("Ekran Kartı", None)
        purpose = specs.get("Kullanım Amacı", None)
        
        # Güncelleme tarihini al
        guncelleme_tarihi = format_date(datetime.now())
        # Güncelleme sorgusu
        update_query = """
        UPDATE [dbo].[TrendyolLaptop]
        SET Eskifiyat =Yenifiyat, Satici=?,Yenifiyat=?,Kampanya=?,Dikkat=?, Marka = ?, Model = ?, Ram = ?, Depolama = ?, islemciTipi = ?, 
            islemciNesli = ?, islemciModeli = ?, Ekrankarti = ?, KullanimAmaci = ?, Guncellemetarihi = ?,EkranEbat=?
        WHERE Id = ?
        """
        cursor.execute(update_query, (satıcı,YeniFiyat,kampanya,dikkat,brand, model, ram, storage, cpu_type, cpu_gen, cpu_model, gpu, purpose,guncelleme_tarihi,screen_size, urun_id))
        conn.commit()
        print(f"Updated product ID: {urun_id}")
    except Exception as e:
        print(f"Error processing product ID {urun_id}: {e}")

# Kaynakları kapat
driver.quit()
conn.close()
