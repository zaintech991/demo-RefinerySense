'use client'

import { useEffect, useState } from 'react'
import { assetsApi, sensorsApi, healthApi, type Asset, type SensorReading, type HealthScore } from '@/lib/api'
import { SensorWebSocket } from '@/lib/websocket'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'
import { Activity, Thermometer, Gauge, Waves, Zap, TrendingUp } from 'lucide-react'

export default function MonitoringPage() {
  const [assets, setAssets] = useState<Asset[]>([])
  const [selectedAsset, setSelectedAsset] = useState<number | null>(null)
  const [readings, setReadings] = useState<SensorReading[]>([])
  const [healthScore, setHealthScore] = useState<HealthScore | null>(null)
  const [realTimeData, setRealTimeData] = useState<any>(null)
  const [chartData, setChartData] = useState<any[]>([])

  useEffect(() => {
    loadAssets()
  }, [])

  useEffect(() => {
    if (selectedAsset) {
      loadReadings()
      loadHealthScore()
    }
  }, [selectedAsset])

  useEffect(() => {
    if (selectedAsset && realTimeData) {
      const newData = {
        time: new Date(realTimeData.data.reading.timestamp).toLocaleTimeString(),
        temperature: realTimeData.data.reading.temperature,
        pressure: realTimeData.data.reading.pressure,
        vibration: realTimeData.data.reading.vibration,
        flow: realTimeData.data.reading.flow,
        rpm: realTimeData.data.reading.rpm,
      }
      setChartData((prev) => {
        const updated = [...prev, newData]
        return updated.slice(-50) // Keep last 50 points
      })
      setHealthScore(realTimeData.data.health)
    }
  }, [realTimeData, selectedAsset])

  const loadAssets = async () => {
    try {
      const response = await assetsApi.getAll()
      console.log('Assets response:', response.data)
      setAssets(response.data || [])
      if (response.data && response.data.length > 0 && !selectedAsset) {
        setSelectedAsset(response.data[0].id)
      } else if (response.data && response.data.length === 0) {
        console.warn('No assets found. Please run the demo data initialization script.')
      }
    } catch (error: any) {
      console.error('Error loading assets:', error)
      if (error.response) {
        console.error('Response status:', error.response.status)
        console.error('Response data:', error.response.data)
      } else if (error.request) {
        console.error('No response received. Is the backend running?')
      }
    }
  }

  const loadReadings = async () => {
    if (!selectedAsset) return
    try {
      const response = await sensorsApi.getReadings(selectedAsset, 50)
      setReadings(response.data)
      // Prepare chart data
      const data = response.data
        .slice()
        .reverse()
        .map((r) => ({
          time: new Date(r.timestamp).toLocaleTimeString(),
          temperature: r.temperature,
          pressure: r.pressure,
          vibration: r.vibration,
          flow: r.flow,
          rpm: r.rpm,
        }))
      setChartData(data)
    } catch (error) {
      console.error('Error loading readings:', error)
    }
  }

  const loadHealthScore = async () => {
    if (!selectedAsset) return
    try {
      const response = await healthApi.getLatestScore(selectedAsset)
      setHealthScore(response.data)
    } catch (error) {
      console.error('Error loading health score:', error)
    }
  }

  useEffect(() => {
    if (!selectedAsset) return

    const ws = new SensorWebSocket(
      selectedAsset,
      (data) => {
        setRealTimeData(data)
      },
      (error) => {
        console.error('WebSocket error:', error)
      }
    )

    ws.connect()

    return () => {
      ws.disconnect()
    }
  }, [selectedAsset])

  const currentAsset = assets.find((a) => a.id === selectedAsset)

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Live Monitoring</h1>

        {/* Asset Selector */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Select Asset</label>
          {assets.length === 0 ? (
            <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
              <p className="text-yellow-400 mb-2">
                No assets found. Please initialize demo data:
              </p>
              <div className="bg-gray-800 p-3 rounded mt-2 font-mono text-sm">
                <div className="text-gray-300"># Activate virtual environment first</div>
                <div className="text-white">cd backend</div>
                <div className="text-white">source .venv/bin/activate  # or: source venv/bin/activate</div>
                <div className="text-white">python scripts/init_demo_data.py</div>
              </div>
              <p className="text-yellow-300 text-sm mt-2">
                After running the script, refresh this page.
              </p>
            </div>
          ) : (
            <select
              value={selectedAsset || ''}
              onChange={(e) => setSelectedAsset(Number(e.target.value))}
              className="bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700 w-full"
            >
              {assets.map((asset) => (
                <option key={asset.id} value={asset.id}>
                  {asset.name} ({asset.asset_type})
                </option>
              ))}
            </select>
          )}
        </div>

        {currentAsset && (
          <>
            {/* Health Score Card */}
            {healthScore && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <MetricCard
                  icon={Activity}
                  label="Health Index"
                  value={healthScore.health_index.toFixed(1)}
                  unit="/100"
                  color={healthScore.health_index > 70 ? 'green' : healthScore.health_index > 40 ? 'yellow' : 'red'}
                />
                <MetricCard
                  icon={TrendingUp}
                  label="RUL"
                  value={healthScore.rul_days ? healthScore.rul_days.toFixed(1) : 'N/A'}
                  unit="days"
                />
                <MetricCard
                  icon={Zap}
                  label="Risk Score"
                  value={healthScore.failure_risk_score ? healthScore.failure_risk_score.toFixed(1) : 'N/A'}
                  unit="/100"
                />
                <MetricCard
                  icon={Activity}
                  label="Anomaly Score"
                  value={healthScore.anomaly_score ? healthScore.anomaly_score.toFixed(1) : 'N/A'}
                  unit="/100"
                />
              </div>
            )}

            {/* Current Sensor Values */}
            {realTimeData?.data?.reading && (
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
                <SensorCard
                  icon={Thermometer}
                  label="Temperature"
                  value={realTimeData.data.reading.temperature}
                  unit="°C"
                />
                <SensorCard
                  icon={Gauge}
                  label="Pressure"
                  value={realTimeData.data.reading.pressure}
                  unit="bar"
                />
                <SensorCard
                  icon={Waves}
                  label="Vibration"
                  value={realTimeData.data.reading.vibration}
                  unit="mm/s"
                />
                <SensorCard
                  icon={Activity}
                  label="Flow"
                  value={realTimeData.data.reading.flow}
                  unit="L/min"
                />
                <SensorCard
                  icon={Zap}
                  label="RPM"
                  value={realTimeData.data.reading.rpm}
                  unit="rpm"
                />
              </div>
            )}

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              <ChartCard title="Temperature">
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="time" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                    <Area type="monotone" dataKey="temperature" stroke="#0EA5E9" fill="#0EA5E9" fillOpacity={0.3} />
                  </AreaChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Pressure">
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="time" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                    <Area type="monotone" dataKey="pressure" stroke="#10B981" fill="#10B981" fillOpacity={0.3} />
                  </AreaChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartCard title="Vibration">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="time" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                    <Line type="monotone" dataKey="vibration" stroke="#F59E0B" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Flow">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="time" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                    <Line type="monotone" dataKey="flow" stroke="#8B5CF6" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>
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
  unit: string
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
        <span className="text-lg text-gray-400 ml-1">{unit}</span>
      </div>
    </div>
  )
}

function SensorCard({ icon: Icon, label, value, unit }: {
  icon: any
  label: string
  value: number | null | undefined
  unit: string
}) {
  return (
    <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-5 h-5 text-primary-400" />
        <span className="text-gray-400 text-sm">{label}</span>
      </div>
      <div className="text-2xl font-bold text-white">
        {value?.toFixed(2) || 'N/A'}
        <span className="text-sm text-gray-400 ml-1">{unit}</span>
      </div>
    </div>
  )
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
      <h3 className="text-xl font-semibold mb-4">{title}</h3>
      {children}
    </div>
  )
}

