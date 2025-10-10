import React, { useState } from 'react';
import { CommentSection } from './CommentSection';
import { User, Calendar, Mail, MessageCircle, GraduationCap, BookOpen } from 'lucide-react';

export const SkillCard = ({ skill, onAddComment }) => {
  const [showComments, setShowComments] = useState(false);

  const formatDate = (date) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }).format(date);
  };

  const isOffer = skill.type === 'offer';

  return (
    <div className={`bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border-2 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 ${
      isOffer ? 'border-green-100 hover:border-green-200' : 'border-blue-100 hover:border-blue-200'
    }`}>
      <div className="p-6">
        {/* Header with type indicator */}
        <div className="flex items-center justify-between mb-4">
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
            isOffer 
              ? 'bg-green-100 text-green-700' 
              : 'bg-blue-100 text-blue-700'
          }`}>
            {isOffer ? (
              <>
                <GraduationCap className="w-4 h-4" />
                Can Teach
              </>
            ) : (
              <>
                <BookOpen className="w-4 h-4" />
                Wants to Learn
              </>
            )}
          </div>
          <div className="flex items-center gap-1 text-gray-500 text-sm">
            <Calendar className="w-4 h-4" />
            {formatDate(skill.createdAt)}
          </div>
        </div>

        {/* Name and Skill */}
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <User className="w-5 h-5 text-gray-600" />
            <h3 className="text-lg font-bold text-gray-800">{skill.name}</h3>
          </div>
          <h4 className={`text-xl font-semibold mb-3 ${
            isOffer ? 'text-green-600' : 'text-blue-600'
          }`}>
            {skill.skill}
          </h4>
        </div>

        {/* Description */}
        <p className="text-gray-700 mb-4 leading-relaxed">
          {skill.description}
        </p>

        {/* Contact Info */}
        {skill.contact && (
          <div className="mb-4 p-3 bg-gray-50 rounded-xl">
            <div className="flex items-center gap-2 text-gray-700">
              <Mail className="w-4 h-4" />
              <span className="text-sm font-medium">Contact:</span>
              <span className="text-sm">{skill.contact}</span>
            </div>
          </div>
        )}

        {/* Comments Toggle */}
        <button
          onClick={() => setShowComments(!showComments)}
          className={`w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl transition-all duration-200 font-medium ${
            isOffer
              ? 'bg-green-50 hover:bg-green-100 text-green-700'
              : 'bg-blue-50 hover:bg-blue-100 text-blue-700'
          }`}
        >
          <MessageCircle className="w-4 h-4" />
          {skill.comments.length === 0 
            ? 'Leave a comment' 
            : `${skill.comments.length} comment${skill.comments.length !== 1 ? 's' : ''}`
          }
        </button>
      </div>

      {/* Comments Section */}
      {showComments && (
        <div className="border-t border-gray-100">
          <CommentSection
            skillId={skill.id}
            comments={skill.comments}
            onAddComment={onAddComment}
            skillType={skill.type}
          />
        </div>
      )}
    </div>
  );
};