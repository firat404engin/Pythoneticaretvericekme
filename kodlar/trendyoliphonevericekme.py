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

# TrendyolIphone tablosundaki tüm Urunurl değerlerini al
cursor.execute("SELECT Id, Urunurl FROM [dbo].[TrendyolIphone] ORDER BY Id ASC")
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

        # Satıcı ismini çek
        try:
            satıcı = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "seller-name-text"))
            ).text
        except Exception as e:
            satıcı = "Satıcı bulunamadı"
            print(f"Satıcı ismi alınamadı: {e}")

        # Stok durumunu çek
        try:
            stok_durumu_element = driver.find_element(By.CLASS_NAME, "add-to-basket-button-text")
            stok_durumu = "Var" if "Sepete Ekle" in stok_durumu_element.text else "Yok"
        except Exception as e:
            stok_durumu = "Yok"
            print(f"Stok durumu alınamadı: {e}")

        # Marka bilgisi çekme
        try:
            marka_element = driver.find_element(By.CLASS_NAME, "product-brand-name-with-link")
            marka = marka_element.text
        except Exception as e:
            marka = "Marka bilgisi bulunamadı"
        # Dikkat alanını çek
        try:
            dikkat_element = driver.find_elements(By.CLASS_NAME, "stock-warning-badge-text")
            dikkat = dikkat_element[0].text if dikkat_element else None
        except Exception as e:
            dikkat = None
            print(f"Dikkat alanı alınamadı: {e}")

        # Kampanya bilgisini çek
        try:
            kampanya_element = driver.find_element(By.CLASS_NAME, "banner-content")
            kampanya = kampanya_element.text
        except Exception as e:
            kampanya = "Kampanya bilgisi bulunamadı"
            print(f"Kampanya bilgisi alınamadı: {e}")

        # Dahili hafıza ve telefon modeli
        try:
            attributes = driver.find_elements(By.CLASS_NAME, "attribute-item")
            dahilihafiza = telefonmodeli = None
            for attribute in attributes:
                label = attribute.find_element(By.CLASS_NAME, "attribute-label").text.strip()
                value = attribute.find_element(By.CLASS_NAME, "attribute-value").text.strip()

                if label == "Dahili Hafıza":
                    dahilihafiza = value
                elif label == "Cep Telefonu Modeli":
                    telefonmodeli = value
        except Exception as e:
            print(f"Özellikler alınamadı: {e}")

        # Renk bilgisi
        try:
            renk = None
            attributes = driver.find_elements(By.CLASS_NAME, "detail-attr-item")
            for attribute in attributes:
                label = attribute.find_element(By.CLASS_NAME, "attr-name").text.strip()
                value = attribute.find_element(By.CLASS_NAME, "attr-value-name-w").text.strip()

                if label == "Renk":
                    renk = value
                    break  # Renk bulunduğunda döngüyü sonlandır
        except Exception as e:
            renk = "Renk bilgisi bulunamadı"

        # Yeni fiyat bilgisini çek
        try:
            fiyat_element = driver.find_element(By.CLASS_NAME, "prc-dsc")
            fiyat_text = fiyat_element.text
            YeniFiyat = float(fiyat_text.replace(".", "").replace(",", ".").replace(" TL", ""))
        except Exception as e:
            YeniFiyat = None
            print(f"Fiyat bilgisi alınamadı: {e}")
         # Stok durumunu çek
        stok_durumu = None
        
        try:
            # Sepete Ekle butonunun metnini kontrol et
            stok_durumu_element = driver.find_element(By.CLASS_NAME, "add-to-basket-button-text")
            
            # Eğer buton "Sepete Ekle" metnini taşıyorsa, stok var
            if "Sepete Ekle" in stok_durumu_element.text:
                stok_durumu = "Var"
            else:
                stok_durumu = "Yok"  # Eğer buton "Sepete Ekle" değilse, stok yok

        except Exception as e:
            stok_durumu = "Yok"
            print(f"Stok durumu alınamadı: {e}")

         
        # Eğer stok durumu "Yok" ise, alternatif satıcı ve URL bilgilerini al
        if stok_durumu == "Yok":
            try:
                # Alternatif satıcı bilgisi
                alternatif_satici_element = driver.find_element(By.CLASS_NAME, "merchant-name")
                alternatif_satici = alternatif_satici_element.text
            except Exception as e:
                alternatif_satici = "Alternatif satıcı bulunamadı"
                print(f"Alternatif satıcı alınamadı: {e}")

            try:
                # Alternatif satıcı URL'si
                alternatif_satici_url_element = driver.find_element(By.CLASS_NAME, "merchant-box").find_element(By.TAG_NAME, "a")
                alternatif_satici_url = alternatif_satici_url_element.get_attribute("href")
            except Exception as e:
                alternatif_satici_url = "URL bulunamadı"
                print(f"Alternatif satıcı URL'si alınamadı: {e}")
        else:
            alternatif_satici = None
            alternatif_satici_url = None

        # Güncelleme tarihini al
        guncelleme_tarihi = format_date(datetime.now())

        # Veritabanında ilgili ürünü güncelle
        try:
            cursor.execute("""
        UPDATE [dbo].[TrendyolIphone]
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
    """, (satıcı, stok_durumu, guncelleme_tarihi, dikkat, kampanya, YeniFiyat, dahilihafiza, telefonmodeli, renk, marka, urun_id))

            conn.commit()  # Değişiklikleri kaydet
            print(f"Ürün ID: {urun_id}, Satıcı: {satıcı}, Stok Durumu: {stok_durumu}, Dikkat: {dikkat}, Renk: {renk}, "
                  f"Kampanya: {kampanya}, Yeni Fiyat: {YeniFiyat}, Güncelleme Tarihi: {guncelleme_tarihi}, "
                  f"Dahili Hafıza: {dahilihafiza}, Cep Telefonu Modeli: {telefonmodeli}, Marka: {marka}")
        except Exception as e:
            print(f"Veritabanı güncellenirken hata: {e}")

    except Exception as e:
        print(f"Ürün ID: {urun_id} için işlem hatası: {e}")

# Veritabanı bağlantısını kapat
conn.close()
driver.quit()
