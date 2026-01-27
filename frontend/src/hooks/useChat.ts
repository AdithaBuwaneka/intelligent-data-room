/**
 * useChat Hook
 *
 * Manages chat state, session, and message operations.
 * Handles communication with the backend API.
 */

import { useState, useCallback } from 'react';
import type { Message, QueryResponse } from '../types';

const SESSION_KEY = 'idr_session_id';

interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  sessionId: string;
  sendMessage: (content: string, fileUrl: string) => Promise<QueryResponse>;
  clearMessages: () => void;
  clearError: () => void;
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

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId] = useState<string>(getOrCreateSessionId);

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
    [sessionId]
  );

  /**
   * Clear all messages
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
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
    error,
    sessionId,
    sendMessage,
    clearMessages,
    clearError,
  };
}

export default useChat;
