# TESTLER: Otomatik kontroller. Veri hattının her parçasının doğru çalıştığını denetler.
#   Çalıştırmak için (veri_hatti klasöründen): .venv/bin/python -m unittest -v
#
# BU DOSYA (tests/test_hat.py): Bandı (hat.py) denetler: satırlar doğru sırayla dört alt
#   katmandan geçiyor mu?
#
# AYRINTI: Gerçek bağlantı yerine bir satır listesi verilir. Kayıtların doğru sırayla
#   çıktığını, hata veren bir alıcının diğerlerini durdurmadığını ve bağlantı kapanırken
#   hata çıksa da dosyaların kapandığını denetler.

import contextlib
import io
import unittest

from okuyucu.ayristirma import ProtokolV1Ayristirici
from okuyucu.donusturme import BirimCevirici, MesajDonusturucu, SiraTakipcisi, ZamanEslestirici
from okuyucu.hat import VeriHatti
from sozlesme import CihazBilgisi, HamSatir, Olay, OlayTuru, Olcum


class ListeKaynagi:
    def __init__(self, satirlar: list[str]) -> None:
        self._satirlar = satirlar
        self.kapandi = False

    def satirlar(self):
        yield from self._satirlar

    def kapat(self) -> None:
        self.kapandi = True


class ListeAlici:
    def __init__(self) -> None:
        self.kayitlar = []
        self.kapandi = False

    def al(self, kayit) -> None:
        self.kayitlar.append(kayit)

    def kapat(self) -> None:
        self.kapandi = True


class HataVerenAlici:
    def al(self, kayit) -> None:
        raise RuntimeError("bilerek verilen hata")

    def kapat(self) -> None:
        raise RuntimeError("bilerek verilen hata")


class KapanirkenHataVerenKaynak(ListeKaynagi):
    def kapat(self) -> None:
        raise OSError("bilerek verilen hata")


class ElleSaat:
    def __init__(self) -> None:
        self.t = 1000.0

    def simdi(self) -> float:
        self.t += 0.01
        return self.t


def hat_kur(satirlar, alicilar):
    kaynak = ListeKaynagi(satirlar)
    hat = VeriHatti(
        kaynak=kaynak,
        ayristirici=ProtokolV1Ayristirici(),
        donusturucu=MesajDonusturucu(SiraTakipcisi(), BirimCevirici(), ZamanEslestirici()),
        alicilar=alicilar,
        saat=ElleSaat(),
    )
    return hat, kaynak


SATIRLAR = [
    "I,0,0,v=1,hz=50,acc=2,gyro=250",
    "S,1,20,1500,-412,215,16120,-35,12,4",
    "bozuk bir satır",
    "S,3,60,1501,-410,214,16121,-34,11,5",
]


class VeriHattiTestleri(unittest.TestCase):
    def test_satirlar_kayitlara_cevrilip_dagitilir(self):
        alici = ListeAlici()
        hat, kaynak = hat_kur(SATIRLAR, [alici])
        hat.calistir()

        turler = [type(k).__name__ if not isinstance(k, Olay) else f"Olay:{k.tur.value}" for k in alici.kayitlar]
        self.assertEqual(
            turler,
            [
                "Olay:baglanti",
                "HamSatir", "CihazBilgisi",
                "HamSatir", "Olcum",
                "HamSatir", "Olay:bozuk",
                "HamSatir", "Olay:kayip", "Olcum",
                "Olay:baglanti",
            ],
        )
        self.assertEqual(sum(isinstance(k, HamSatir) for k in alici.kayitlar), len(SATIRLAR))
        self.assertTrue(kaynak.kapandi)
        self.assertTrue(alici.kapandi)

    def test_hata_veren_alici_digerlerini_durdurmaz(self):
        saglam = ListeAlici()
        hat, _ = hat_kur(SATIRLAR, [HataVerenAlici(), saglam])
        uyarilar = io.StringIO()
        with contextlib.redirect_stderr(uyarilar):
            hat.calistir()
        self.assertEqual(sum(isinstance(k, Olcum) for k in saglam.kayitlar), 2)
        self.assertEqual(sum(isinstance(k, CihazBilgisi) for k in saglam.kayitlar), 1)
        self.assertTrue(saglam.kapandi)
        self.assertEqual(uyarilar.getvalue().count("HataVerenAlici hata verdi"), 1)

    def test_baglanti_kapanirken_hata_verse_de_alicilar_kapanir(self):
        alici = ListeAlici()
        hat = VeriHatti(
            kaynak=KapanirkenHataVerenKaynak(SATIRLAR),
            ayristirici=ProtokolV1Ayristirici(),
            donusturucu=MesajDonusturucu(SiraTakipcisi(), BirimCevirici(), ZamanEslestirici()),
            alicilar=[alici],
            saat=ElleSaat(),
        )
        with contextlib.redirect_stderr(io.StringIO()):
            hat.calistir()
        self.assertTrue(alici.kapandi)

    def test_uzun_bozuk_satir_olaya_kisaltilarak_yazilir(self):
        alici = ListeAlici()
        cop = "x" * 1500
        hat, _ = hat_kur([cop], [alici])
        hat.calistir()
        bozuk = [k for k in alici.kayitlar if isinstance(k, Olay) and k.tur.value == "bozuk"]
        self.assertEqual(len(bozuk), 1)
        self.assertLess(len(bozuk[0].ayrinti), 200)
        ham = [k for k in alici.kayitlar if isinstance(k, HamSatir)]
        self.assertEqual(ham[0].metin, cop)


if __name__ == "__main__":
    unittest.main()
