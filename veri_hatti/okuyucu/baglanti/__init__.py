# OKUYUCU: Veri hattının asıl işi. ESP32'den gelen satırları, diğer katmanların
#   anlayacağı kayıtlara çevirir ve onlara teslim eder.
#
# BU KLASÖR (okuyucu/baglanti/): 1. alt katman. Kablodan (şimdilik sahte ESP32'den)
#   gelen satırları alır.
#
# AYRINTI: İçinde seri_kaynak.py var. Bağlantı türü değişirse (örneğin kablosuz) buraya
#   yeni bir dosya eklenir, diğer alt katmanlar değişmez. pyserial yalnızca gerçekten
#   bağlanırken gereksin diye bu dosya hiçbir şeyi içe aktarmaz. Kullanmak için: from
#   okuyucu.baglanti.seri_kaynak import SeriKaynak
