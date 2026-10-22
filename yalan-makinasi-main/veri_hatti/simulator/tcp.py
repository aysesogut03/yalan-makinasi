# SİMÜLATÖR: Sahte ESP32. Kart gelene kadar gerçek ESP32'nin yerine veri üretir.
#
# BU DOSYA (simulator/tcp.py): USB kablosunun yerini tutar: satırları okuyucuya iletir.
#
# AYRINTI: Sahte ESP32 bu bilgisayarda 7600 numaralı TCP kapısını açar ve bağlanan
#   okuyucuya satırları gönderir. Okuyucu bu adresi pyserial ile gerçek bir seri port
#   gibi açtığı için okuyucunun kodu gerçek ESP32 ile aynı kalır. Yalnızca bu
#   bilgisayardan gelen bağlantıları kabul eder. 7000 kapısı kullanılmaz, çünkü
#   macOS'ta onu AirPlay dinler; adres de localhost değil 127.0.0.1 yazılır, yoksa
#   bağlantı IPv6'dan AirPlay'e gidebilir.

import socket


class BaglantiKoptu(Exception):
    pass


class TcpSunucu:
    def __init__(self, kapi: int = 7600) -> None:
        self._soket = socket.create_server(("127.0.0.1", kapi))

    @property
    def kapi(self) -> int:
        return self._soket.getsockname()[1]

    def baglanti_bekle(self) -> "TcpSatirCikisi":
        istemci, _ = self._soket.accept()
        return TcpSatirCikisi(istemci)

    def kapat(self) -> None:
        self._soket.close()

    def __enter__(self) -> "TcpSunucu":
        return self

    def __exit__(self, *_) -> None:
        self.kapat()


class TcpSatirCikisi:
    def __init__(self, soket: socket.socket) -> None:
        self._soket = soket

    def gonder(self, satir: str) -> None:
        try:
            self._soket.sendall((satir + "\n").encode("ascii"))
        except OSError as hata:
            raise BaglantiKoptu() from hata

    def kapat(self) -> None:
        self._soket.close()
