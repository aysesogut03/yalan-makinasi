# OKUYUCU: Veri hattının asıl işi. ESP32'den gelen satırları, diğer katmanların
#   anlayacağı kayıtlara çevirir ve onlara teslim eder.
#
# BU DOSYA (okuyucu/dagitim/konsol_alici.py): Çalışırken ekrana saniyede bir özet basar.
#
# AYRINTI: Verinin akıp akmadığını görmek içindir, kayıt tutmaz. Olayları (kayıp satır
#   gibi) hemen gösterir. Örnek çıktı:
#     14:30:06  ölçüm  50  atım 1  GSR 1501 mV  ivme z +0.990 g

import time
from collections.abc import Callable

from sozlesme import Atim, CihazBilgisi, Kayit, Olay, Olcum


class KonsolAlici:
    def __init__(self, yaz: Callable[[str], None] = print, aralik_s: float = 1.0) -> None:
        self._yaz = yaz
        self._aralik_s = aralik_s
        self._donem_basi: float | None = None
        self._olcum_sayisi = 0
        self._atim_sayisi = 0
        self._son_olcum: Olcum | None = None

    def al(self, kayit: Kayit) -> None:
        match kayit:
            case Olcum():
                if self._donem_basi is None:
                    self._donem_basi = kayit.t
                elif kayit.t - self._donem_basi >= self._aralik_s:
                    self._ozet_yaz()
                    self._donem_basi = kayit.t
                self._olcum_sayisi += 1
                self._son_olcum = kayit
            case Atim():
                self._atim_sayisi += 1
            case Olay():
                self._yaz(f"[olay] {kayit.tur.value}: {kayit.ayrinti}")
            case CihazBilgisi():
                self._yaz(
                    f"[cihaz] protokol v{kayit.surum}, {kayit.hz} Hz, "
                    f"±{kayit.acc_g} g, ±{kayit.gyro_dps} °/s"
                )

    def kapat(self) -> None:
        pass

    def _ozet_yaz(self) -> None:
        olcum = self._son_olcum
        saat = time.strftime("%H:%M:%S", time.localtime(olcum.t))
        self._yaz(
            f"{saat}  ölçüm {self._olcum_sayisi:3d}  atım {self._atim_sayisi}  "
            f"GSR {olcum.gsr_mv} mV  ivme z {olcum.az_g:+.3f} g"
        )
        self._olcum_sayisi = 0
        self._atim_sayisi = 0
