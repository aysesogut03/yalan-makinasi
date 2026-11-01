# OKUYUCU: Veri hattının asıl işi. ESP32'den gelen satırları, diğer katmanların
#   anlayacağı kayıtlara çevirir ve onlara teslim eder.
#
# BU DOSYA (okuyucu/hat.py): Satırı sırayla dört alt katmandan geçiren "bant".
#
# AYRINTI: Gelen her satırı önce ham haliyle kaydettirir, sonra ayrıştırmaya verir
#   (bozuksa "bozuk" olayı yazdırır), çıkan mesajı dönüştürmeye verir ve oluşan
#   kayıtları bütün alıcılara dağıtır. Bir alıcı hata verirse diğerleri çalışmaya devam
#   eder. Bağlantı kopunca ya da Ctrl+C'ye basılınca her şeyi düzgünce kapatır. Bozuk
#   satırın olaya yalnızca ilk 80 karakteri yazılır; tamamı ham.log'da kalır.

import sys

from sozlesme import HamSatir, Kayit, Olay, OlayTuru, VeriAlici

from .kurallar import Ayristirici, BozukSatir, Donusturucu, Saat, SatirKaynagi

OLAYDA_EN_FAZLA_KARAKTER = 80


class VeriHatti:
    def __init__(
        self,
        kaynak: SatirKaynagi,
        ayristirici: Ayristirici,
        donusturucu: Donusturucu,
        alicilar: list[VeriAlici],
        saat: Saat,
    ) -> None:
        self._kaynak = kaynak
        self._ayristirici = ayristirici
        self._donusturucu = donusturucu
        self._alicilar = alicilar
        self._saat = saat
        self._hata_veren_alicilar: set[int] = set()

    def calistir(self) -> None:
        self._dagit(Olay(self._simdi(), OlayTuru.BAGLANTI, "okuma başladı"))
        try:
            for satir in self._kaynak.satirlar():
                self._isle(satir, self._simdi())
        finally:
            self._dagit(Olay(self._simdi(), OlayTuru.BAGLANTI, "okuma bitti"))
            try:
                self._kaynak.kapat()
            except Exception as hata:
                print(f"UYARI: bağlantı kapatılırken hata: {hata!r}", file=sys.stderr)
            for alici in self._alicilar:
                self._guvenle(alici, alici.kapat)

    def _simdi(self) -> float:
        return round(self._saat.simdi(), 3)

    def _isle(self, satir: str, t_gelis: float) -> None:
        self._dagit(HamSatir(t_gelis, satir))
        try:
            mesaj = self._ayristirici.ayristir(satir)
        except BozukSatir as hata:
            ozet = satir[:OLAYDA_EN_FAZLA_KARAKTER] + ("…" if len(satir) > OLAYDA_EN_FAZLA_KARAKTER else "")
            self._dagit(Olay(t_gelis, OlayTuru.BOZUK, f"{hata} | satır: {ozet!r}"))
            return
        for kayit in self._donusturucu.donustur(mesaj, t_gelis):
            self._dagit(kayit)

    def _dagit(self, kayit: Kayit) -> None:
        for alici in self._alicilar:
            self._guvenle(alici, alici.al, kayit)

    def _guvenle(self, alici: VeriAlici, metot, *argumanlar) -> None:
        try:
            metot(*argumanlar)
        except Exception as hata:
            if id(alici) not in self._hata_veren_alicilar:
                self._hata_veren_alicilar.add(id(alici))
                print(
                    f"UYARI: {type(alici).__name__} hata verdi ve atlandı: {hata!r} "
                    "(bu alıcının sonraki hataları gösterilmeyecek)",
                    file=sys.stderr,
                )
