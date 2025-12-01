import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface Asset {
  id: number
  name: string
  asset_type: string
  location?: string
  status: string
  created_at: string
  updated_at: string
}

export interface SensorReading {
  id: number
  asset_id: number
  timestamp: string
  temperature?: number
  pressure?: number
  vibration?: number
  flow?: number
  rpm?: number
}

export interface HealthScore {
  id: number
  asset_id: number
  timestamp: string
  health_index: number
  twin_deviation_score?: number
  anomaly_score?: number
  rul_days?: number
  failure_risk_score?: number
}

export interface Alert {
  id: number
  asset_id: number
  timestamp: string
  alert_type: string
  severity: string
  message: string
  resolved: boolean
  resolved_at?: string
}

export interface DigitalTwinState {
  id: number
  asset_id: number
  timestamp: string
  expected_temperature?: number
  expected_pressure?: number
  expected_vibration?: number
  expected_flow?: number
  expected_rpm?: number
  deviation_score?: number
}

// API functions
export const assetsApi = {
  getAll: () => api.get<Asset[]>('/api/assets/'),
  getById: (id: number) => api.get<Asset>(`/api/assets/${id}`),
  getMetrics: (id: number) => api.get(`/api/assets/${id}/metrics`),
}

export const sensorsApi = {
  getReadings: (assetId?: number, limit = 100) =>
    api.get<SensorReading[]>('/api/sensors/readings', {
      params: { asset_id: assetId, limit },
    }),
}

export const healthApi = {
  getScores: (assetId?: number, limit = 100) =>
    api.get<HealthScore[]>('/api/health/scores', {
      params: { asset_id: assetId, limit },
    }),
  getLatestScore: (assetId: number) =>
    api.get<HealthScore>(`/api/health/scores/${assetId}/latest`),
  getForecast: (assetId: number, param = 'temperature', horizonHours = 24) =>
    api.get(`/api/health/forecast/${assetId}`, {
      params: { param, horizon_hours: horizonHours },
    }),
}

export const alertsApi = {
  getAll: (assetId?: number, resolved?: boolean, severity?: string) =>
    api.get<Alert[]>('/api/alerts', {
      params: { asset_id: assetId, resolved, severity },
    }),
  resolve: (alertId: number) => api.post(`/api/alerts/${alertId}/resolve`),
}

export const chatApi = {
  sendMessage: (message: string, conversationId?: string) =>
    api.post('/api/chat/', { message, conversation_id: conversationId }),
}

export default api

