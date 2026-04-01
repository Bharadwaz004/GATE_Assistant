/**
 * Zustand store — single store with slices for auth, user, plan, and UI.
 */
import { create } from 'zustand';
import { authAPI, userAPI, planAPI, matchAPI } from '../utils/api';

const useStore = create((set, get) => ({
  // ═══════════════════════════════════════════════════════════
  // AUTH SLICE
  // ═══════════════════════════════════════════════════════════
  token: localStorage.getItem('access_token') || null,
  userId: localStorage.getItem('user_id') || null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  initializing: !!localStorage.getItem('access_token'),
  authLoading: false,
  authError: null,

  signup: async (email, password, fullName) => {
    set({ authLoading: true, authError: null });
    try {
      const { data } = await authAPI.signup({ email, password, full_name: fullName });
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user_id', data.user_id);
      set({
        token: data.access_token,
        userId: data.user_id,
        isAuthenticated: true,
        isOnboarded: data.is_onboarded,
        authLoading: false,
      });
      return data;
    } catch (err) {
      const msg = err.response?.data?.detail || 'Signup failed';
      set({ authError: msg, authLoading: false });
      throw err;
    }
  },

  login: async (email, password) => {
    set({ authLoading: true, authError: null });
    try {
      const { data } = await authAPI.login({ email, password });
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user_id', data.user_id);
      set({
        token: data.access_token,
        userId: data.user_id,
        isAuthenticated: true,
        isOnboarded: data.is_onboarded,
        authLoading: false,
      });
      return data;
    } catch (err) {
      const msg = err.response?.data?.detail || 'Login failed';
      set({ authError: msg, authLoading: false });
      throw err;
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
    set({
      token: null, userId: null, isAuthenticated: false,
      profile: null, isOnboarded: false,
      dailyPlan: null, weeklyPlan: null, streak: null,
      progress: null, matches: null,
    });
  },

  // ═══════════════════════════════════════════════════════════
  // USER / PROFILE SLICE
  // ═══════════════════════════════════════════════════════════
  profile: null,
  isOnboarded: false,
  profileLoading: false,

  submitOnboarding: async (data) => {
    set({ profileLoading: true });
    try {
      const { data: profile } = await userAPI.onboarding(data);
      set({ profile, isOnboarded: true, profileLoading: false });
      return profile;
    } catch (err) {
      set({ profileLoading: false });
      throw err;
    }
  },

  fetchProfile: async () => {
    set({ profileLoading: true });
    try {
      const { data } = await userAPI.getProfile();
      set({ profile: data, isOnboarded: data.is_onboarded, profileLoading: false, initializing: false });
      return data;
    } catch (err) {
      set({ profileLoading: false, initializing: false });
      throw err;
    }
  },

  // ═══════════════════════════════════════════════════════════
  // PLAN SLICE
  // ═══════════════════════════════════════════════════════════
  dailyPlan: null,
  weeklyPlan: null,
  planLoading: false,
  planError: null,

  generatePlan: async (weekNumber, forceRegenerate = false) => {
    set({ planLoading: true, planError: null });
    try {
      const { data } = await planAPI.generate({
        week_number: weekNumber,
        force_regenerate: forceRegenerate,
      });
      set({ weeklyPlan: data, planLoading: false });
      return data;
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to generate plan';
      set({ planError: msg, planLoading: false });
      throw err;
    }
  },

  fetchDailyPlan: async (date) => {
    set({ planLoading: true });
    try {
      const { data } = await planAPI.getDaily(date);
      set({ dailyPlan: data, planLoading: false });
      return data;
    } catch (err) {
      set({ planLoading: false });
      throw err;
    }
  },

  updateTask: async (taskId, status, notes) => {
    try {
      const { data } = await planAPI.updateTask({ task_id: taskId, status, notes });
      // Refresh daily plan after update
      const plan = get().dailyPlan;
      if (plan) {
        const updatedTasks = plan.tasks.map((t) =>
          t.id === taskId ? { ...t, status } : t
        );
        const completed = updatedTasks.filter((t) => t.status === 'completed').length;
        set({
          dailyPlan: {
            ...plan,
            tasks: updatedTasks,
            completion_rate: plan.tasks.length > 0
              ? Math.round((completed / plan.tasks.length) * 1000) / 10
              : 0,
          },
        });
      }
      return data;
    } catch (err) {
      throw err;
    }
  },

  // ═══════════════════════════════════════════════════════════
  // STREAK SLICE
  // ═══════════════════════════════════════════════════════════
  streak: null,

  fetchStreak: async () => {
    try {
      const { data } = await planAPI.getStreak();
      set({ streak: data });
      return data;
    } catch (err) {
      console.error('Failed to fetch streak:', err);
    }
  },

  // ═══════════════════════════════════════════════════════════
  // PROGRESS SLICE
  // ═══════════════════════════════════════════════════════════
  progress: null,
  progressLoading: false,

  fetchProgress: async () => {
    set({ progressLoading: true });
    try {
      const { data } = await planAPI.getProgress();
      set({ progress: data, streak: data.streak, progressLoading: false });
      return data;
    } catch (err) {
      set({ progressLoading: false });
      throw err;
    }
  },

  // ═══════════════════════════════════════════════════════════
  // MATCHING SLICE
  // ═══════════════════════════════════════════════════════════
  matches: null,
  matchLoading: false,

  fetchMatches: async (topN = 10) => {
    set({ matchLoading: true });
    try {
      const { data } = await matchAPI.getMatches(topN);
      set({ matches: data, matchLoading: false });
      return data;
    } catch (err) {
      set({ matchLoading: false });
      throw err;
    }
  },

  // ═══════════════════════════════════════════════════════════
  // UI SLICE
  // ═══════════════════════════════════════════════════════════
  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}));

export default useStore;
