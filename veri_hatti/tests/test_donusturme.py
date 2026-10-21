# TESTLER: Otomatik kontroller. Veri hattının her parçasının doğru çalıştığını denetler.
#   Çalıştırmak için (veri_hatti klasöründen): .venv/bin/python -m unittest -v
#
# BU DOSYA (tests/test_donusturme.py): Dönüştürmeyi denetler: birim, saat, kayıp satır,
#   yeniden başlama doğru mu?
#
# AYRINTI: Birim çevirmenin (16384 → 1 g), zaman eşleştirmenin, kayıp satırın ve
#   ESP32'nin yeniden başlamasının doğru fark edildiğini; I satırı gelmezse varsayılan
#   aralıklarla devam edildiğini denetler.

import unittest

from okuyucu.donusturme import BirimCevirici, MesajDonusturucu, SiraTakipcisi, ZamanEslestirici
from okuyucu.mesajlar import AtimMesaji, BilgiMesaji, HataMesaji, OlcumMesaji
from sozlesme import Atim, CihazBilgisi, Olay, OlayTuru, Olcum

BILGI = BilgiMesaji(seq=0, ms=0, surum=1, hz=50, acc_g=2, gyro_dps=250)


def olcum_mesaji(seq: int, ms: int) -> OlcumMesaji:
    return OlcumMesaji(seq, ms, gsr=1500, ax=-412, ay=0, az=16384, gx=0, gy=131, gz=-262)


def yeni_donusturucu() -> MesajDonusturucu:
    return MesajDonusturucu(SiraTakipcisi(), BirimCevirici(), ZamanEslestirici())


def olaylar(kayitlar, tur: OlayTuru) -> list[Olay]:
    return [k for k in kayitlar if isinstance(k, Olay) and k.tur == tur]


class YardimciTestleri(unittest.TestCase):
    def test_birim_cevirici_varsayilan_aralik(self):
        cevirici = BirimCevirici()
        self.assertEqual(cevirici.ivme_g(16384), 1.0)
        self.assertEqual(cevirici.ivme_g(-412), -0.02515)
        self.assertEqual(cevirici.donus_dps(131), 1.0)

    def test_birim_cevirici_baska_aralik(self):
        cevirici = BirimCevirici()
        cevirici.ayarla(acc_g=4, gyro_dps=500)
        self.assertEqual(cevirici.ivme_g(8192), 1.0)
        self.assertEqual(cevirici.donus_dps(65.5), 1.0)

    def test_zaman_eslestirici(self):
        zaman = ZamanEslestirici()
        self.assertEqual(zaman.bilgisayar_zamani(20000, t_gelis=1000.0), 1000.0)
        self.assertEqual(zaman.bilgisayar_zamani(20840, t_gelis=1005.0), 1000.84)
        zaman.sifirla()
        self.assertEqual(zaman.bilgisayar_zamani(0, t_gelis=2000.0), 2000.0)

    def test_sira_takipcisi(self):
        sira = SiraTakipcisi()
        self.assertEqual([sira.kayip_say(n) for n in (5, 6, 7)], [0, 0, 0])
        self.assertEqual(sira.kayip_say(10), 2)
        self.assertTrue(sira.geri_gitti_mi(3))
        self.assertFalse(sira.geri_gitti_mi(11))


class MesajDonusturucuTestleri(unittest.TestCase):
    def test_bilgi_ve_olcum(self):
        donusturucu = yeni_donusturucu()
        self.assertEqual(
            donusturucu.donustur(BILGI, t_gelis=1000.0),
            [CihazBilgisi(t=1000.0, surum=1, hz=50, acc_g=2, gyro_dps=250)],
        )
        self.assertEqual(
            donusturucu.donustur(olcum_mesaji(1, 20), t_gelis=1000.5),
            [Olcum(1000.02, 1, 20, 1500, -0.02515, 0.0, 1.0, 0.0, 1.0, -2.0)],
        )

    def test_atim_ve_hata(self):
        donusturucu = yeni_donusturucu()
        donusturucu.donustur(BILGI, t_gelis=1000.0)
        self.assertEqual(donusturucu.donustur(AtimMesaji(1, 800), 1000.9), [Atim(1000.8, 1, 800)])
        self.assertEqual(
            donusturucu.donustur(HataMesaji(2, 900, "MPU_YOK"), 1001.0),
            [Olay(1000.9, OlayTuru.HATA, "MPU_YOK")],
        )

    def test_kayip_satir(self):
        donusturucu = yeni_donusturucu()
        donusturucu.donustur(BILGI, 1000.0)
        donusturucu.donustur(olcum_mesaji(1, 20), 1000.0)
        kayitlar = donusturucu.donustur(olcum_mesaji(4, 80), 1000.1)
        self.assertEqual(kayitlar[0], Olay(1000.08, OlayTuru.KAYIP, "2 satır"))
        self.assertIsInstance(kayitlar[1], Olcum)

    def test_i_satiri_gelmezse_bir_kez_uyarir_ve_devam_eder(self):
        donusturucu = yeni_donusturucu()
        ilk = donusturucu.donustur(olcum_mesaji(500, 10000), 1000.0)
        self.assertEqual(len(olaylar(ilk, OlayTuru.HATA)), 1)
        self.assertIn("I satırı gelmedi", ilk[0].ayrinti)
        self.assertEqual(ilk[1].az_g, 1.0)
        ikinci = donusturucu.donustur(olcum_mesaji(501, 10020), 1000.02)
        self.assertEqual(olaylar(ikinci, OlayTuru.HATA), [])

    def test_yeni_i_satiri_yeniden_baslama_demektir(self):
        donusturucu = yeni_donusturucu()
        donusturucu.donustur(BILGI, 1000.0)
        donusturucu.donustur(olcum_mesaji(1, 20), 1000.02)
        kayitlar = donusturucu.donustur(BILGI, t_gelis=1500.0)
        self.assertEqual(len(olaylar(kayitlar, OlayTuru.YENIDEN_BASLAMA)), 1)
        self.assertEqual(kayitlar[-1].t, 1500.0)
        sonra = donusturucu.donustur(olcum_mesaji(1, 20), 1500.02)
        self.assertEqual(sonra, [Olcum(1500.02, 1, 20, 1500, -0.02515, 0.0, 1.0, 0.0, 1.0, -2.0)])

    def test_geri_giden_sira_numarasi_yeniden_baslama_demektir(self):
        donusturucu = yeni_donusturucu()
        donusturucu.donustur(BILGI, 1000.0)
        donusturucu.donustur(olcum_mesaji(100, 2000), 1002.0)
        kayitlar = donusturucu.donustur(olcum_mesaji(3, 60), t_gelis=1600.0)
        self.assertEqual(len(olaylar(kayitlar, OlayTuru.YENIDEN_BASLAMA)), 1)
        self.assertEqual(olaylar(kayitlar, OlayTuru.KAYIP), [])
        self.assertEqual(kayitlar[-1].t, 1600.0)


if __name__ == "__main__":
    unittest.main()
