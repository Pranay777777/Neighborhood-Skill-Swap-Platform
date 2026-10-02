import React, { useEffect, useRef, useState } from 'react';
import { api } from '../api';

// Landing pages for the links in verification and reset emails.
export const TokenPage = ({ kind }) => {
  const token = new URLSearchParams(window.location.search).get('token') ?? '';
  const [state, setState] = useState({ status: kind === 'verify' ? 'working' : 'form', text: '' });
  const [password, setPassword] = useState('');
  const sent = useRef(false);

  useEffect(() => {
    if (kind !== 'verify' || sent.current) return;
    sent.current = true; // StrictMode runs effects twice; the token is single-use
    api('/auth/verify-email', { method: 'POST', body: { token }, auth: false })
      .then(() => setState({ status: 'done', text: 'Email verified. You can sign in and post now.' }))
      .catch((err) => setState({ status: 'error', text: err.message }));
  }, [kind, token]);

  const reset = async (e) => {
    e.preventDefault();
    try {
      await api('/auth/reset-password', { method: 'POST', body: { token, new_password: password }, auth: false });
      setState({ status: 'done', text: 'Password changed. Every other session was signed out.' });
    } catch (err) {
      setState({ status: 'error', text: err.message });
    }
  };

  return (
    <div className="bg-white/90 rounded-2xl shadow-lg border border-green-100 p-8 max-w-md mx-auto space-y-4">
      <h2 className="text-2xl font-bold text-gray-800">{kind === 'verify' ? 'Verify email' : 'Choose a new password'}</h2>
      {state.status === 'form' && (
        <form onSubmit={reset} className="space-y-4">
          <label className="block text-sm font-medium text-gray-700">
            New password
            <input
              type="password"
              minLength={10}
              required
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full mt-1 px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500"
            />
          </label>
          <button type="submit" className="w-full bg-gradient-to-r from-green-500 to-blue-500 text-white font-semibold py-3 rounded-xl">
            Save password
          </button>
        </form>
      )}
      {state.status === 'working' && <p className="text-gray-600">Checking your link…</p>}
      {state.text && (
        <p role={state.status === 'error' ? 'alert' : 'status'} className={state.status === 'error' ? 'text-red-600' : 'text-green-700'}>
          {state.text}
        </p>
      )}
      {state.status !== 'form' && state.status !== 'working' && (
        <a href="/" className="inline-block text-blue-600 hover:underline">Back to the board</a>
      )}
    </div>
  );
};
