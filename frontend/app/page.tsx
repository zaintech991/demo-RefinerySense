'use client'

import Link from 'next/link'
import { ArrowRight, Activity, Cpu, BarChart3, AlertTriangle, MessageSquare, Zap } from 'lucide-react'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-32">
          <div className="text-center">
            <h1 className="text-5xl md:text-7xl font-bold text-white mb-6">
              RefinerySense
            </h1>
            <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto">
              Advanced Digital Twin & Predictive Maintenance System
              <br />
              for Refinery Equipment
            </p>
            <div className="flex justify-center gap-4">
              <Link
                href="/monitoring"
                className="bg-primary-600 hover:bg-primary-700 text-white font-semibold py-3 px-8 rounded-lg transition-colors flex items-center gap-2"
              >
                Get Started
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                href="/digital-twin"
                className="bg-gray-800 hover:bg-gray-700 text-white font-semibold py-3 px-8 rounded-lg transition-colors"
              >
                Learn More
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-white mb-4">Key Features</h2>
          <p className="text-gray-400 text-lg">Comprehensive monitoring and predictive analytics</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          <FeatureCard
            icon={Activity}
            title="Live Monitoring"
            description="Real-time sensor data streaming with WebSocket support for instant updates"
            href="/monitoring"
          />
          <FeatureCard
            icon={Cpu}
            title="Digital Twin"
            description="Asset-level digital twins with expected behavior modeling and deviation analysis"
            href="/digital-twin"
          />
          <FeatureCard
            icon={BarChart3}
            title="Predictive Maintenance"
            description="ML-powered forecasting, anomaly detection, and RUL estimation"
            href="/predictive"
          />
          <FeatureCard
            icon={AlertTriangle}
            title="Smart Alerts"
            description="Threshold-based and ML-driven alerting system with severity levels"
            href="/alerts"
          />
          <FeatureCard
            icon={MessageSquare}
            title="AI Assistant"
            description="Intelligent chat assistant powered by Groq LLM for equipment insights"
            href="/assistant"
          />
          <FeatureCard
            icon={Zap}
            title="Real-Time Analytics"
            description="Advanced time-series analysis with interactive charts and visualizations"
            href="/monitoring"
          />
        </div>
      </div>

      {/* Stats Section */}
      <div className="bg-gray-800/50 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <StatItem value="99.9%" label="Uptime" />
            <StatItem value="< 3s" label="Latency" />
            <StatItem value="24/7" label="Monitoring" />
            <StatItem value="ML-Powered" label="Predictions" />
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <h2 className="text-4xl font-bold text-white mb-4">Ready to Get Started?</h2>
        <p className="text-gray-400 text-lg mb-8">
          Start monitoring your refinery equipment with advanced predictive maintenance
        </p>
        <Link
          href="/monitoring"
          className="bg-primary-600 hover:bg-primary-700 text-white font-semibold py-3 px-8 rounded-lg transition-colors inline-flex items-center gap-2"
        >
          View Dashboard
          <ArrowRight className="w-5 h-5" />
        </Link>
      </div>
    </div>
  )
}

function FeatureCard({ icon: Icon, title, description, href }: {
  icon: any
  title: string
  description: string
  href: string
}) {
  return (
    <Link
      href={href}
      className="bg-gray-800/50 hover:bg-gray-800 p-6 rounded-lg transition-all hover:scale-105 border border-gray-700"
    >
      <Icon className="w-12 h-12 text-primary-400 mb-4" />
      <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
      <p className="text-gray-400">{description}</p>
    </Link>
  )
}

function StatItem({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <div className="text-4xl font-bold text-primary-400 mb-2">{value}</div>
      <div className="text-gray-400">{label}</div>
    </div>
  )
}

