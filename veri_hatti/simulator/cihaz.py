# SİMÜLATÖR: Sahte ESP32. Kart gelene kadar gerçek ESP32'nin yerine veri üretir.
#
# BU DOSYA (simulator/cihaz.py): ESP32'nin "beyni": hangi satırı ne zaman göndereceğine
#   karar verir.
#
# AYRINTI: Gerçek ESP32 kodundaki (Arduino) yapıya benzer: _setup açılışta bir kez
#   çalışır ve I satırını gönderir; _loop her 20 ms'de bir çalışır, arada kalp atımı
#   olduysa önce B satırını, sonra ölçüm (S) satırını gönderir. Her satıra bir sıra
#   numarası ve ESP32 zamanı koyar. Gerçek ESP32 kodu yazılırken bu akış C++'a
#   taşınacak.

from . import protokol
from .kurallar import GsrSensoru, IvmeSensoru, NabizSensoru, Saat, SatirCikisi


class SahteEsp32:
    def __init__(
        self,
        saat: Saat,
        gsr: GsrSensoru,
        ivme: IvmeSensoru,
        nabiz: NabizSensoru,
        cikis: SatirCikisi,
        hz: int = 50,
    ) -> None:
        if hz <= 0:
            raise ValueError("hz pozitif olmalı")
        self._saat = saat
        self._gsr = gsr
        self._ivme = ivme
        self._nabiz = nabiz
        self._cikis = cikis
        self._hz = hz
        self._seq = 0
        self._olcum_no = 0
        self._baslangic = 0.0
        self._sonraki_atim = 0.0

    def calistir(self, sure_s: float | None = None) -> None:
        self._setup()
        while sure_s is None or self._siradaki_olcum_ani() < sure_s:
            self._loop()

    def _setup(self) -> None:
        self._baslangic = self._saat.simdi()
        self._sonraki_atim = self._nabiz.sonraki_aralik()
        self._gonder(
            protokol.bilgi_satiri(
                self._seq, 0, self._hz, self._ivme.acc_araligi_g, self._ivme.gyro_araligi_dps
            )
        )

    def _loop(self) -> None:
        an = self._siradaki_olcum_ani()
        self._bekle(an)
        while self._sonraki_atim <= an:
            self._gonder(protokol.atim_satiri(self._seq, _ms(self._sonraki_atim)))
            self._sonraki_atim += self._nabiz.sonraki_aralik()
        self._gonder(
            protokol.olcum_satiri(self._seq, _ms(an), self._gsr.oku_mv(an), self._ivme.oku(an))
        )
        self._olcum_no += 1

    def _siradaki_olcum_ani(self) -> float:
        return self._olcum_no / self._hz

    def _bekle(self, an: float) -> None:
        kalan = an - (self._saat.simdi() - self._baslangic)
        if kalan > 0:
            self._saat.uyu(kalan)

    def _gonder(self, satir: str) -> None:
        self._cikis.gonder(satir)
        self._seq += 1


def _ms(saniye: float) -> int:
    return round(saniye * 1000)
