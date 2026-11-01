import React, { useState } from 'react';

interface NewSessionProps {
  onGoToMeasure: () => void;
}

const KNOWN_QUESTIONS = [
  'Adın ekranda yazan ad mı?',
  'Bugün bu oturuma katılmayı kabul ediyor musun?',
  'Şu anda burada mısın?',
  'Bu bir test oturumu mu?',
];

const INITIAL_CURIOUS = [
  'Bu deney ortamında kendini rahat hissediyor musun?',
  'Şu anda bir soru daha yanıtlamak ister misin?',
];

const Pill: React.FC = () => (
  <span className="shrink-0 rounded-full bg-brand-yellow/70 px-3 py-1 text-[10px] font-bold text-yellow-900 ring-1 ring-yellow-300/60">
    Bekliyor
  </span>
);

const QuestionRow: React.FC<{ index: number; text: string }> = ({ index, text }) => (
  <li className="flex items-center justify-between gap-3 rounded-xl border border-gray-100 bg-white px-4 py-3 text-xs text-gray-700 shadow-sm transition hover:border-gray-200 hover:shadow-card">
    <span>
      <span className="mr-1 font-bold text-gray-400">{index}.</span> {text}
    </span>
    <Pill />
  </li>
);

export const NewSession: React.FC<NewSessionProps> = ({ onGoToMeasure }) => {
  const [participant, setParticipant] = useState('K-104');
  const [curious, setCurious] = useState<string[]>(INITIAL_CURIOUS);
  const [newQuestion, setNewQuestion] = useState('');

  const addQuestion = () => {
    const t = newQuestion.trim();
    if (!t) return;
    setCurious((prev) => [...prev, t]);
    setNewQuestion('');
  };

  const canProceed = participant !== '';

  return (
    <div className="max-w-6xl animate-fadeUp space-y-5">
      {/* Üst başlık + rozet */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <span className="mb-1 block text-[11px] font-bold uppercase tracking-[0.18em] text-brand-orange">
            ARAŞTIRMA ARAYÜZÜ / 01
          </span>
          <h1 className="text-3xl font-black tracking-tight text-brand-navy sm:text-4xl">Yeni Oturum</h1>
        </div>
        <span className="inline-flex shrink-0 items-center gap-2 rounded-full border border-yellow-300/60 bg-brand-yellow/70 px-3 py-1.5 text-[11px] font-bold text-yellow-900">
          <span className="h-1.5 w-1.5 rounded-full bg-yellow-900/70" />
          ÖRNEK / SİMÜLASYON
        </span>
      </div>

      {/* Uyarı bandı */}
      <div className="flex items-start gap-3 rounded-xl border border-orange-200/70 bg-gradient-to-r from-orange-50 to-amber-50/40 p-3.5 text-xs leading-relaxed text-gray-700">
        <span className="mt-0.5 h-4 w-1 shrink-0 rounded-full bg-brand-orange" />
        <p>
          Bu sistem yalanı kesin olarak tespit etmez. Stres, hareket, sağlık durumu ve ortam gibi etkenler sinyalleri değiştirebilir.
        </p>
      </div>

      {/* Hata bandı (katılımcı seçilmediyse) */}
      {!canProceed && (
        <div className="flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 p-3.5 text-xs font-medium text-rose-700">
          <span className="mt-0.5 h-4 w-1 shrink-0 rounded-full bg-rose-400" />
          <p>Katılımcı kodunu ve yaş aralığını girin.</p>
        </div>
      )}

      <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
        {/* Sol sütun */}
        <div className="space-y-5">
          {/* Katılımcı ve oturum hazırlığı */}
          <section className="rounded-2xl border border-gray-100 bg-white p-6 shadow-card">
            <h3 className="mb-4 text-lg font-bold text-brand-navy">Katılımcı ve oturum hazırlığı</h3>

            <label className="block">
              <span className="mb-1.5 block text-[11px] font-semibold text-gray-500">Katılımcı seçimi</span>
              <select
                value={participant}
                onChange={(e) => setParticipant(e.target.value)}
                className="w-full cursor-pointer rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-brand-navy outline-none transition focus:border-brand-orange focus:ring-4 focus:ring-brand-orange/10"
              >
                <option value="">Seçiniz</option>
                <option value="K-104">K-104 · örnek demo</option>
              </select>
            </label>

            <p className="mt-2.5 text-[11px] text-gray-400">
              K-104 örneği yalnızca demo içindir. Kayıtlı katılımcılar açık rıza onayıyla görünür.
            </p>
          </section>

          {/* Bilinen cevaplı 4 soru */}
          <section className="rounded-2xl border border-gray-100 bg-white p-6 shadow-card">
            <h3 className="mb-4 text-lg font-bold text-brand-navy">Bilinen cevaplı 4 soru</h3>
            <ul className="space-y-2.5">
              {KNOWN_QUESTIONS.map((q, i) => (
                <QuestionRow key={q} index={i + 1} text={q} />
              ))}
            </ul>
          </section>

          {/* Merak edilen sorular */}
          <section className="rounded-2xl border border-gray-100 bg-white p-6 shadow-card">
            <h3 className="mb-4 text-lg font-bold text-brand-navy">Merak edilen sorular</h3>
            <ul className="space-y-2.5">
              {curious.map((q, i) => (
                <QuestionRow key={`${q}-${i}`} index={i + 1} text={q} />
              ))}
            </ul>

            <div className="mt-5">
              <span className="mb-1.5 block text-[11px] font-semibold text-gray-500">Yeni soru metni</span>
              <div className="flex gap-2.5">
                <input
                  value={newQuestion}
                  onChange={(e) => setNewQuestion(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addQuestion()}
                  className="min-w-0 flex-1 rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-brand-navy outline-none transition focus:border-brand-orange focus:ring-4 focus:ring-brand-orange/10"
                />
                <button
                  type="button"
                  onClick={addQuestion}
                  className="shrink-0 rounded-xl bg-gray-100 px-4 py-3 text-xs font-bold text-gray-700 transition hover:bg-gray-200"
                >
                  Soru ekle
                </button>
              </div>
            </div>
          </section>
        </div>

        {/* Sağ sütun */}
        <aside className="space-y-5 lg:sticky lg:top-24">
          <section className="rounded-2xl border border-gray-100 bg-white p-6 shadow-card">
            <h3 className="mb-2 text-lg font-bold text-brand-navy">Deneysel gözlem</h3>
            <p className="mb-5 text-xs leading-relaxed text-gray-500">
              Önce ölçüm ekranında kalibrasyon yapın. Dört bilinen soru tamamlanınca merak edilen sorular açılır.
              Gerçek biyometrik veri bu prototipte okunmaz.
            </p>
            <button
              type="button"
              onClick={onGoToMeasure}
              disabled={!canProceed}
              className="w-full rounded-xl bg-brand-orange px-5 py-3 text-xs font-bold text-white shadow-glow transition hover:-translate-y-0.5 hover:bg-orange-500 active:translate-y-0 disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-none disabled:hover:translate-y-0"
            >
              Ölçüme geç ↗
            </button>
          </section>
        </aside>
      </div>

      <footer className="border-t border-gray-200/70 pt-5 text-[11px] text-gray-400">
        Sinyal Hattı · Araştırma demosu · Tıbbi veya adli doğrulama aracı değildir.
      </footer>
    </div>
  );
};

export default NewSession;