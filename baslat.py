# BAŞLATICI: Bütün sistemi tek komutla açar, Ctrl+C ile hepsini birlikte kapatır.
#
# BU DOSYA (baslat.py): Backend'i, arayüzü, ESP32 kaynağını ve veri hattını sırayla başlatır.
#
# AYRINTI: Her parça kendi klasöründe, kendi ortamıyla çalışır; bu dosya yalnızca onları
#   sırayla açar, kapılarının açılmasını bekler ve çıktılarını başlarına etiket koyarak tek
#   pencerede gösterir. Parçalardan biri beklenmedik şekilde kapanırsa hepsi kapatılır.
#   Yalnızca Python'un kendi kütüphanelerini kullanır; macOS ve Windows'ta çalışır.
#   Yeni bir bilgisayarda bir kez:
#     python3 baslat.py --kur              ortamları ve paketleri kurar
#   Çalıştırma:
#     python3 baslat.py                    sahte ESP32 ile (donanım gerekmez)
#     python3 baslat.py --wokwi            Wokwi ile (VS Code'da: Wokwi: Start Simulator)
#     python3 baslat.py --adres COM3       gerçek ESP32 ile (macOS: /dev/cu.usbserial-0001)
#     python3 baslat.py --goruntu          görüntü işlemeyi de açar (Windows, 8001 kapısı)
#   Windows'ta "python3" yerine "python" yazılır.

import argparse
import os
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path

KOK = Path(__file__).resolve().parent
WINDOWS = os.name == "nt"
ARAYUZ_ADRESI = "http://localhost:5173"
WOKWI_KAPISI = 4000


def ortam_python(klasor: Path) -> Path:
    return klasor / ".venv" / ("Scripts/python.exe" if WINDOWS else "bin/python")


def npm_komutu() -> str:
    return "npm.cmd" if WINDOWS else "npm"


def kapi_acik_mi(kapi: int) -> bool:
    for adres in ("127.0.0.1", "::1"):
        aile = socket.AF_INET6 if ":" in adres else socket.AF_INET
        try:
            with socket.socket(aile, socket.SOCK_STREAM) as s:
                s.settimeout(0.3)
                if s.connect_ex((adres, kapi)) == 0:
                    return True
        except OSError:
            pass
    return False


@dataclass
class Parca:
    ad: str
    komut: list[str]
    klasor: Path
    kapi: int
    bekleme_s: float = 40
    surec: subprocess.Popen | None = field(default=None, repr=False)


class Yonetici:
    def __init__(self) -> None:
        self._parcalar: list[Parca] = []
        self._yazma_kilidi = threading.Lock()

    def yaz(self, ad: str, metin: str) -> None:
        with self._yazma_kilidi:
            print(f"[{ad}] {metin}", flush=True)

    def baslat(self, parca: Parca) -> None:
        ortam = dict(os.environ, PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
        ayar = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if WINDOWS else {"start_new_session": True}
        self.yaz(parca.ad, "başlatılıyor…")
        parca.surec = subprocess.Popen(
            parca.komut, cwd=parca.klasor, env=ortam,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **ayar,
        )
        self._parcalar.append(parca)
        threading.Thread(target=self._ciktiyi_aktar, args=(parca,), daemon=True).start()
        self._hazir_olmasini_bekle(parca)

    def _ciktiyi_aktar(self, parca: Parca) -> None:
        for satir in parca.surec.stdout:
            metin = satir.decode("utf-8", errors="replace").rstrip()
            if metin:
                self.yaz(parca.ad, metin)

    def _hazir_olmasini_bekle(self, parca: Parca) -> None:
        bitis = time.monotonic() + parca.bekleme_s
        while time.monotonic() < bitis:
            if parca.surec.poll() is not None:
                raise RuntimeError(f"{parca.ad} açılırken kapandı (yukarıdaki [{parca.ad}] satırlarına bakın)")
            if kapi_acik_mi(parca.kapi):
                self.yaz(parca.ad, f"hazır (kapı {parca.kapi})")
                return
            time.sleep(0.3)
        raise RuntimeError(f"{parca.ad} {parca.bekleme_s:.0f} saniyede hazır olmadı")

    def kapanan_var_mi(self) -> Parca | None:
        return next((p for p in self._parcalar if p.surec.poll() is not None), None)

    def hepsini_kapat(self) -> None:
        for parca in reversed(self._parcalar):
            if parca.surec.poll() is None:
                self.yaz(parca.ad, "kapatılıyor…")
                self._durdur(parca.surec)
        self._parcalar.clear()

    def _durdur(self, surec: subprocess.Popen) -> None:
        if WINDOWS:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(surec.pid)], capture_output=True)
            return
        for isaret, sure in ((signal.SIGINT, 5), (signal.SIGTERM, 3), (signal.SIGKILL, 2)):
            try:
                os.killpg(surec.pid, isaret)
            except ProcessLookupError:
                return
            try:
                surec.wait(timeout=sure)
                return
            except subprocess.TimeoutExpired:
                continue


