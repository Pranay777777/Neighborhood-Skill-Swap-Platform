import React, { useCallback, useEffect, useState } from 'react';
import { Header } from './components/Header';
import { AddSkillForm } from './components/AddSkillForm';
import { SkillBoard } from './components/SkillBoard';
import { AuthPanel } from './components/AuthPanel';
import { TokenPage } from './components/TokenPage';
import { MyRequests } from './components/MyRequests';
import { api } from './api';
import { useAuth } from './auth';

const withDates = (skill) => ({
  ...skill,
  createdAt: new Date(skill.created_at),
  comments: skill.comments.map((c) => ({ ...c, createdAt: new Date(c.created_at) })),
});

function Board() {
  const { user, ready } = useAuth();
  const [skills, setSkills] = useState([]);
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      setSkills((await api('/skills')).map(withDates));
      setRequests(user ? await api('/me/requests') : []);
    } catch (err) {
      setError(err.message);
    }
  }, [user]);

  useEffect(() => {
    if (ready) load();
  }, [ready, load]);

  // An action's error stays up until the next action; a reload must not wipe it.
  const run = (fn) => async (...args) => {
    setError(null);
    try {
      await fn(...args);
      await load();
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const addSkill = run((data) => api('/skills', { method: 'POST', body: data }));
  const addComment = run((skillId, content) =>
    api(`/skills/${skillId}/comments`, { method: 'POST', body: { content } }));
  const deleteSkill = run((skillId) => api(`/skills/${skillId}`, { method: 'DELETE' }));
  const requestSwap = run((skillId, message) =>
    api(`/skills/${skillId}/requests`, { method: 'POST', body: { message } }));
  const answer = run((id, status) => api(`/requests/${id}`, { method: 'PATCH', body: { status } }));

  const ownSkillIds = new Set(skills.filter((s) => s.owner_id === user?.id).map((s) => s.id));

  return (
    <>
      {error && (
        <p role="alert" className="mb-6 p-4 rounded-xl bg-red-50 text-red-700">{error}</p>
      )}
      {ready && !user && <AuthPanel />}
      {user && !user.email_verified && (
        <p role="status" className="mb-6 p-4 rounded-xl bg-yellow-50 text-yellow-800">
          Verify your email to post skills, comments and swap requests — the link is in your inbox.
        </p>
      )}
      {user?.email_verified && <AddSkillForm onAddSkill={addSkill} />}
      {user && (
        <MyRequests requests={requests} userId={user.id} ownSkillIds={ownSkillIds} onAnswer={answer} />
      )}
      <SkillBoard
        skills={skills}
        user={user}
        onAddComment={addComment}
        onDelete={deleteSkill}
        onRequest={requestSwap}
      />
    </>
  );
}

function App() {
  const path = window.location.pathname;
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-blue-50 to-purple-50">
      <Header />
      <main className="container mx-auto px-4 py-8 max-w-6xl">
        {path === '/verify-email' ? (
          <TokenPage kind="verify" />
        ) : path === '/reset-password' ? (
          <TokenPage kind="reset" />
        ) : (
          <Board />
        )}
      </main>
      <footer className="bg-white/60 backdrop-blur-sm border-t border-green-100 py-6 mt-16">
        <div className="container mx-auto px-4 text-center">
          <p className="text-gray-600">Building stronger communities, one skill at a time 🌟</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
