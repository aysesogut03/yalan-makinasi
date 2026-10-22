# OKUYUCU: Veri hattının asıl işi. ESP32'den gelen satırları, diğer katmanların
#   anlayacağı kayıtlara çevirir ve onlara teslim eder.
#
# BU KLASÖR (okuyucu/dagitim/): 4. alt katman. Kayıtları, onları kullanacak yerlere
#   teslim eder.
#
# AYRINTI:
#   oturum_kaydedici.py  sonucu kayitlar/ klasöründeki dosyalara yazar
#   konsol_alici.py      çalışırken ekrana saniyede bir özet basar
#   Yeni bir teslim yeri (örneğin A grubu için canlı yayın) buraya yeni bir dosya olarak
#   eklenir; diğer alt katmanlar değişmez.

from .konsol_alici import KonsolAlici
from .oturum_kaydedici import OturumKaydedici

__all__ = ["KonsolAlici", "OturumKaydedici"]
