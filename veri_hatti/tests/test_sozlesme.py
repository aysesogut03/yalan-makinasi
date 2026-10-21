# TESTLER: Otomatik kontroller. Veri hattının her parçasının doğru çalıştığını denetler.
#   Çalıştırmak için (veri_hatti klasöründen): .venv/bin/python -m unittest -v
#
# BU DOSYA (tests/test_sozlesme.py): Sözleşmeyi denetler: kayıt tipleri README'de
#   yazanla aynı mı?
#
# AYRINTI: Kayıt tiplerinin alanları README.md'deki CSV sütunlarıyla karşılaştırılır.
#   Biri ekip onayı olmadan bir alanı değiştirirse bu testler kırılır; diğer grupların
#   kodu bu alanlara güvenir.

import unittest
from dataclasses import FrozenInstanceError, fields

from sozlesme import Atim, Olay, OlayTuru, Olcum


def alan_adlari(tip) -> list[str]:
    return [alan.name for alan in fields(tip)]


class SozlesmeTestleri(unittest.TestCase):
    def test_olcum_sutunlari(self):
        self.assertEqual(
            alan_adlari(Olcum),
            ["t", "seq", "esp_ms", "gsr_mv", "ax_g", "ay_g", "az_g", "gx_dps", "gy_dps", "gz_dps"],
        )

    def test_atim_sutunlari(self):
        self.assertEqual(alan_adlari(Atim), ["t", "seq", "esp_ms"])

    def test_olay_sutunlari(self):
        self.assertEqual(alan_adlari(Olay), ["t", "tur", "ayrinti"])

    def test_olay_turleri(self):
        self.assertEqual(
            {tur.value for tur in OlayTuru},
            {"kayip", "bozuk", "hata", "yeniden_baslama", "baglanti"},
        )

    def test_kayitlar_degistirilemez(self):
        atim = Atim(t=1792281600.134, seq=1043, esp_ms=20851)
        with self.assertRaises(FrozenInstanceError):
            atim.t = 0.0


if __name__ == "__main__":
    unittest.main()
