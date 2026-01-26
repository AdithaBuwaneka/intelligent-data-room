/**
 * LoadingSpinner Component
 *
 * Displays animated loading indicators for various states.
 */

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}

export function LoadingSpinner({ size = 'md', text }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <div
        className={`${sizeClasses[size]} border-2 border-gray-200 border-t-blue-600 rounded-full animate-spin`}
      />
      {text && <p className="text-sm text-gray-500">{text}</p>}
    </div>
  );
}

/**
 * Typing indicator with bouncing dots (for chat)
 */
export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-4 py-3 bg-gray-100 rounded-2xl rounded-bl-md w-fit">
      <div className="w-2 h-2 bg-gray-400 rounded-full loading-dot" />
      <div className="w-2 h-2 bg-gray-400 rounded-full loading-dot" />
      <div className="w-2 h-2 bg-gray-400 rounded-full loading-dot" />
    </div>
  );
}

export default LoadingSpinner;
