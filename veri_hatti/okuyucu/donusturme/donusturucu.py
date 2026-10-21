# OKUYUCU: Veri hattının asıl işi. ESP32'den gelen satırları, diğer katmanların
#   anlayacağı kayıtlara çevirir ve onlara teslim eder.
#
# BU DOSYA (okuyucu/donusturme/donusturucu.py): Diğer üç dosyayı kullanarak asıl
#   çeviriyi yapar: ESP32 mesajı → kayıt.
#
# AYRINTI: Her mesaj için sırayla: (1) ESP32 yeniden başladı mı, (2) arada satır
#   kayboldu mu, (3) ESP32 saatini bilgisayar saatine çevir, (4) mesajı kayda çevir;
#   ölçümlerde birimleri de çevir. Kaybolan satır ve yeniden başlama "olay" olarak
#   kaydedilir. I satırı hiç gelmezse varsayılan aralıklarla devam edilir ve bu bir kez
#   not edilir.

from sozlesme import Atim, CihazBilgisi, Kayit, Olay, OlayTuru, Olcum

from ..mesajlar import AtimMesaji, BilgiMesaji, HataMesaji, Mesaj, OlcumMesaji
from .birim_cevirici import VARSAYILAN_ACC_G, VARSAYILAN_GYRO_DPS, BirimCevirici
from .sira_takipcisi import SiraTakipcisi
from .zaman_eslestirici import ZamanEslestirici


class MesajDonusturucu:
    def __init__(self, sira: SiraTakipcisi, birim: BirimCevirici, zaman: ZamanEslestirici) -> None:
        self._sira = sira
        self._birim = birim
        self._zaman = zaman
        self._bilgi_geldi = False
        self._uyari_verildi = False

    def donustur(self, mesaj: Mesaj, t_gelis: float) -> list[Kayit]:
        kayitlar: list[Kayit] = []

        neden = self._yeniden_baslama_nedeni(mesaj)
        if neden:
            kayitlar.append(Olay(t_gelis, OlayTuru.YENIDEN_BASLAMA, neden))
            self._sifirla()

        kayip = self._sira.kayip_say(mesaj.seq)

        t = self._zaman.bilgisayar_zamani(mesaj.ms, t_gelis)
        if kayip:
            kayitlar.append(Olay(t, OlayTuru.KAYIP, f"{kayip} satır"))

        kayitlar.extend(self._kayda_cevir(mesaj, t))
        return kayitlar

    def _yeniden_baslama_nedeni(self, mesaj: Mesaj) -> str | None:
        if not self._sira.basladi:
            return None
        if isinstance(mesaj, BilgiMesaji):
            return "yeni I satırı geldi"
        if self._sira.geri_gitti_mi(mesaj.seq):
            return f"sıra numarası geri gitti ({self._sira.son} → {mesaj.seq})"
        return None

    def _sifirla(self) -> None:
        self._sira.sifirla()
        self._zaman.sifirla()
        self._birim.ayarla(VARSAYILAN_ACC_G, VARSAYILAN_GYRO_DPS)
        self._bilgi_geldi = False
        self._uyari_verildi = False

    def _kayda_cevir(self, mesaj: Mesaj, t: float) -> list[Kayit]:
        match mesaj:
            case BilgiMesaji():
                self._birim.ayarla(mesaj.acc_g, mesaj.gyro_dps)
                self._bilgi_geldi = True
                return [CihazBilgisi(t, mesaj.surum, mesaj.hz, mesaj.acc_g, mesaj.gyro_dps)]

            case OlcumMesaji():
                kayitlar: list[Kayit] = []
                if not self._bilgi_geldi and not self._uyari_verildi:
                    kayitlar.append(
                        Olay(
                            t,
                            OlayTuru.HATA,
                            f"I satırı gelmedi; varsayılan aralıklar kullanılıyor "
                            f"(±{VARSAYILAN_ACC_G} g, ±{VARSAYILAN_GYRO_DPS} °/s)",
                        )
                    )
                    self._uyari_verildi = True
                birim = self._birim
                kayitlar.append(
                    Olcum(
                        t=t,
                        seq=mesaj.seq,
                        esp_ms=mesaj.ms,
                        gsr_mv=mesaj.gsr,
                        ax_g=birim.ivme_g(mesaj.ax),
                        ay_g=birim.ivme_g(mesaj.ay),
                        az_g=birim.ivme_g(mesaj.az),
                        gx_dps=birim.donus_dps(mesaj.gx),
                        gy_dps=birim.donus_dps(mesaj.gy),
                        gz_dps=birim.donus_dps(mesaj.gz),
                    )
                )
                return kayitlar

            case AtimMesaji():
                return [Atim(t, mesaj.seq, mesaj.ms)]

            case HataMesaji():
                return [Olay(t, OlayTuru.HATA, mesaj.kod)]

        return []
