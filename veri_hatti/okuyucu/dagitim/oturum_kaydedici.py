# OKUYUCU: Veri hattının asıl işi. ESP32'den gelen satırları, diğer katmanların
#   anlayacağı kayıtlara çevirir ve onlara teslim eder.
#
# BU DOSYA (okuyucu/dagitim/oturum_kaydedici.py): Sonucu kayitlar/ klasöründeki
#   dosyalara yazar.
#
# AYRINTI: Her test için kayitlar/ altında tarih ve saatle adlandırılmış bir klasör açar
#   (örnek: kayitlar/2026-10-18_14-30-05/) ve içine şunları yazar:
#     olcumler.csv   ölçümler (A ve B grupları kullanır)
#     atimlar.csv    kalp atımlarının zamanları
#     olaylar.csv    kayıp ya da bozuk satır, hata, yeniden başlama, bağlantı olayları
#     oturum.json    testin bilgileri: başlangıç, bitiş, kaynak, ESP32 ayarları
#     ham.log        ESP32'den gelen her satır, olduğu gibi
#   Her satır hemen diske yazılır; program beklenmedik şekilde kapanırsa veri kaybolmaz.

import csv
import json
import time
from dataclasses import astuple, fields
from pathlib import Path

from sozlesme import Atim, CihazBilgisi, HamSatir, Kayit, Olay, Olcum

from ..kurallar import Saat


class OturumKaydedici:
    def __init__(self, kok_klasor: Path, saat: Saat, kaynak: str, gsr_kalibrasyon: int | None = None) -> None:
        self._saat = saat
        baslangic = round(saat.simdi(), 3)
        self.klasor = _yeni_klasor(kok_klasor, baslangic)
        self._oturum = {
            "baslangic": baslangic,
            "baslangic_yerel": _yerel_saat(baslangic),
            "bitis": None,
            "bitis_yerel": None,
            "kaynak": kaynak,
            "protokol_surumu": None,
            "hz": None,
            "acc_g": None,
            "gyro_dps": None,
            "gsr_kalibrasyon": gsr_kalibrasyon,
        }
        self._oturumu_yaz()
        self._dosyalar = []
        self._olcumler = self._csv_ac("olcumler.csv", Olcum)
        self._atimlar = self._csv_ac("atimlar.csv", Atim)
        self._olaylar = self._csv_ac("olaylar.csv", Olay)
        self._ham = self._dosya_ac("ham.log")
        self._kapandi = False

    def al(self, kayit: Kayit) -> None:
        match kayit:
            case Olcum():
                self._olcumler.writerow([_hucre(deger) for deger in astuple(kayit)])
            case Atim():
                self._atimlar.writerow([_hucre(deger) for deger in astuple(kayit)])
            case Olay():
                self._olaylar.writerow([_hucre(kayit.t), kayit.tur.value, kayit.ayrinti])
            case HamSatir():
                self._ham.write(f"{kayit.t_gelis:.3f} {kayit.metin}\n")
            case CihazBilgisi():
                self._oturum.update(
                    protokol_surumu=kayit.surum, hz=kayit.hz, acc_g=kayit.acc_g, gyro_dps=kayit.gyro_dps
                )
                self._oturumu_yaz()

    def kapat(self) -> None:
        if self._kapandi:
            return
        self._kapandi = True
        for dosya in self._dosyalar:
            dosya.close()
        bitis = round(self._saat.simdi(), 3)
        self._oturum.update(bitis=bitis, bitis_yerel=_yerel_saat(bitis))
        self._oturumu_yaz()

    def _dosya_ac(self, ad: str):
        dosya = open(self.klasor / ad, "w", encoding="utf-8", newline="", buffering=1)
        self._dosyalar.append(dosya)
        return dosya

    def _csv_ac(self, ad: str, tip):
        yazici = csv.writer(self._dosya_ac(ad), lineterminator="\n")
        yazici.writerow([alan.name for alan in fields(tip)])
        return yazici

    def _oturumu_yaz(self) -> None:
        metin = json.dumps(self._oturum, ensure_ascii=False, indent=2)
        (self.klasor / "oturum.json").write_text(metin + "\n", encoding="utf-8")


def _yeni_klasor(kok_klasor: Path, baslangic: float) -> Path:
    ad = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(baslangic))
    klasor = kok_klasor / ad
    sira = 2
    while klasor.exists():
        klasor = kok_klasor / f"{ad}_{sira}"
        sira += 1
    klasor.mkdir(parents=True)
    return klasor


def _yerel_saat(t: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


def _hucre(deger):
    if isinstance(deger, float):
        if deger == 0:
            return "0"
        return f"{deger:.6f}".rstrip("0").rstrip(".")
    return deger
