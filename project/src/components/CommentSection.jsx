import React, { useState } from 'react';
import { Send, User, Clock } from 'lucide-react';

export const CommentSection = ({ skillId, comments, onAddComment, skillType, canPost }) => {
  const [newComment, setNewComment] = useState({ content: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newComment.content.trim()) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onAddComment(skillId, newComment.content.trim());
      setNewComment({ content: '' });
    } catch {
      // the board shows the error; keep what was typed
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatTimeAgo = (date) => {
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));
    
    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${diffInHours}h ago`;
    } else {
      const diffInDays = Math.floor(diffInHours / 24);
      return `${diffInDays}d ago`;
    }
  };

  const isOffer = skillType === 'offer';

  return (
    <div className="p-6 space-y-4">
      {/* Existing Comments */}
      {comments.length > 0 && (
        <div className="space-y-3 mb-6">
          <h4 className="font-medium text-gray-800 text-sm">Comments</h4>
          {comments.map(comment => (
            <div key={comment.id} className="bg-gray-50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <User className="w-4 h-4 text-gray-500" />
                <span className="font-medium text-gray-800 text-sm">{comment.author}</span>
                <div className="flex items-center gap-1 text-gray-400 text-xs ml-auto">
                  <Clock className="w-3 h-3" />
                  {formatTimeAgo(comment.createdAt)}
                </div>
              </div>
              <p className="text-gray-700 text-sm leading-relaxed">{comment.content}</p>
            </div>
          ))}
        </div>
      )}

      {/* Add Comment Form */}
      {canPost ? (
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <textarea
            placeholder="Leave a comment..."
            aria-label="Comment"
            value={newComment.content}
            onChange={(e) => setNewComment(prev => ({ ...prev, content: e.target.value }))}
            rows={3}
            className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 resize-none"
            required
          />
        </div>
        <button
          type="submit"
          disabled={isSubmitting || !newComment.content.trim()}
          className={`w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg text-sm font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed ${
            isOffer
              ? 'bg-green-500 hover:bg-green-600 text-white'
              : 'bg-blue-500 hover:bg-blue-600 text-white'
          }`}
        >
          {isSubmitting ? (
            <>
              <div className="animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent"></div>
              Posting...
            </>
          ) : (
            <>
              <Send className="w-3 h-3" />
              Post Comment
            </>
          )}
        </button>
      </form>
      ) : (
        <p className="text-sm text-gray-500">Sign in with a verified email to comment.</p>
      )}
    </div>
  );
};