import customtkinter as ctk
import threading
import time
import re
import os
import subprocess
import platform
import json
import csv
from tkinter import filedialog
from datetime import datetime
from selenium.webdriver.common.by import By
from analiz_motoru2 import SmartShoppingAgent
from db_manager2 import DBManager
from telethon.sync import TelegramClient
import asyncio

from config import TELEGRAM_API_ID, TELEGRAM_API_HASH

# ==================== KURUMSAL RENK PALETI ====================
class Colors:
    # Ana Renkler - Koyu ve Profesyonel
    PRIMARY = "#2563EB"        # Kurumsal mavi
    PRIMARY_DARK = "#1D4ED8"   # Koyu mavi
    PRIMARY_LIGHT = "#3B82F6"  # Açık mavi

    # Arka Plan - Nötr ve Zarif
    BG_PRIMARY = "#FAFAFA"     # Ana arka plan (açık gri)
    BG_CARD = "#FFFFFF"        # Kart arka planı (beyaz)
    BG_SIDEBAR = "#F3F4F6"     # Sidebar/panel
    BG_INPUT = "#F9FAFB"       # Input arka planı
    BG_DARK = "#111827"        # Koyu mod

    # Metin - Okunabilir ve Profesyonel
    TEXT_PRIMARY = "#111827"   # Ana metin (koyu)
    TEXT_SECONDARY = "#6B7280" # İkincil metin (gri)
    TEXT_MUTED = "#9CA3AF"     # Soluk metin
    TEXT_WHITE = "#FFFFFF"     # Beyaz metin

    # Durum Renkleri - Profesyonel tonlar
    SUCCESS = "#059669"        # Koyu yeşil
    SUCCESS_LIGHT = "#D1FAE5"  # Açık yeşil bg
    WARNING = "#D97706"        # Koyu turuncu
    WARNING_LIGHT = "#FEF3C7"  # Açık turuncu bg
    ERROR = "#DC2626"          # Koyu kırmızı
    ERROR_LIGHT = "#FEE2E2"    # Açık kırmızı bg
    INFO = "#0284C7"           # Bilgi mavisi

    # Kenarlık ve Ayırıcılar
    BORDER = "#E5E7EB"         # Açık kenarlık
    BORDER_DARK = "#D1D5DB"    # Koyu kenarlık
    DIVIDER = "#F3F4F6"        # Ayırıcı

    # Vurgu
    ACCENT = "#7C3AED"         # Mor vurgu
    ACCENT_LIGHT = "#EDE9FE"   # Açık mor bg


class ConfirmationPopup(ctk.CTkToplevel):
    def __init__(self, master, title, message, on_confirm):
        super().__init__(master)
        self.title(title)
        self.geometry("400x200")
        self.configure(fg_color=Colors.BG_CARD)
        self.attributes("-topmost", True)
        self.on_confirm = on_confirm

        # İçerik
        content = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, corner_radius=0)
        content.pack(fill="both", expand=True, padx=24, pady=20)

        # Başlık
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(header, text="✓", font=("Arial", 24),
                    text_color=Colors.SUCCESS,
                    fg_color=Colors.SUCCESS_LIGHT, width=40, height=40,
                    corner_radius=20).pack(side="left")
        ctk.CTkLabel(header, text="Hedef Fiyata Ulaşıldı",
                    font=("Segoe UI", 16, "bold"),
                    text_color=Colors.TEXT_PRIMARY).pack(side="left", padx=12)

        ctk.CTkLabel(content, text=message, font=("Segoe UI", 13),
                    text_color=Colors.TEXT_SECONDARY, wraplength=350,
                    justify="left").pack(anchor="w", pady=(0, 20))

        # Butonlar
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(btn_frame, text="Sepete Ekle", fg_color=Colors.PRIMARY,
                     hover_color=Colors.PRIMARY_DARK, width=120, height=38,
                     corner_radius=6, font=("Segoe UI", 13, "bold"),
                     command=self.confirm).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Vazgeç", fg_color="transparent",
                     hover_color=Colors.BG_SIDEBAR, width=100, height=38,
                     corner_radius=6, font=("Segoe UI", 13),
                     text_color=Colors.TEXT_SECONDARY, border_width=1,
                     border_color=Colors.BORDER,
                     command=self.cancel).pack(side="right")

    def confirm(self):
        self.on_confirm(True)
        self.destroy()

    def cancel(self):
        self.on_confirm(False)
        self.destroy()


