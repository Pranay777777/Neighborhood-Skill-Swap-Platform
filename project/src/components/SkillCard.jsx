import React, { useState } from 'react';
import { CommentSection } from './CommentSection';
import { User, Calendar, Mail, MessageCircle, GraduationCap, BookOpen, Trash2, Handshake } from 'lucide-react';

export const SkillCard = ({ skill, user, onAddComment, onDelete, onRequest }) => {
  const [showComments, setShowComments] = useState(false);
  const [requestText, setRequestText] = useState('');
  const [requestSent, setRequestSent] = useState(false);
  const isOwner = user?.id === skill.owner_id;
  const canPost = Boolean(user?.email_verified);

  const sendRequest = async (e) => {
    e.preventDefault();
    try {
      await onRequest(skill.id, requestText.trim());
      setRequestText('');
      setRequestSent(true);
    } catch {
      // the board shows the error
    }
  };

  const formatDate = (date) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }).format(date);
  };

  const isOffer = skill.type === 'offer';

  return (
    <article aria-label={skill.skill} className={`bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border-2 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 ${
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

        {isOwner && (
          <button
            onClick={() => onDelete(skill.id).catch(() => {})}
            aria-label={`Delete ${skill.skill}`}
            className="mb-4 flex items-center gap-2 text-sm text-red-600 hover:text-red-700"
          >
            <Trash2 className="w-4 h-4" /> Delete
          </button>
        )}

        {canPost && !isOwner && (
          requestSent ? (
            <p role="status" className="mb-4 text-sm text-green-700">Swap request sent — only {skill.name} can see it.</p>
          ) : (
            <form onSubmit={sendRequest} className="mb-4 flex gap-2">
              <input
                value={requestText}
                onChange={(e) => setRequestText(e.target.value)}
                placeholder="Private message to propose a swap"
                aria-label={`Swap request for ${skill.skill}`}
                maxLength={1000}
                required
                className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500"
              />
              <button type="submit" className="flex items-center gap-1 px-3 py-2 rounded-lg bg-purple-500 hover:bg-purple-600 text-white text-sm">
                <Handshake className="w-4 h-4" /> Request
              </button>
            </form>
          )
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
            canPost={canPost}
          />
        </div>
      )}
    </article>
  );
};