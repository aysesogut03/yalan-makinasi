# OKUYUCU: Veri hattının asıl işi. ESP32'den gelen satırları, diğer katmanların
#   anlayacağı kayıtlara çevirir ve onlara teslim eder.
#
# BU DOSYA (okuyucu/donusturme/birim_cevirici.py): Ham sayıları birime çevirir (16384 →
#   1 g, 131 → 1 °/s).
#
# AYRINTI: MPU6050 ivmeyi ve dönüş hızını birimsiz tam sayı olarak verir. Kaç sayının 1
#   g ya da 1 °/s ettiği sensörün ölçüm aralığına bağlıdır (MPU6050 veri sayfası);
#   aralığı ESP32 açılışta I satırıyla bildirir. I satırı gelmezse varsayılan aralıklar
#   (±2 g, ±250 °/s) kullanılır. Sonuçlar ivmede 5, dönüş hızında 4 ondalık basamağa
#   yuvarlanır.

VARSAYILAN_ACC_G = 2
VARSAYILAN_GYRO_DPS = 250

GYRO_OLCEGI = {250: 131.0, 500: 65.5, 1000: 32.8, 2000: 16.4}

IVME_BASAMAK = 5
DONUS_BASAMAK = 4


class BirimCevirici:
    def __init__(self) -> None:
        self.ayarla(VARSAYILAN_ACC_G, VARSAYILAN_GYRO_DPS)

    def ayarla(self, acc_g: int, gyro_dps: int) -> None:
        self._ivme_olcegi = 32768 / acc_g
        self._donus_olcegi = GYRO_OLCEGI.get(gyro_dps, 32768 / gyro_dps)

    def ivme_g(self, ham: int) -> float:
        return round(ham / self._ivme_olcegi, IVME_BASAMAK)

    def donus_dps(self, ham: int) -> float:
        return round(ham / self._donus_olcegi, DONUS_BASAMAK)
