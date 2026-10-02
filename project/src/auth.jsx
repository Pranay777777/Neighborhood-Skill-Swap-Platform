import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { api, refreshSession, tokens } from './api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  const loadMe = useCallback(async () => {
    try {
      setUser(await api('/auth/me'));
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    // Restore the session from the stored refresh token, if any.
    refreshSession()
      .then((ok) => (ok ? loadMe() : null))
      .finally(() => setReady(true));
  }, [loadMe]);

  const login = async (email, password) => {
    tokens.set(await api('/auth/login', { method: 'POST', body: { email, password }, auth: false }));
    await loadMe();
  };

  const logout = async () => {
    const refresh_token = tokens.refresh();
    tokens.clear();
    setUser(null);
    if (refresh_token) {
      await api('/auth/logout', { method: 'POST', body: { refresh_token }, auth: false }).catch(() => {});
    }
  };

  return (
    <AuthContext.Provider value={{ user, ready, login, logout, reload: loadMe }}>
      {children}
    </AuthContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext);
