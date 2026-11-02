import React, { useState } from 'react';
import { authService } from '../services/api';

interface LoginProps {
  onLoginSuccess: () => void;
}

export const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authService.login(username, password);
      // Başarılı girişte App.tsx'teki state'i tetikle
      onLoginSuccess();
    } catch (err: any) {
      console.error('Giriş hatası:', err);
      setError(err.response?.data?.detail || 'Kullanıcı adı veya şifre hatalı!');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-900 p-4">
      <div className="w-full max-w-md rounded-3xl bg-white p-8 shadow-2xl">
        <div className="mb-6 text-center">
          <span className="text-xs font-bold uppercase tracking-widest text-brand-orange">
            SİNYAL HATTI
          </span>
          <h1 className="mt-1 text-2xl font-black text-brand-navy">Sisteme Giriş Yap</h1>
        </div>

        {error && (
          <div className="mb-4 rounded-xl bg-red-50 p-3 text-xs font-semibold text-red-600 border border-red-200">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-1">
              Kullanıcı Adı
            </label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="admin"
              className="w-full rounded-xl border border-gray-200 bg-gray-50 p-3 text-sm outline-none transition focus:border-brand-orange focus:bg-white text-gray-900"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-1">
              Şifre
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••"
              className="w-full rounded-xl border border-gray-200 bg-gray-50 p-3 text-sm outline-none transition focus:border-brand-orange focus:bg-white text-gray-900"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-brand-navy py-3 text-xs font-bold text-white transition hover:bg-brand-cardNav disabled:opacity-50 cursor-pointer"
          >
            {loading ? 'Giriş Yapılıyor...' : 'Giriş Yap'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;