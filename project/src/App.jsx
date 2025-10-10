import React, { useState } from 'react';
import { Header } from './components/Header';
import { AddSkillForm } from './components/AddSkillForm';
import { SkillBoard } from './components/SkillBoard';

function App() {
  const [skills, setSkills] = useState([
    {
      id: '1',
      name: 'Sarah Chen',
      skill: 'Guitar Lessons',
      type: 'offer',
      description: 'I can teach acoustic guitar for beginners. Available weekends and evenings.',
      contact: 'sarah.music@email.com',
      createdAt: new Date('2025-01-20'),
      comments: [
        {
          id: '1',
          author: 'Mike',
          content: 'This sounds great! I\'ve been wanting to learn guitar.',
          createdAt: new Date('2025-01-21')
        }
      ]
    },
    {
      id: '2',
      name: 'David Rodriguez',
      skill: 'Spanish Conversation',
      type: 'request',
      description: 'Looking for someone to practice Spanish conversation with. I\'m intermediate level.',
      contact: 'david.learns@email.com',
      createdAt: new Date('2025-01-19'),
      comments: []
    },
    {
      id: '3',
      name: 'Emma Thompson',
      skill: 'Vegetable Gardening',
      type: 'offer',
      description: 'Happy to share tips on growing vegetables in small spaces. 10+ years experience!',
      contact: 'green.thumb.emma@email.com',
      createdAt: new Date('2025-01-18'),
      comments: [
        {
          id: '2',
          author: 'Lisa',
          content: 'Perfect timing! I just started a small garden.',
          createdAt: new Date('2025-01-19')
        },
        {
          id: '3',
          author: 'Tom',
          content: 'Do you have experience with tomatoes?',
          createdAt: new Date('2025-01-20')
        }
      ]
    }
  ]);

  const addSkill = (skillData) => {
    const newSkill = {
      ...skillData,
      id: Date.now().toString(),
      createdAt: new Date(),
      comments: []
    };
    setSkills(prev => [newSkill, ...prev]);
  };

  const addComment = (skillId, author, content) => {
    setSkills(prev => prev.map(skill => 
      skill.id === skillId 
        ? {
            ...skill,
            comments: [
              ...skill.comments,
              {
                id: Date.now().toString(),
                author,
                content,
                createdAt: new Date()
              }
            ]
          }
        : skill
    ));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-blue-50 to-purple-50">
      <Header />
      <main className="container mx-auto px-4 py-8 max-w-6xl">
        <AddSkillForm onAddSkill={addSkill} />
        <SkillBoard skills={skills} onAddComment={addComment} />
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