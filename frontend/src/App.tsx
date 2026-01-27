/**
 * Intelligent Data Room - Main App Component
 *
 * A GenAI-powered data analysis platform using multi-agent system.
 * Users can upload CSV/XLSX files and chat with their data.
 */

import { useState, useEffect } from 'react';
import { FileUpload } from './components/FileUpload';
import { ChatInterface } from './components/ChatInterface';
import { useChat } from './hooks/useChat';
import { useFileUpload } from './hooks/useFileUpload';
import type { FileMetadata } from './types';

function App() {
  const { messages, isLoading, sessionId, sendMessage, startNewChat } = useChat();
  const { file, isUploading, setFile, setIsUploading, setError, restoreFile, clearFile } = useFileUpload();
  const [showError, setShowError] = useState<string | null>(null);

  // Restore file on mount (in case of browser refresh)
  useEffect(() => {
    restoreFile(sessionId);
  }, [sessionId, restoreFile]);

  // Handle starting a new chat
  const handleNewChat = () => {
    startNewChat();
    clearFile();
    setShowError(null);
  };

  // Handle file upload completion
  const handleFileUploaded = (metadata: FileMetadata) => {
    setFile(metadata);
    setShowError(null);
  };

  // Handle errors
  const handleError = (errorMessage: string) => {
    setShowError(errorMessage);
    setError(errorMessage);
  };

  // Handle send message
  const handleSendMessage = async (content: string) => {
    if (!file) {
      throw new Error('No file uploaded');
    }
    return sendMessage(content, file.fileUrl);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <svg
                  className="w-5 h-5 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              <h1 className="text-xl font-semibold text-gray-900">
                Intelligent Data Room
              </h1>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={handleNewChat}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                title="Start a new chat session"
              >
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
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                New Chat
              </button>
              <span className="text-xs text-gray-400">
                Session: {sessionId.slice(0, 8)}...
              </span>
              <div className="text-sm text-gray-500">
                AI-Powered Data Analysis
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {showError && (
        <div className="bg-red-50 border-b border-red-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-red-700">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="text-sm">{showError}</span>
              </div>
              <button
                onClick={() => setShowError(null)}
                className="text-red-700 hover:text-red-900"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
          {/* Sidebar - File Upload */}
          <div className="lg:col-span-1">
            <FileUpload
              onFileUploaded={handleFileUploaded}
              sessionId={sessionId}
              isUploading={isUploading}
              onUploadStart={() => setIsUploading(true)}
              onUploadEnd={() => setIsUploading(false)}
              onError={handleError}
            />

            {/* Info Card */}
            <div className="card p-6 mt-6">
              <h3 className="text-sm font-medium text-gray-900 mb-3">
                How it works
              </h3>
              <ul className="space-y-3 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0">
                    1
                  </span>
                  <span>Upload your CSV or XLSX file</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0">
                    2
                  </span>
                  <span>Ask questions in natural language</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0">
                    3
                  </span>
                  <span>AI analyzes and visualizes results</span>
                </li>
              </ul>

              {/* Agent Info */}
              <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-xs text-gray-500 mb-2">Powered by Multi-Agent System:</p>
                <div className="flex gap-2">
                  <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded">
                    Planner Agent
                  </span>
                  <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">
                    Executor Agent
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Chat Interface */}
          <div className="lg:col-span-2">
            <ChatInterface
              messages={messages}
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
              fileUploaded={file}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-500">
            Powered by LangGraph + PandasAI + Google Gemini | Built for GenAI Challenge
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
