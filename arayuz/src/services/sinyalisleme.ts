export interface Ornek {
  t: number;
  v: number;
}

const MIN_SURE_SN = 15;

const hareketliOrtalama = (x: number[], pencere: number): number[] => {
  const n = x.length;
  const yari = Math.max(1, Math.floor(pencere / 2));
  const toplam = new Array<number>(n + 1).fill(0);
  for (let i = 0; i < n; i++) toplam[i + 1] = toplam[i] + x[i];
  const cikis = new Array<number>(n);
  for (let i = 0; i < n; i++) {
    const a = Math.max(0, i - yari);
    const b = Math.min(n, i + yari + 1);
    cikis[i] = (toplam[b] - toplam[a]) / (b - a);
  }
  return cikis;
};

export function nabizTahmini(atimlar: number[], simdi: number): number | null {
  const son = atimlar.slice(-8);
  if (son.length < 3 || simdi - son[son.length - 1] > 3) return null;
  const aralik: number[] = [];
  for (let i = 1; i < son.length; i++) {
    const d = son[i] - son[i - 1];
    if (d >= 0.3 && d <= 2.0) aralik.push(d);
  }
  if (aralik.length < 2) return null;
  const ort = aralik.reduce((a, b) => a + b, 0) / aralik.length;
  return Math.round(60 / ort);
}

export function solunumTahmini(ornekler: Ornek[]): number | null {
  const n = ornekler.length;
  if (n < 50) return null;
  const sure = ornekler[n - 1].t - ornekler[0].t;
  if (sure < MIN_SURE_SN) return null;

  const fs = (n - 1) / sure;
  const ham = ornekler.map((o) => o.v);
  const yumusak = hareketliOrtalama(ham, Math.round(fs * 0.6));
  const egilim = hareketliOrtalama(ham, Math.round(fs * 10));
  const s = yumusak.map((y, i) => y - egilim[i]);

  const ort = s.reduce((a, b) => a + b, 0) / n;
  const sd = Math.sqrt(s.reduce((a, b) => a + (b - ort) ** 2, 0) / n);
  if (sd < 1e-6) return null;
  const esik = sd * 0.3;

  const kesisimler: number[] = [];
  let altta = s[0] < -esik;
  for (let i = 1; i < n; i++) {
    if (s[i] < -esik) {
      altta = true;
    } else if (altta && s[i] > esik) {
      const t = ornekler[i].t;
      if (kesisimler.length === 0 || t - kesisimler[kesisimler.length - 1] > 1.5) kesisimler.push(t);
      altta = false;
    }
  }
  if (kesisimler.length < 3) return null;

  const aralik = (kesisimler[kesisimler.length - 1] - kesisimler[0]) / (kesisimler.length - 1);
  const dakika = 60 / aralik;
  return dakika >= 4 && dakika <= 40 ? Math.round(dakika) : null;
}