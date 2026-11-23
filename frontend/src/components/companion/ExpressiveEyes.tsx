import React, { useState, useEffect } from 'react';
import { CompanionEyeState } from '../../types';

interface ExpressiveEyesProps {
  state?: CompanionEyeState;
  lookTarget?: { x: number; y: number } | null;
  size?: 'sm' | 'md';
}

export const ExpressiveEyes: React.FC<ExpressiveEyesProps> = ({
  state = 'idle',
  lookTarget = null,
  size = 'md'
}) => {
  const [blink, setBlink] = useState(false);
  const [pupilOffset, setPupilOffset] = useState({ x: 0, y: 0 });

  // Natural spontaneous blinking without constant CPU load
  useEffect(() => {
    let timeout: NodeJS.Timeout;
    const triggerRandomBlink = () => {
      const nextDelay = 3500 + Math.random() * 4000;
      timeout = setTimeout(() => {
        setBlink(true);
        setTimeout(() => {
          setBlink(false);
          triggerRandomBlink();
        }, 160);
      }, nextDelay);
    };

    triggerRandomBlink();
    return () => clearTimeout(timeout);
  }, []);

  // Micro pupil tracking for natural gaze
  useEffect(() => {
    if (lookTarget) {
      const offsetX = Math.max(-3, Math.min(3, (lookTarget.x - window.innerWidth / 2) / 60));
      const offsetY = Math.max(-2, Math.min(2, (lookTarget.y - 40) / 40));
      setPupilOffset({ x: offsetX, y: offsetY });
    } else {
      setPupilOffset({ x: 0, y: 0 });
    }
  }, [lookTarget]);

  const eyeWidth = size === 'sm' ? 'w-2.5' : 'w-3.5';
  const eyeHeight = size === 'sm' ? 'h-3.5' : 'h-5';
  const pupilSize = size === 'sm' ? 'w-1.5 h-1.5' : 'w-2 h-2';

  const isSquinting = state === 'processing';
  const isListening = state === 'listening';
  const isHappy = state === 'happy';

  return (
    <div className="flex items-center gap-2 select-none pointer-events-none transition-transform duration-200">
      {/* Left Eye */}
      <div
        className={`relative ${eyeWidth} ${eyeHeight} bg-lavender/90 rounded-full flex items-center justify-center transition-all duration-150 ${
          blink ? 'scale-y-[0.08]' : isSquinting ? 'scale-y-50' : 'scale-y-100'
        } ${isListening ? 'animate-pulse bg-lavender shadow-[0_0_12px_rgba(157,140,255,0.8)]' : ''}`}
      >
        {!blink && !isSquinting && (
          <div
            className={`absolute ${pupilSize} bg-obsidian-400 rounded-full transition-transform duration-100`}
            style={{
              transform: `translate(${pupilOffset.x}px, ${pupilOffset.y}px)`,
            }}
          />
        )}
      </div>

      {/* Right Eye */}
      <div
        className={`relative ${eyeWidth} ${eyeHeight} bg-lavender/90 rounded-full flex items-center justify-center transition-all duration-150 ${
          blink ? 'scale-y-[0.08]' : isSquinting ? 'scale-y-50' : 'scale-y-100'
        } ${isListening ? 'animate-pulse bg-lavender shadow-[0_0_12px_rgba(157,140,255,0.8)]' : ''}`}
      >
        {!blink && !isSquinting && (
          <div
            className={`absolute ${pupilSize} bg-obsidian-400 rounded-full transition-transform duration-100`}
            style={{
              transform: `translate(${pupilOffset.x}px, ${pupilOffset.y}px)`,
            }}
          />
        )}
      </div>
    </div>
  );
};
