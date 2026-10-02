import React from 'react';
import { Inbox, Check, X } from 'lucide-react';

// Swap requests the signed-in user sent or received; only the skill owner can answer.
export const MyRequests = ({ requests, userId, ownSkillIds, onAnswer }) => {
  if (requests.length === 0) return null;
  return (
    <section aria-label="My swap requests" className="bg-white/90 rounded-2xl shadow-lg border border-purple-100 p-6 mb-8">
      <h2 className="flex items-center gap-2 text-xl font-bold text-gray-800 mb-4">
        <Inbox className="w-5 h-5 text-purple-500" />
        My swap requests
      </h2>
      <ul className="space-y-3">
        {requests.map((r) => {
          const received = ownSkillIds.has(r.skill_id) && r.requester_id !== userId;
          return (
            <li key={r.id} className="bg-gray-50 rounded-xl p-4">
              <p className="text-sm text-gray-500">
                {received ? `${r.requester} → your “${r.skill}”` : `You → “${r.skill}”`} · <span className="font-medium">{r.status}</span>
              </p>
              <p className="text-gray-800 mt-1">{r.message}</p>
              {received && r.status === 'pending' && (
                <div className="flex gap-2 mt-3">
                  <button onClick={() => onAnswer(r.id, 'accepted')} className="flex items-center gap-1 px-3 py-1 rounded-lg bg-green-500 text-white text-sm">
                    <Check className="w-4 h-4" /> Accept
                  </button>
                  <button onClick={() => onAnswer(r.id, 'declined')} className="flex items-center gap-1 px-3 py-1 rounded-lg bg-gray-200 text-gray-800 text-sm">
                    <X className="w-4 h-4" /> Decline
                  </button>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
};
