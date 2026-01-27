/**
 * ChatInterface Component
 *
 * Main chat interface for interacting with the data analysis AI.
 * Handles message input, sending queries, and displaying responses.
 */

import { useState, useCallback } from 'react';
import type { Message, FileMetadata, QueryResponse } from '../types';
import MessageList from './MessageList';

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (content: string) => Promise<QueryResponse>;
  isLoading: boolean;
  fileUploaded: FileMetadata | null;
}

export function ChatInterface({
  messages,
  onSendMessage,
  isLoading,
  fileUploaded,
}: ChatInterfaceProps) {
  const [input, setInput] = useState('');

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      const trimmedInput = input.trim();
      if (!trimmedInput || isLoading || !fileUploaded) return;

      setInput('');
      await onSendMessage(trimmedInput);
    },
    [input, isLoading, fileUploaded, onSendMessage]
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const isDisabled = !fileUploaded || isLoading;

  // Sample prompts for users
  const samplePrompts = [
    'Show total Sales by Category',
    'What are the top 5 states by profit?',
    'Create a pie chart of sales by region',
    'How has profit changed over the years?',
  ];

  const handleSamplePrompt = (prompt: string) => {
    if (!isDisabled) {
      setInput(prompt);
    }
  };

  return (
    <div className="card h-[500px] sm:h-[550px] lg:h-[600px] flex flex-col">
      {/* Header */}
      <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-gray-100">
        <h2 className="text-base sm:text-lg font-medium text-gray-900">Chat with your Data</h2>
        <p className="text-xs sm:text-sm text-gray-500 truncate">
          {fileUploaded
            ? `Analyzing: ${fileUploaded.filename}`
            : 'Upload a file to start asking questions'}
        </p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6">
        {messages.length === 0 && fileUploaded && !isLoading ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Ready to analyze your data!
              </h3>
              <p className="text-sm text-gray-500 mb-6">
                Ask questions about your {fileUploaded.filename}
              </p>
            </div>

            {/* Sample prompts */}
            <div className="w-full max-w-md">
              <p className="text-xs font-medium text-gray-500 uppercase mb-3 text-center">
                Try these prompts
              </p>
              <div className="flex flex-wrap gap-2 justify-center">
                {samplePrompts.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleSamplePrompt(prompt)}
                    className="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <MessageList messages={messages} isLoading={isLoading} />
        )}
      </div>

      {/* Input Area */}
      <div className="px-6 py-4 border-t border-gray-100">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              fileUploaded
                ? 'Ask a question about your data...'
                : 'Upload a file first to start chatting'
            }
            className="input-field flex-1"
            disabled={isDisabled}
          />
          <button
            type="submit"
            disabled={isDisabled || !input.trim()}
            className="btn-primary flex items-center gap-2"
          >
            <span>Send</span>
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          </button>
        </form>

        {/* File not uploaded warning */}
        {!fileUploaded && (
          <p className="text-xs text-amber-600 mt-2 flex items-center gap-1">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            Please upload a CSV or XLSX file to start chatting
          </p>
        )}
      </div>
    </div>
  );
}

export default ChatInterface;