def parcalari_hazirla(argumanlar: argparse.Namespace) -> tuple[list[Parca], str | None]:
    veri_hatti, backend = KOK / "veri_hatti", KOK / "backend"
    parcalar = [
        Parca("backend", [str(ortam_python(backend)), "-m", "uvicorn", "main:app", "--port", "8000",
                          "--log-level", "warning"], backend, 8000),
        Parca("arayüz", [npm_komutu(), "run", "dev", "--", "--port", "5173", "--strictPort"], KOK / "arayuz", 5173),
    ]
    adres = None
    if argumanlar.wokwi:
        adres = f"rfc2217://localhost:{WOKWI_KAPISI}"
    elif argumanlar.adres:
        adres = argumanlar.adres
    else:
        parcalar.append(Parca("sahte ESP32", [str(ortam_python(veri_hatti)), "-m", "simulator"], veri_hatti, 7600))
    okuyucu = [str(ortam_python(veri_hatti)), "-m", "okuyucu"] + (["--adres", adres] if adres else [])
    if argumanlar.sessiz:
        okuyucu.append("--sessiz")
    parcalar.append(Parca("veri hattı", okuyucu, veri_hatti, 8765, bekleme_s=20))
    if argumanlar.goruntu:
        goruntu = KOK / "goruntu_isleme"
        parcalar.append(Parca("görüntü", [str(ortam_python(goruntu)), "server.py", "--port", "8001"], goruntu, 8001,
                              bekleme_s=90))
    return parcalar, ("wokwi" if argumanlar.wokwi else None)


def eksikleri_bul(parcalar: list[Parca]) -> list[str]:
    eksik = []
    if shutil.which(npm_komutu()) is None:
        eksik.append("npm bulunamadı: Node.js kurulmalı (https://nodejs.org)")
    if not (KOK / "arayuz" / "node_modules").exists():
        eksik.append("arayuz/node_modules yok")
    for klasor in sorted({p.klasor for p in parcalar if p.klasor.name != "arayuz"}):
        if not ortam_python(klasor).exists():
            eksik.append(f"{klasor.name}/.venv yok")
    return eksik


def kur(goruntu: bool) -> int:
    klasorler = [KOK / "veri_hatti", KOK / "backend"] + ([KOK / "goruntu_isleme"] if goruntu else [])
    for klasor in klasorler:
        print(f"[kurulum] {klasor.name}: Python ortamı ve paketleri…", flush=True)
        if not ortam_python(klasor).exists():
            subprocess.run([sys.executable, "-m", "venv", str(klasor / ".venv")], check=True)
        subprocess.run([str(ortam_python(klasor)), "-m", "pip", "install", "-q", "-r", "requirements.txt"],
                       cwd=klasor, check=True)
    print("[kurulum] arayuz: npm paketleri…", flush=True)
    npm_islem = "ci" if (KOK / "arayuz" / "package-lock.json").exists() else "install"
    subprocess.run([npm_komutu(), npm_islem], cwd=KOK / "arayuz", check=True)
    print("[kurulum] tamam. Çalıştırmak için: python3 baslat.py", flush=True)
    return 0


