# OKUYUCU: Veri hattının asıl işi. ESP32'den gelen satırları, diğer katmanların
#   anlayacağı kayıtlara çevirir ve onlara teslim eder.
#
# BU KLASÖR (okuyucu/): Veri bu sırayla dört alt katmandan geçer: al → anla → çevir →
#   teslim et.
#
# AYRINTI:
#   baglanti/     1. kablodan gelen satırları alır
#   ayristirma/   2. satırı parçalarına ayırır, kurala uyuyor mu diye kontrol eder
#   donusturme/   3. asıl çeviri: ham sayı → birim, ESP32 saati → bilgisayar saati
#   dagitim/      4. sonucu dosyalara yazar, ekrana özet basar
#   Alt katmanlar birbirini kullanmaz; hepsini __main__.py birbirine bağlar. Bu sayede
#   bir alt katman değişince diğerleri bozulmaz. Çalıştırmak için (veri_hatti
#   klasöründen): .venv/bin/python -m okuyucu
