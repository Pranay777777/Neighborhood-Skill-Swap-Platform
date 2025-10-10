import React from 'react';
import { Users, Heart } from 'lucide-react';

export const Header = () => {
  return (
    <header className="bg-white/80 backdrop-blur-sm border-b border-green-100 sticky top-0 z-10 shadow-sm">
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-center text-center">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-gradient-to-r from-green-500 to-blue-500 rounded-full">
              <Users className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
              SkillSwap Street
            </h1>
            <Heart className="w-6 h-6 text-red-400 animate-pulse" />
          </div>
        </div>
        <p className="text-gray-600 text-center text-lg max-w-2xl mx-auto">
          Connect and Exchange Skills in Your Neighborhood! 
          <span className="block text-sm mt-1">Share what you know, learn what you need, build community together</span>
        </p>
      </div>
    </header>
  );
};