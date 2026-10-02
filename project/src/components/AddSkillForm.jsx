import React, { useState } from 'react';
import { Plus, Lightbulb, MessageSquare, Mail } from 'lucide-react';

export const AddSkillForm = ({ onAddSkill }) => {
  const [formData, setFormData] = useState({
    skill: '',
    type: 'offer',
    description: '',
    contact: ''
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.skill.trim() || !formData.description.trim()) {
      return;
    }

    setIsSubmitting(true);
    
    try {
      await onAddSkill({
        skill: formData.skill.trim(),
        type: formData.type,
        description: formData.description.trim(),
        contact: formData.contact.trim() || undefined
      });
      setFormData({ skill: '', type: 'offer', description: '', contact: '' });
    } catch {
      // the board shows the error; keep what was typed
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border border-green-100 p-6 md:p-8 mb-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full">
          <Plus className="w-5 h-5 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-gray-800">Share Your Skills</h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid gap-6">
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <Lightbulb className="w-4 h-4" />
              Skill *
            </label>
            <input
              type="text"
              value={formData.skill}
              onChange={(e) => handleChange('skill', e.target.value)}
              placeholder="e.g., Piano, Coding, Cooking, Gardening"
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 placeholder-gray-400"
              required
            />
          </div>
        </div>

        <div>
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
            What would you like to do?
          </label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="type"
                value="offer"
                checked={formData.type === 'offer'}
                onChange={(e) => handleChange('type', e.target.value)}
                className="w-4 h-4 text-green-600 focus:ring-green-500 focus:ring-2"
              />
              <span className="text-sm text-gray-700 font-medium">I can teach this</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="type"
                value="request"
                checked={formData.type === 'request'}
                onChange={(e) => handleChange('type', e.target.value)}
                className="w-4 h-4 text-blue-600 focus:ring-blue-500 focus:ring-2"
              />
              <span className="text-sm text-gray-700 font-medium">I want to learn this</span>
            </label>
          </div>
        </div>

        <div>
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
            <MessageSquare className="w-4 h-4" />
            Description *
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => handleChange('description', e.target.value)}
            placeholder="Tell us more about your skill or what you're looking for. Include availability, experience level, etc."
            rows={4}
            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 placeholder-gray-400 resize-none"
            required
          />
        </div>

        <div>
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
            <Mail className="w-4 h-4" />
            Contact Info (Optional)
          </label>
          <input
            type="text"
            value={formData.contact}
            onChange={(e) => handleChange('contact', e.target.value)}
            placeholder="Email, phone, or preferred contact method"
            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 placeholder-gray-400"
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting || !formData.skill.trim() || !formData.description.trim()}
          className="w-full bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 disabled:from-gray-300 disabled:to-gray-400 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-200 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
        >
          {isSubmitting ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
              Adding...
            </>
          ) : (
            <>
              <Plus className="w-5 h-5" />
              Add to Skill Board
            </>
          )}
        </button>
      </form>
    </div>
  );
};