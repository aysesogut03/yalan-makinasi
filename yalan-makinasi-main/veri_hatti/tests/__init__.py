# TESTLER: Otomatik kontroller. Veri hattının her parçasının doğru çalıştığını denetler.
#   Çalıştırmak için (veri_hatti klasöründen): .venv/bin/python -m unittest -v
#
# BU KLASÖR (tests/): Her dosyanın adı, hangi parçayı denetlediğini söyler.
#
# AYRINTI:
#   test_simulator.py    sahte ESP32
#   test_baglanti.py     bağlantı (1. alt katman)
#   test_ayristirma.py   ayrıştırma (2. alt katman)
#   test_donusturme.py   dönüştürme (3. alt katman)
#   test_dagitim.py      dağıtım (4. alt katman)
#   test_hat.py          bant (hat.py)
#   test_sozlesme.py     sözleşme
#   test_uctan_uca.py    hepsi birlikte: sahte ESP32 → okuyucu → dosyalar
#   test_hatali_veri.py  gerçek program, bilerek hatalı veriyle ve bağlantı kopmasıyla
#   pyserial kurulu değilse (python3 -m unittest) bağlantıyla ilgili testler atlanır.
