/**
 * MessageList Component
 *
 * Displays chat messages with user/assistant styling.
 * Supports rendering execution plans and chart data.
 */

import React, { useEffect, useRef } from 'react';
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
 * Filter out chart file paths from message content
 * These paths (like temp_charts/xxx.png) should not be displayed in chat
 */
function filterChartPaths(content: string): string {
  if (!content) return content;
  
  // Remove lines that are only chart file paths
  const lines = content.split('\n');
  const filteredLines = lines.filter(line => {
    const trimmed = line.trim();
    // Filter out lines that are just file paths to temp_charts or chart files
    if (/^(temp_charts|charts|exports)?[\\\/]?[\w-]+\.(png|jpg|jpeg|svg)$/i.test(trimmed)) {
      return false;
    }
    // Filter out empty lines if they're consecutive
    return true;
  });
  
  const result = filteredLines.join('\n').trim();
  // If result is empty or just whitespace, return a single space to avoid rendering issues
  return result || content;
}

/**
 * Format message content with rich styling for lists, rankings, and data
 */
function formatMessageContent(content: string): React.ReactNode {
  if (!content) return <span>{content}</span>;
  
  const filteredContent = filterChartPaths(content);
  const lines = filteredContent.split('\n');
  
  return (
    <div className="space-y-1">
      {lines.map((line, index) => {
        const trimmed = line.trim();
        
        if (!trimmed) return <div key={index} className="h-1" />;
        
        // Header lines ending with colon
        if (trimmed.endsWith(':') && trimmed.length < 60 && !trimmed.includes(' - ')) {
          return (
            <div key={index} className="font-semibold text-gray-800 mt-2 first:mt-0">
              {trimmed}
            </div>
          );
        }
        
        // Bullet points with values (- Item: value)
        if (trimmed.startsWith('- ')) {
          const itemContent = trimmed.slice(2);
          const colonIndex = itemContent.lastIndexOf(':');
          
          if (colonIndex > 0 && colonIndex < itemContent.length - 1) {
            const name = itemContent.slice(0, colonIndex).trim();
            const value = itemContent.slice(colonIndex + 1).trim();
            
            return (
              <div key={index} className="flex items-center gap-2 py-1.5 px-3 bg-gradient-to-r from-gray-50 to-white rounded-lg border border-gray-100">
                <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0" />
                <span className="flex-1 text-gray-700 truncate font-medium" title={name}>{name}</span>
                <span className="font-mono text-blue-600 font-semibold bg-blue-50 px-2 py-0.5 rounded">{value}</span>
              </div>
            );
          }
          
          return (
            <div key={index} className="flex items-center gap-2 py-1">
              <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0" />
              <span className="text-gray-700">{itemContent}</span>
            </div>
          );
        }
        
        // Numbered list (1. Item)
        const numberedMatch = trimmed.match(/^(\d+)\.\s+(.+)$/);
        if (numberedMatch) {
          return (
            <div key={index} className="flex items-center gap-2 py-1">
              <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
                {numberedMatch[1]}
              </span>
              <span className="text-gray-700">{numberedMatch[2]}</span>
            </div>
          );
        }
        
        return <div key={index} className="text-gray-700">{trimmed}</div>;
      })}
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
              {isUser ? (
                <p className="whitespace-nowrap-for-short">{message.content}</p>
              ) : (
                formatMessageContent(message.content)
              )}
            </div>

            {/* Execution plan (collapsible) */}
            {message.plan && <ExecutionPlan plan={message.plan} />}

            {/* Chart display - only render if config has valid data */}
            {message.chartConfig && message.chartConfig.data && message.chartConfig.data.length > 0 && (
              <ChartDisplay config={message.chartConfig} />
            )}

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
 * Collapsible execution plan display with improved formatting
 */
function ExecutionPlan({ plan }: { plan: string }) {
  // Parse the plan into formatted sections
  const formatPlan = (text: string) => {
    const lines = text.split('\n');
    
    return lines.map((line, index) => {
      const trimmedLine = line.trim();
      
      // Skip empty lines
      if (!trimmedLine) {
        return <div key={index} className="h-2" />;
      }
      
      // Bold headers (e.g., **OBJECTIVE:**)
      if (trimmedLine.startsWith('**') && trimmedLine.includes(':**')) {
        const headerMatch = trimmedLine.match(/^\*\*([^*]+)\*\*:?\s*(.*)/);
        if (headerMatch) {
          return (
            <div key={index} className="mt-3 first:mt-0">
              <span className="font-semibold text-blue-700">{headerMatch[1]}:</span>
              {headerMatch[2] && <span className="ml-1">{headerMatch[2]}</span>}
            </div>
          );
        }
      }
      
      // Numbered steps (e.g., 1. Step description)
      if (/^\d+\.\s/.test(trimmedLine)) {
        const stepMatch = trimmedLine.match(/^(\d+)\.\s+(.+)/);
        if (stepMatch) {
          return (
            <div key={index} className="flex gap-2 ml-2 mt-1">
              <span className="flex-shrink-0 w-5 h-5 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">
                {stepMatch[1]}
              </span>
              <span className="text-gray-700">{stepMatch[2]}</span>
            </div>
          );
        }
      }
      
      // Bullet points (e.g., - Item)
      if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('• ')) {
        return (
          <div key={index} className="flex gap-2 ml-4 mt-1">
            <span className="text-gray-400">•</span>
            <span className="text-gray-600">{trimmedLine.slice(2)}</span>
          </div>
        );
      }
      
      // YES/NO indicators
      if (trimmedLine.includes('YES -') || trimmedLine.includes('YES–') || trimmedLine.toUpperCase().startsWith('YES')) {
        return (
          <div key={index} className="flex items-center gap-2 mt-1">
            <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded font-medium">YES</span>
            <span className="text-gray-600">{trimmedLine.replace(/^YES\s*[-–]?\s*/i, '')}</span>
          </div>
        );
      }
      
      if (trimmedLine.toUpperCase().startsWith('NO') && !trimmedLine.toLowerCase().startsWith('no ')) {
        return (
          <div key={index} className="flex items-center gap-2 mt-1">
            <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded font-medium">NO</span>
            <span className="text-gray-600">{trimmedLine.replace(/^NO\s*[-–]?\s*/i, '')}</span>
          </div>
        );
      }
      
      // Regular text
      return (
        <div key={index} className="text-gray-700 mt-1">
          {trimmedLine}
        </div>
      );
    });
  };

  return (
    <details className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200 overflow-hidden">
      <summary className="px-4 py-2.5 text-sm font-medium text-blue-700 cursor-pointer hover:bg-blue-100/50 flex items-center gap-2 transition-colors">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
          />
        </svg>
        View Execution Plan
        <span className="ml-auto text-xs text-blue-500">Click to expand</span>
      </summary>
      <div className="px-4 py-3 text-sm border-t border-blue-200 bg-white">
        {formatPlan(plan)}
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
