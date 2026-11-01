# SİMÜLATÖR: Sahte ESP32. Kart gelene kadar gerçek ESP32'nin yerine veri üretir.
#
# BU DOSYA (simulator/protokol.py): Sayıları "S,1042,20840,..." gibi satırlara yazar.
#
# AYRINTI: Satırların nasıl göründüğü yalnızca burada yazılıdır (kuralları README.md'nin
#   4. bölümünde). Protokol değişirse cihaz.py değil bu dosya değişir.

SURUM = 1


def bilgi_satiri(seq: int, ms: int, hz: int, acc_g: int, gyro_dps: int) -> str:
    return f"I,{seq},{ms},v={SURUM},hz={hz},acc={acc_g},gyro={gyro_dps}"


def olcum_satiri(seq: int, ms: int, gsr_mv: int, ivme: tuple[int, int, int, int, int, int]) -> str:
    return ",".join(str(alan) for alan in ("S", seq, ms, gsr_mv, *ivme))


def atim_satiri(seq: int, ms: int) -> str:
    return f"B,{seq},{ms}"
