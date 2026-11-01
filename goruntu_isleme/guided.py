"""Rehberli kayıt: soruları ekranda gösterir, etiketi (doğru/yalan) zamanlamaya göre OTOMATİK koyar.

El ile t/l tuşlarına basmak hataya açık (ilk 4 kayıtta hiç etiket yoktu) ve dengesiz veri
üretiyor. Burada sıra karıştırılmış, doğru/yalan sayısı eşit ve her bölüm aynı sürede.

Soru havuzu tasarımı: kişisel ve olgusal (cevabı sadece kişi bilir, uydurması kolay), evet/hayır
değil (kısa cevap az özellik verir), duygusal/hassas konu yok, hepsi benzer zorlukta 20-30 sn'lik
bir anlatım ister. Hangi sorunun doğru, hangisinin yalan cevaplanacağı rastgele atanır; böylece soru
türü etikete karışmaz (her soru tek kez, deneğe göre farklı koşulda sorulur).
Sınırlama: talimatla söylenen yalan, kendiliğinden söylenen yalandan farklı davranabilir.
"""
import random

from features import CALIBRATION_SECONDS

# Kalibrasyon (kontrol) soruları: DOĞRU, kısa, kolay; kişinin sakin konuşma davranışını yakalar.
CONTROL = [
    "Adın ne?",
    "Nerede yaşıyorsun?",
    "Bugün günlerden ne?",
    "Kaç yaşındasın?",
]

# Asıl sorular: her biri doğru VEYA yalan cevaplanabilir (uzunluk ~55 karakter: bant genişliği).
QUESTIONS = [
    "Bu sabahtan beri neler yaptın? Anlat.",
    "En son ne yedin, nerede ve kiminle? Anlat.",
    "Bulunduğun odayı tarif et: neler var?",
    "En son izlediğin film/dizi neydi? Konusunu anlat.",
    "Dün akşam yemekten sonra ne yaptın? Anlat.",
    "Telefonundaki son fotoğraf neyin? Anlat.",
    "Bu sabah evden nasıl çıktın? Yolda ne gördün?",
    "En son gittiğin yer neresiydi? Orada ne yaptın?",
    "Çantanda ya da cebinde şu an neler var?",
    "Dün öğle yemeğinde ne yedin? Anlat.",
    "Geçen hafta sonunu anlat: neler yaptın?",
    "En sevdiğin yemeği ve nasıl yapıldığını anlat.",
]


class Guided:
    INTRO = CALIBRATION_SECONDS   # sn: kontrol soruları, doğru cevaplar (kalibrasyonla aynı süre)
    BASELINE_FROM = 12  # intro'nun bu saniyesinden sonrası 'baseline' etiketli (10 sn'lik pencere dolsun)
    CONTROL_EVERY = 11  # sn: kontrol sorusu değişim aralığı
    REST = 6        # sn: sıradaki soruyu göster, etiket yok
    SPEAK = 30      # sn: konuşma
    SETTLE = 3      # konuşmanın ilk bu kadar saniyesi etiketsiz (başlama gecikmesi)

    def __init__(self, pairs=6, seed=None):
        pairs = min(pairs, len(QUESTIONS) // 2)          # her soru tek kez sorulur
        rng = random.Random(seed)
        order = ["truth"] * pairs + ["lie"] * pairs
        while True:                          # arka arkaya 3 aynı etiket olmasın
            rng.shuffle(order)
            if all(len(set(order[i:i + 3])) > 1 for i in range(len(order) - 2)):
                break
        qs = rng.sample(QUESTIONS, len(order))
        self.plan = list(zip(order, qs))     # (etiket, soru)
        self.t0 = None
        self.finished = False

    @property
    def duration(self):
        return self.INTRO + len(self.plan) * (self.REST + self.SPEAK)

    def state(self, now):
        """{'label','kind','title','text','left','index','total'} döndürür."""
        if self.t0 is None:
            self.t0 = now
        e = now - self.t0
        n = len(self.plan)
        if e < self.INTRO:
            q = CONTROL[int(e // self.CONTROL_EVERY) % len(CONTROL)]
            return dict(label="baseline" if e >= self.BASELINE_FROM else "", kind="rest",
                        title="KONTROL SORULARI (DOĞRU cevapla)", index=0, total=n,
                        text=f"SOR: {q}", left=self.INTRO - e)
        e -= self.INTRO
        slot = self.REST + self.SPEAK
        i = int(e // slot)
        if i >= n:
            self.finished = True
            return dict(label="", kind="done", title="KAYIT BİTTİ", index=n, total=n,
                        text="q ile çık, sonra: python evaluate.py", left=0)
        w = e - i * slot
        lab, q = self.plan[i]
        word = "DOĞRU SÖYLE" if lab == "truth" else "YALAN SÖYLE"
        if w < self.REST:
            return dict(label="", kind="rest", title=f"SIRADAKİ: {word}", index=i + 1,
                        total=n, text=f"Soru: {q}", left=self.REST - w)
        sp = w - self.REST
        hint = "" if lab == "truth" else "   (uydur, ikna edici ol)"
        return dict(label=lab if sp >= self.SETTLE else "", kind=lab,
                    title=f"ŞİMDİ: {word}", index=i + 1, total=n,
                    text=f"SOR: {q}{hint}", left=self.SPEAK - sp)
