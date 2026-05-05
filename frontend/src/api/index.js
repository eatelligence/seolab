import { get, post, patch, del, api } from '@/lib/api';

// ---------- Projects ----------
export const projectsApi = {
  list: (params) => get('/projects', params),
  create: (body) => post('/projects', body),
  get: (id) => get(`/projects/${id}`),
  update: (id, body) => patch(`/projects/${id}`, body),
  remove: (id) => del(`/projects/${id}`),
};

// ---------- Tags ----------
export const tagsApi = {
  list: () => get('/project-tags'),
  create: (body) => post('/project-tags', body),
  update: (id, body) => patch(`/project-tags/${id}`, body),
  remove: (id) => del(`/project-tags/${id}`),
};

// ---------- Dashboard ----------
export const dashboardApi = {
  get: (projectId, days = 90) => get(`/projects/${projectId}/dashboard`, { days }),
};

// ---------- Keywords ----------
export const keywordsApi = {
  list: (projectId, params) => get(`/projects/${projectId}/keywords`, params),
  research: (projectId, body) => post(`/projects/${projectId}/keywords/research`, body),
  related: (projectId, params) => get(`/projects/${projectId}/keywords/related`, params),
  questions: (projectId, params) => get(`/projects/${projectId}/keywords/questions`, params),
  save: (projectId, body) => post(`/projects/${projectId}/keywords/save`, body),
  remove: (projectId, kid) => del(`/projects/${projectId}/keywords/${kid}`),
  exportUrl: (projectId) => `${api.defaults.baseURL}/projects/${projectId}/keywords/export.csv`,
  lists: {
    list: (projectId) => get(`/projects/${projectId}/keyword-lists`),
    create: (projectId, body) => post(`/projects/${projectId}/keyword-lists`, body),
    get: (projectId, id) => get(`/projects/${projectId}/keyword-lists/${id}`),
    remove: (projectId, id) => del(`/projects/${projectId}/keyword-lists/${id}`),
  },
};

// ---------- Rank Tracker ----------
export const rankingsApi = {
  list: (projectId) => get(`/projects/${projectId}/rankings`),
  checkNow: (projectId) => post(`/projects/${projectId}/rankings/check`),
  startTracking: (projectId, kid) => post(`/projects/${projectId}/keywords/${kid}/track`),
  stopTracking: (projectId, kid) => del(`/projects/${projectId}/keywords/${kid}/track`),
  history: (projectId, kid, days = 90) => get(`/projects/${projectId}/keywords/${kid}/history`, { days }),
  visibility: (projectId, days = 90) => get(`/projects/${projectId}/visibility`, { days }),
  alerts: (projectId, days = 7) => get(`/projects/${projectId}/rankings/alerts`, { days }),
};

// ---------- GSC ----------
export const gscApi = {
  authUrl: (projectId) => get(`/projects/${projectId}/gsc/auth-url`),
  status: (projectId) => get(`/projects/${projectId}/gsc/status`),
  properties: (projectId) => get(`/projects/${projectId}/gsc/properties`),
  setProperty: (projectId, site_url) => post(`/projects/${projectId}/gsc/property`, { site_url }),
  disconnect: (projectId) => del(`/projects/${projectId}/gsc`),
  performance: (projectId, days = 90) => get(`/projects/${projectId}/gsc/performance`, { days }),
  topKeywords: (projectId, params) => get(`/projects/${projectId}/gsc/top-keywords`, params),
  topPages: (projectId, params) => get(`/projects/${projectId}/gsc/top-pages`, params),
};

// ---------- Site Audit ----------
export const auditApi = {
  start: (projectId, body) => post(`/projects/${projectId}/audit/runs`, body || { run_pagespeed: true }),
  list: (projectId, limit = 20) => get(`/projects/${projectId}/audit/runs`, { limit }),
  latest: (projectId) => get(`/projects/${projectId}/audit/runs/latest`),
  get: (projectId, runId) => get(`/projects/${projectId}/audit/runs/${runId}`),
  issues: (projectId, runId, params) => get(`/projects/${projectId}/audit/runs/${runId}/issues`, params),
  pages: (projectId, runId, params) => get(`/projects/${projectId}/audit/runs/${runId}/pages`, params),
  page: (projectId, runId, pageId) => get(`/projects/${projectId}/audit/runs/${runId}/pages/${pageId}`),
  pdfUrl: (projectId, runId) => `${api.defaults.baseURL}/projects/${projectId}/audit/runs/${runId}/report.pdf`,
};

// ---------- Backlinks ----------
export const backlinksApi = {
  overview: (projectId) => get(`/projects/${projectId}/backlinks/overview`),
  list: (projectId, limit = 100) => get(`/projects/${projectId}/backlinks/list`, { limit }),
  refdomains: (projectId, limit = 100) => get(`/projects/${projectId}/backlinks/refdomains`, { limit }),
  anchors: (projectId, limit = 100) => get(`/projects/${projectId}/backlinks/anchors`, { limit }),
  toxic: (projectId, limit = 200) => get(`/projects/${projectId}/backlinks/toxic`, { limit }),
  history: (projectId, days = 90) => get(`/projects/${projectId}/backlinks/history`, { days }),
  snapshot: (projectId) => post(`/projects/${projectId}/backlinks/snapshot`),
};

// ---------- Competitors ----------
export const competitorsApi = {
  overview: (projectId) => get(`/projects/${projectId}/competitors/overview`),
  keywordGap: (projectId, limit = 200) => get(`/projects/${projectId}/competitors/keyword-gap`, { limit }),
  contentGap: (projectId, limit = 50) => get(`/projects/${projectId}/competitors/content-gap`, { limit }),
  serpOverlap: (projectId) => get(`/projects/${projectId}/competitors/serp-overlap`),
};

// ---------- Content Tools ----------
export const contentApi = {
  brief: (projectId, body) => post(`/projects/${projectId}/content/seo-brief`, body),
  optimize: (projectId, body) => post(`/projects/${projectId}/content/optimize`, body),
  meta: (projectId, body) => post(`/projects/${projectId}/content/meta`, body),
  calendar: (projectId, body) => post(`/projects/${projectId}/content/calendar`, body),
};

// ---------- AI Visibility ----------
export const aiVisApi = {
  queries: (projectId) => get(`/projects/${projectId}/ai-visibility/queries`),
  createQuery: (projectId, body) => post(`/projects/${projectId}/ai-visibility/queries`, body),
  updateQuery: (projectId, qid, body) => patch(`/projects/${projectId}/ai-visibility/queries/${qid}`, body),
  removeQuery: (projectId, qid) => del(`/projects/${projectId}/ai-visibility/queries/${qid}`),
  checkAll: (projectId) => post(`/projects/${projectId}/ai-visibility/check`),
  checkOne: (projectId, qid) => post(`/projects/${projectId}/ai-visibility/queries/${qid}/check`),
  checks: (projectId, qid, limit = 30) => get(`/projects/${projectId}/ai-visibility/queries/${qid}/checks`, { limit }),
  overview: (projectId, days = 30) => get(`/projects/${projectId}/ai-visibility/overview`, { days }),
  history: (projectId, days = 90) => get(`/projects/${projectId}/ai-visibility/history`, { days }),
  suggestions: (projectId) => get(`/projects/${projectId}/ai-visibility/suggestions`),
};
