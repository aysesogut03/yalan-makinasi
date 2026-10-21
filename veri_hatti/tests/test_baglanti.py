# TESTLER: Otomatik kontroller. Veri hattının her parçasının doğru çalıştığını denetler.
#   Çalıştırmak için (veri_hatti klasöründen): .venv/bin/python -m unittest -v
#
# BU DOSYA (tests/test_baglanti.py): Bağlantıyı denetler: baytlar doğru satırlara
#   ayrılıyor mu?
#
# AYRINTI: Bir test sunucusu baytları parça parça gönderir. Parçalanmış satırların
#   birleştirildiğini, satır sonu gelmeyen verinin sonsuza dek birikmediğini ve kapalı
#   bir adrese bağlanılamadığını denetler. pyserial kurulu değilse atlanır.

import importlib.util
import socket
import threading
import time
import unittest

PYSERIAL_VAR = importlib.util.find_spec("serial") is not None


@unittest.skipUnless(PYSERIAL_VAR, "pyserial kurulu değil (README.md, 7. bölüm)")
class SeriKaynakTestleri(unittest.TestCase):
    def satirlari_al(self, *parcalar: bytes) -> list[str]:
        from okuyucu.baglanti.seri_kaynak import SeriKaynak

        with socket.create_server(("127.0.0.1", 0)) as sunucu:
            kapi = sunucu.getsockname()[1]

            def gonderici():
                baglanti, _ = sunucu.accept()
                with baglanti:
                    for parca in parcalar:
                        baglanti.sendall(parca)
                        time.sleep(0.05)

            is_parcacigi = threading.Thread(target=gonderici)
            is_parcacigi.start()
            kaynak = SeriKaynak(f"socket://127.0.0.1:{kapi}")
            try:
                satirlar = list(kaynak.satirlar())
            finally:
                kaynak.kapat()
            is_parcacigi.join(timeout=2)
        return satirlar

    def test_parca_parca_gelen_satirlar_birlestirilir(self):
        self.assertEqual(self.satirlari_al(b"B,1,8", b"00\r\nB,2,1600\n"), ["B,1,800", "B,2,1600"])

    def test_satir_sonu_gelmeyen_veri_sonsuza_dek_birikmez(self):
        from okuyucu.baglanti.seri_kaynak import EN_UZUN_SATIR

        satirlar = self.satirlari_al(b"x" * (EN_UZUN_SATIR + 500))
        self.assertEqual(len(satirlar), 1)
        self.assertGreater(len(satirlar[0]), EN_UZUN_SATIR)

    def test_kapali_adrese_baglanilamaz(self):
        from okuyucu.baglanti.seri_kaynak import BaglantiKurulamadi, SeriKaynak

        with socket.create_server(("127.0.0.1", 0)) as gecici:
            kapi = gecici.getsockname()[1]
        with self.assertRaises(BaglantiKurulamadi):
            SeriKaynak(f"socket://127.0.0.1:{kapi}")


if __name__ == "__main__":
    unittest.main()
