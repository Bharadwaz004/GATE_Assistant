/**
 * Extended API client — analytics endpoints.
 */
import api from './api';

export const analyticsAPI = {
  getDailyHours: (days = 30) =>
    api.get('/analytics/daily-hours', { params: { days } }),
  getSubjectBreakdown: () =>
    api.get('/analytics/subject-breakdown'),
  getWeakTopics: (threshold = 50) =>
    api.get('/analytics/weak-topics', { params: { threshold } }),
  getImprovementTrend: (weeks = 8) =>
    api.get('/analytics/improvement-trend', { params: { weeks } }),
};
