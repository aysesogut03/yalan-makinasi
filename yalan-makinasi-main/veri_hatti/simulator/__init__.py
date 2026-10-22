# SİMÜLATÖR: Sahte ESP32. Kart gelene kadar gerçek ESP32'nin yerine veri üretir.
#
# BU KLASÖR (simulator/): Sensörleri okuyormuş gibi davranıp protokol satırları
#   gönderir.
#
# AYRINTI:
#   sensorler.py   sahte GSR, ivmeölçer ve nabız değerleri üretir
#   cihaz.py       ESP32'nin "beyni": hangi satırı ne zaman göndereceğine karar verir
#   protokol.py    sayıları "S,1042,20840,..." gibi satırlara yazar
#   tcp.py         USB kablosunun yerini tutar: satırları okuyucuya iletir
#   kurallar.py    parçaların uyması gereken kurallar
#   __main__.py    başlangıç dosyası: parçaları kurar ve çalıştırır
#   Okuyucuyla hiç kod paylaşmaz; ikisini birleştiren tek şey satırların biçimi.
#   Çalıştırmak için (veri_hatti klasöründen): python3 -m simulator
