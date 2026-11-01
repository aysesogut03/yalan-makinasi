# SİMÜLATÖR: Sahte ESP32. Kart gelene kadar gerçek ESP32'nin yerine veri üretir.
#
# BU DOSYA (simulator/sensorler.py): Sahte GSR, ivmeölçer ve nabız değerleri üretir.
#
# AYRINTI: Basit dalgalar (sinüs) ve biraz rastgele gürültü kullanılır; stres tepkisi
#   taklit edilmez. GSR yavaşça iner çıkar. İvmeölçer, karına bantlanmış gibi nefesle
#   hafifçe öne arkaya eğilir (dakikada 15 nefes). Nabız dakikada yaklaşık 75'tir. Aynı
#   tohumla (--tohum) çalıştırılınca aynı sayılar üretilir.

import math
import random

INT16_EN_KUCUK = -32768
INT16_EN_BUYUK = 32767

IVME_OLCEGI = {2: 16384, 4: 8192, 8: 4096, 16: 2048}
GYRO_OLCEGI = {250: 131.0, 500: 65.5, 1000: 32.8, 2000: 16.4}


def _int16(deger: float) -> int:
    return max(INT16_EN_KUCUK, min(INT16_EN_BUYUK, round(deger)))


class SahteGsr:
    def __init__(
        self,
        rastgele: random.Random,
        taban_mv: float = 1500.0,
        dalga_mv: float = 40.0,
        dalga_suresi_s: float = 90.0,
        gurultu_mv: float = 3.0,
    ) -> None:
        self._rastgele = rastgele
        self._taban_mv = taban_mv
        self._dalga_mv = dalga_mv
        self._dalga_suresi_s = dalga_suresi_s
        self._gurultu_mv = gurultu_mv

    def oku_mv(self, t: float) -> int:
        dalga =self._dalga_mv * math.sin(2 * math.pi * t / self._dalga_suresi_s)
        gurultu = self._rastgele.gauss(0, self._gurultu_mv)
        return max(0, min(3300, round(self._taban_mv + dalga + gurultu)))


class SahteIvme:
    def __init__(
        self,
        rastgele: random.Random,
        nefes_dk: float = 15.0,
        taban_egim_derece: float = 8.0,
        nefes_egim_derece: float = 1.5,
        ivme_gurultu_g: float = 0.004,
        gyro_gurultu_dps: float = 0.3,
        acc_araligi_g: int = 2,
        gyro_araligi_dps: int = 250,
    ) -> None:
        if acc_araligi_g not in IVME_OLCEGI:
            raise ValueError(f"İvme aralığı {sorted(IVME_OLCEGI)} değerlerinden biri olmalı")
        if gyro_araligi_dps not in GYRO_OLCEGI:
            raise ValueError(f"Dönüş aralığı {sorted(GYRO_OLCEGI)} değerlerinden biri olmalı")
        self._rastgele = rastgele
        self._nefes_hz = nefes_dk / 60
        self._taban_egim = taban_egim_derece
        self._nefes_egim = nefes_egim_derece
        self._ivme_gurultu = ivme_gurultu_g
        self._gyro_gurultu = gyro_gurultu_dps
        self.acc_araligi_g = acc_araligi_g
        self.gyro_araligi_dps = gyro_araligi_dps

    def oku(self, t: float) -> tuple[int, int, int, int, int, int]:
        acisal_frekans = 2 * math.pi * self._nefes_hz
        egim_derece = self._taban_egim + self._nefes_egim * math.sin(acisal_frekans * t)
        egim = math.radians(egim_derece)
        egim_hizi_dps = self._nefes_egim * acisal_frekans * math.cos(acisal_frekans * t)

        gurultu = self._rastgele.gauss
        ivme_g = (
            math.sin(egim) + gurultu(0, self._ivme_gurultu),
            gurultu(0, self._ivme_gurultu),
            math.cos(egim) + gurultu(0, self._ivme_gurultu),
        )
        donus_dps = (
            gurultu(0, self._gyro_gurultu),
            egim_hizi_dps + gurultu(0, self._gyro_gurultu),
            gurultu(0, self._gyro_gurultu),
        )

        ivme_olcegi = IVME_OLCEGI[self.acc_araligi_g]
        gyro_olcegi = GYRO_OLCEGI[self.gyro_araligi_dps]
        ax, ay, az = (_int16(deger * ivme_olcegi) for deger in ivme_g)
        gx, gy, gz = (_int16(deger * gyro_olcegi) for deger in donus_dps)
        return ax, ay, az, gx, gy, gz


class SahteNabiz:
    def __init__(
        self,
        rastgele: random.Random,
        nabiz_dk: float = 75.0,
        degiskenlik: float = 0.04,
    ) -> None:
        self._rastgele = rastgele
        self._ortalama_aralik = 60 / nabiz_dk
        self._degiskenlik = degiskenlik

    def sonraki_aralik(self) -> float:
        aralik = self._rastgele.gauss(self._ortalama_aralik, self._ortalama_aralik * self._degiskenlik)
        return max(0.3, aralik)
