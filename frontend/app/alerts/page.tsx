'use client'

import { useEffect, useState } from 'react'
import { assetsApi, alertsApi, type Asset, type Alert } from '@/lib/api'
import { AlertTriangle, CheckCircle, XCircle, Info, Clock } from 'lucide-react'
import { format } from 'date-fns'

export default function AlertsPage() {
  const [assets, setAssets] = useState<Asset[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [filterAsset, setFilterAsset] = useState<number | null>(null)
  const [filterResolved, setFilterResolved] = useState<boolean | null>(null)
  const [filterSeverity, setFilterSeverity] = useState<string>('')

  useEffect(() => {
    loadAssets()
    loadAlerts()
  }, [filterAsset, filterResolved, filterSeverity])

  const loadAssets = async () => {
    try {
      const response = await assetsApi.getAll()
      setAssets(response.data)
    } catch (error) {
      console.error('Error loading assets:', error)
    }
  }

  const loadAlerts = async () => {
    try {
      const response = await alertsApi.getAll(
        filterAsset || undefined,
        filterResolved !== null ? filterResolved : undefined,
        filterSeverity || undefined
      )
      setAlerts(response.data)
    } catch (error) {
      console.error('Error loading alerts:', error)
    }
  }

  const handleResolve = async (alertId: number) => {
    try {
      await alertsApi.resolve(alertId)
      loadAlerts()
    } catch (error) {
      console.error('Error resolving alert:', error)
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <XCircle className="w-5 h-5 text-red-400" />
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-400" />
      default:
        return <Info className="w-5 h-5 text-blue-400" />
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'border-red-700 bg-red-900/20'
      case 'warning':
        return 'border-yellow-700 bg-yellow-900/20'
      default:
        return 'border-blue-700 bg-blue-900/20'
    }
  }

  const criticalCount = alerts.filter((a) => a.severity === 'critical' && !a.resolved).length
  const warningCount = alerts.filter((a) => a.severity === 'warning' && !a.resolved).length
  const activeCount = alerts.filter((a) => !a.resolved).length

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 flex items-center gap-3">
          <AlertTriangle className="w-10 h-10 text-primary-400" />
          Alerts & Logs
        </h1>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <StatCard label="Active Alerts" value={activeCount.toString()} color="red" />
          <StatCard label="Critical" value={criticalCount.toString()} color="red" />
          <StatCard label="Warnings" value={warningCount.toString()} color="yellow" />
          <StatCard label="Total Alerts" value={alerts.length.toString()} color="blue" />
        </div>

        {/* Filters */}
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 mb-8">
          <h3 className="text-lg font-semibold mb-4">Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Asset</label>
              <select
                value={filterAsset || ''}
                onChange={(e) => setFilterAsset(e.target.value ? Number(e.target.value) : null)}
                className="w-full bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600"
              >
                <option value="">All Assets</option>
                {assets.map((asset) => (
                  <option key={asset.id} value={asset.id}>
                    {asset.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Status</label>
              <select
                value={filterResolved === null ? '' : filterResolved ? 'resolved' : 'active'}
                onChange={(e) =>
                  setFilterResolved(
                    e.target.value === '' ? null : e.target.value === 'resolved'
                  )
                }
                className="w-full bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600"
              >
                <option value="">All</option>
                <option value="active">Active</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Severity</label>
              <select
                value={filterSeverity}
                onChange={(e) => setFilterSeverity(e.target.value)}
                className="w-full bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600"
              >
                <option value="">All</option>
                <option value="critical">Critical</option>
                <option value="warning">Warning</option>
                <option value="info">Info</option>
              </select>
            </div>
          </div>
        </div>

        {/* Alerts List */}
        <div className="space-y-4">
          {alerts.length === 0 ? (
            <div className="bg-gray-800 p-8 rounded-lg border border-gray-700 text-center">
              <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
              <p className="text-gray-400 text-lg">No alerts found</p>
            </div>
          ) : (
            alerts.map((alert) => {
              const asset = assets.find((a) => a.id === alert.asset_id)
              return (
                <div
                  key={alert.id}
                  className={`bg-gray-800 p-6 rounded-lg border ${getSeverityColor(alert.severity)}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 flex-1">
                      {getSeverityIcon(alert.severity)}
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="font-semibold text-lg">{alert.message}</span>
                          <span className="px-2 py-1 bg-gray-700 rounded text-xs uppercase">
                            {alert.severity}
                          </span>
                          <span className="px-2 py-1 bg-gray-700 rounded text-xs">
                            {alert.alert_type}
                          </span>
                        </div>
                        <div className="text-sm text-gray-400 space-y-1">
                          <div className="flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            {format(new Date(alert.timestamp), 'PPpp')}
                          </div>
                          {asset && (
                            <div>
                              Asset: <span className="text-white">{asset.name}</span>
                            </div>
                          )}
                          {alert.resolved && alert.resolved_at && (
                            <div className="text-green-400">
                              Resolved: {format(new Date(alert.resolved_at), 'PPpp')}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    {!alert.resolved && (
                      <button
                        onClick={() => handleResolve(alert.id)}
                        className="px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors flex items-center gap-2"
                      >
                        <CheckCircle className="w-4 h-4" />
                        Resolve
                      </button>
                    )}
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  const colorClasses = {
    red: 'text-red-400 border-red-700',
    yellow: 'text-yellow-400 border-yellow-700',
    blue: 'text-blue-400 border-blue-700',
    green: 'text-green-400 border-green-700',
  }

  return (
    <div className={`bg-gray-800 p-6 rounded-lg border ${colorClasses[color as keyof typeof colorClasses]}`}>
      <div className="text-gray-400 text-sm mb-2">{label}</div>
      <div className={`text-3xl font-bold ${colorClasses[color as keyof typeof colorClasses].split(' ')[0]}`}>
        {value}
      </div>
    </div>
  )
}

