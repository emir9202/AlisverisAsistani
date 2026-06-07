


# 🛒 Yapay Zeka Tabanlı Alışveriş Asistanı

Bu proje, e-ticaret sayfalarını analiz eden, ürün fiyatlarını ve özelliklerini çıkaran ve kullanıcının niyetini anlayan akıllı bir alışveriş asistanıdır. Yapay zeka motoru olarak aşırı hızlı **Groq API (Llama 3)** kullanılmaktadır. Ayrıca web otomasyonu için **Selenium** ve mesajlaşma entegrasyonu için **Telethon** (Telegram) altyapılarını içerir.

## 🚀 Özellikler

* **Akıllı Piyasa Analizi:** İncelenen ürünün fiyatının makul olup olmadığını piyasa standartlarına göre değerlendirir.
* **Yapay Zeka ile Fiyat Çıkarma:** Karmaşık HTML yapılarından bile ürünün gerçek fiyatını AI kullanarak bulur.
* **Niyet Analizi (Intent Recognition):** Kullanıcının sadece bilgi mi almak istediğini yoksa ürünü listeye/sepete mi eklemek istediğini anlar.
* **Modern Arayüz:** CustomTkinter ile hazırlanmış kullanıcı dostu grafik arayüz.

---

## 🛠️ Kurulum Adımları

Projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları sırasıyla uygulayın.

### 1. Projeyi İndirin

Bilgisayarınızın terminalini (veya komut istemini) açın ve projeyi klonlayın:

```bash
git clone https://github.com/emir9202/AlisverisAistani.git
cd AlisverisAsistani

```

*(Not: Klonlamak yerine GitHub üzerinden ZIP olarak da indirebilirsiniz.)*

### 2. Sanal Ortam (Virtual Environment) Oluşturun

Proje bağımlılıklarının sisteminizle çakışmaması için temiz bir sanal ortam oluşturun:

```bash
python -m venv venv

```

### 3. Sanal Ortamı Aktifleştirin

İşletim sisteminize göre uygun komutu çalıştırarak sanal ortamı aktif edin:

* **Windows (Komut İstemi - CMD):**
```cmd
.\venv\Scripts\activate.bat

```


* **Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1

```


* **Mac / Linux:**
```bash
source venv/bin/activate

```



*(Aktifleştirme başarılı olduğunda komut satırının başında `(venv)` yazısını göreceksiniz.)*

### 4. Gerekli Kütüphaneleri Kurun

Projeyi çalıştırmak için gereken tüm kütüphaneleri tek seferde kurun:

```bash
pip install -r requirements.txt

```

---

## 🔐 Ortam Değişkenleri ve API Ayarları

Güvenlik nedeniyle API şifreleri GitHub'a yüklenmemiştir. Projeyi çalıştırmadan önce ana klasörde **`.env`** adında yeni bir dosya oluşturun ve içine kendi bilgilerinizi aşağıdaki gibi ekleyin:

```env
# Groq Yapay Zeka API Anahtarı
GROQ_API_KEY=kendi_groq_api_anahtarinizi_buraya_yazin
TELEGRAM_API_ID=abcd123
TELEGRAM_API_HASH=abcdef123456



```

---

## ▶️ Projeyi Çalıştırma

Tüm kurulumları tamamladıktan ve `.env` dosyanızı ayarladıktan sonra, sanal ortamınız `(venv)` aktifken aşağıdaki komutla projeyi başlatabilirsiniz:

```bash
python ShoppingAssistant.py

```
