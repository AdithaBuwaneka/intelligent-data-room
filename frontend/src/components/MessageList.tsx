/**
 * MessageList Component
 *
 * Displays chat messages with user/assistant styling.
 * Supports rendering execution plans and chart data.
 */

import { useEffect, useRef } from 'react';
import type { Message } from '../types';
import { TypingIndicator } from './LoadingSpinner';
import ChartDisplay from './ChartDisplay';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Empty state
  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400">
        <svg
          className="w-16 h-16 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
        <p className="text-center">Upload a file and start asking questions</p>
        <p className="text-sm mt-2">Try: "Show total sales by category"</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {/* Typing indicator when loading */}
      {isLoading && (
        <div className="flex justify-start">
          <TypingIndicator />
        </div>
      )}

      {/* Scroll anchor */}
      <div ref={messagesEndRef} />
    </div>
  );
}

/**
 * Individual message bubble component
 */
function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[85%] ${isUser ? 'order-2' : 'order-1'}`}>
        {/* Avatar */}
        <div className={`flex items-start gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
              isUser ? 'bg-blue-600' : 'bg-gray-200'
            }`}
          >
            {isUser ? (
              <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
              </svg>
            ) : (
              <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
              </svg>
            )}
          </div>

          {/* Message content */}
          <div className="flex flex-col gap-2">
            <div
              className={
                isUser
                  ? 'message-user'
                  : 'message-assistant'
              }
            >
              <p className="whitespace-pre-wrap break-words">{message.content}</p>
            </div>

            {/* Execution plan (collapsible) */}
            {message.plan && <ExecutionPlan plan={message.plan} />}

            {/* Chart display */}
            {message.chartConfig && <ChartDisplay config={message.chartConfig} />}

            {/* Timestamp */}
            <p className={`text-xs text-gray-400 ${isUser ? 'text-right' : 'text-left'}`}>
              {formatTime(message.timestamp)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Collapsible execution plan display
 */
function ExecutionPlan({ plan }: { plan: string }) {
  return (
    <details className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
      <summary className="px-3 py-2 text-xs font-medium text-gray-600 cursor-pointer hover:bg-gray-100 flex items-center gap-2">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
          />
        </svg>
        View Execution Plan
      </summary>
      <div className="px-3 py-2 text-xs text-gray-700 border-t border-gray-200 bg-white">
        <pre className="whitespace-pre-wrap font-mono">{plan}</pre>
      </div>
    </details>
  );
}

/**
 * Format timestamp for display
 */
function formatTime(date: Date): string {
  return new Date(date).toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

export default MessageList;