def wokwiyi_bekle(yonetici: Yonetici) -> None:
    if kapi_acik_mi(WOKWI_KAPISI):
        return
    yonetici.yaz("wokwi", "VS Code'da Cmd/Ctrl+Shift+P → 'Wokwi: Start Simulator' ile simülasyonu başlatın…")
    bitis = time.monotonic() + 180
    while not kapi_acik_mi(WOKWI_KAPISI):
        if time.monotonic() > bitis:
            raise RuntimeError(f"Wokwi 3 dakikada açılmadı ({WOKWI_KAPISI} kapısı kapalı)")
        time.sleep(0.5)
    yonetici.yaz("wokwi", "simülasyon açık")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    komut_satiri = argparse.ArgumentParser(prog="python3 baslat.py", description="Bütün sistemi tek komutla açar.")
    kaynak = komut_satiri.add_mutually_exclusive_group()
    kaynak.add_argument("--wokwi", action="store_true", help="Wokwi simülasyonuna bağlan (4000 kapısı)")
    kaynak.add_argument("--adres", help="gerçek ESP32'nin seri portu (COM3, /dev/cu.usbserial-0001)")
    komut_satiri.add_argument("--goruntu", action="store_true", help="görüntü işlemeyi de aç (Windows, 8001 kapısı)")
    komut_satiri.add_argument("--sessiz", action="store_true", help="veri hattının saniyelik özetini gösterme")
    komut_satiri.add_argument("--tarayici-yok", action="store_true", help="tarayıcıyı kendiliğinden açma")
    komut_satiri.add_argument("--kur", action="store_true", help="ortamları ve paketleri kur, sonra çık")
    argumanlar = komut_satiri.parse_args(argv)

    if argumanlar.kur:
        return kur(argumanlar.goruntu)

    parcalar, bekle = parcalari_hazirla(argumanlar)
    eksik = eksikleri_bul(parcalar)
    if eksik:
        print("Kurulum eksik:\n  - " + "\n  - ".join(eksik) + "\nÖnce şunu çalıştırın: python3 baslat.py --kur")
        return 1
    dolu = [f"{p.kapi} ({p.ad})" for p in parcalar if kapi_acik_mi(p.kapi)]
    if dolu:
        print("Bu kapılar başka bir program tarafından kullanılıyor: " + ", ".join(dolu)
              + "\nÖnceki çalıştırma açık kalmış olabilir; onu kapatıp yeniden deneyin.")
        return 1

    yonetici = Yonetici()
    try:
        for parca in parcalar:
            if parca.ad == "veri hattı" and bekle == "wokwi":
                wokwiyi_bekle(yonetici)
            yonetici.baslat(parca)
        yonetici.yaz("başlatıcı", f"sistem hazır: {ARAYUZ_ADRESI}  (giriş: admin / 123, kapatmak için Ctrl+C)")
        if not argumanlar.tarayici_yok:
            webbrowser.open(ARAYUZ_ADRESI)
        while True:
            kapanan = yonetici.kapanan_var_mi()
            if kapanan:
                yonetici.yaz("başlatıcı", f"{kapanan.ad} kapandı; bütün sistem kapatılıyor")
                return 1
            time.sleep(0.5)
    except KeyboardInterrupt:
        print(flush=True)
        yonetici.yaz("başlatıcı", "kapatılıyor…")
        return 0
    except RuntimeError as hata:
        yonetici.yaz("başlatıcı", f"HATA: {hata}")
        return 1
    finally:
        yonetici.hepsini_kapat()


if __name__ == "__main__":
    sys.exit(main())
