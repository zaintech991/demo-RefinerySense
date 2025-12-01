'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Activity, Cpu, AlertTriangle, MessageSquare, Home, BarChart3 } from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { href: '/', label: 'Home', icon: Home },
  { href: '/monitoring', label: 'Live Monitoring', icon: Activity },
  { href: '/digital-twin', label: 'Digital Twin', icon: Cpu },
  { href: '/predictive', label: 'Predictive Maintenance', icon: BarChart3 },
  { href: '/alerts', label: 'Alerts & Logs', icon: AlertTriangle },
  { href: '/assistant', label: 'AI Assistant', icon: MessageSquare },
]

export default function Navbar() {
  const pathname = usePathname()

  return (
    <nav className="bg-gray-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <Link href="/" className="text-xl font-bold text-primary-400">
                RefinerySense
              </Link>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={clsx(
                      'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors',
                      isActive
                        ? 'border-primary-400 text-primary-400'
                        : 'border-transparent text-gray-300 hover:border-gray-300 hover:text-gray-100'
                    )}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {item.label}
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}

