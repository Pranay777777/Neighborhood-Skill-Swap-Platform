import React, { useState } from 'react';
import { LogIn, UserPlus, KeyRound } from 'lucide-react';
import { api } from '../api';
import { useAuth } from '../auth';

const input =
  'w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 placeholder-gray-400';

const TABS = [
  { id: 'login', label: 'Sign in', icon: LogIn },
  { id: 'register', label: 'Create account', icon: UserPlus },
  { id: 'forgot', label: 'Forgot password', icon: KeyRound },
];

export const AuthPanel = () => {
  const { login } = useAuth();
  const [tab, setTab] = useState('login');
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [message, setMessage] = useState(null);
  const [busy, setBusy] = useState(false);

  const change = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setMessage(null);
    try {
      if (tab === 'login') {
        await login(form.email, form.password);
      } else if (tab === 'register') {
        await api('/auth/register', { method: 'POST', body: form, auth: false });
        setMessage({ ok: true, text: 'Account created. Check your email for the verification link, then sign in.' });
        setTab('login');
      } else {
        const r = await api('/auth/forgot-password', { method: 'POST', body: { email: form.email }, auth: false });
        setMessage({ ok: true, text: r.detail });
      }
    } catch (err) {
      setMessage({ ok: false, text: err.message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border border-green-100 p-6 md:p-8 mb-8">
      <div role="tablist" className="flex flex-wrap gap-2 mb-6">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            role="tab"
            aria-selected={tab === id}
            onClick={() => { setTab(id); setMessage(null); }}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
              tab === id ? 'bg-gradient-to-r from-green-500 to-blue-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      <form onSubmit={submit} className="space-y-4 max-w-md">
        {tab === 'register' && (
          <label className="block text-sm font-medium text-gray-700">
            Name
            <input className={`${input} mt-1`} value={form.name} onChange={change('name')} required maxLength={80} autoComplete="name" />
          </label>
        )}
        <label className="block text-sm font-medium text-gray-700">
          Email
          <input className={`${input} mt-1`} type="email" value={form.email} onChange={change('email')} required autoComplete="email" />
        </label>
        {tab !== 'forgot' && (
          <label className="block text-sm font-medium text-gray-700">
            Password
            <input
              className={`${input} mt-1`}
              type="password"
              value={form.password}
              onChange={change('password')}
              required
              minLength={tab === 'register' ? 10 : undefined}
              autoComplete={tab === 'register' ? 'new-password' : 'current-password'}
            />
          </label>
        )}
        {message && (
          <p role={message.ok ? 'status' : 'alert'} className={`text-sm ${message.ok ? 'text-green-700' : 'text-red-600'}`}>
            {message.text}
          </p>
        )}
        <button
          type="submit"
          disabled={busy}
          className="w-full bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 disabled:opacity-50 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200"
        >
          {TABS.find((t) => t.id === tab).label}
        </button>
      </form>
    </div>
  );
};
