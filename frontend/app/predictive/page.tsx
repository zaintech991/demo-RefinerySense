'use client'

import { useEffect, useState } from 'react'
import { assetsApi, healthApi, type Asset, type HealthScore } from '@/lib/api'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts'
import { BarChart3, Clock, AlertTriangle, TrendingDown } from 'lucide-react'

export default function PredictivePage() {
  const [assets, setAssets] = useState<Asset[]>([])
  const [selectedAsset, setSelectedAsset] = useState<number | null>(null)
  const [healthScores, setHealthScores] = useState<HealthScore[]>([])
  const [forecast, setForecast] = useState<any>(null)
  const [forecastParam, setForecastParam] = useState<string>('temperature')

  useEffect(() => {
    loadAssets()
  }, [])

  useEffect(() => {
    if (selectedAsset) {
      loadHealthScores()
      loadForecast()
    }
  }, [selectedAsset, forecastParam])

  const loadAssets = async () => {
    try {
      const response = await assetsApi.getAll()
      setAssets(response.data)
      if (response.data.length > 0 && !selectedAsset) {
        setSelectedAsset(response.data[0].id)
      }
    } catch (error) {
      console.error('Error loading assets:', error)
    }
  }

  const loadHealthScores = async () => {
    if (!selectedAsset) return
    try {
      const response = await healthApi.getScores(selectedAsset, 100)
      setHealthScores(response.data)
    } catch (error) {
      console.error('Error loading health scores:', error)
    }
  }

  const loadForecast = async () => {
    if (!selectedAsset) return
    try {
      const response = await healthApi.getForecast(selectedAsset, forecastParam, 24)
      setForecast(response.data)
    } catch (error) {
      console.error('Error loading forecast:', error)
    }
  }

  const currentAsset = assets.find((a) => a.id === selectedAsset)
  const latestHealth = healthScores[0]

  // Prepare chart data
  const healthChartData = healthScores
    .slice()
    .reverse()
    .slice(-30)
    .map((h) => ({
      date: new Date(h.timestamp).toLocaleDateString(),
      health: h.health_index,
      rul: h.rul_days || 0,
      risk: h.failure_risk_score || 0,
    }))

  // Combine historical and forecast data
  const forecastChartData = forecast
    ? [
        ...healthChartData.slice(-10).map((d, i) => ({
          time: `T-${10 - i}`,
          value: d.health,
          type: 'historical',
        })),
        ...forecast.values.slice(0, 12).map((v: number, i: number) => ({
          time: `T+${i + 1}`,
          value: v,
          type: 'forecast',
        })),
      ]
    : []

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 flex items-center gap-3">
          <BarChart3 className="w-10 h-10 text-primary-400" />
          Predictive Maintenance
        </h1>

        {/* Asset Selector */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Select Asset</label>
          <select
            value={selectedAsset || ''}
            onChange={(e) => setSelectedAsset(Number(e.target.value))}
            className="bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700"
          >
            {assets.map((asset) => (
              <option key={asset.id} value={asset.id}>
                {asset.name} ({asset.asset_type})
              </option>
            ))}
          </select>
        </div>

        {currentAsset && latestHealth && (
          <>
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
              <MetricCard
                icon={BarChart3}
                label="Health Index"
                value={latestHealth.health_index.toFixed(1)}
                unit="/100"
                color={latestHealth.health_index > 70 ? 'green' : latestHealth.health_index > 40 ? 'yellow' : 'red'}
              />
              <MetricCard
                icon={Clock}
                label="Remaining Useful Life"
                value={latestHealth.rul_days ? `${latestHealth.rul_days.toFixed(1)} days` : 'N/A'}
                color={latestHealth.rul_days && latestHealth.rul_days < 30 ? 'red' : latestHealth.rul_days && latestHealth.rul_days < 90 ? 'yellow' : 'green'}
              />
              <MetricCard
                icon={AlertTriangle}
                label="Failure Risk"
                value={latestHealth.failure_risk_score ? latestHealth.failure_risk_score.toFixed(1) : 'N/A'}
                unit="/100"
                color={latestHealth.failure_risk_score && latestHealth.failure_risk_score > 70 ? 'red' : latestHealth.failure_risk_score && latestHealth.failure_risk_score > 40 ? 'yellow' : 'green'}
              />
              <MetricCard
                icon={TrendingDown}
                label="Anomaly Score"
                value={latestHealth.anomaly_score ? latestHealth.anomaly_score.toFixed(1) : 'N/A'}
                unit="/100"
              />
            </div>

            {/* Health Trend Chart */}
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 mb-8">
              <h3 className="text-xl font-semibold mb-4">Health Index Trend (Last 30 Days)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={healthChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="date" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" domain={[0, 100]} />
                  <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                  <Line
                    type="monotone"
                    dataKey="health"
                    stroke="#0EA5E9"
                    strokeWidth={2}
                    name="Health Index"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* RUL Timeline */}
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 mb-8">
              <h3 className="text-xl font-semibold mb-4">Remaining Useful Life Timeline</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={healthChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="date" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                  <Bar dataKey="rul" fill="#10B981" name="RUL (days)" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Forecast Section */}
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 mb-8">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold">Forecast</h3>
                <select
                  value={forecastParam}
                  onChange={(e) => setForecastParam(e.target.value)}
                  className="bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600"
                >
                  <option value="temperature">Temperature</option>
                  <option value="pressure">Pressure</option>
                  <option value="vibration">Vibration</option>
                  <option value="flow">Flow</option>
                </select>
              </div>
              {forecastChartData.length > 0 && (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={forecastChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="time" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#0EA5E9"
                      strokeWidth={2}
                      name="Value"
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
              {forecast && (
                <div className="mt-4 text-sm text-gray-400">
                  Forecast confidence: {(forecast.confidence * 100).toFixed(0)}% | Method: {forecast.method}
                </div>
              )}
            </div>

            {/* Risk Assessment */}
            {latestHealth.rul_days && (
              <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <h3 className="text-xl font-semibold mb-4">Maintenance Recommendation</h3>
                <div className="space-y-3">
                  {latestHealth.rul_days < 7 ? (
                    <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="w-5 h-5 text-red-400" />
                        <span className="font-semibold text-red-400">Critical: Immediate Maintenance Required</span>
                      </div>
                      <p className="text-gray-300">
                        Estimated RUL is only {latestHealth.rul_days.toFixed(1)} days. Schedule maintenance immediately.
                      </p>
                    </div>
                  ) : latestHealth.rul_days < 30 ? (
                    <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="w-5 h-5 text-yellow-400" />
                        <span className="font-semibold text-yellow-400">Warning: Schedule Maintenance Soon</span>
                      </div>
                      <p className="text-gray-300">
                        Estimated RUL is {latestHealth.rul_days.toFixed(1)} days. Plan maintenance within the next week.
                      </p>
                    </div>
                  ) : (
                    <div className="bg-green-900/20 border border-green-700 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Clock className="w-5 h-5 text-green-400" />
                        <span className="font-semibold text-green-400">Normal: No Immediate Action Required</span>
                      </div>
                      <p className="text-gray-300">
                        Estimated RUL is {latestHealth.rul_days.toFixed(1)} days. Continue monitoring.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function MetricCard({ icon: Icon, label, value, unit, color }: {
  icon: any
  label: string
  value: string
  unit?: string
  color?: 'green' | 'yellow' | 'red'
}) {
  const colorClasses = {
    green: 'text-green-400',
    yellow: 'text-yellow-400',
    red: 'text-red-400',
  }

  return (
    <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <Icon className={`w-6 h-6 ${color ? colorClasses[color] : 'text-primary-400'}`} />
        <span className="text-gray-400 text-sm">{label}</span>
      </div>
      <div className={`text-3xl font-bold ${color ? colorClasses[color] : 'text-white'}`}>
        {value}
        {unit && <span className="text-lg text-gray-400 ml-1">{unit}</span>}
      </div>
    </div>
  )
}

