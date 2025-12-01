'use client'

import { useEffect, useState } from 'react'
import { assetsApi, sensorsApi, type Asset, type SensorReading } from '@/lib/api'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { Cpu, TrendingUp, AlertCircle } from 'lucide-react'

export default function DigitalTwinPage() {
  const [assets, setAssets] = useState<Asset[]>([])
  const [selectedAsset, setSelectedAsset] = useState<number | null>(null)
  const [readings, setReadings] = useState<SensorReading[]>([])
  const [twinData, setTwinData] = useState<any[]>([])
  const [scenario, setScenario] = useState<string>('normal')

  useEffect(() => {
    loadAssets()
  }, [])

  useEffect(() => {
    if (selectedAsset) {
      loadReadings()
    }
  }, [selectedAsset])

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

  const loadReadings = async () => {
    if (!selectedAsset) return
    try {
      const response = await sensorsApi.getReadings(selectedAsset, 100)
      setReadings(response.data)
      prepareTwinData(response.data)
    } catch (error) {
      console.error('Error loading readings:', error)
    }
  }

  const prepareTwinData = (readings: SensorReading[]) => {
    // Simulate expected values based on asset type
    const asset = assets.find((a) => a.id === selectedAsset)
    if (!asset) return

    const baseValues = {
      pump: { temp: 65, pressure: 2.5, vibration: 2.5, flow: 120 },
      compressor: { temp: 85, pressure: 8.5, vibration: 3.5, flow: 250 },
      heat_exchanger: { temp: 95, pressure: 4.2, vibration: 1.8, flow: 180 },
    }

    const base = baseValues[asset.asset_type as keyof typeof baseValues] || baseValues.pump

    // Apply scenario
    let multiplier = 1.0
    if (scenario === 'load_increase') multiplier = 1.5
    if (scenario === 'load_decrease') multiplier = 0.7
    if (scenario === 'temp_spike') multiplier = 1.3

    const data = readings
      .slice()
      .reverse()
      .slice(-50)
      .map((r, i) => {
        const expectedTemp = base.temp * multiplier + Math.sin(i / 10) * 2
        const expectedPressure = base.pressure * multiplier + Math.sin(i / 8) * 0.2
        const expectedVibration = base.vibration * multiplier + Math.sin(i / 12) * 0.3
        const expectedFlow = base.flow * multiplier + Math.sin(i / 15) * 10

        const deviationTemp = r.temperature ? Math.abs(r.temperature - expectedTemp) / expectedTemp * 100 : 0
        const deviationPressure = r.pressure ? Math.abs(r.pressure - expectedPressure) / expectedPressure * 100 : 0

        return {
          time: new Date(r.timestamp).toLocaleTimeString(),
          actualTemp: r.temperature,
          expectedTemp: expectedTemp.toFixed(2),
          actualPressure: r.pressure,
          expectedPressure: expectedPressure.toFixed(2),
          actualVibration: r.vibration,
          expectedVibration: expectedVibration.toFixed(2),
          actualFlow: r.flow,
          expectedFlow: expectedFlow.toFixed(2),
          deviationScore: ((deviationTemp + deviationPressure) / 2).toFixed(1),
        }
      })

    setTwinData(data)
  }

  useEffect(() => {
    if (readings.length > 0) {
      prepareTwinData(readings)
    }
  }, [scenario, selectedAsset, readings])

  const currentAsset = assets.find((a) => a.id === selectedAsset)
  const avgDeviation = twinData.length > 0
    ? (twinData.reduce((sum, d) => sum + parseFloat(d.deviationScore), 0) / twinData.length).toFixed(1)
    : '0'

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 flex items-center gap-3">
          <Cpu className="w-10 h-10 text-primary-400" />
          Digital Twin Simulation
        </h1>

        {/* Asset Selector and Scenario */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <div>
            <label className="block text-sm font-medium mb-2">Select Asset</label>
            <select
              value={selectedAsset || ''}
              onChange={(e) => setSelectedAsset(Number(e.target.value))}
              className="w-full bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700"
            >
              {assets.map((asset) => (
                <option key={asset.id} value={asset.id}>
                  {asset.name} ({asset.asset_type})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Scenario</label>
            <select
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              className="w-full bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700"
            >
              <option value="normal">Normal Operation</option>
              <option value="load_increase">Load Increase (+50%)</option>
              <option value="load_decrease">Load Decrease (-30%)</option>
              <option value="temp_spike">Temperature Spike</option>
            </select>
          </div>
        </div>

        {currentAsset && (
          <>
            {/* Deviation Score Card */}
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-semibold mb-2">Average Deviation Score</h3>
                  <p className="text-gray-400">How much actual values deviate from expected behavior</p>
                </div>
                <div className="text-right">
                  <div className={`text-5xl font-bold ${
                    parseFloat(avgDeviation) < 10 ? 'text-green-400' :
                    parseFloat(avgDeviation) < 25 ? 'text-yellow-400' : 'text-red-400'
                  }`}>
                    {avgDeviation}%
                  </div>
                  <div className="text-gray-400 text-sm mt-2">
                    {parseFloat(avgDeviation) < 10 ? 'Excellent' :
                     parseFloat(avgDeviation) < 25 ? 'Good' : 'Needs Attention'}
                  </div>
                </div>
              </div>
            </div>

            {/* Comparison Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              <ChartCard title="Temperature: Actual vs Expected">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={twinData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="time" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="actualTemp"
                      stroke="#EF4444"
                      strokeWidth={2}
                      name="Actual"
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="expectedTemp"
                      stroke="#10B981"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      name="Expected"
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Pressure: Actual vs Expected">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={twinData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="time" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="actualPressure"
                      stroke="#EF4444"
                      strokeWidth={2}
                      name="Actual"
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="expectedPressure"
                      stroke="#10B981"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      name="Expected"
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartCard title="Vibration: Actual vs Expected">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={twinData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="time" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="actualVibration"
                      stroke="#EF4444"
                      strokeWidth={2}
                      name="Actual"
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="expectedVibration"
                      stroke="#10B981"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      name="Expected"
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Flow: Actual vs Expected">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={twinData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="time" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="actualFlow"
                      stroke="#EF4444"
                      strokeWidth={2}
                      name="Actual"
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="expectedFlow"
                      stroke="#10B981"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      name="Expected"
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>

            {/* Info Box */}
            <div className="mt-8 bg-blue-900/20 border border-blue-700 rounded-lg p-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-6 h-6 text-blue-400 mt-1" />
                <div>
                  <h3 className="text-lg font-semibold mb-2">About Digital Twin</h3>
                  <p className="text-gray-300">
                    The Digital Twin compares actual sensor readings against expected behavior models.
                    Large deviations indicate potential issues. Use scenarios to simulate different operating conditions
                    and see how the asset should behave under various loads.
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
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

