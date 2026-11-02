import csv
import json
import time
from collections import deque
from pathlib import Path

KAYIT_DIZINI = Path(__file__).resolve().parent.parent / "veri_hatti" / "kayitlar"
PENCERE_SN = 40
MIN_SURE_SN = 15
BAYAT_SN = 3
MIN_KAYIT_BAYT = 100000


def sayi(deger):
    try:
        return float(str(deger).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None


def oturum_klasorleri():
    if not KAYIT_DIZINI.exists():
        return []
    return sorted(k for k in KAYIT_DIZINI.iterdir() if k.is_dir())


def canli_mi(klasor):
    try:
        return time.time() - (klasor / "olcumler.csv").stat().st_mtime < 10
    except OSError:
        return False


def en_guncel_oturum():
    klasorler = oturum_klasorleri()
    for klasor in reversed(klasorler):
        try:
            boyut = (klasor / "olcumler.csv").stat().st_size
        except OSError:
            continue
        if boyut > MIN_KAYIT_BAYT or canli_mi(klasor):
            return klasor
    return klasorler[-1] if klasorler else None


def oturum_meta(klasor):
    try:
        with open(klasor / "oturum.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def csv_oku(yol):
    try:
        with open(yol, "r", encoding="utf-8-sig", newline="") as f:
            return [satir for satir in csv.DictReader(f) if satir]
    except OSError:
        return []


def _atim_araliklari(zamanlar):
    return [b - a for a, b in zip(zamanlar, zamanlar[1:]) if 0.3 <= b - a <= 2.0]


def nabiz_tahmini(atimlar, simdi):
    son = atimlar[-8:]
    if len(son) < 3 or simdi - son[-1] > 3:
        return None
    aralik = _atim_araliklari(son)
    if len(aralik) < 2:
        return None
    return round(60 / (sum(aralik) / len(aralik)))


def _hareketli_ortalama(x, pencere):
    yari = max(1, pencere // 2)
    toplam = [0.0]
    for v in x:
        toplam.append(toplam[-1] + v)
    n = len(x)
    cikis = []
    for i in range(n):
        a = max(0, i - yari)
        b = min(n, i + yari + 1)
        cikis.append((toplam[b] - toplam[a]) / (b - a))
    return cikis


def solunum_tahmini(ornekler):
    n = len(ornekler)
    if n < 50:
        return None
    sure = ornekler[-1][0] - ornekler[0][0]
    if sure < MIN_SURE_SN:
        return None
    fs = (n - 1) / sure
    ham = [v for _, v in ornekler]
    yumusak = _hareketli_ortalama(ham, round(fs * 0.6))
    egilim = _hareketli_ortalama(ham, round(fs * 10))
    s = [y - e for y, e in zip(yumusak, egilim)]
    ort = sum(s) / n
    sd = (sum((v - ort) ** 2 for v in s) / n) ** 0.5
    if sd < 1e-6:
        return None
    esik = sd * 0.3
    kesisimler = []
    altta = s[0] < -esik
    for i in range(1, n):
        if s[i] < -esik:
            altta = True
        elif altta and s[i] > esik:
            t = ornekler[i][0]
            if not kesisimler or t - kesisimler[-1] > 1.5:
                kesisimler.append(t)
            altta = False
    if len(kesisimler) < 3:
        return None
    aralik = (kesisimler[-1] - kesisimler[0]) / (len(kesisimler) - 1)
    dakika = 60 / aralik
    return round(dakika) if 4 <= dakika <= 40 else None


def oturum_ozeti(klasor):
    olcum = csv_oku(klasor / "olcumler.csv")
    atim = csv_oku(klasor / "atimlar.csv")
    zaman = [z for z in (sayi(r.get("t")) for r in olcum) if z is not None]
    gsr = [g for g in (sayi(r.get("gsr_mv")) for r in olcum) if g is not None]
    atim_t = [z for z in (sayi(r.get("t")) for r in atim) if z is not None]
    aralik = _atim_araliklari(atim_t)
    return {
        "ortalama_bpm": round(60 / (sum(aralik) / len(aralik)), 1) if aralik else 0.0,
        "ortalama_gsr": round(sum(gsr) / len(gsr), 1) if gsr else 0.0,
        "sure_sn": round(zaman[-1] - zaman[0], 1) if len(zaman) > 1 else 0.0,
        "olcum_sayisi": len(olcum),
        "atim_sayisi": len(atim),
    }


class _DosyaTakipci:
    def __init__(self, yol):
        self.yol = yol
        self.konum = 0
        self.baslik = None
        self.artik = ""

    def yeni_satirlar(self):
        try:
            with open(self.yol, "rb") as f:
                f.seek(self.konum)
                veri = f.read()
        except OSError:
            return []
        self.konum += len(veri)
        satirlar = (self.artik + veri.decode("utf-8", errors="ignore")).split("\n")
        self.artik = satirlar.pop()
        sonuc = []
        for satir in satirlar:
            satir = satir.strip("\r")
            if not satir:
                continue
            alanlar = next(csv.reader([satir]))
            if self.baslik is None:
                self.baslik = [a.lstrip("\ufeff").strip() for a in alanlar]
                continue
            sonuc.append(dict(zip(self.baslik, alanlar)))
        return sonuc


class CanliOkuyucu:
    def __init__(self, klasor, oynat=False):
        self.oynat = oynat
        self._olcum = _DosyaTakipci(klasor / "olcumler.csv")
        self._atim = _DosyaTakipci(klasor / "atimlar.csv")
        self._bek_olcum = deque()
        self._bek_atim = deque()
        self._sanal_t = None
        self._az = deque()
        self._atimlar = deque(maxlen=20)
        self._son_gsr = None
        self._son_t = 0.0
        self._son_gelis = 0.0

    @property
    def bitti(self):
        return self.oynat and self._sanal_t is not None and not self._bek_olcum

    def _al(self, bekleyen):
        alinan = []
        while bekleyen and (sayi(bekleyen[0].get("t")) or 0.0) <= self._sanal_t:
            alinan.append(bekleyen.popleft())
        return alinan

    def _isle(self, olcum, atim):
        for r in olcum:
            t, gsr, az = sayi(r.get("t")), sayi(r.get("gsr_mv")), sayi(r.get("az_g"))
            if t is None or gsr is None:
                continue
            self._son_t, self._son_gsr, self._son_gelis = t, gsr, time.monotonic()
            if az is not None:
                self._az.append((t, az))
        while self._az and self._son_t - self._az[0][0] > PENCERE_SN:
            self._az.popleft()
        for r in atim:
            t = sayi(r.get("t"))
            if t is not None:
                self._atimlar.append(t)

    def ilerle(self):
        olcum = self._olcum.yeni_satirlar()
        atim = self._atim.yeni_satirlar()
        if self.oynat:
            self._bek_olcum.extend(olcum)
            self._bek_atim.extend(atim)
            if self._sanal_t is None:
                if not self._bek_olcum:
                    return
                self._sanal_t = (sayi(self._bek_olcum[0].get("t")) or 0.0) + 20
            else:
                self._sanal_t += 1.0
            olcum = self._al(self._bek_olcum)
            atim = self._al(self._bek_atim)
        self._isle(olcum, atim)

    def nokta(self):
        if self._son_gsr is None or time.monotonic() - self._son_gelis > BAYAT_SN:
            return None
        nabiz = nabiz_tahmini(list(self._atimlar), self._son_t)
        solunum = solunum_tahmini(list(self._az))
        if nabiz is None or solunum is None:
            return None
        return {
            "timestamp": round(self._son_t * 1000),
            "heartRate": nabiz,
            "ppg": nabiz,
            "gsr": round(self._son_gsr, 1),
            "respiration": solunum,
        }