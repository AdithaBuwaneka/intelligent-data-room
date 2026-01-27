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
  const { messages, isLoading, sessionId, sendMessage, startNewChat, previousSessions, switchToSession, clearMessages, loadSessions } = useChat();
  const { file, isUploading, setFile, setIsUploading, setError, restoreFile, clearFile } = useFileUpload();
  const [showError, setShowError] = useState<string | null>(null);
  const [showSessionMenu, setShowSessionMenu] = useState(false);

  // Restore file on mount (in case of browser refresh)
  useEffect(() => {
    restoreFile(sessionId);
  }, [sessionId, restoreFile]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = () => setShowSessionMenu(false);
    if (showSessionMenu) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [showSessionMenu]);

  // Handle starting a new chat
  const handleNewChat = () => {
    startNewChat();
    clearFile();
    setShowError(null);
    setShowSessionMenu(false);
  };

  // Handle clearing current chat
  const handleClearChat = async () => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      await fetch(`${API_URL}/api/history/${sessionId}`, { method: 'DELETE' });
      clearMessages();
      // Reload sessions to update the message count
      await loadSessions();
    } catch (err) {
      console.error('Failed to clear chat:', err);
    }
  };

  // Handle switching to a previous session
  const handleSwitchSession = (targetSessionId: string) => {
    switchToSession(targetSessionId);
    setShowSessionMenu(false);
    clearFile();
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
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14 sm:h-16">
            {/* Logo */}
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="w-8 h-8 sm:w-9 sm:h-9 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center shadow-sm">
                <span className="text-lg sm:text-xl">📊</span>
              </div>
              <div>
                <h1 className="text-lg sm:text-xl font-semibold text-gray-900">
                  Intelligent Data Room
                </h1>
                <p className="text-xs text-gray-500 hidden sm:block">🤖 AI-Powered Data Analysis</p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 sm:gap-3">
              {/* New Chat Button */}
              <button
                onClick={handleNewChat}
                className="flex items-center gap-1 sm:gap-1.5 px-2.5 sm:px-3 py-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                title="New chat"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span className="hidden sm:inline">New</span>
              </button>

              {/* Clear Chat Button - only show if messages exist */}
              {messages.length > 0 && (
                <button
                  onClick={handleClearChat}
                  className="flex items-center gap-1 sm:gap-1.5 px-2.5 sm:px-3 py-1.5 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
                  title="Clear chat"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  <span className="hidden sm:inline">Clear</span>
                </button>
              )}

              {/* Session History Dropdown */}
              <div className="relative">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowSessionMenu(!showSessionMenu);
                  }}
                  className="flex items-center gap-1 sm:gap-1.5 px-2.5 sm:px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                  title="Chat history"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="hidden sm:inline">History</span>
                  {previousSessions.length > 0 && (
                    <span className="ml-0.5 sm:ml-1 px-1.5 py-0.5 text-xs bg-blue-100 text-blue-600 rounded-full">
                      {previousSessions.length}
                    </span>
                  )}
                </button>

                {/* Dropdown Menu */}
                {showSessionMenu && (
                  <div 
                    className="absolute right-0 mt-2 w-72 sm:w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="p-3 border-b border-gray-100">
                      <p className="text-sm font-medium text-gray-900">Chat History</p>
                      <p className="text-xs text-gray-500 mt-0.5">Switch to a previous conversation</p>
                    </div>
                    <div className="max-h-64 overflow-y-auto">
                      {previousSessions.length === 0 ? (
                        <div className="p-6 text-center">
                          <svg className="w-8 h-8 text-gray-300 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                          </svg>
                          <p className="text-sm text-gray-500">No previous chats</p>
                        </div>
                      ) : (
                        previousSessions.map((session) => (
                          <button
                            key={session.sessionId}
                            onClick={() => handleSwitchSession(session.sessionId)}
                            className="w-full px-4 py-3 text-left hover:bg-gray-50 border-b border-gray-50 last:border-0 transition-colors"
                          >
                            <p className="text-sm text-gray-900 truncate font-medium">{session.preview}</p>
                            <p className="text-xs text-gray-400 mt-1">
                              {session.messageCount} messages • {new Date(session.lastActivity).toLocaleDateString()}
                            </p>
                          </button>
                        ))
                      )}
                    </div>
                  </div>
                )}
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
                <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <span className="text-sm">{showError}</span>
              </div>
              <button onClick={() => setShowError(null)} className="text-red-700 hover:text-red-900 p-1">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
          {/* Sidebar - File Upload & Info */}
          <div className="lg:col-span-1 space-y-4">
            <FileUpload
              onFileUploaded={handleFileUploaded}
              sessionId={sessionId}
              isUploading={isUploading}
              onUploadStart={() => setIsUploading(true)}
              onUploadEnd={() => setIsUploading(false)}
              onError={handleError}
              initialFile={file}
            />

            {/* Quick Start Guide */}
            <div className="card p-4 sm:p-5">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Quick Start</h3>
              <ol className="space-y-2.5 text-sm text-gray-600">
                <li className="flex items-start gap-2.5">
                  <span className="w-5 h-5 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">1</span>
                  <span>Upload a CSV or Excel file</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="w-5 h-5 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">2</span>
                  <span>Ask questions in plain English</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="w-5 h-5 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">3</span>
                  <span>Get instant insights & charts</span>
                </li>
              </ol>

              {/* Example queries */}
              <div className="mt-4 pt-3 border-t border-gray-100">
                <p className="text-xs font-medium text-gray-500 mb-2">Example questions:</p>
                <div className="space-y-1.5">
                  <p className="text-xs text-gray-500 italic">"Show total sales by category"</p>
                  <p className="text-xs text-gray-500 italic">"Which region has the highest profit?"</p>
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
      <footer className="border-t border-gray-200 bg-white py-3">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-xs text-gray-400">
            Powered by Google Gemini AI • Multi-Agent System
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
