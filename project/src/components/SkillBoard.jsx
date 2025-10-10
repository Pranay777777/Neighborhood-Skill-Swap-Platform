import React from 'react';
import { SkillCard } from './SkillCard';
import { Grid3X3, Sparkles } from 'lucide-react';

export const SkillBoard = ({ skills, onAddComment }) => {
  const offers = skills.filter(skill => skill.type === 'offer');
  const requests = skills.filter(skill => skill.type === 'request');

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full">
          <Grid3X3 className="w-5 h-5 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-gray-800">Community Skills</h2>
        <Sparkles className="w-5 h-5 text-yellow-500" />
      </div>

      {skills.length === 0 ? (
        <div className="text-center py-12 bg-white/60 rounded-2xl border border-gray-100">
          <div className="text-6xl mb-4">🌱</div>
          <h3 className="text-xl font-semibold text-gray-600 mb-2">No skills shared yet</h3>
          <p className="text-gray-500">Be the first to share your skills with the community!</p>
        </div>
      ) : (
        <>
          {offers.length > 0 && (
            <section>
              <h3 className="text-xl font-semibold text-green-700 mb-4 flex items-center gap-2">
                <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                Skills Available to Teach ({offers.length})
              </h3>
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {offers.map(skill => (
                  <SkillCard 
                    key={skill.id} 
                    skill={skill} 
                    onAddComment={onAddComment}
                  />
                ))}
              </div>
            </section>
          )}

          {requests.length > 0 && (
            <section>
              <h3 className="text-xl font-semibold text-blue-700 mb-4 flex items-center gap-2">
                <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
                Skills People Want to Learn ({requests.length})
              </h3>
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {requests.map(skill => (
                  <SkillCard 
                    key={skill.id} 
                    skill={skill} 
                    onAddComment={onAddComment}
                  />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
};