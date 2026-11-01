# OKUYUCU: Veri hattının asıl işi. ESP32'den gelen satırları, diğer katmanların
#   anlayacağı kayıtlara çevirir ve onlara teslim eder.
#
# BU DOSYA (okuyucu/ayristirma/protokol_v1.py): Satırı parçalarına ayırır, kurala uyuyor
#   mu diye kontrol eder.
#
# AYRINTI: Okuyucunun 2. alt katmanı. Satırı virgüllerden böler, ilk harfe bakarak
#   türünü bulur (S ölçüm, B atım, I bilgi, E hata) ve her alanı README.md'nin 4.
#   bölümündeki kurallara göre denetler: alan sayısı, tam sayı mı, izin verilen aralıkta
#   mı. Kurala uyan satırı ESP32 mesajına çevirir, uymayanı nedenini söyleyerek
#   reddeder. Örnek: "B,1043,20851" → AtimMesaji(seq=1043, ms=20851)

import re

from ..kurallar import BozukSatir
from ..mesajlar import AtimMesaji, BilgiMesaji, HataMesaji, Mesaj, OlcumMesaji

SURUM = 1

GSR_EN_BUYUK_MV = 3300
INT16_EN_KUCUK = -32768
INT16_EN_BUYUK = 32767

_TAM_SAYI = re.compile(r"-?[0-9]+")
_HATA_KODU = re.compile(r"[A-Z0-9_]+")


class ProtokolV1Ayristirici:
    def __init__(self) -> None:
        self._cozuculer = {
            "I": self._bilgi,
            "S": self._olcum,
            "B": self._atim,
            "E": self._hata,
        }

    def ayristir(self, satir: str) -> Mesaj:
        satir = satir.rstrip("\r\n")
        if not satir:
            raise BozukSatir("boş satır")
        alanlar = satir.split(",")
        cozucu = self._cozuculer.get(alanlar[0])
        if cozucu is None:
            raise BozukSatir(f"bilinmeyen mesaj türü: {alanlar[0][:20]!r}")
        return cozucu(alanlar)

    def _bilgi(self, alanlar: list[str]) -> BilgiMesaji:
        seq, ms = _seq_ve_ms(alanlar)
        ayarlar = {}
        for alan in alanlar[3:]:
            ad, esittir, deger = alan.partition("=")
            if not esittir:
                raise BozukSatir(f"I satırında 'ad=değer' biçiminde olmayan alan: {alan!r}")
            ayarlar[ad] = deger
        eksik = [ad for ad in ("v", "hz", "acc", "gyro") if ad not in ayarlar]
        if eksik:
            raise BozukSatir(f"I satırında eksik alan: {', '.join(eksik)}")
        surum = _tam_sayi(ayarlar["v"], "v")
        if surum != SURUM:
            raise BozukSatir(f"desteklenmeyen protokol sürümü: {surum} (bu ayrıştırıcı v{SURUM} içindir)")
        return BilgiMesaji(
            seq=seq,
            ms=ms,
            surum=surum,
            hz=_pozitif(ayarlar["hz"], "hz"),
            acc_g=_pozitif(ayarlar["acc"], "acc"),
            gyro_dps=_pozitif(ayarlar["gyro"], "gyro"),
        )

    def _olcum(self, alanlar: list[str]) -> OlcumMesaji:
        _alan_sayisini_denetle(alanlar, 10)
        seq, ms = _seq_ve_ms(alanlar)
        gsr = _aralikta(alanlar[3], "gsr", 0, GSR_EN_BUYUK_MV)
        ax, ay, az, gx, gy, gz = (
            _aralikta(deger, ad, INT16_EN_KUCUK, INT16_EN_BUYUK)
            for ad, deger in zip(("ax", "ay", "az", "gx", "gy", "gz"), alanlar[4:])
        )
        return OlcumMesaji(seq, ms, gsr, ax, ay, az, gx, gy, gz)

    def _atim(self, alanlar: list[str]) -> AtimMesaji:
        _alan_sayisini_denetle(alanlar, 3)
        seq, ms = _seq_ve_ms(alanlar)
        return AtimMesaji(seq, ms)

    def _hata(self, alanlar: list[str]) -> HataMesaji:
        _alan_sayisini_denetle(alanlar, 4)
        seq, ms = _seq_ve_ms(alanlar)
        kod = alanlar[3]
        if not _HATA_KODU.fullmatch(kod):
            raise BozukSatir(f"geçersiz hata kodu: {kod!r}")
        return HataMesaji(seq, ms, kod)


def _alan_sayisini_denetle(alanlar: list[str], beklenen: int) -> None:
    if len(alanlar) != beklenen:
        raise BozukSatir(f"{alanlar[0]} satırında {beklenen} alan olmalı, {len(alanlar)} alan var")


def _seq_ve_ms(alanlar: list[str]) -> tuple[int, int]:
    if len(alanlar) < 3:
        raise BozukSatir(f"{alanlar[0]} satırında seq ve ms alanları eksik")
    return _aralikta(alanlar[1], "seq", 0, None), _aralikta(alanlar[2], "ms", 0, None)


def _tam_sayi(metin: str, ad: str) -> int:
    if not _TAM_SAYI.fullmatch(metin):
        raise BozukSatir(f"{ad} tam sayı değil: {metin!r}")
    return int(metin)


def _aralikta(metin: str, ad: str, en_kucuk: int, en_buyuk: int | None) -> int:
    deger = _tam_sayi(metin, ad)
    if deger < en_kucuk or (en_buyuk is not None and deger > en_buyuk):
        raise BozukSatir(f"{ad} izin verilen aralığın dışında: {deger}")
    return deger


def _pozitif(metin: str, ad: str) -> int:
    return _aralikta(metin, ad, 1, None)
