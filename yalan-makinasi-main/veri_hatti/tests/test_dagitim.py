# TESTLER: Otomatik kontroller. Veri hattının her parçasının doğru çalıştığını denetler.
#   Çalıştırmak için (veri_hatti klasöründen): .venv/bin/python -m unittest -v
#
# BU DOSYA (tests/test_dagitim.py): Dağıtımı denetler: dosyalar ve ekran özeti doğru mu?
#
# AYRINTI: Kayıtların doğru dosyalara doğru biçimde yazıldığını, aynı saniyede başlayan
#   iki testin ayrı klasörlere gittiğini ve ekrana saniyede bir özet basıldığını
#   denetler.

import csv
import json
import tempfile
import unittest
from pathlib import Path

from okuyucu.dagitim import KonsolAlici, OturumKaydedici
from sozlesme import Atim, CihazBilgisi, HamSatir, Olay, OlayTuru, Olcum


class ElleSaat:
    def __init__(self, t: float) -> None:
        self.t = t

    def simdi(self) -> float:
        return self.t


def csv_oku(yol: Path) -> list[list[str]]:
    with open(yol, encoding="utf-8", newline="") as dosya:
        return list(csv.reader(dosya))


class OturumKaydediciTestleri(unittest.TestCase):
    def setUp(self):
        self._gecici = tempfile.TemporaryDirectory()
        self.kok = Path(self._gecici.name)

    def tearDown(self):
        self._gecici.cleanup()

    def test_kayitlar_dosyalara_yazilir(self):
        saat = ElleSaat(1792281600.0)
        kaydedici = OturumKaydedici(self.kok, saat, kaynak="socket://127.0.0.1:7600", gsr_kalibrasyon=512)
        kaydedici.al(CihazBilgisi(1792281600.0, surum=1, hz=50, acc_g=2, gyro_dps=250))
        kaydedici.al(Olcum(1792281600.02, 1, 20, 1500, -0.02515, 0.00006, 0.98389, -0.2672, 2.4, 0.0))
        kaydedici.al(Atim(1792281600.8, 2, 800))
        kaydedici.al(Olay(1792281600.9, OlayTuru.KAYIP, "2 satır"))
        kaydedici.al(HamSatir(1792281600.021, "S,1,20,1500,-412,1,16120,-35,314,0"))
        saat.t = 1792281700.0
        kaydedici.kapat()

        klasor = kaydedici.klasor
        self.assertEqual(
            csv_oku(klasor / "olcumler.csv"),
            [
                ["t", "seq", "esp_ms", "gsr_mv", "ax_g", "ay_g", "az_g", "gx_dps", "gy_dps", "gz_dps"],
                ["1792281600.02", "1", "20", "1500", "-0.02515", "0.00006", "0.98389", "-0.2672", "2.4", "0"],
            ],
        )
        self.assertEqual(csv_oku(klasor / "atimlar.csv"), [["t", "seq", "esp_ms"], ["1792281600.8", "2", "800"]])
        self.assertEqual(csv_oku(klasor / "olaylar.csv"), [["t", "tur", "ayrinti"], ["1792281600.9", "kayip", "2 satır"]])
        self.assertEqual(
            (klasor / "ham.log").read_text(encoding="utf-8"),
            "1792281600.021 S,1,20,1500,-412,1,16120,-35,314,0\n",
        )
        oturum = json.loads((klasor / "oturum.json").read_text(encoding="utf-8"))
        self.assertEqual(oturum["hz"], 50)
        self.assertEqual(oturum["protokol_surumu"], 1)
        self.assertEqual(oturum["gsr_kalibrasyon"], 512)
        self.assertEqual(oturum["bitis"], 1792281700.0)

    def test_ayni_saniyede_iki_test_ayri_klasore_yazilir(self):
        saat = ElleSaat(1792281600.0)
        birinci = OturumKaydedici(self.kok, saat, kaynak="a")
        ikinci = OturumKaydedici(self.kok, saat, kaynak="b")
        self.assertNotEqual(birinci.klasor, ikinci.klasor)
        self.assertTrue(ikinci.klasor.name.endswith("_2"))
        birinci.kapat()
        ikinci.kapat()


class KonsolAliciTestleri(unittest.TestCase):
    def test_saniyede_bir_ozet_ve_olaylar_hemen(self):
        satirlar: list[str] = []
        konsol = KonsolAlici(yaz=satirlar.append)
        for n in range(106):
            konsol.al(Olcum(1000 + n * 0.02, n, n * 20, 1500, 0.0, 0.0, 0.99, 0.0, 0.0, 0.0))
        konsol.al(Olay(1002.2, OlayTuru.BOZUK, "deneme"))
        ozetler = [satir for satir in satirlar if "ölçüm" in satir]
        self.assertEqual(len(ozetler), 2)
        self.assertIn("ölçüm  50", ozetler[0])
        self.assertEqual(satirlar[-1], "[olay] bozuk: deneme")


if __name__ == "__main__":
    unittest.main()
