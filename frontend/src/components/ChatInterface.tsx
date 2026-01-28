/**
 * ChatInterface Component
 *
 * Main chat interface for interacting with the data analysis AI.
 * Handles message input, sending queries, and displaying responses.
 *
 * DYNAMIC SUGGESTIONS:
 * Generates relevant sample prompts based on the uploaded file's columns.
 * Updates automatically when a different file is uploaded.
 */

import { useState, useCallback, useMemo } from 'react';
import type { Message, FileMetadata, QueryResponse } from '../types';
import MessageList from './MessageList';

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (content: string) => Promise<QueryResponse>;
  isLoading: boolean;
  fileUploaded: FileMetadata | null;
}

/**
 * Generate dynamic sample prompts based on file columns.
 * Creates relevant suggestions that match the actual data.
 */
function generateDynamicPrompts(columns: string[]): string[] {
  if (!columns || columns.length === 0) {
    return [
      'How many rows are in this dataset?',
      'What columns are available?',
      'Show summary statistics',
      'What is the data about?',
    ];
  }

  const prompts: string[] = [];
  const colLower = columns.map(c => c.toLowerCase());

  // Find potential categorical columns (common patterns)
  const categoryPatterns = ['category', 'type', 'region', 'state', 'country', 'segment', 'department', 'status', 'company', 'name'];
  const numericPatterns = ['sales', 'profit', 'revenue', 'amount', 'price', 'quantity', 'count', 'total', 'cost'];
  const datePatterns = ['date', 'year', 'month', 'time', 'period'];

  // Find matching columns
  const categoryCol = columns.find(c => categoryPatterns.some(p => c.toLowerCase().includes(p)));
  const numericCol = columns.find(c => numericPatterns.some(p => c.toLowerCase().includes(p)));
  const dateCol = columns.find(c => datePatterns.some(p => c.toLowerCase().includes(p)));

  // Generate prompts based on found columns
  if (numericCol && categoryCol) {
    prompts.push(`Show total ${numericCol} by ${categoryCol}`);
    prompts.push(`What are the top 5 ${categoryCol}s by ${numericCol}?`);
  }

  if (categoryCol) {
    prompts.push(`Create a pie chart by ${categoryCol}`);
  }

  if (numericCol && dateCol) {
    prompts.push(`How has ${numericCol} changed over time?`);
  }

  // Add generic prompts if we don't have enough
  if (prompts.length < 2) {
    prompts.push(`How many rows are in this dataset?`);
  }

  if (prompts.length < 3 && columns.length > 0) {
    prompts.push(`Show distribution of ${columns[0]}`);
  }

  if (prompts.length < 4) {
    prompts.push(`Show summary statistics`);
  }

  // Return up to 4 prompts
  return prompts.slice(0, 4);
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

  // DYNAMIC: Generate sample prompts based on file columns
  // Updates automatically when different file is uploaded
  const samplePrompts = useMemo(() => {
    if (fileUploaded?.columns) {
      return generateDynamicPrompts(fileUploaded.columns);
    }
    return [
      'How many rows are in this dataset?',
      'What columns are available?',
      'Show summary statistics',
      'What is the data about?',
    ];
  }, [fileUploaded?.columns]);

  // FOLLOW-UP SUGGESTIONS: Generate based on last analysis
  // Shows after a chart/analysis is displayed
  const followUpSuggestions = useMemo(() => {
    if (messages.length === 0) return [];

    // Find last assistant message with chart
    const lastAssistantMsg = [...messages].reverse().find(
      m => m.role === 'assistant' && m.chartConfig
    );

    if (!lastAssistantMsg?.chartConfig) return [];

    const suggestions: string[] = [];
    const chartType = lastAssistantMsg.chartConfig.type;

    // Suggest different chart types
    if (chartType !== 'pie') {
      suggestions.push('Show as pie chart');
    }
    if (chartType !== 'bar') {
      suggestions.push('Show as bar chart');
    }
    if (chartType !== 'line') {
      suggestions.push('Show as line chart');
    }

    // Suggest limit changes
    suggestions.push('Top 10 instead');
    suggestions.push('Show more');

    return suggestions.slice(0, 4);
  }, [messages]);

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

      {/* Follow-up Suggestions - shown after analysis */}
      {followUpSuggestions.length > 0 && !isLoading && messages.length > 0 && (
        <div className="px-4 py-2 border-t border-gray-100 bg-gray-50">
          <p className="text-xs text-gray-500 mb-2">Quick follow-ups:</p>
          <div className="flex flex-wrap gap-2">
            {followUpSuggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => handleSamplePrompt(suggestion)}
                disabled={isDisabled}
                className="px-2.5 py-1 text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-md transition-colors disabled:opacity-50"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

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
