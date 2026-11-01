# OKUYUCU: Veri hattının asıl işi. ESP32'den gelen satırları, diğer katmanların
#   anlayacağı kayıtlara çevirir ve onlara teslim eder.
#
# BU DOSYA (okuyucu/__main__.py): Başlangıç dosyası: parçaları kurar ve çalıştırır.
#
# AYRINTI: "python -m okuyucu" yazınca çalışan dosya budur. Dört alt katmanın
#   parçalarını oluşturur, birbirine bağlar ve bandı (hat.py) başlatır. Parçaları
#   birbirine bağlayan tek yer burası olduğu için, örneğin yeni bir alıcı eklemek ya da
#   bağlantıyı değiştirmek yalnızca bu dosyada bir satırı değiştirir. Kayıtlar dosyalara
#   yazılırken aynı anda arayüze de canlı yayınlanır (WebSocket, ws://127.0.0.1:8765);
#   yayın açılamazsa uyarı verilir ve kayıt yine sürer. Kullanım:
#     .venv/bin/python -m okuyucu                                  sahte ESP32'ye bağlanır
#     .venv/bin/python -m okuyucu --adres /dev/cu.usbserial-0001    gerçek ESP32 (macOS)
#     .venv\Scripts\python -m okuyucu --adres COM3                  gerçek ESP32 (Windows)
#     .venv/bin/python -m okuyucu --canli-yok                       arayüze yayın yapmadan

import argparse
import sys
import time
from pathlib import Path

from .ayristirma import ProtokolV1Ayristirici
from .baglanti.seri_kaynak import BaglantiKurulamadi, SeriKaynak
from .dagitim import KonsolAlici, OturumKaydedici
from .donusturme import BirimCevirici, MesajDonusturucu, SiraTakipcisi, ZamanEslestirici
from .hat import VeriHatti


class BilgisayarSaati:
    def simdi(self) -> float:
        return time.time()


def _argumanlari_oku(argv: list[str] | None) -> argparse.Namespace:
    komut_satiri = argparse.ArgumentParser(
        prog="python -m okuyucu",
        description="ESP32 satırlarını okur, kayıtlara çevirir ve kaydeder.",
    )
    komut_satiri.add_argument(
        "--adres", default="socket://127.0.0.1:7600",
        help="seri port ya da sahte ESP32 adresi (varsayılan: socket://127.0.0.1:7600)",
    )
    komut_satiri.add_argument("--baud", type=int, default=115200, help="seri port hızı (varsayılan: 115200)")
    komut_satiri.add_argument("--kayit-klasoru", default="kayitlar", help="kayıtların yazılacağı klasör (varsayılan: kayitlar)")
    komut_satiri.add_argument("--gsr-kalibrasyon", type=int, default=None, help="GSR sensörünün kalibrasyon değeri (oturum.json'a yazılır)")
    komut_satiri.add_argument("--sessiz", action="store_true", help="ekrana özet basma")
    komut_satiri.add_argument("--canli-kapi", type=int, default=8765, help="arayüze canlı yayın kapısı (varsayılan: 8765)")
    komut_satiri.add_argument("--canli-yok", action="store_true", help="arayüze canlı yayın yapma")
    return komut_satiri.parse_args(argv)


def _canli_yayin(kapi: int):
    try:
        from .dagitim.websocket_alici import WebSocketAlici

        return WebSocketAlici(port=kapi)
    except (ImportError, RuntimeError) as hata:
        print(f"Arayüze canlı yayın açılamadı, kayıt yine de sürüyor: {hata}", file=sys.stderr)
        return None


def main(argv: list[str] | None = None) -> int:
    argumanlar = _argumanlari_oku(argv)
    saat = BilgisayarSaati()

    try:
        kaynak = SeriKaynak(argumanlar.adres, baud=argumanlar.baud)
    except BaglantiKurulamadi as hata:
        print(f"Bağlanılamadı: {hata}", file=sys.stderr)
        print("Sahte ESP32 çalışıyor mu? Başka bir terminalde: python3 -m simulator", file=sys.stderr)
        return 1

    kaydedici = OturumKaydedici(
        Path(argumanlar.kayit_klasoru), saat, kaynak=argumanlar.adres, gsr_kalibrasyon=argumanlar.gsr_kalibrasyon
    )
    alicilar = [kaydedici]
    if not argumanlar.sessiz:
        alicilar.append(KonsolAlici())
    canli = None if argumanlar.canli_yok else _canli_yayin(argumanlar.canli_kapi)
    if canli is not None:
        alicilar.append(canli)

    hat = VeriHatti(
        kaynak=kaynak,
        ayristirici=ProtokolV1Ayristirici(),
        donusturucu=MesajDonusturucu(SiraTakipcisi(), BirimCevirici(), ZamanEslestirici()),
        alicilar=alicilar,
        saat=saat,
    )

    print(f"Bağlandı: {argumanlar.adres}")
    if canli is not None:
        print(f"Arayüze canlı yayın: ws://127.0.0.1:{argumanlar.canli_kapi}")
    print(f"Kayıt klasörü: {kaydedici.klasor}  (durdurmak için Ctrl+C)")
    try:
        hat.calistir()
        print("Bağlantı kapandı.")
    except KeyboardInterrupt:
        print("\nDurduruldu.")
    print(f"Kayıt tamamlandı: {kaydedici.klasor}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
