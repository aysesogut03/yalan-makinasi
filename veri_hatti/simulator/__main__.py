# SİMÜLATÖR: Sahte ESP32. Kart gelene kadar gerçek ESP32'nin yerine veri üretir.
#
# BU DOSYA (simulator/__main__.py): Başlangıç dosyası: parçaları kurar ve çalıştırır.
#
# AYRINTI: "python3 -m simulator" yazınca çalışan dosya budur. Saati, sensörleri ve TCP
#   bağlantısını oluşturup cihaz.py'ye verir. Her yeni bağlantıda sahte ESP32'yi
#   sıfırdan başlatır, çünkü birçok gerçek ESP32 kartı da seri port açılınca yeniden
#   başlar. Kullanım:
#     python3 -m simulator
#     python3 -m simulator --nabiz 90 --tohum 42      (bütün ayarlar: --help)

import argparse
import random
import time

from .cihaz import SahteEsp32
from .sensorler import SahteGsr, SahteIvme, SahteNabiz
from .tcp import BaglantiKoptu, TcpSunucu


class GercekSaat:
    def simdi(self) -> float:
        return time.monotonic()

    def uyu(self, saniye: float) -> None:
        time.sleep(saniye)


def _argumanlari_oku(argv: list[str] | None) -> argparse.Namespace:
    komut_satiri = argparse.ArgumentParser(
        prog="python3 -m simulator",
        description="Protokol v1 satırları gönderen sahte ESP32.",
    )
    komut_satiri.add_argument("--kapi", type=int, default=7600, help="dinlenecek TCP kapısı (varsayılan: 7600)")
    komut_satiri.add_argument("--hz", type=int, default=50, help="saniyedeki ölçüm sayısı (varsayılan: 50)")
    komut_satiri.add_argument("--nabiz", type=float, default=75.0, help="dakikadaki kalp atımı (varsayılan: 75)")
    komut_satiri.add_argument("--nefes", type=float, default=15.0, help="dakikadaki nefes (varsayılan: 15)")
    komut_satiri.add_argument("--tohum", type=int, default=None, help="rastgele tohum; aynı tohum aynı veriyi üretir")
    return komut_satiri.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    argumanlar = _argumanlari_oku(argv)
    rastgele = random.Random(argumanlar.tohum)

    with TcpSunucu(argumanlar.kapi) as sunucu:
        print(f"Sahte ESP32 hazır: socket://127.0.0.1:{sunucu.kapi} (durdurmak için Ctrl+C)", flush=True)
        while True:
            cikis = sunucu.baglanti_bekle()
            print("Okuyucu bağlandı, veri gönderiliyor.", flush=True)
            esp32 = SahteEsp32(
                saat=GercekSaat(),
                gsr=SahteGsr(rastgele),
                ivme=SahteIvme(rastgele, nefes_dk=argumanlar.nefes),
                nabiz=SahteNabiz(rastgele, nabiz_dk=argumanlar.nabiz),
                cikis=cikis,
                hz=argumanlar.hz,
            )
            try:
                esp32.calistir()
            except BaglantiKoptu:
                print("Bağlantı koptu, yeni bağlantı bekleniyor.", flush=True)
            finally:
                cikis.kapat()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSahte ESP32 durduruldu.")
