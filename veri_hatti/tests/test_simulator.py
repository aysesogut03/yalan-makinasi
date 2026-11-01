# TESTLER: Otomatik kontroller. Veri hattının her parçasının doğru çalıştığını denetler.
#   Çalıştırmak için (veri_hatti klasöründen): .venv/bin/python -m unittest -v
#
# BU DOSYA (tests/test_simulator.py): Sahte ESP32'yi denetler: ürettiği satırlar
#   protokole uyuyor mu?
#
# AYRINTI: İlk satırın I satırı olduğunu, saniyede 50 ölçüm geldiğini, sıra
#   numaralarında boşluk olmadığını, zamanın geri gitmediğini ve nabzın dakikada 75
#   civarında olduğunu denetler. Sahte ESP32'ye gerçek saat yerine beklemeyen bir saat
#   verilir; böylece dakikalarca veri bir anda üretilir.

import random
import socket
import threading
import time
import unittest

from simulator.cihaz import SahteEsp32
from simulator.sensorler import SahteGsr, SahteIvme, SahteNabiz
from simulator.tcp import BaglantiKoptu, TcpSunucu


class BeklemeyenSaat:
    def __init__(self) -> None:
        self.t = 0.0

    def simdi(self) -> float:
        return self.t

    def uyu(self, saniye: float) -> None:
        self.t += saniye


class ListeCikisi:
    def __init__(self) -> None:
        self.satirlar: list[str] = []

    def gonder(self, satir: str) -> None:
        self.satirlar.append(satir)


def sahte_esp32_satirlari(sure_s: float, tohum: int = 1, hz: int = 50) -> list[str]:
    rastgele = random.Random(tohum)
    cikis = ListeCikisi()
    esp32 = SahteEsp32(
        BeklemeyenSaat(), SahteGsr(rastgele), SahteIvme(rastgele), SahteNabiz(rastgele), cikis, hz=hz
    )
    esp32.calistir(sure_s)
    return cikis.satirlar


def turu(satirlar: list[str], tur: str) -> list[list[str]]:
    return [satir.split(",") for satir in satirlar if satir.startswith(tur + ",")]


class SahteEsp32Testleri(unittest.TestCase):
    def test_ilk_satir_bilgi_satiri(self):
        satirlar = sahte_esp32_satirlari(0.1)
        self.assertEqual(satirlar[0], "I,0,0,v=1,hz=50,acc=2,gyro=250")

    def test_saniyede_hz_kadar_olcum(self):
        satirlar = sahte_esp32_satirlari(2.0, hz=50)
        self.assertEqual(len(turu(satirlar, "S")), 100)

    def test_olcum_zamanlari_esit_aralikli(self):
        satirlar = sahte_esp32_satirlari(2.0, hz=50)
        zamanlar = [int(alanlar[2]) for alanlar in turu(satirlar, "S")]
        self.assertEqual(zamanlar, [20 * n for n in range(100)])

    def test_sira_numaralari_bosluksuz(self):
        satirlar = sahte_esp32_satirlari(5.0)
        sira_numaralari = [int(satir.split(",")[1]) for satir in satirlar]
        self.assertEqual(sira_numaralari, list(range(len(satirlar))))

    def test_zaman_geri_gitmez(self):
        satirlar = sahte_esp32_satirlari(10.0)
        zamanlar = [int(satir.split(",")[2]) for satir in satirlar]
        self.assertEqual(zamanlar, sorted(zamanlar))

    def test_olcum_satiri_alanlari_gecerli(self):
        for alanlar in turu(sahte_esp32_satirlari(5.0), "S"):
            self.assertEqual(len(alanlar), 10)
            gsr, *ivme = (int(alan) for alan in alanlar[3:])
            self.assertTrue(0 <= gsr <= 3300)
            for deger in ivme:
                self.assertTrue(-32768 <= deger <= 32767)

    def test_nabiz_dakikada_yaklasik_75(self):
        atimlar = turu(sahte_esp32_satirlari(60.0), "B")
        self.assertTrue(65 <= len(atimlar) <= 85, f"{len(atimlar)} atım")

    def test_ayni_tohum_ayni_veri(self):
        self.assertEqual(sahte_esp32_satirlari(3.0, tohum=5), sahte_esp32_satirlari(3.0, tohum=5))


class TcpTestleri(unittest.TestCase):
    def test_satirlar_satir_sonuyla_gider(self):
        with TcpSunucu(kapi=0) as sunucu:
            def gonderici():
                cikis = sunucu.baglanti_bekle()
                cikis.gonder("I,0,0,v=1")
                cikis.gonder("B,1,800")
                cikis.kapat()

            is_parcacigi = threading.Thread(target=gonderici)
            is_parcacigi.start()
            gelen = b""
            with socket.create_connection(("127.0.0.1", sunucu.kapi), timeout=2) as istemci:
                while parca := istemci.recv(1024):
                    gelen += parca
            is_parcacigi.join(timeout=2)

        self.assertEqual(gelen, b"I,0,0,v=1\nB,1,800\n")

    def test_kopan_baglanti_hata_verir(self):
        with TcpSunucu(kapi=0) as sunucu:
            istemci = socket.create_connection(("127.0.0.1", sunucu.kapi), timeout=2)
            cikis = sunucu.baglanti_bekle()
            istemci.close()
            with self.assertRaises(BaglantiKoptu):
                for _ in range(100):
                    cikis.gonder("S,0,0,0,0,0,0,0,0,0")
                    time.sleep(0.01)
            cikis.kapat()


if __name__ == "__main__":
    unittest.main()