class CodeInputDialog(ctk.CTkToplevel):
    def __init__(self, master, phone):
        super().__init__(master)
        self.title("Telegram Doğrulama")
        self.geometry("360x220")
        self.configure(fg_color=Colors.BG_CARD)
        self.attributes("-topmost", True)
        self.result = None

        content = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, corner_radius=0)
        content.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(content, text="Doğrulama Kodu",
                    font=("Segoe UI", 18, "bold"),
                    text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(content, text=f"Telegram'a gönderilen kodu girin ({phone})",
                    font=("Segoe UI", 12),
                    text_color=Colors.TEXT_SECONDARY).pack(anchor="w", pady=(4, 16))

        self.entry = ctk.CTkEntry(content, width=310, height=44, corner_radius=6,
                                  font=("Segoe UI", 15), justify="center",
                                  fg_color=Colors.BG_INPUT, border_width=1,
                                  border_color=Colors.BORDER,
                                  placeholder_text="• • • • • •")
        self.entry.pack(pady=(0, 16))

        ctk.CTkButton(content, text="Doğrula", command=self.submit,
                     fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_DARK,
                     width=310, height=42, corner_radius=6,
                     font=("Segoe UI", 14, "bold")).pack()

    def submit(self):
        self.result = self.entry.get().strip()
        self.destroy()


class AgentGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Fiyat Takip Sistemi")
        self.geometry("1150x850")
        self.configure(fg_color=Colors.BG_PRIMARY)
        ctk.set_appearance_mode("light")

        self.db = DBManager()
        self.products = self.db.get_active_products()
        self.is_monitoring = False
        self.agent = None
        self.lock = threading.Lock()
        self.browser_connected = False
        self.current_category = "Tümü"

        self.setup_ui()
        self.load_settings()
        self.render_list()

    def setup_ui(self):
        # Ana grid yapılandırması
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Sol Sidebar
        self.create_sidebar()

        # Ana İçerik Alanı
        self.create_main_content()

    def create_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, width=280, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # Logo ve Başlık
        header = ctk.CTkFrame(sidebar, fg_color="transparent", height=80)
        header.pack(fill="x", padx=20, pady=(24, 20))

        logo_frame = ctk.CTkFrame(header, fg_color=Colors.PRIMARY, width=42, height=42, corner_radius=8)
        logo_frame.pack(side="left")
        logo_frame.pack_propagate(False)
        ctk.CTkLabel(logo_frame, text="FT", font=("Segoe UI", 16, "bold"),
                    text_color=Colors.TEXT_WHITE).place(relx=0.5, rely=0.5, anchor="center")

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=12)
        ctk.CTkLabel(title_frame, text="Fiyat Takip",
                    font=("Segoe UI", 17, "bold"),
                    text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Profesyonel Sistem",
                    font=("Segoe UI", 11),
                    text_color=Colors.TEXT_MUTED).pack(anchor="w")

        # Ayırıcı
        ctk.CTkFrame(sidebar, fg_color=Colors.BORDER, height=1).pack(fill="x", padx=20)

        # Menü Bölümü
        menu_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        menu_frame.pack(fill="x", padx=16, pady=20)

        ctk.CTkLabel(menu_frame, text="GENEL",
                    font=("Segoe UI", 10, "bold"),
                    text_color=Colors.TEXT_MUTED).pack(anchor="w", padx=8, pady=(0, 8))

        # Tarayıcı Butonu
        self.browser_btn = ctk.CTkButton(menu_frame, text="  Tarayıcıyı Başlat",
                                         width=240, height=42, anchor="w",
                                         fg_color="transparent", hover_color=Colors.BG_SIDEBAR,
                                         text_color=Colors.TEXT_PRIMARY,
                                         font=("Segoe UI", 13),
                                         image=None,
                                         command=self.launch_browser)
        self.browser_btn.pack(fill="x", pady=2)

        self.disconnect_btn = ctk.CTkButton(menu_frame, text="  Bağlantıyı Kes",
                                            width=240, height=42, anchor="w",
                                            fg_color="transparent", hover_color=Colors.BG_SIDEBAR,
                                            text_color=Colors.TEXT_MUTED,
                                            font=("Segoe UI", 13),
                                            state="disabled",
                                            command=self.disconnect_browser)
        self.disconnect_btn.pack(fill="x", pady=2)

        # Bağlantı Durumu
        status_frame = ctk.CTkFrame(menu_frame, fg_color=Colors.BG_SIDEBAR, corner_radius=8, height=40)
        status_frame.pack(fill="x", pady=(12, 0))

        status_inner = ctk.CTkFrame(status_frame, fg_color="transparent")
        status_inner.pack(fill="x", padx=12, pady=10)

        self.status_dot = ctk.CTkLabel(status_inner, text="●", font=("Arial", 8),
                                       text_color=Colors.ERROR)
        self.status_dot.pack(side="left")
        self.status_text = ctk.CTkLabel(status_inner, text="Bağlantı Yok",
                                        font=("Segoe UI", 11),
                                        text_color=Colors.TEXT_SECONDARY)
        self.status_text.pack(side="left", padx=8)

        # Telegram Bölümü
        ctk.CTkFrame(sidebar, fg_color=Colors.BORDER, height=1).pack(fill="x", padx=20, pady=16)

        tg_section = ctk.CTkFrame(sidebar, fg_color="transparent")
        tg_section.pack(fill="x", padx=20)

        ctk.CTkLabel(tg_section, text="BİLDİRİMLER",
                    font=("Segoe UI", 10, "bold"),
                    text_color=Colors.TEXT_MUTED).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(tg_section, text="Telegram Numarası",
                    font=("Segoe UI", 12),
                    text_color=Colors.TEXT_SECONDARY).pack(anchor="w", pady=(0, 6))

        self.phone_entry = ctk.CTkEntry(tg_section, placeholder_text="+90 5XX XXX XX XX",
                                        width=240, height=38, corner_radius=6,
                                        fg_color=Colors.BG_INPUT, border_width=1,
                                        border_color=Colors.BORDER,
                                        font=("Segoe UI", 12))
        self.phone_entry.pack(anchor="w", pady=(0, 8))

        tg_btn_frame = ctk.CTkFrame(tg_section, fg_color="transparent")
        tg_btn_frame.pack(fill="x")

        ctk.CTkButton(tg_btn_frame, text="Kaydet", width=115, height=34,
                     fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_DARK,
                     corner_radius=6, font=("Segoe UI", 12),
                     command=self.save_settings).pack(side="left", padx=(0, 8))

        ctk.CTkButton(tg_btn_frame, text="Test Et", width=115, height=34,
                     fg_color="transparent", hover_color=Colors.BG_SIDEBAR,
                     corner_radius=6, font=("Segoe UI", 12),
                     text_color=Colors.TEXT_PRIMARY, border_width=1,
                     border_color=Colors.BORDER,
                     command=lambda: self.send_telegram("Test mesajı gönderildi.")).pack(side="left")

        # Alt Kısım - AI Asistan
        spacer = ctk.CTkFrame(sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        bottom_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=20)

        self.chat_btn = ctk.CTkButton(bottom_frame, text="AI Asistan",
                                      width=240, height=44,
                                      fg_color=Colors.ACCENT, hover_color="#6D28D9",
                                      corner_radius=8, font=("Segoe UI", 13, "bold"),
                                      command=self.toggle_chat)
        self.chat_btn.pack()

    def create_main_content(self):
        main = ctk.CTkFrame(self, fg_color=Colors.BG_PRIMARY, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # Üst Bar
        topbar = ctk.CTkFrame(main, fg_color=Colors.BG_CARD, height=70, corner_radius=0)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_propagate(False)

        topbar_inner = ctk.CTkFrame(topbar, fg_color="transparent")
        topbar_inner.pack(fill="both", expand=True, padx=32, pady=16)

        ctk.CTkLabel(topbar_inner, text="Ürün Takip Paneli",
                    font=("Segoe UI", 20, "bold"),
                    text_color=Colors.TEXT_PRIMARY).pack(side="left")

        # İçerik Alanı
        content = ctk.CTkFrame(main, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=32, pady=24)
        content.grid_rowconfigure(2, weight=1)  # Ürün listesi genişleyebilir
        content.grid_columnconfigure(0, weight=1)

        # Dashboard
        self.create_dashboard(content)

        # Ürün Ekleme Kartı
        self.create_add_product_card(content)

        # Ürün Listesi
        self.create_product_list(content)

        # Alt Kontroller
        self.create_bottom_controls(content)

    def create_dashboard(self, parent):
        """Dashboard kartları - istatistikler ve özet bilgiler"""
        dash_frame = ctk.CTkFrame(parent, fg_color="transparent")
        dash_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        dash_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Label referanslarını sıfırla
        self.dash_value_labels = []
        self.dashboard_cards = []

        # İstatistik kartları
        stats = self.get_dashboard_stats()

        cards_data = [
            {
                "title": "Toplam Ürün",
                "value": str(stats["total"]),
                "subtitle": "takip ediliyor",
                "icon": "📦",
                "color": Colors.PRIMARY,
                "bg": "#EFF6FF"
            },
            {
                "title": "Aktif Takip",
                "value": "Açık" if self.is_monitoring else "Kapalı",
                "subtitle": "takip durumu",
                "icon": "🔔",
                "color": Colors.SUCCESS if self.is_monitoring else Colors.TEXT_MUTED,
                "bg": Colors.SUCCESS_LIGHT if self.is_monitoring else Colors.BG_SIDEBAR
            },
            {
                "title": "En Düşük",
                "value": f"₺{stats['lowest_price']:.0f}" if stats['lowest_price'] > 0 else "-",
                "subtitle": stats['lowest_product'][:15] if stats['lowest_product'] else "henüz veri yok",
                "icon": "📉",
                "color": Colors.SUCCESS,
                "bg": Colors.SUCCESS_LIGHT
            },
            {
                "title": "Kategoriler",
                "value": str(stats["category_count"]),
                "subtitle": "farklı kategori",
                "icon": "🏷️",
                "color": Colors.ACCENT,
                "bg": Colors.ACCENT_LIGHT
            }
        ]

        self.dashboard_cards = []
        for i, data in enumerate(cards_data):
            card = ctk.CTkFrame(dash_frame, fg_color=Colors.BG_CARD, corner_radius=12,
                               border_width=1, border_color=Colors.BORDER, height=110)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            card.grid_propagate(False)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=16, pady=14)

            # Üst satır - ikon ve başlık
            top_row = ctk.CTkFrame(inner, fg_color="transparent")
            top_row.pack(fill="x")

            icon_frame = ctk.CTkFrame(top_row, fg_color=data["bg"], width=36, height=36, corner_radius=8)
            icon_frame.pack(side="left")
            icon_frame.pack_propagate(False)
            ctk.CTkLabel(icon_frame, text=data["icon"], font=("Arial", 16)).place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkLabel(top_row, text=data["title"], font=("Segoe UI", 11),
                        text_color=Colors.TEXT_SECONDARY).pack(side="left", padx=10)

            # Ana değer
            value_label = ctk.CTkLabel(inner, text=data["value"], font=("Segoe UI", 22, "bold"),
                        text_color=data["color"])
            value_label.pack(anchor="w", pady=(8, 0))

            # Alt açıklama
            ctk.CTkLabel(inner, text=data["subtitle"], font=("Segoe UI", 10),
                        text_color=Colors.TEXT_MUTED).pack(anchor="w")

            self.dashboard_cards.append(card)
            self.dash_value_labels.append(value_label)

    def get_dashboard_stats(self):
        """Dashboard için istatistikleri hesapla"""
        products = self.db.get_active_products()
        category_stats = self.db.get_category_stats()

        # En düşük fiyatlı ürünü bul
        lowest_price = 0
        lowest_product = ""
        for p in products:
            if p['min_price'] > 0:
                if lowest_price == 0 or p['min_price'] < lowest_price:
                    lowest_price = p['min_price']
                    lowest_product = p['name']

        return {
            "total": len(products),
            "category_count": len([c for c, v in category_stats.items() if c != "Tümü" and v > 0]),
            "lowest_price": lowest_price,
            "lowest_product": lowest_product
        }

    def update_dashboard(self):
        """Dashboard kartlarını güncelle"""
        if hasattr(self, 'dashboard_cards'):
            stats = self.get_dashboard_stats()
            # Dashboard'u yeniden oluştur
            for card in self.dashboard_cards:
                card.destroy()
            # Parent'ı bul ve dashboard'u yeniden oluştur
            main_content = self.winfo_children()[1]  # Ana içerik alanı
            content = main_content.winfo_children()[1]  # İçerik frame'i
            self.create_dashboard(content)

    def refresh_dashboard_values(self):
        """Dashboard değerlerini güncelle (label referansları ile)"""
        if hasattr(self, 'dash_value_labels'):
            stats = self.get_dashboard_stats()
            # Toplam ürün
            self.dash_value_labels[0].configure(text=str(stats["total"]))
            # Aktif takip
            self.dash_value_labels[1].configure(
                text="Açık" if self.is_monitoring else "Kapalı",
                text_color=Colors.SUCCESS if self.is_monitoring else Colors.TEXT_MUTED
            )
            # En düşük fiyat
            self.dash_value_labels[2].configure(
                text=f"₺{stats['lowest_price']:.0f}" if stats['lowest_price'] > 0 else "-"
            )
            # Kategori sayısı
            self.dash_value_labels[3].configure(text=str(stats["category_count"]))

    def create_add_product_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=Colors.BG_CARD, corner_radius=12,
                           border_width=1, border_color=Colors.BORDER)
        card.grid(row=1, column=0, sticky="ew", pady=(0, 20))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=20)

        # Başlık
        ctk.CTkLabel(inner, text="Yeni Ürün Ekle",
                    font=("Segoe UI", 15, "bold"),
                    text_color=Colors.TEXT_PRIMARY).pack(anchor="w", pady=(0, 16))

        # Form satırı
        form_row = ctk.CTkFrame(inner, fg_color="transparent")
        form_row.pack(fill="x")

        # Ürün Adı
        name_frame = ctk.CTkFrame(form_row, fg_color="transparent")
        name_frame.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(name_frame, text="Ürün Adı", font=("Segoe UI", 11),
                    text_color=Colors.TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.name_entry = ctk.CTkEntry(name_frame, placeholder_text="Ürün adı girin",
                                       width=160, height=40, corner_radius=6,
                                       fg_color=Colors.BG_INPUT, border_width=1,
                                       border_color=Colors.BORDER, font=("Segoe UI", 12))
        self.name_entry.pack()

        # URL
        url_frame = ctk.CTkFrame(form_row, fg_color="transparent")
        url_frame.pack(side="left", fill="x", expand=True, padx=(0, 12))
        ctk.CTkLabel(url_frame, text="Ürün URL", font=("Segoe UI", 11),
                    text_color=Colors.TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.url_entry = ctk.CTkEntry(url_frame, placeholder_text="https://www.trendyol.com/...",
                                      height=40, corner_radius=6,
                                      fg_color=Colors.BG_INPUT, border_width=1,
                                      border_color=Colors.BORDER, font=("Segoe UI", 12))
        self.url_entry.pack(fill="x")

        # Takip Modu
        mode_frame = ctk.CTkFrame(form_row, fg_color="transparent")
        mode_frame.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(mode_frame, text="Takip Modu", font=("Segoe UI", 11),
                    text_color=Colors.TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.mode_var = ctk.StringVar(value="Fiyat")
        self.mode_menu = ctk.CTkOptionMenu(mode_frame, values=["Fiyat", "İndirim", "Stok"],
                                           variable=self.mode_var, width=110, height=40,
                                           fg_color=Colors.BG_INPUT,
                                           button_color=Colors.BORDER,
                                           button_hover_color=Colors.PRIMARY,
                                           dropdown_fg_color=Colors.BG_CARD,
                                           corner_radius=6, font=("Segoe UI", 12),
                                           command=self.toggle_price_entry)
        self.mode_menu.pack()

        # Hedef Fiyat
        price_frame = ctk.CTkFrame(form_row, fg_color="transparent")
        price_frame.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(price_frame, text="Hedef Fiyat", font=("Segoe UI", 11),
                    text_color=Colors.TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.ins_entry = ctk.CTkEntry(price_frame, placeholder_text="₺",
                                      width=100, height=40, corner_radius=6,
                                      fg_color=Colors.BG_INPUT, border_width=1,
                                      border_color=Colors.BORDER, font=("Segoe UI", 12))
        self.ins_entry.pack()

        # Kategori
        cat_frame = ctk.CTkFrame(form_row, fg_color="transparent")
        cat_frame.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(cat_frame, text="Kategori", font=("Segoe UI", 11),
                    text_color=Colors.TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.category_var = ctk.StringVar(value="Genel")
        self.category_menu = ctk.CTkOptionMenu(cat_frame, values=self.db.get_categories(),
                                               variable=self.category_var, width=110, height=40,
                                               fg_color=Colors.BG_INPUT,
                                               button_color=Colors.BORDER,
                                               button_hover_color=Colors.ACCENT,
                                               dropdown_fg_color=Colors.BG_CARD,
                                               corner_radius=6, font=("Segoe UI", 12))
        self.category_menu.pack()

        # Oto-Pilot
        autopilot_frame = ctk.CTkFrame(form_row, fg_color="transparent")
        autopilot_frame.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(autopilot_frame, text="Otomatik", font=("Segoe UI", 11),
                    text_color=Colors.TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.autopilot_var = ctk.BooleanVar(value=False)
        self.autopilot_switch = ctk.CTkSwitch(autopilot_frame, text="",
                                              variable=self.autopilot_var,
                                              progress_color=Colors.PRIMARY,
                                              button_color=Colors.TEXT_WHITE,
                                              button_hover_color=Colors.TEXT_WHITE,
                                              width=46, height=24)
        self.autopilot_switch.pack(pady=8)

        # Ekle Butonu
        self.add_btn = ctk.CTkButton(form_row, text="Ekle", width=100, height=40,
                                     fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_DARK,
                                     corner_radius=6, font=("Segoe UI", 13, "bold"),
                                     command=self.add_to_list)
        self.add_btn.pack(side="right")

    def create_product_list(self, parent):
        # Liste Kartı
        list_card = ctk.CTkFrame(parent, fg_color=Colors.BG_CARD, corner_radius=12,
                                border_width=1, border_color=Colors.BORDER)
        list_card.grid(row=2, column=0, sticky="nsew", pady=(0, 20))

        # Başlık
        header = ctk.CTkFrame(list_card, fg_color="transparent", height=56)
        header.pack(fill="x", padx=24, pady=(16, 0))

        ctk.CTkLabel(header, text="Takip Edilen Ürünler",
                    font=("Segoe UI", 15, "bold"),
                    text_color=Colors.TEXT_PRIMARY).pack(side="left")

        # Dışa Aktarma Butonları
        export_frame = ctk.CTkFrame(header, fg_color="transparent")
        export_frame.pack(side="right", padx=(0, 12))

        ctk.CTkButton(export_frame, text="CSV", width=50, height=26,
                     fg_color="transparent", hover_color=Colors.SUCCESS_LIGHT,
                     corner_radius=4, font=("Segoe UI", 10),
                     text_color=Colors.SUCCESS, border_width=1,
                     border_color=Colors.SUCCESS,
                     command=self.export_csv).pack(side="left", padx=(0, 6))

        ctk.CTkButton(export_frame, text="JSON", width=50, height=26,
                     fg_color="transparent", hover_color=Colors.INFO + "20",
                     corner_radius=4, font=("Segoe UI", 10),
                     text_color=Colors.INFO, border_width=1,
                     border_color=Colors.INFO,
                     command=self.export_json).pack(side="left")

        self.product_count = ctk.CTkLabel(header, text="0 ürün",
                                          font=("Segoe UI", 12),
                                          text_color=Colors.TEXT_MUTED,
                                          fg_color=Colors.BG_SIDEBAR,
                                          corner_radius=12, width=60, height=26)
        self.product_count.pack(side="right")

        # Kategori Filtreleme - Yatay Kaydırmalı
        filter_container = ctk.CTkFrame(list_card, fg_color="transparent", height=45)
        filter_container.pack(fill="x", padx=24, pady=(12, 0))
        filter_container.pack_propagate(False)

        # Yatay scroll frame
        filter_scroll = ctk.CTkScrollableFrame(filter_container, fg_color="transparent",
                                                orientation="horizontal", height=40,
                                                scrollbar_button_color=Colors.BORDER,
                                                scrollbar_button_hover_color=Colors.TEXT_MUTED)
        filter_scroll.pack(fill="both", expand=True)

        self.category_buttons = {}
        categories = ["Tümü"] + self.db.get_categories()

        for cat in categories:
            btn = ctk.CTkButton(filter_scroll, text=cat, height=30,
                               fg_color=Colors.PRIMARY if cat == "Tümü" else "transparent",
                               hover_color=Colors.PRIMARY_LIGHT,
                               text_color=Colors.TEXT_WHITE if cat == "Tümü" else Colors.TEXT_SECONDARY,
                               corner_radius=15, font=("Segoe UI", 11),
                               border_width=1, border_color=Colors.BORDER,
                               command=lambda c=cat: self.filter_by_category(c))
            btn.pack(side="left", padx=(0, 6))
            self.category_buttons[cat] = btn

        # Ayırıcı
        ctk.CTkFrame(list_card, fg_color=Colors.BORDER, height=1).pack(fill="x", padx=24, pady=12)

        # Liste
        self.list_frame = ctk.CTkScrollableFrame(list_card, fg_color="transparent",
                                                  scrollbar_button_color=Colors.BORDER,
                                                  scrollbar_button_hover_color=Colors.TEXT_MUTED)
        self.list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def create_bottom_controls(self, parent):
        bottom = ctk.CTkFrame(parent, fg_color="transparent")
        bottom.grid(row=3, column=0, sticky="ew")

        # Log Kartı
        log_card = ctk.CTkFrame(bottom, fg_color=Colors.BG_CARD, corner_radius=12,
                               border_width=1, border_color=Colors.BORDER, height=100)
        log_card.pack(fill="x", pady=(0, 16))
        log_card.pack_propagate(False)

        log_header = ctk.CTkFrame(log_card, fg_color="transparent")
        log_header.pack(fill="x", padx=16, pady=(12, 8))
        ctk.CTkLabel(log_header, text="Sistem Logları",
                    font=("Segoe UI", 12, "bold"),
                    text_color=Colors.TEXT_SECONDARY).pack(side="left")

        self.status_box = ctk.CTkTextbox(log_card, height=50,
                                         font=("Consolas", 11),
                                         fg_color=Colors.BG_SIDEBAR,
                                         text_color=Colors.TEXT_PRIMARY,
                                         corner_radius=6, border_width=0)
        self.status_box.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        # Kontrol Butonları
        btn_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        btn_frame.pack(fill="x")

        self.start_btn = ctk.CTkButton(btn_frame, text="Takibi Başlat", height=48,
                                       fg_color=Colors.SUCCESS, hover_color="#047857",
                                       corner_radius=8, font=("Segoe UI", 14, "bold"),
                                       command=self.start_monitoring)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.stop_btn = ctk.CTkButton(btn_frame, text="Durdur", height=48,
                                      fg_color=Colors.BG_SIDEBAR, hover_color=Colors.ERROR,
                                      text_color=Colors.TEXT_PRIMARY,
                                      corner_radius=8, font=("Segoe UI", 14, "bold"),
                                      border_width=1, border_color=Colors.BORDER,
                                      command=self.stop_monitoring)
        self.stop_btn.pack(side="left", fill="x", expand=True)

    def load_settings(self):
        self.telegram_phone = self.db.get_setting("tg_phone", "")
        if self.telegram_phone:
            self.phone_entry.insert(0, self.telegram_phone)

    def save_settings(self):
        self.telegram_phone = self.phone_entry.get().strip()
        self.db.set_setting("tg_phone", self.telegram_phone)
        self.log("Telefon numarası kaydedildi.")

    def update_connection_status(self, connected):
        self.browser_connected = connected
        if connected:
            self.status_dot.configure(text_color=Colors.SUCCESS)
            self.status_text.configure(text="Bağlı", text_color=Colors.SUCCESS)
            self.browser_btn.configure(state="disabled", text_color=Colors.TEXT_MUTED)
            self.disconnect_btn.configure(state="normal", text_color=Colors.ERROR)
        else:
            self.status_dot.configure(text_color=Colors.ERROR)
            self.status_text.configure(text="Bağlantı Yok", text_color=Colors.TEXT_SECONDARY)
            self.browser_btn.configure(state="normal", text_color=Colors.TEXT_PRIMARY)
            self.disconnect_btn.configure(state="disabled", text_color=Colors.TEXT_MUTED)

    def toggle_chat(self):
        if not hasattr(self, "chat_window") or self.chat_window is None or not self.chat_window.winfo_exists():
            self.chat_window = ctk.CTkToplevel(self)
            self.chat_window.title("AI Asistan")
            self.chat_window.geometry("400x550")
            self.chat_window.configure(fg_color=Colors.BG_CARD)
            self.chat_window.attributes("-topmost", True)

            # Header
            chat_header = ctk.CTkFrame(self.chat_window, fg_color=Colors.BG_SIDEBAR, height=60, corner_radius=0)
            chat_header.pack(fill="x")
            chat_header.pack_propagate(False)

            header_inner = ctk.CTkFrame(chat_header, fg_color="transparent")
            header_inner.pack(fill="both", expand=True, padx=20, pady=12)

            ctk.CTkLabel(header_inner, text="AI Asistan",
                        font=("Segoe UI", 16, "bold"),
                        text_color=Colors.TEXT_PRIMARY).pack(side="left")

            ctk.CTkLabel(header_inner, text="●  Aktif",
                        font=("Segoe UI", 11),
                        text_color=Colors.SUCCESS).pack(side="right")

            # Chat alanı
            self.chat_history_area = ctk.CTkScrollableFrame(self.chat_window, fg_color=Colors.BG_CARD,
                                                            scrollbar_button_color=Colors.BORDER)
            self.chat_history_area.pack(fill="both", expand=True, padx=0, pady=0)

            # Hızlı butonlar
            quick_frame = ctk.CTkFrame(self.chat_window, fg_color=Colors.BG_SIDEBAR, height=50)
            quick_frame.pack(fill="x")

            quick_inner = ctk.CTkFrame(quick_frame, fg_color="transparent")
            quick_inner.pack(fill="x", padx=16, pady=10)

            buttons = [
                ("Analiz Et",     lambda: self.show_product_selector("analiz")),
                ("Fiyat Geçmişi", lambda: self.show_product_selector("fiyat")),
                ("Sepete Ekle",   lambda: self.show_product_selector("sepet")),
            ]

            for text, cmd in buttons:
                ctk.CTkButton(quick_inner, text=text, height=30, width=110,
                             fg_color="transparent", hover_color=Colors.BG_CARD,
                             corner_radius=6, font=("Segoe UI", 11),
                             text_color=Colors.TEXT_PRIMARY,
                             border_width=1, border_color=Colors.BORDER,
                             command=cmd).pack(side="left", padx=4)

            # Input
            input_frame = ctk.CTkFrame(self.chat_window, fg_color=Colors.BG_CARD, height=70)
            input_frame.pack(fill="x", side="bottom")
            input_frame.pack_propagate(False)

            input_inner = ctk.CTkFrame(input_frame, fg_color="transparent")
            input_inner.pack(fill="x", padx=16, pady=14)

            self.chat_input = ctk.CTkEntry(input_inner, placeholder_text="Mesajınızı yazın...",
                                           height=42, corner_radius=8,
                                           fg_color=Colors.BG_INPUT, border_width=1,
                                           border_color=Colors.BORDER,
                                           font=("Segoe UI", 12))
            self.chat_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
            self.chat_input.bind("<Return>", lambda e: self.send_chat_message())

            self.chat_send_btn = ctk.CTkButton(input_inner, text="→", width=42, height=42,
                                               fg_color=Colors.PRIMARY, hover_color=Colors.PRIMARY_DARK,
                                               corner_radius=8, font=("Arial", 18),
                                               command=self.send_chat_message)
            self.chat_send_btn.pack(side="right")

            self.chat_btn.configure(text="Kapat", fg_color=Colors.TEXT_MUTED)
            self.update_chat_history("Asistan", "Merhaba! Size nasıl yardımcı olabilirim?")
        else:
            self.chat_window.destroy()
            self.chat_window = None
            self.chat_btn.configure(text="AI Asistan", fg_color=Colors.ACCENT)

    def send_chat_message(self):
        msg = self.chat_input.get().strip()
        if not msg:
            return

        self.update_chat_history("Siz", msg)
        self.chat_input.delete(0, 'end')

        def process_ai():
            try:
                lower_msg = msg.lower()

                sepet_keywords  = ["sepete ekle", "sepete at", "satın al", "almak istiyorum",
                                   "sipariş ver", "satın almak", "ekle", "buy"]
                analiz_keywords = ["analiz", "değer mi", "pahalı mı", "ucuz mu",
                                   "özellik", "mantıklı", "incele"]
                fiyat_keywords  = ["fiyat geçmişi", "fiyat geçmis", "geçmiş fiyat",
                                   "fiyatlar", "fiyat tarih"]

                if any(w in lower_msg for w in sepet_keywords):
                    self.after(0, lambda: self.show_product_selector("sepet"))
                elif any(w in lower_msg for w in fiyat_keywords):
                    self.after(0, lambda: self.show_product_selector("fiyat"))
                elif any(w in lower_msg for w in analiz_keywords):
                    self.after(0, lambda: self.show_product_selector("analiz"))
                else:
                    if self.agent is None:
                        from analiz_motoru2 import SmartShoppingAgent
                        self.agent = SmartShoppingAgent()
                    res = self.agent._get_groq_response(msg)
                    self.after(0, lambda: self.update_chat_history("Asistan", res))
            except Exception as e:
                self.after(0, lambda: self.update_chat_history("Sistem", f"Hata: {str(e)}"))

        threading.Thread(target=process_ai, daemon=True).start()

    def quick_action(self, msg):
        if hasattr(self, "chat_input") and self.chat_input.winfo_exists():
            self.chat_input.delete(0, 'end')
            self.chat_input.insert(0, msg)
            self.send_chat_message()

    def show_product_selector(self, action_type):
        """Chat alanında takip listesindeki ürünleri buton olarak gösterir."""
        if not hasattr(self, "chat_history_area") or not self.chat_history_area.winfo_exists():
            return

        questions = {
            "sepet": "Hangi ürünü sepete eklememi istiyorsunuz?",
            "analiz": "Hangi ürünü analiz etmemi istiyorsunuz?",
            "fiyat": "Hangi ürünün fiyat geçmişini görmek istiyorsunuz?",
        }
        self.update_chat_history("Asistan", questions.get(action_type, "Hangi üründen bahsediyorsunuz?"))

        products = self.db.get_active_products()
        if not products:
            self.update_chat_history("Asistan", "Takip listesinde henüz ürün bulunmuyor.")
            return

        container = ctk.CTkFrame(self.chat_history_area, fg_color="transparent")
        container.pack(fill="x", pady=(0, 8), padx=16, anchor="w")

        for product in products:
            p = product
            name_display = p["name"][:45] + ("…" if len(p["name"]) > 45 else "")
            ctk.CTkButton(
                container,
                text=name_display,
                height=34,
                anchor="w",
                fg_color=Colors.BG_SIDEBAR,
                hover_color=Colors.BORDER,
                text_color=Colors.TEXT_PRIMARY,
                font=("Segoe UI", 11),
                border_width=1,
                border_color=Colors.BORDER,
                corner_radius=8,
                command=lambda prod=p: self.execute_action_on_product(prod, action_type),
            ).pack(fill="x", pady=2)

        self.chat_history_area._parent_canvas.yview_moveto(1.0)

    def execute_action_on_product(self, product, action_type):
        """Seçilen ürün üzerinde istenilen eylemi gerçekleştirir."""
        self.update_chat_history("Siz", product["name"])

        def _run():
            try:
                if action_type in ("sepet", "analiz"):
                    if not self.browser_connected or not self.agent or not self.agent.driver:
                        self.after(0, lambda: self.update_chat_history(
                            "Asistan", "Bu işlem için önce tarayıcıyı başlatın."))
                        return
                    self.agent.driver.get(product["url"])
                    time.sleep(2.5)

                if action_type == "sepet":
                    selectors = (
                        ".add-to-basket, .add-to-cart-button, "
                        "[class*='addToBasket'], [class*='add-to-basket'], "
                        "button[class*='sepet'], button[class*='basket']"
                    )
                    try:
                        btn = self.agent.driver.find_element(By.CSS_SELECTOR, selectors)
                        self.agent.driver.execute_script("arguments[0].click();", btn)
                        name = product["name"]
                        self.after(0, lambda: self.update_chat_history(
                            "Asistan", f"{name} sepete eklendi!"))
                    except Exception:
                        self.after(0, lambda: self.update_chat_history(
                            "Asistan", "Sepet butonu bulunamadı. Ürün stokta olmayabilir."))

                elif action_type == "analiz":
                    res = self.agent.get_market_analysis()
                    self.after(0, lambda: self.update_chat_history("Asistan", res))

                elif action_type == "fiyat":
                    history = self.db.get_price_history(product["url"], limit=5)
                    if history:
                        lines = [f"{product['name']} – Son Fiyatlar:"]
                        for h in reversed(history):
                            ts = h["timestamp"][:10]
                            lines.append(f"  {ts}: ₺{h['price']}")
                        self.after(0, lambda: self.update_chat_history("Asistan", "\n".join(lines)))
                    else:
                        self.after(0, lambda: self.update_chat_history(
                            "Asistan", "Bu ürün için henüz fiyat geçmişi yok."))

            except Exception as e:
                err = str(e)
                self.after(0, lambda: self.update_chat_history("Sistem", f"Hata: {err}"))

        threading.Thread(target=_run, daemon=True).start()

    def update_chat_history(self, sender, text):
        if hasattr(self, "chat_history_area") and self.chat_history_area.winfo_exists():
            is_user = (sender == "Siz")

            bubble_frame = ctk.CTkFrame(self.chat_history_area, fg_color="transparent")
            bubble_frame.pack(fill="x", pady=8, padx=16)

            if is_user:
                bg_color = Colors.PRIMARY
                text_color = Colors.TEXT_WHITE
            elif sender == "Sistem":
                bg_color = Colors.ERROR_LIGHT
                text_color = Colors.ERROR
            else:
                bg_color = Colors.BG_SIDEBAR
                text_color = Colors.TEXT_PRIMARY

            msg_bubble = ctk.CTkFrame(bubble_frame, fg_color=bg_color, corner_radius=12)
            msg_bubble.pack(side="right" if is_user else "left")

            lbl = ctk.CTkLabel(msg_bubble, text=text, font=("Segoe UI", 12),
                              wraplength=280, justify="left", text_color=text_color)
            lbl.pack(padx=14, pady=10)

            self.chat_history_area._parent_canvas.yview_moveto(1.0)

    def launch_browser(self):
        self.log("Tarayıcı başlatılıyor...")

        def _start():
            try:
                if self.agent is None:
                    self.agent = SmartShoppingAgent()

                if self.agent.driver:
                    self.after(0, lambda: self.update_connection_status(True))
                    self.after(0, lambda: self.log("Tarayıcı hazır. Trendyol'a giriş yapabilirsiniz."))
                    # Trendyol ana sayfasını aç
                    self.agent.driver.get("https://www.trendyol.com")
                else:
                    self.after(0, lambda: self.log("Tarayıcı başlatılamadı."))
            except Exception as e:
                self.after(0, lambda: self.log(f"Hata: {e}"))

        threading.Thread(target=_start, daemon=True).start()

    def disconnect_browser(self):
        self.log("Tarayıcı bağlantısı kesiliyor...")

        def _stop():
            try:
                if self.agent:
                    self.agent.close()
                    self.agent = None
                self.after(0, lambda: self.update_connection_status(False))
                self.after(0, lambda: self.log("Tarayıcı bağlantısı kesildi."))
            except Exception as e:
                self.after(0, lambda: self.log(f"Bağlantı kesme hatası: {e}"))
                self.after(0, lambda: self.update_connection_status(False))

        threading.Thread(target=_stop, daemon=True).start()

    def send_telegram(self, message):
        phone = self.db.get_setting("tg_phone", "")

        if not phone:
            self.log("Lütfen telefon numaranızı kaydedin.")
            return

        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            session_name = f"session_{phone.replace('+', '')}"
            try:
                client = TelegramClient(session_name, TELEGRAM_API_ID, TELEGRAM_API_HASH)
                client.connect()

                if not client.is_user_authorized():
                    client.send_code_request(phone)
                    diag = CodeInputDialog(self, phone)
                    self.wait_window(diag)
                    if diag.result:
                        client.sign_in(phone, diag.result)
                    else:
                        self.log("Onay kodu girilmedi.")
                        return

                client.send_message('me', message, parse_mode='html')
                client.disconnect()
                self.log("Telegram mesajı gönderildi.")
            except Exception as e:
                self.log(f"Telegram hatası: {e}")
            finally:
                loop.close()

        threading.Thread(target=_run, daemon=True).start()

    def filter_by_category(self, category):
        """Kategoriye göre filtreleme"""
        self.current_category = category

        # Buton stillerini güncelle
        for cat, btn in self.category_buttons.items():
            if cat == category:
                btn.configure(fg_color=Colors.PRIMARY, text_color=Colors.TEXT_WHITE)
            else:
                btn.configure(fg_color="transparent", text_color=Colors.TEXT_SECONDARY)

        self.render_list()

    def toggle_price_entry(self, choice):
        if choice == "Fiyat":
            self.ins_entry.configure(state="normal", fg_color=Colors.BG_INPUT)
        else:
            self.ins_entry.delete(0, 'end')
            self.ins_entry.configure(state="disabled", fg_color=Colors.BG_SIDEBAR)

    def log(self, message):
        timestamp = time.strftime('%H:%M:%S')
        self.after(0, lambda: self.status_box.insert("end", f"[{timestamp}] {message}\n"))
        self.after(0, lambda: self.status_box.see("end"))

    def add_to_list(self):
        current_mode = self.mode_var.get()
        name = self.name_entry.get().strip() or f"Ürün {len(self.products) + 1}"
        url = self.url_entry.get().strip()

        if not url:
            self.log("Lütfen URL girin.")
            return

        target_price = 0
        if current_mode == "Fiyat":
            try:
                target_price = float(re.findall(r'\d+', self.ins_entry.get())[0])
            except:
                self.log("Geçersiz fiyat girdiniz.")
                return

        success = self.db.add_product({
            "name": name, "url": url, "mode": current_mode,
            "target": target_price, "autopilot": int(self.autopilot_var.get()),
            "category": self.category_var.get()
        })

        if success:
            with self.lock:
                self.products = self.db.get_active_products()
            self.render_list()
            self.name_entry.delete(0, 'end')
            self.url_entry.delete(0, 'end')
            self.ins_entry.delete(0, 'end')
            self.log(f"{name} listeye eklendi.")
        else:
            self.log("Bu ürün zaten listede.")

    def render_list(self):
        def _update():
            for widget in self.list_frame.winfo_children():
                widget.destroy()

            # Dashboard'u güncelle
            self.refresh_dashboard_values()

            with self.lock:
                # Kategoriye göre filtrele
                if self.current_category == "Tümü":
                    filtered_products = self.products
                else:
                    filtered_products = [p for p in self.products if p.get('category', 'Genel') == self.current_category]

                count = len(filtered_products)
                self.product_count.configure(text=f"{count} ürün")

                if not filtered_products:
                    empty_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
                    empty_frame.pack(fill="both", expand=True, pady=60)
                    if self.current_category == "Tümü":
                        ctk.CTkLabel(empty_frame, text="Henüz ürün eklenmedi",
                                    font=("Segoe UI", 14),
                                    text_color=Colors.TEXT_MUTED).pack()
                        ctk.CTkLabel(empty_frame, text="Yukarıdaki formu kullanarak ürün ekleyebilirsiniz",
                                    font=("Segoe UI", 12),
                                    text_color=Colors.TEXT_MUTED).pack(pady=4)
                    else:
                        ctk.CTkLabel(empty_frame, text=f"'{self.current_category}' kategorisinde ürün yok",
                                    font=("Segoe UI", 14),
                                    text_color=Colors.TEXT_MUTED).pack()
                    return

                for p in filtered_products:
                    card = ctk.CTkFrame(self.list_frame, fg_color=Colors.BG_SIDEBAR,
                                       corner_radius=8, height=72)
                    card.pack(fill="x", pady=4, padx=4)
                    card.pack_propagate(False)

                    inner = ctk.CTkFrame(card, fg_color="transparent")
                    inner.pack(fill="both", expand=True, padx=16, pady=12)

                    # Sol - Bilgiler
                    left = ctk.CTkFrame(inner, fg_color="transparent")
                    left.pack(side="left", fill="y")

                    name_row = ctk.CTkFrame(left, fg_color="transparent")
                    name_row.pack(anchor="w")

                    ctk.CTkLabel(name_row, text=p['name'][:35],
                                font=("Segoe UI", 13, "bold"),
                                text_color=Colors.TEXT_PRIMARY).pack(side="left")

                    # Kategori rozeti
                    cat = p.get('category', 'Genel')
                    cat_colors = {
                        "Elektronik": "#3B82F6",
                        "Giyim": "#EC4899",
                        "Ev & Yaşam": "#10B981",
                        "Kozmetik": "#F59E0B",
                        "Spor": "#8B5CF6",
                        "Kitap & Hobi": "#6366F1",
                        "Bebek": "#F472B6",
                        "Diğer": "#6B7280",
                        "Genel": "#9CA3AF"
                    }
                    ctk.CTkLabel(name_row, text=cat,
                                font=("Segoe UI", 9),
                                text_color=Colors.TEXT_WHITE,
                                fg_color=cat_colors.get(cat, "#9CA3AF"),
                                corner_radius=4).pack(side="left", padx=8)

                    if p.get('autopilot'):
                        ctk.CTkLabel(name_row, text="OTOMATİK",
                                    font=("Segoe UI", 9, "bold"),
                                    text_color=Colors.TEXT_WHITE,
                                    fg_color=Colors.WARNING,
                                    corner_radius=4).pack(side="left", padx=4)

                    mode_text = f"Hedef: ₺{p['target']}" if p['mode'] == "Fiyat" else f"Mod: {p['mode']}"
                    ctk.CTkLabel(left, text=mode_text, font=("Segoe UI", 11),
                                text_color=Colors.TEXT_SECONDARY).pack(anchor="w", pady=(2, 0))

                    # Sağ - Fiyat ve Sil
                    right = ctk.CTkFrame(inner, fg_color="transparent")
                    right.pack(side="right", fill="y")

                    price_frame = ctk.CTkFrame(right, fg_color="transparent")
                    price_frame.pack(side="left", padx=(0, 16))

                    if p['last_price'] > 0:
                        ctk.CTkLabel(price_frame, text=f"₺{p['last_price']:.2f}",
                                    font=("Segoe UI", 15, "bold"),
                                    text_color=Colors.SUCCESS).pack(anchor="e")
                    ctk.CTkLabel(price_frame, text=f"Min: ₺{p['min_price']:.2f}",
                                font=("Segoe UI", 10),
                                text_color=Colors.TEXT_MUTED).pack(anchor="e")

                    ctk.CTkButton(right, text="Sil", width=60, height=32,
                                 fg_color="transparent", hover_color=Colors.ERROR_LIGHT,
                                 corner_radius=6, font=("Segoe UI", 11),
                                 text_color=Colors.ERROR,
                                 border_width=1, border_color=Colors.ERROR,
                                 command=lambda u=p['url']: self.manual_remove(u)).pack(side="right")

        self.after(0, _update)

    def manual_remove(self, url):
        self.db.delete_product(url)
        with self.lock:
            self.products = self.db.get_active_products()
        self.render_list()
        self.log("Ürün silindi.")

    def export_json(self):
        """Ürün listesini JSON olarak dışa aktar"""
        if not self.products:
            self.log("Dışa aktarılacak ürün yok.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"urunler_{timestamp}.json"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON dosyası", "*.json"), ("Tüm dosyalar", "*.*")],
            initialfile=default_name,
            title="JSON Olarak Kaydet"
        )

        if not file_path:
            return

        try:
            export_data = {
                "export_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_products": len(self.products),
                "products": []
            }

            for p in self.products:
                export_data["products"].append({
                    "name": p["name"],
                    "url": p["url"],
                    "mode": p["mode"],
                    "target": p["target"],
                    "autopilot": p["autopilot"],
                    "min_price": p["min_price"],
                    "last_price": p["last_price"],
                    "category": p.get("category", "Genel")
                })

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            self.log(f"JSON olarak kaydedildi: {os.path.basename(file_path)}")
        except Exception as e:
            self.log(f"JSON kaydetme hatası: {e}")

    def export_csv(self):
        """Ürün listesini CSV olarak dışa aktar"""
        if not self.products:
            self.log("Dışa aktarılacak ürün yok.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"urunler_{timestamp}.csv"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV dosyası", "*.csv"), ("Tüm dosyalar", "*.*")],
            initialfile=default_name,
            title="CSV Olarak Kaydet"
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                # Başlık satırı
                writer.writerow([
                    "Ürün Adı", "URL", "Takip Modu", "Hedef Fiyat",
                    "Otomatik", "En Düşük Fiyat", "Son Fiyat", "Kategori"
                ])
                # Veriler
                for p in self.products:
                    writer.writerow([
                        p["name"],
                        p["url"],
                        p["mode"],
                        p["target"],
                        "Evet" if p["autopilot"] else "Hayır",
                        p["min_price"],
                        p["last_price"],
                        p.get("category", "Genel")
                    ])

            self.log(f"CSV olarak kaydedildi: {os.path.basename(file_path)}")
        except Exception as e:
            self.log(f"CSV kaydetme hatası: {e}")

    def start_monitoring(self):
        if not self.products:
            self.log("Takip listesi boş.")
            return
        self.is_monitoring = True
        self.start_btn.configure(state="disabled", text="Takip Ediliyor...", fg_color=Colors.WARNING)
        self.refresh_dashboard_values()
        threading.Thread(target=self.monitoring_thread, daemon=True).start()

    def stop_monitoring(self):
        self.is_monitoring = False
        self.start_btn.configure(state="normal", text="Takibi Başlat", fg_color=Colors.SUCCESS)
        self.refresh_dashboard_values()
        self.log("Takip durduruldu.")

    def monitoring_thread(self):
        try:
            if not self.agent:
                self.agent = SmartShoppingAgent()
                if self.agent.driver:
                    self.after(0, lambda: self.update_connection_status(True))
        except Exception as e:
            self.log(f"Bağlantı hatası: {e}")
            self.stop_monitoring()
            return

        while self.is_monitoring:
            with self.lock:
                items_to_check = list(self.products)

            for product in items_to_check:
                if not self.is_monitoring:
                    break
                if not any(p['url'] == product['url'] for p in self.products):
                    continue

                self.log(f"Kontrol: {product['name']}")
                try:
                    self.agent.driver.get(product['url'])
                    time.sleep(4)
                except:
                    self.log("Tarayıcı bağlantısı kesildi.")
                    self.after(0, lambda: self.update_connection_status(False))
                    self.stop_monitoring()
                    break

                c_price = 0
                selectors = [
                    "span.ty-plus-price-discounted-price",
                    ".product-price-container .selling-price",
                    ".prc-slg", ".prc-dsc",
                    "span.discounted",
                    ".product-price-container",
                    "div[class*='price']"
                ]

                for sel in selectors:
                    try:
                        elements = self.agent.driver.find_elements(By.CSS_SELECTOR, sel)
                        for el in elements:
                            if el.is_displayed() and el.text:
                                clean_text = el.text.replace(".", "").replace(",", ".")
                                price_match = re.findall(r"\d+\.\d+|\d+", clean_text)
                                if price_match:
                                    c_price = min([float(p) for p in price_match if float(p) > 0])
                                    break
                        if c_price > 0:
                            break
                    except:
                        continue

                if c_price > 0:
                    new_min = c_price if product['min_price'] == 0 else min(c_price, product['min_price'])
                    self.db.update_price(product['url'], c_price, new_min)
                    product['min_price'], product['last_price'] = new_min, c_price

                    alert = False
                    if product['mode'] == "Fiyat" and c_price <= product['target']:
                        alert = True
                    elif product['mode'] == "İndirim" and product['last_price'] > 0 and c_price < product['last_price']:
                        alert = True
                    elif product['mode'] == "Stok":
                        try:
                            if not self.agent.driver.find_elements(By.CSS_SELECTOR, ".passive, .sold-out"):
                                alert = True
                        except:
                            pass

                    self.render_list()
                    if alert:
                        self.log(f"HEDEF: {product['name']} (₺{c_price})")
                        self.send_telegram(f"<b>{product['name']}</b>\nFiyat: ₺{c_price}\n{product['url']}")
                        if product.get('autopilot'):
                            self.execute_buy(product)
                            self.db.move_to_history(product, status="OTO-SEPET")
                        else:
                            self.after(0, lambda p=product: self.show_popup(p))
                            self.db.move_to_history(product, status="MANUEL")
                        with self.lock:
                            self.products = self.db.get_active_products()
                        self.render_list()
                else:
                    self.log(f"{product['name']} - Fiyat okunamadı")

            if self.is_monitoring:
                time.sleep(15)

    def execute_buy(self, product):
        try:
            btn = self.agent.driver.find_element(By.CSS_SELECTOR, ".add-to-basket, .add-to-cart-button")
            self.agent.driver.execute_script("arguments[0].click();", btn)
            self.log(f"Otomatik sepete eklendi: {product['name']}")
            self.send_telegram(f"<b>{product['name']}</b> sepete eklendi!")
        except:
            self.log("Sepet butonu bulunamadı.")

    def show_popup(self, product):
        def on_confirm(choice):
            if choice:
                self.execute_buy(product)

        ConfirmationPopup(self, "Hedef Fiyat",
                         f"{product['name']} belirlediğiniz hedefe ulaştı.", on_confirm)


if __name__ == "__main__":
    app = AgentGUI()
    app.mainloop()
