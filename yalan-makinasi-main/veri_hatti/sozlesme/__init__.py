# SÖZLEŞME: Diğer gruplarla ortak sözlük. Onlara verdiğimiz verinin biçimini tanımlar;
#   diğer katmanlar bizim kodumuzdan yalnızca bu klasörü kullanır.
#
# BU KLASÖR (sozlesme/): Kayıt tipleri ve kayıt alan programların uyacağı kural.
#
# AYRINTI:
#   kayitlar.py    Olcum, Atim, Olay gibi kayıt tipleri (CSV sütunları bunlar)
#   kurallar.py    "kayıt alan her program al() ve kapat() metotlarına sahip olmalı" kuralı
#   Kullanım: from sozlesme import Olcum, VeriAlici. Yalnızca ekip onayıyla değiştirilir
#   (projenin ana README.md'si, 4. bölüm).

from .kurallar import VeriAlici
from .kayitlar import Atim, CihazBilgisi, HamSatir, Kayit, Olay, OlayTuru, Olcum

__all__ = ["Atim", "CihazBilgisi", "HamSatir", "Kayit", "Olay", "OlayTuru", "Olcum", "VeriAlici"]
