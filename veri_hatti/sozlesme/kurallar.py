# SÖZLEŞME: Diğer gruplarla ortak sözlük. Onlara verdiğimiz verinin biçimini tanımlar;
#   diğer katmanlar bizim kodumuzdan yalnızca bu klasörü kullanır.
#
# BU DOSYA (sozlesme/kurallar.py): "Kayıt alan her program al() ve kapat() metotlarına
#   sahip olmalı" kuralı.
#
# AYRINTI: Bu kuralın adı VeriAlici. Veri hattı kayıtlarını kimin kullandığını bilmez;
#   yalnızca bu kurala uyan alıcılara teslim eder. CSV kaydedici de bir alıcıdır,
#   ileride sinyal işleme de olabilir. Alıcı tanımadığı kayıt türlerini yok sayar. Örnek
#   bir alıcı README.md'nin 5. bölümünde.

from typing import Protocol

from .kayitlar import Kayit


class VeriAlici(Protocol):
    def al(self, kayit: Kayit) -> None:
        ...

    def kapat(self) -> None:
        ...
