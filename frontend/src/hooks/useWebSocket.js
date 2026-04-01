/**
 * useWebSocket — manages a persistent WebSocket connection
 * for real-time updates (plan generated, task updated, streak changes).
 */
import { useEffect, useRef, useCallback } from 'react';
import useStore from '../store/useStore';

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
const RECONNECT_DELAY = 3000;
const MAX_RECONNECT_ATTEMPTS = 5;

export default function useWebSocket() {
  const wsRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef(null);

  const token = useStore((s) => s.token);
  const isAuthenticated = useStore((s) => s.isAuthenticated);
  const fetchDailyPlan = useStore((s) => s.fetchDailyPlan);
  const fetchStreak = useStore((s) => s.fetchStreak);
  const fetchMatches = useStore((s) => s.fetchMatches);

  const handleMessage = useCallback((event) => {
    try {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'plan_generated':
          // Refresh daily plan when background generation completes
          fetchDailyPlan();
          break;

        case 'task_updated':
          // Already handled optimistically in the store
          break;

        case 'streak_updated':
          fetchStreak();
          break;

        case 'new_match':
          fetchMatches(5);
          break;

        case 'pong':
          // Keepalive response, do nothing
          break;

        default:
          console.log('[WS] Unknown message type:', data.type);
      }
    } catch (err) {
      console.error('[WS] Failed to parse message:', err);
    }
  }, [fetchDailyPlan, fetchStreak, fetchMatches]);

  const connect = useCallback(() => {
    if (!token || !isAuthenticated) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`${WS_BASE}/ws?token=${token}`);

    ws.onopen = () => {
      console.log('[WS] Connected');
      reconnectAttemptsRef.current = 0;
    };

    ws.onmessage = handleMessage;

    ws.onclose = (event) => {
      console.log(`[WS] Closed (code=${event.code})`);
      wsRef.current = null;

      // Don't reconnect on auth failure
      if (event.code === 4001) return;

      // Auto-reconnect with backoff
      if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = RECONNECT_DELAY * Math.pow(1.5, reconnectAttemptsRef.current);
        reconnectTimerRef.current = setTimeout(() => {
          reconnectAttemptsRef.current += 1;
          connect();
        }, delay);
      }
    };

    ws.onerror = () => {
      console.error('[WS] Error occurred');
    };

    wsRef.current = ws;
  }, [token, isAuthenticated, handleMessage]);

  // Keepalive ping every 30s
  useEffect(() => {
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // Connect on auth, disconnect on logout
  useEffect(() => {
    if (isAuthenticated && token) {
      connect();
    }

    return () => {
      clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [isAuthenticated, token, connect]);

  return {
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
  };
}
