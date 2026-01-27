/**
 * useChat Hook
 *
 * Manages chat state, session, and message operations.
 * Handles communication with the backend API.
 * Supports chat history restoration, new chat creation, and session switching.
 */

import { useState, useCallback, useEffect } from 'react';
import type { Message, QueryResponse } from '../types';

const SESSION_KEY = 'idr_session_id';

interface SessionInfo {
  sessionId: string;
  preview: string;
  messageCount: number;
  createdAt: string;
  lastActivity: string;
}

interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  isRestoring: boolean;
  error: string | null;
  sessionId: string;
  previousSessions: SessionInfo[];
  sendMessage: (content: string, fileUrl: string) => Promise<QueryResponse>;
  clearMessages: () => void;
  clearError: () => void;
  startNewChat: () => void;
  switchToSession: (sessionId: string) => void;
  restoreHistory: () => Promise<void>;
  loadSessions: () => Promise<void>;
}

/**
 * Generate or retrieve session ID
 */
function getOrCreateSessionId(): string {
  const stored = localStorage.getItem(SESSION_KEY);
  if (stored) return stored;

  const newId = crypto.randomUUID();
  localStorage.setItem(SESSION_KEY, newId);
  return newId;
}

/**
 * Create a brand new session ID
 */
function createNewSessionId(): string {
  const newId = crypto.randomUUID();
  localStorage.setItem(SESSION_KEY, newId);
  return newId;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>(getOrCreateSessionId);
  const [previousSessions, setPreviousSessions] = useState<SessionInfo[]>([]);

  /**
   * Load sessions list from MongoDB via API
   */
  const loadSessions = useCallback(async () => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/api/sessions`);

      if (response.ok) {
        const data = await response.json();
        const sessions: SessionInfo[] = data.sessions
          .filter((s: { session_id: string }) => s.session_id !== sessionId)
          .map((s: {
            session_id: string;
            preview: string;
            message_count: number;
            created_at: string;
            last_activity: string;
          }) => ({
            sessionId: s.session_id,
            preview: s.preview,
            messageCount: s.message_count,
            createdAt: s.created_at,
            lastActivity: s.last_activity,
          }));
        setPreviousSessions(sessions);
      }
    } catch (err) {
      console.warn('Failed to load sessions:', err);
    }
  }, [sessionId]);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  /**
   * Restore chat history from backend
   */
  const restoreHistory = useCallback(async () => {
    setIsRestoring(true);
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/api/history/${sessionId}`);

      if (response.ok) {
        const data = await response.json();
        if (data.messages && data.messages.length > 0) {
          const restoredMessages: Message[] = data.messages.map((msg: {
            id: string;
            role: 'user' | 'assistant';
            content: string;
            timestamp: string;
            plan?: string;
            chart_config?: unknown;
          }) => ({
            id: msg.id,
            role: msg.role,
            content: msg.content,
            timestamp: new Date(msg.timestamp),
            plan: msg.plan,
            chartConfig: msg.chart_config,
          }));
          setMessages(restoredMessages);
        }
      }
    } catch (err) {
      console.warn('Failed to restore chat history:', err);
    } finally {
      setIsRestoring(false);
    }
  }, [sessionId]);

  // Restore history on mount and session change
  useEffect(() => {
    restoreHistory();
  }, [restoreHistory]);

  /**
   * Send a message and get AI response
   */
  const sendMessage = useCallback(
    async (content: string, fileUrl: string): Promise<QueryResponse> => {
      // Add user message immediately
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      try {
        const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await fetch(`${API_URL}/api/query`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            session_id: sessionId,
            question: content,
            file_url: fileUrl,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Failed to get response');
        }

        const data: QueryResponse = await response.json();

        // Add assistant message
        const assistantMessage: Message = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.answer,
          timestamp: new Date(),
          plan: data.plan,
          chartConfig: data.chart_config,
        };

        setMessages((prev) => [...prev, assistantMessage]);

        // Reload sessions list to update previews
        loadSessions();

        return data;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'An unexpected error occurred';
        setError(errorMessage);

        // Add error message as assistant response
        const errorResponseMessage: Message = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `Sorry, I encountered an error: ${errorMessage}. Please try again.`,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, errorResponseMessage]);

        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, loadSessions]
  );

  /**
   * Clear all messages (keep same session)
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  /**
   * Start a completely new chat session
   */
  const startNewChat = useCallback(() => {
    setMessages([]);
    setError(null);
    const newId = createNewSessionId();
    setSessionId(newId);
    localStorage.removeItem('idr_uploaded_file');
    // Reload sessions to show the old session in the list
    setTimeout(() => loadSessions(), 100);
  }, [loadSessions]);

  /**
   * Switch to a previous session
   */
  const switchToSession = useCallback((targetSessionId: string) => {
    setMessages([]);
    setError(null);
    localStorage.setItem(SESSION_KEY, targetSessionId);
    setSessionId(targetSessionId);
    // History will be restored by the useEffect
  }, []);

  /**
   * Clear error
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    isRestoring,
    error,
    sessionId,
    previousSessions,
    sendMessage,
    clearMessages,
    clearError,
    startNewChat,
    switchToSession,
    restoreHistory,
    loadSessions,
  };
}

export default useChat;
