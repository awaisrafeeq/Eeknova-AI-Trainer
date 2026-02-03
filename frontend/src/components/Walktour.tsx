'use client';
import React, { useState, useEffect } from 'react';

interface WalktourStep {
  id: string;
  title: string;
  content: string;
  target: string;
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
}

interface WalktourProps {
  steps?: WalktourStep[];
  onComplete: () => void;
  isActive: boolean;
}

const defaultSteps: WalktourStep[] = [
  {
    id: 'avatar',
    title: '3D Avatar',
    content: 'Meet your AI fitness companion! Currently showing Mountain Pose. This 3D avatar demonstrates yoga poses and provides visual guidance. Watch carefully and follow along for perfect form!',
    target: 'avatar',
    position: 'right'
  },
  {
    id: 'yoga',
    title: 'Yoga Module',
    content: 'Practice yoga poses with real-time AI feedback. Our system analyzes your form and provides corrections to help you improve.',
    target: 'yoga-module',
    position: 'right'
  },
  {
    id: 'zumba',
    title: 'Zumba Module',
    content: 'High-energy dance workouts with rhythm tracking. Follow along to energetic routines and burn calories while having fun!',
    target: 'zumba-module',
    position: 'right'
  },
  {
    id: 'chess',
    title: 'Chess Module',
    content: 'Challenge your mind with strategic chess games. Play against AI or improve your skills with interactive tutorials.',
    target: 'chess-module',
    position: 'right'
  },
  {
    id: 'dashboard',
    title: 'Dashboard',
    content: 'Track your progress, view workout history, and monitor your fitness goals all in one place.',
    target: 'dashboard-module',
    position: 'right'
  },
  {
    id: 'settings',
    title: 'Settings',
    content: 'Customize your profile, adjust preferences, and manage your account settings here.',
    target: 'settings-module',
    position: 'right'
  }
];

export default function Walktour({ steps = defaultSteps, onComplete, isActive }: WalktourProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    console.log('Walktour component - isActive changed:', isActive);
    console.log('Walktour steps length:', steps.length);
    console.log('Walktour steps:', steps.map(s => s.title));
    setIsVisible(isActive);
  }, [isActive, steps]);

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const skipTour = () => {
    handleComplete();
  };

  const handleComplete = () => {
    setIsVisible(false);
    onComplete();
  };

  const getCurrentTargetElement = () => {
    const step = steps[currentStep];
    if (!step) return null;
    
    console.log('Looking for element with target:', step.target);
    
    let element = document.querySelector(`[data-walktour="${step.target}"]`) || 
           document.querySelector(`[href*="${step.target}"]`) ||
           document.querySelector(`button:has-text("${step.title}")`);
    
    // Special case for avatar - also look for Avatar3D component
    if (step.target === 'avatar' && !element) {
      element = document.querySelector('.avatar-wrap') || 
                document.querySelector('[class*="avatar"]') ||
                document.querySelector('canvas') ||
                document.querySelector('[style*="position: relative"]') ||
                document.querySelector('img[alt="Avatar"]');
    }
    
    console.log('Found element:', element);
    if (element) {
      console.log('Element classes:', element.className);
      console.log('Element tag:', element.tagName);
    }
    
    return element;
  };

  const getHighlightPosition = () => {
    const element = getCurrentTargetElement();
    if (!element) return { top: 0, left: 0, width: 0, height: 0, bottom: 0, right: 0 };
    
    const rect = element.getBoundingClientRect();
    return {
      top: rect.top + window.scrollY,
      left: rect.left + window.scrollX,
      width: rect.width,
      height: rect.height,
      bottom: rect.bottom + window.scrollY,
      right: rect.right + window.scrollX
    };
  };

  const getPopupPosition = () => {
    const step = steps[currentStep];
    const element = getCurrentTargetElement();
    
    // If element not found, show in center
    if (!element) {
      console.log('Element not found, showing in center');
      return {
        top: '50%',
        left: '50%'
      };
    }
    
    const targetPos = getHighlightPosition();
    
    const positions = {
      top: { top: targetPos.top - 120, left: targetPos.left + targetPos.width / 2 },
      bottom: { top: targetPos.bottom + 20, left: targetPos.left + targetPos.width / 2 },
      left: { top: targetPos.top + targetPos.height / 2, left: targetPos.left - 320 },
      right: { top: targetPos.top + targetPos.height / 2, left: targetPos.right + 20 },
      center: { top: '50%', left: '50%' }
    };

    return positions[step.position || 'center'];
  };

  if (!isVisible || currentStep >= steps.length) {
    console.log('Walktour not visible or step out of range:', { isVisible, currentStep, stepsLength: steps.length });
    return null;
  }

  const step = steps[currentStep];
  console.log('Current step:', step);
  const popupPos = getPopupPosition();
  console.log('Popup position:', popupPos);

  return (
    <>
      {/* Overlay - completely transparent */}
      <div className="fixed inset-0 bg-transparent z-40" onClick={skipTour} />
      
      {/* Highlight area - only show if element found */}
      {(() => {
        const element = getCurrentTargetElement();
        if (element) {
          const pos = getHighlightPosition();
          return (
            <div
              className="absolute z-40 border-4 border-blue-400 rounded-lg pointer-events-none"
              style={{
                ...pos,
                boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.1)',
                transition: 'all 0.3s ease'
              }}
            />
          );
        }
        return null;
      })()}
      
      {/* Popup */}
      <div
        className="fixed z-50 bg-white rounded-xl shadow-2xl p-6 max-w-sm transform -translate-x-1/2 -translate-y-1/2"
        style={{
          top: popupPos.top === '50%' ? '50%' : popupPos.top,
          left: popupPos.left === '50%' ? '50%' : popupPos.left,
          transform: popupPos.top === '50%' ? 'translate(-50%, -50%)' : 'translate(-50%, -50%)'
        }}
      >
        <div className="mb-4">
          <h3 className="text-xl font-bold text-gray-900 mb-2">{step.title}</h3>
          <p className="text-gray-600">{step.content}</p>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">
            Step {currentStep + 1} of {steps.length}
          </span>
          <div className="flex gap-2">
            <button
              onClick={skipTour}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
            >
              Skip
            </button>
            <button
              onClick={nextStep}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              {currentStep === steps.length - 1 ? 'Finish' : 'Next'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
