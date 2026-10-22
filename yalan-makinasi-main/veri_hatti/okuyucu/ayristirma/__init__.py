# OKUYUCU: Veri hattının asıl işi. ESP32'den gelen satırları, diğer katmanların
#   anlayacağı kayıtlara çevirir ve onlara teslim eder.
#
# BU KLASÖR (okuyucu/ayristirma/): 2. alt katman. Satırı parçalarına ayırır, kurala
#   uyuyor mu diye kontrol eder.
#
# AYRINTI: İçinde protokol_v1.py var. Protokolün yeni bir sürümü gelirse buraya yeni bir
#   dosya eklenir.

from .protokol_v1 import ProtokolV1Ayristirici

__all__ = ["ProtokolV1Ayristirici"]
