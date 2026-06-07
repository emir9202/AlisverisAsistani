import re
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from groq import Groq
from config import GROQ_API_KEY, MODEL_NAME

class SmartShoppingAgent:
    def __init__(self, headless=False):
        # Groq istemcisi
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model_name = MODEL_NAME

        # Chrome ayarları
        chrome_options = Options()

        # Kullanıcı profili - oturum bilgilerini saklar
        user_data = os.path.join(os.getcwd(), "chrome_profile")
        chrome_options.add_argument(f"--user-data-dir={user_data}")

        # Temel ayarlar
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1400,900")
        chrome_options.add_argument("--start-maximized")

        # Headless mod (opsiyonel)
        if headless:
            chrome_options.add_argument("--headless=new")

        # Bot algılamayı azalt
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        try:
            # Otomatik olarak doğru ChromeDriver'ı indir
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"Chrome başlatılamadı: {e}")
            self.driver = None

    def _get_groq_response(self, prompt):
        """Tüm Groq API isteklerini tek merkezden yöneten yardımcı fonksiyon."""
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                temperature=0.1,
                max_tokens=500
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"AI Hatası: {str(e)}"

    def get_market_analysis(self):
        """Herhangi bir e-ticaret sayfasını analiz eder."""
        try:
            if not self.driver:
                return "Tarayıcı bağlı değil."

            title = self.driver.title
            body_text = self.driver.find_element(By.TAG_NAME, "body").text[:5000]

            prompt = f"""
            Ürün Başlığı: {title}
            Sayfa İçeriği: {body_text}

            Sen evrensel bir alışveriş asistanısın. Bu sayfadaki ürünü incele:
            1. Fiyat makul mü? (Piyasa ortalamasını düşün)
            2. Ürünün öne çıkan özellikleri neler?
            3. Güvenilirlik analizi yap (Fiyat çok mu düşük?)
            Yanıtını samimi ve kısa bir özet olarak ver.
            """
            return self._get_groq_response(prompt)
        except Exception as e:
            return f"Analiz hatası: {str(e)}"

    def extract_price_with_ai(self, html_snippet):
        """Eğer CSS seçiciler başarısız olursa, fiyatı metinden AI ile bulur."""
        prompt = f"Aşağıdaki metin içindeki ürünün satış fiyatını sadece sayı olarak yaz (Örn: 1540.50). Eğer bulamazsan '0' yaz:\n\n{html_snippet}"
        try:
            response_text = self._get_groq_response(prompt)
            price = re.findall(r"\d+\.\d+|\d+", response_text)
            return float(price[0]) if price else 0
        except:
            return 0

    def smart_process(self, user_query, current_url):
        """Sadece analiz yapmaz, kullanıcın niyetini (intent) anlar."""
        prompt = f"""
        Kullanıcı sorusu: {user_query}
        Şu anki URL: {current_url}

        Sen bir alışveriş asistanısın. Kullanıcın niyetini şu kategorilerden birine sok:
        1. ANALIZ: Ürün fiyatı/özellikleri hakkında yorum isterse.
        2. TAKIP: "Takibe al", "listeye ekle" gibi komutlar.
        3. SEPET: "Sepete ekle", "almak istiyorum" gibi komutlar.

        Yanıtını şu formatta ver:
        Eylem: [KATEGORI]
        Cevap: [Kullanıcıya vereceğin doğal dildeki yanıt]
        """
        return self._get_groq_response(prompt)

    def analyze_product_with_ai(self):
        if not self.driver:
            return {"stok": False, "fiyat": "Bilinmiyor"}
        try:
            body_text = self.driver.find_element(By.TAG_NAME, "body").text[:2500]
            return {"stok": "EVET", "fiyat": "Analiz Edildi"}
        except:
            return {"stok": "HATA", "fiyat": "0"}

    def close(self):
        """Tarayıcıyı kapat"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
