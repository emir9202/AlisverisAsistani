import sqlite3
from datetime import datetime


class DBManager:
    def __init__(self, db_name="asistan.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()
        self.migrate_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # Aktif takip listesi
        cursor.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            url TEXT UNIQUE,
            mode TEXT,
            target REAL,
            autopilot INTEGER,
            min_price REAL DEFAULT 0,
            last_price REAL DEFAULT 0,
            category TEXT DEFAULT 'Genel'
        )''')

        # Geçmiş tablosu
        cursor.execute('''CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            url TEXT,
            final_price REAL,
            status TEXT,
            timestamp TEXT,
            category TEXT DEFAULT 'Genel'
        )''')

        # Uygulama Ayarları Tablosu
        cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )''')

        # Fiyat geçmişi tablosu
        cursor.execute('''CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            price REAL,
            timestamp TEXT
        )''')

        self.conn.commit()

    def migrate_tables(self):
        """Eski tablolara yeni sütunları ekle"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN category TEXT DEFAULT 'Genel'")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # Sütun zaten var

    # --- KATEGORİLER ---
    def get_categories(self):
        """Tüm kategorileri getir"""
        return [
            "Genel",
            "Elektronik",
            "Giyim",
            "Ev & Yaşam",
            "Kozmetik",
            "Spor",
            "Kitap & Hobi",
            "Bebek",
            "Diğer"
        ]

    def get_products_by_category(self, category):
        """Kategoriye göre ürünleri getir"""
        cursor = self.conn.cursor()
        if category == "Tümü":
            return self.get_active_products()
        cursor.execute("""SELECT name, url, mode, target, autopilot, min_price, last_price, category
                         FROM products WHERE category = ?""", (category,))
        rows = cursor.fetchall()
        return [{"name": r[0], "url": r[1], "mode": r[2], "target": r[3],
                 "autopilot": bool(r[4]), "min_price": r[5], "last_price": r[6],
                 "category": r[7]} for r in rows]

    def get_category_stats(self):
        """Her kategorideki ürün sayısını getir"""
        cursor = self.conn.cursor()
        cursor.execute("""SELECT category, COUNT(*) FROM products GROUP BY category""")
        rows = cursor.fetchall()
        stats = {"Tümü": 0}
        for r in rows:
            stats[r[0]] = r[1]
            stats["Tümü"] += r[1]
        return stats

    # --- AYARLAR ---
    def set_setting(self, key, value):
        """Bir ayarı kaydeder veya günceller."""
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        self.conn.commit()

    def get_setting(self, key, default=""):
        """Bir ayarı getirir, yoksa varsayılan değeri döner."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default

    # --- ÜRÜNLER ---
    def add_product(self, data):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''INSERT INTO products (name, url, mode, target, autopilot, category)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                           (data['name'], data['url'], data['mode'], data['target'],
                            data['autopilot'], data.get('category', 'Genel')))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_active_products(self):
        cursor = self.conn.cursor()
        cursor.execute("""SELECT name, url, mode, target, autopilot, min_price, last_price, category
                         FROM products""")
        rows = cursor.fetchall()
        return [{"name": r[0], "url": r[1], "mode": r[2], "target": r[3],
                 "autopilot": bool(r[4]), "min_price": r[5], "last_price": r[6],
                 "category": r[7] if len(r) > 7 else "Genel"} for r in rows]

    def update_price(self, url, last_price, min_price):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE products SET last_price = ?, min_price = ? WHERE url = ?",
                      (last_price, min_price, url))
        # Fiyat geçmişine kaydet
        cursor.execute('''INSERT INTO price_history (url, price, timestamp) VALUES (?, ?, ?)''',
                      (url, last_price, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.conn.commit()

    def update_product_category(self, url, category):
        """Ürün kategorisini güncelle"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE products SET category = ? WHERE url = ?", (category, url))
        self.conn.commit()

    def get_price_history(self, url, limit=30):
        """Ürünün fiyat geçmişini getir"""
        cursor = self.conn.cursor()
        cursor.execute("""SELECT price, timestamp FROM price_history
                         WHERE url = ? ORDER BY timestamp DESC LIMIT ?""", (url, limit))
        rows = cursor.fetchall()
        return [{"price": r[0], "timestamp": r[1]} for r in rows]

    def move_to_history(self, product, status):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO history (name, url, final_price, status, timestamp, category)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                       (product['name'], product['url'], product.get('last_price', 0),
                        status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        product.get('category', 'Genel')))
        cursor.execute("DELETE FROM products WHERE url = ?", (product['url'],))
        self.conn.commit()

    def delete_product(self, url):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, last_price, category FROM products WHERE url = ?", (url,))
        row = cursor.fetchone()
        if row:
            self.move_to_history({
                'name': row[0],
                'url': url,
                'last_price': row[1],
                'category': row[2] if len(row) > 2 else 'Genel'
            }, status="KULLANICI SİLDİ")

    def get_history(self, limit=50):
        """Geçmiş kayıtlarını getir"""
        cursor = self.conn.cursor()
        cursor.execute("""SELECT name, url, final_price, status, timestamp, category
                         FROM history ORDER BY timestamp DESC LIMIT ?""", (limit,))
        rows = cursor.fetchall()
        return [{"name": r[0], "url": r[1], "final_price": r[2], "status": r[3],
                 "timestamp": r[4], "category": r[5] if len(r) > 5 else "Genel"} for r in rows]
