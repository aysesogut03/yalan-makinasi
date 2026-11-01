# TESTLER: Otomatik kontroller. Veri hattının her parçasının doğru çalıştığını denetler.
#   Çalıştırmak için (veri_hatti klasöründen): .venv/bin/python -m unittest -v
#
# BU DOSYA (tests/test_uctan_uca.py): Hepsini birlikte dener: sahte ESP32 → okuyucu →
#   dosyalar.
#
# AYRINTI: Sahte ESP32 gerçek zamanda 1,5 saniye veri gönderir, okuyucu bunu kaydeder.
#   Hiç kayıp ya da bozuk satır olmadığı, zamanların 20 ms arayla geldiği, birimlerin
#   çevrildiği ve dosyaların oluştuğu denetlenir. Ayrıca okuyucunun varsayılan adresinin
#   sahte ESP32'ninkiyle aynı olduğu ve macOS'un AirPlay için kullandığı kapılara (5000,
#   7000) denk gelmediği denetlenir. pyserial kurulu değilse atlanır.

import csv
import importlib.util
import json
import random
import tempfile
import threading
import time
import unittest
from pathlib import Path

from okuyucu.ayristirma import ProtokolV1Ayristirici
from okuyucu.dagitim import OturumKaydedici
from okuyucu.donusturme import BirimCevirici, MesajDonusturucu, SiraTakipcisi, ZamanEslestirici
from okuyucu.hat import VeriHatti
from simulator.__main__ import GercekSaat
from simulator.cihaz import SahteEsp32
from simulator.sensorler import SahteGsr, SahteIvme, SahteNabiz
from simulator.tcp import TcpSunucu
from sozlesme import CihazBilgisi, HamSatir, Olay, OlayTuru, Olcum

PYSERIAL_VAR = importlib.util.find_spec("serial") is not None
SURE_S = 1.5


class BilgisayarSaati:
    def simdi(self) -> float:
        return time.time()


class ListeAlici:
    def __init__(self) -> None:
        self.kayitlar = []

    def al(self, kayit) -> None:
        self.kayitlar.append(kayit)

    def kapat(self) -> None:
        pass


@unittest.skipUnless(PYSERIAL_VAR, "pyserial kurulu değil (README.md, 7. bölüm)")
class UctanUcaTest(unittest.TestCase):
    def test_sahte_esp32_den_kayit_dosyalarina(self):
        from okuyucu.baglanti.seri_kaynak import SeriKaynak

        with TcpSunucu(kapi=0) as sunucu, tempfile.TemporaryDirectory() as gecici:
            def sahte_esp32():
                cikis = sunucu.baglanti_bekle()
                rastgele = random.Random(1)
                SahteEsp32(
                    GercekSaat(), SahteGsr(rastgele), SahteIvme(rastgele), SahteNabiz(rastgele), cikis, hz=50
                ).calistir(SURE_S)
                cikis.kapat()

            is_parcacigi = threading.Thread(target=sahte_esp32)
            is_parcacigi.start()

            saat = BilgisayarSaati()
            adres = f"socket://127.0.0.1:{sunucu.kapi}"
            toplayici = ListeAlici()
            kaydedici = OturumKaydedici(Path(gecici), saat, kaynak=adres)
            hat = VeriHatti(
                kaynak=SeriKaynak(adres),
                ayristirici=ProtokolV1Ayristirici(),
                donusturucu=MesajDonusturucu(SiraTakipcisi(), BirimCevirici(), ZamanEslestirici()),
                alicilar=[kaydedici, toplayici],
                saat=saat,
            )
            baslangic = time.time()
            hat.calistir()
            is_parcacigi.join(timeout=5)

            kayitlar = toplayici.kayitlar
            olcumler = [k for k in kayitlar if isinstance(k, Olcum)]
            sorunlar = [k for k in kayitlar if isinstance(k, Olay) and k.tur != OlayTuru.BAGLANTI]

            self.assertEqual(sorunlar, [])
            self.assertEqual(sum(isinstance(k, CihazBilgisi) for k in kayitlar), 1)
            self.assertEqual(len(olcumler), int(SURE_S * 50))

            self.assertLess(abs(olcumler[0].t - baslangic), 1.0)
            araliklar = {round(b.t - a.t, 3) for a, b in zip(olcumler, olcumler[1:])}
            self.assertEqual(araliklar, {0.02})

            self.assertTrue(all(0.95 < o.az_g < 1.05 for o in olcumler))

            klasor = kaydedici.klasor
            with open(klasor / "olcumler.csv", encoding="utf-8", newline="") as dosya:
                self.assertEqual(len(list(csv.reader(dosya))), 1 + len(olcumler))
            ham_satir_sayisi = sum(isinstance(k, HamSatir) for k in kayitlar)
            self.assertEqual(len((klasor / "ham.log").read_text(encoding="utf-8").splitlines()), ham_satir_sayisi)
            oturum = json.loads((klasor / "oturum.json").read_text(encoding="utf-8"))
            self.assertEqual((oturum["hz"], oturum["protokol_surumu"]), (50, 1))
            self.assertIsNotNone(oturum["bitis"])

    def test_varsayilan_adresler_birbirini_tutar(self):
        from okuyucu.__main__ import _argumanlari_oku as okuyucu_ayarlari
        from simulator.__main__ import _argumanlari_oku as simulator_ayarlari

        kapi = simulator_ayarlari([]).kapi
        self.assertEqual(okuyucu_ayarlari([]).adres, f"socket://127.0.0.1:{kapi}")
        self.assertNotIn(kapi, (5000, 7000))


if __name__ == "__main__":
    unittest.main()
