# Bu dosya veritabanı bağlantılarını temsil eder.

# KULLANICILAR (Arayüzden giriş yapabilecek admin hesabı)
KULLANICILAR_DB = {
    "admin": {
        "username": "admin",
        "full_name": "Sistem Yöneticisi",
        "password": "123"  # Test için geçici şifre
    }
}

# KATILIMCILAR (Participants.tsx için geçici liste)
KATILIMCILAR_DB = [
    {"id": 1, "ad_soyad": "Ahmet Yılmaz", "yas": 25, "cinsiyet": "Erkek", "test_sayisi": 2},
    {"id": 2, "ad_soyad": "Ayşe Kaya", "yas": 30, "cinsiyet": "Kadın", "test_sayisi": 1}
]

# OTURUMLAR / TEST SONUÇLARI (LiveMeasure.tsx ve SessionHistory.tsx sonuç kaydı)
OTURUMLAR_DB = [
    {
        "id": 1,
        "katilimci_id": 1,
        "test_adi": "Kontrol Grubu Poligraf Testi",
        "notlar": "Sakin ve stabil bir oturum gerçekleşti.",
        "ortalama_bpm": 72.5,
        "ortalama_gsr": 1.45,
        "yalan_skoru": 12.0
    },
    {
        "id": 2,
        "katilimci_id": 2,
        "test_adi": "Stres Tepkisi Uyaran Testi",
        "notlar": "3. soruda belirgin GSR ve nabız yükselmesi gözlendi.",
        "ortalama_bpm": 86.4,
        "ortalama_gsr": 2.15,
        "yalan_skoru": 64.0
    }
]