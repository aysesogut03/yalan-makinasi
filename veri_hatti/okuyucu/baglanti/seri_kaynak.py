# OKUYUCU: Veri hattının asıl işi. ESP32'den gelen satırları, diğer katmanların
#   anlayacağı kayıtlara çevirir ve onlara teslim eder.
#
# BU DOSYA (okuyucu/baglanti/seri_kaynak.py): Kablodan (şimdilik sahte ESP32'den) gelen
#   satırları alır.
#
# AYRINTI: Okuyucunun 1. alt katmanı. pyserial kütüphanesi hem gerçek seri portu
#   (macOS'ta /dev/cu.usbserial-..., Windows'ta COM3) hem de sahte ESP32'nin
#   socket://127.0.0.1:7600 adresini aynı şekilde açar; bu yüzden gerçek ESP32 gelince
#   yalnızca adres değişir. Gelen baytları biriktirip satır sonundan böler. Satır sonu
#   hiç gelmezse (örneğin hız ayarı yanlışsa) biriken veriyi bozuk bir satır olarak
#   verir. Projede pyserial kullanan tek dosya budur.

from collections.abc import Iterator

try:
    import serial
except ImportError as hata:
    raise ImportError("pyserial kurulu değil; kurulum için README.md, 7. bölüm") from hata


EN_UZUN_SATIR = 1000


class BaglantiKurulamadi(Exception):
    pass


class SeriKaynak:
    def __init__(self, adres: str, baud: int = 115200, zaman_asimi_s: float = 1.0) -> None:
        try:
            self._port = serial.serial_for_url(adres, baudrate=baud, timeout=zaman_asimi_s)
        except (serial.SerialException, OSError, ValueError) as hata:
            raise BaglantiKurulamadi(f"{adres}: {hata}") from hata

    def satirlar(self) -> Iterator[str]:
        tampon = b""
        while True:
            try:
                parca = self._port.read(self._port.in_waiting or 1)
            except (serial.SerialException, OSError):
                return
            if not parca:
                continue
            tampon += parca
            *tam_satirlar, tampon = tampon.split(b"\n")
            for satir in tam_satirlar:
                yield satir.decode("ascii", errors="replace").rstrip("\r")
            if len(tampon) > EN_UZUN_SATIR:
                yield tampon.decode("ascii", errors="replace")
                tampon = b""

    def kapat(self) -> None:
        soket = getattr(self._port, "_socket", None)
        if soket is not None:
            soket.close()
        self._port.close()
