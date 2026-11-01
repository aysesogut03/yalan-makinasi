# TESTLER: Otomatik kontroller. Veri hattının her parçasının doğru çalıştığını denetler.
#   Çalıştırmak için (veri_hatti klasöründen): .venv/bin/python -m unittest -v
#
# BU DOSYA (tests/test_hatali_veri.py): Gerçek okuyucu programını bilerek hatalı veri
#   gönderen bir vericiye bağlar: her sorun doğru fark edilip kaydediliyor mu?
#
# AYRINTI: Okuyucu, komut satırından çalıştırıldığı gibi ayrı bir program olarak
#   başlatılır. Verici sırayla şunları gönderir: bağlanınca yarım yakalanan satır,
#   kaybolan satırlar, içinde harf olan bir sayı, Arduino'nun \r\n satır sonu, ESP32'nin
#   bildirdiği bir hata, iki parçada gelen satır, iki çeşit yeniden başlama ve satır
#   sonu olmayan çöp veri. Sonra bağlantıyı keser (kablo çekilmiş gibi). Her sorunun
#   olaylar.csv'ye doğru yazıldığı, düzgün satırların yine kaydedildiği ve programın
#   kendiliğinden düzgünce kapandığı denetlenir. Ayrıca sahte ESP32 kapalıyken okuyucunun
#   anlaşılır bir hatayla çıktığı denetlenir. pyserial kurulu değilse atlanır.

import csv
import importlib.util
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

PYSERIAL_VAR = importlib.util.find_spec("serial") is not None
VERI_HATTI = Path(__file__).resolve().parent.parent

BILGI = b"I,0,0,v=1,hz=50,acc=2,gyro=250\n"


def olcum(seq: int, ms: int) -> bytes:
    return f"S,{seq},{ms},1500,2265,-21,16164,-8,352,17\n".encode()


HATALI_AKIS = [
    ("bağlanınca satırın ortası yakalandı", b",16164,-8,352,17\n"),
    ("normal açılış", BILGI + olcum(1, 0) + olcum(2, 20) + olcum(3, 40)),
    ("4 ve 5 numaralı satırlar kayboldu", olcum(6, 100)),
    ("içinde harf olan sayı", b"S,7,120,15x0,2265,-21,16164,-8,352,17\n"),
    ("bozuk satırdan sonra devam", olcum(8, 140)),
    ("Arduino satır sonu", b"B,9,150\r\n"),
    ("ESP32 hata bildirdi", b"E,10,160,MPU_YOK\n"),
    ("satırın ilk parçası", b"S,11,180,1500,22"),
    ("satırın ikinci parçası", b"65,-21,16164,-8,352,17\n"),
    ("yeni I satırıyla yeniden başlama", BILGI + olcum(1, 20) + olcum(2, 40)),
    ("I satırı olmadan yeniden başlama", olcum(1, 20) + olcum(2, 40)),
    ("satır sonu olmayan çöp veri", bytes(range(32, 127)) * 12),
    ("çöpten sonra düzgün satır", b"\n" + olcum(3, 60)),
]

BEKLENEN_ILK_OLAYLAR = [
    ("baglanti", "okuma başladı"),
    ("bozuk", "bilinmeyen mesaj türü"),
    ("kayip", "2 satır"),
    ("bozuk", "gsr tam sayı değil"),
    ("kayip", "1 satır"),
    ("hata", "MPU_YOK"),
    ("yeniden_baslama", "yeni I satırı"),
    ("yeniden_baslama", "geri gitti"),
    ("hata", "I satırı gelmedi"),
]
BEKLENEN_OLCUMLER = [1, 2, 3, 6, 8, 11, 1, 2, 1, 2, 3]


def okuyucuyu_calistir(adres: str, kayit_klasoru: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "okuyucu", "--adres", adres, "--kayit-klasoru", str(kayit_klasoru)],
        cwd=VERI_HATTI,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )


def csv_oku(yol: Path) -> list[dict[str, str]]:
    with open(yol, encoding="utf-8", newline="") as dosya:
        return list(csv.DictReader(dosya))


@unittest.skipUnless(PYSERIAL_VAR, "pyserial kurulu değil (README.md, 7. bölüm)")
class HataliVeriTestleri(unittest.TestCase):
    def setUp(self):
        self._gecici = tempfile.TemporaryDirectory()
        self.kayitlar = Path(self._gecici.name) / "kayitlar"

    def tearDown(self):
        self._gecici.cleanup()

    def test_hatali_veri_dogru_kaydedilir_ve_kopmada_duzgun_kapanir(self):
        with socket.create_server(("127.0.0.1", 0)) as sunucu:
            kapi = sunucu.getsockname()[1]

            def verici():
                baglanti, _ = sunucu.accept()
                with baglanti:
                    for _, veri in HATALI_AKIS:
                        baglanti.sendall(veri)
                        time.sleep(0.05)
                    time.sleep(0.2)

            is_parcacigi = threading.Thread(target=verici)
            is_parcacigi.start()
            sonuc = okuyucuyu_calistir(f"socket://127.0.0.1:{kapi}", self.kayitlar)
            is_parcacigi.join(timeout=5)

        self.assertEqual(sonuc.returncode, 0, sonuc.stderr)
        self.assertIn("Bağlantı kapandı", sonuc.stdout)
        (oturum,) = self.kayitlar.iterdir()

        olaylar = [(o["tur"], o["ayrinti"]) for o in csv_oku(oturum / "olaylar.csv")]
        ilk = olaylar[: len(BEKLENEN_ILK_OLAYLAR)]
        self.assertEqual([tur for tur, _ in ilk], [tur for tur, _ in BEKLENEN_ILK_OLAYLAR])
        for (tur, ayrinti), (_, beklenen_soz) in zip(ilk, BEKLENEN_ILK_OLAYLAR):
            with self.subTest(tur=tur):
                self.assertIn(beklenen_soz, ayrinti)
        cop_olaylari = olaylar[len(BEKLENEN_ILK_OLAYLAR) : -1]
        self.assertGreaterEqual(len(cop_olaylari), 1)
        self.assertTrue(all(tur == "bozuk" for tur, _ in cop_olaylari))
        self.assertEqual(olaylar[-1], ("baglanti", "okuma bitti"))
        self.assertTrue(all(len(ayrinti) < 200 for _, ayrinti in olaylar))

        self.assertEqual([int(o["seq"]) for o in csv_oku(oturum / "olcumler.csv")], BEKLENEN_OLCUMLER)
        self.assertEqual([int(a["seq"]) for a in csv_oku(oturum / "atimlar.csv")], [9])
        oturum_bilgisi = json.loads((oturum / "oturum.json").read_text(encoding="utf-8"))
        self.assertIsNotNone(oturum_bilgisi["bitis"])

    def test_sahte_esp32_kapaliyken_anlasilir_hatayla_cikar(self):
        with socket.create_server(("127.0.0.1", 0)) as gecici:
            kapi = gecici.getsockname()[1]
        sonuc = okuyucuyu_calistir(f"socket://127.0.0.1:{kapi}", self.kayitlar)
        self.assertEqual(sonuc.returncode, 1)
        self.assertIn("Bağlanılamadı", sonuc.stderr)
        self.assertFalse(self.kayitlar.exists())


if __name__ == "__main__":
    unittest.main()
