# TESTLER: Otomatik kontroller. Veri hattının her parçasının doğru çalıştığını denetler.
#   Çalıştırmak için (veri_hatti klasöründen): .venv/bin/python -m unittest -v
#
# BU DOSYA (tests/test_ayristirma.py): Ayrıştırmayı denetler: doğru satırlar kabul,
#   bozuklar reddediliyor mu?
#
# AYRINTI: Her satır türünün doğru mesaja çevrildiğini, 18 farklı bozuk satır örneğinin
#   nedeniyle reddedildiğini ve sahte ESP32'nin ürettiği her satırın sorunsuz
#   ayrıştırıldığını denetler.

import unittest

from okuyucu.kurallar import BozukSatir
from okuyucu.ayristirma import ProtokolV1Ayristirici
from okuyucu.mesajlar import AtimMesaji, BilgiMesaji, HataMesaji, OlcumMesaji
from tests.test_simulator import sahte_esp32_satirlari


class DogruSatirTestleri(unittest.TestCase):
    def setUp(self):
        self.ayristirici = ProtokolV1Ayristirici()

    def test_olcum_satiri(self):
        mesaj = self.ayristirici.ayristir("S,1042,20840,1475,-412,215,16120,-35,12,4")
        self.assertEqual(mesaj, OlcumMesaji(1042, 20840, 1475, -412, 215, 16120, -35, 12, 4))

    def test_atim_satiri(self):
        self.assertEqual(self.ayristirici.ayristir("B,1043,20851"), AtimMesaji(1043, 20851))

    def test_hata_satiri(self):
        self.assertEqual(self.ayristirici.ayristir("E,1044,20860,MPU_YOK"), HataMesaji(1044, 20860, "MPU_YOK"))

    def test_bilgi_satiri(self):
        mesaj = self.ayristirici.ayristir("I,0,312,v=1,hz=50,acc=2,gyro=250")
        self.assertEqual(mesaj, BilgiMesaji(seq=0, ms=312, surum=1, hz=50, acc_g=2, gyro_dps=250))

    def test_bilgi_satirinda_sira_onemsiz_ve_ek_alan_yok_sayilir(self):
        mesaj = self.ayristirici.ayristir("I,0,312,gyro=250,isim=deneme,acc=2,hz=50,v=1")
        self.assertEqual(mesaj, BilgiMesaji(seq=0, ms=312, surum=1, hz=50, acc_g=2, gyro_dps=250))

    def test_arduino_satir_sonu_kabul_edilir(self):
        self.assertEqual(self.ayristirici.ayristir("B,1043,20851\r"), AtimMesaji(1043, 20851))


class BozukSatirTestleri(unittest.TestCase):
    BOZUK_SATIRLAR = [
        ("boş satır", "", "boş"),
        ("bağlanınca ortasından yakalanmış satır", "16120,-35,12,4", "bilinmeyen mesaj türü"),
        ("yarım gelmiş satır", "S,1042,20840,1475,-412", "10 alan olmalı"),
        ("fazla alan", "S,1042,20840,1475,-412,215,16120,-35,12,4,99", "10 alan olmalı"),
        ("sayıda harf", "S,1042,20840,14x5,-412,215,16120,-35,12,4", "gsr tam sayı değil"),
        ("boşluk", "S,1042,20840,1475,-412,215,16120,-35,12, 4", "tam sayı değil"),
        ("bilinmeyen tür", "X,1,2", "bilinmeyen mesaj türü"),
        ("küçük harf tür", "s,1042,20840,1475,-412,215,16120,-35,12,4", "bilinmeyen mesaj türü"),
        ("GSR aralık dışı", "S,1042,20840,9999,-412,215,16120,-35,12,4", "gsr"),
        ("ivme 16 bit dışı", "S,1042,20840,1475,40000,215,16120,-35,12,4", "ax"),
        ("negatif sıra numarası", "S,-1,20840,1475,-412,215,16120,-35,12,4", "seq"),
        ("atımda ms eksik", "B,1043", "3 alan olmalı"),
        ("geçersiz hata kodu", "E,1044,20860,mpu yok", "hata kodu"),
        ("boş hata kodu", "E,1044,20860,", "hata kodu"),
        ("bilgi satırında eksik alan", "I,0,312,v=1,hz=50,acc=2", "gyro"),
        ("bilgi satırında = yok", "I,0,312,v=1,hz=50,acc=2,gyro", "ad=değer"),
        ("desteklenmeyen sürüm", "I,0,312,v=2,hz=50,acc=2,gyro=250", "sürüm"),
        ("sıfır ölçüm hızı", "I,0,312,v=1,hz=0,acc=2,gyro=250", "hz"),
    ]

    def test_bozuk_satirlar_reddedilir(self):
        ayristirici = ProtokolV1Ayristirici()
        for neden, satir, beklenen_soz in self.BOZUK_SATIRLAR:
            with self.subTest(neden):
                with self.assertRaises(BozukSatir) as hata:
                    ayristirici.ayristir(satir)
                self.assertIn(beklenen_soz, str(hata.exception))


class SahteEsp32UyumTesti(unittest.TestCase):
    def test_sahte_esp32_satirlarinin_hepsi_ayristirilir(self):
        ayristirici = ProtokolV1Ayristirici()
        tur_harfi = {BilgiMesaji: "I", OlcumMesaji: "S", AtimMesaji: "B", HataMesaji: "E"}
        satirlar = sahte_esp32_satirlari(30.0)
        for satir in satirlar:
            mesaj = ayristirici.ayristir(satir)
            self.assertEqual(tur_harfi[type(mesaj)], satir[0])


if __name__ == "__main__":
    unittest.main()
