# OKUYUCU: Veri hattının asıl işi. ESP32'den gelen satırları, diğer katmanların
#   anlayacağı kayıtlara çevirir ve onlara teslim eder.
#
# BU DOSYA (okuyucu/donusturme/zaman_eslestirici.py): ESP32'nin saatini bilgisayarın
#   saatine çevirir.
#
# AYRINTI: ESP32 yalnızca "açıldığımdan beri şu kadar ms geçti" der. İlk satır
#   geldiğinde "ESP32'nin şu ms'si = bilgisayarın şu anı" diye eşleştirme yapılır;
#   sonraki her zaman t = t0 + (esp_ms - ms0) / 1000 ile hesaplanır. Bütün katmanlar
#   aynı saati kullanabilsin diye gereklidir. Sınırı: ESP32 saatinin yavaş kayması
#   düzeltilmez (15 dakikada birkaç on ms).

ZAMAN_BASAMAK = 3


class ZamanEslestirici:
    def __init__(self) -> None:
        self._t0: float | None = None
        self._ms0 = 0

    def bilgisayar_zamani(self, esp_ms: int, t_gelis: float) -> float:
        if self._t0 is None:
            self._t0 = t_gelis
            self._ms0 = esp_ms
        return round(self._t0 + (esp_ms - self._ms0) / 1000, ZAMAN_BASAMAK)

    def sifirla(self) -> None:
        self._t0 = None
