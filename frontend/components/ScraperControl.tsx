'use client'

import { useState, useEffect } from 'react'
import { 
  PlayIcon, 
  StopIcon, 
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon 
} from '@heroicons/react/24/outline'

interface ScraperStatus {
  total_cars: number
  active_cars: number
  recent_cars_24h: number
  last_scrape: string
  status: string
}

export default function ScraperControl() {
  const [status, setStatus] = useState<ScraperStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [scraperRunning, setScraperRunning] = useState(false)

  useEffect(() => {
    fetchStatus()
    // Fetch status every 30 seconds
    const interval = setInterval(fetchStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/scrape/status`)
      if (response.ok) {
        const data = await response.json()
        setStatus(data)
      }
    } catch (error) {
      console.error('Error fetching scraper status:', error)
    }
  }

  const runScraper = async () => {
    setScraperRunning(true)
    setLoading(true)
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/scrape/run`, {
        method: 'POST'
      })
      
      if (response.ok) {
        // Poll for status updates
        const pollInterval = setInterval(async () => {
          await fetchStatus()
        }, 5000)
        
        // Stop polling after 2 minutes
        setTimeout(() => {
          clearInterval(pollInterval)
          setScraperRunning(false)
        }, 120000)
      }
    } catch (error) {
      console.error('Error running scraper:', error)
      setScraperRunning(false)
    } finally {
      setLoading(false)
    }
  }

  const testScrapfly = async () => {
    setLoading(true)
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/scrape/scrapfly`)
      if (response.ok) {
        setTimeout(fetchStatus, 10000) // Fetch status after 10 seconds
      }
    } catch (error) {
      console.error('Error testing Scrapfly:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = () => {
    if (!status) return 'text-gray-500'
    if (status.status === 'healthy') return 'text-green-500'
    if (status.status === 'needs_data') return 'text-red-500'
    return 'text-yellow-500'
  }

  const getStatusIcon = () => {
    if (!status) return <ChartBarIcon className="w-5 h-5" />
    if (status.status === 'healthy') return <CheckCircleIcon className="w-5 h-5 text-green-500" />
    if (status.status === 'needs_data') return <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
    return <ChartBarIcon className="w-5 h-5" />
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Collecteur de Données LeBonCoin
          </h2>
        </div>
        
        {scraperRunning && (
          <div className="flex items-center space-x-2 text-blue-600">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <span className="text-sm font-medium">Collecte en cours...</span>
          </div>
        )}
      </div>

      {status && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {status.total_cars.toLocaleString('fr-FR')}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Total voitures
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {status.active_cars.toLocaleString('fr-FR')}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Actives
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {status.recent_cars_24h.toLocaleString('fr-FR')}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Nouvelles (24h)
            </div>
          </div>
          
          <div className="text-center">
            <div className={`text-lg font-semibold ${getStatusColor()}`}>
              {status.status === 'healthy' ? '✅ Opérationnel' : 
               status.status === 'needs_data' ? '⚠️ Données requises' : '🔄 En cours'}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Statut
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-3">
        <button
          onClick={runScraper}
          disabled={loading || scraperRunning}
          className="flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading || scraperRunning ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>Lancement...</span>
            </>
          ) : (
            <>
              <PlayIcon className="w-4 h-4" />
              <span>🚀 Lancer Collecte Complète</span>
            </>
          )}
        </button>

        <button
          onClick={testScrapfly}
          disabled={loading}
          className="flex items-center justify-center space-x-2 bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-6 rounded-md transition-colors disabled:opacity-50"
        >
          <ChartBarIcon className="w-4 h-4" />
          <span>🧪 Test Scrapfly</span>
        </button>

        <button
          onClick={fetchStatus}
          className="flex items-center justify-center space-x-2 bg-gray-600 hover:bg-gray-700 text-white font-medium py-3 px-6 rounded-md transition-colors"
        >
          <span>🔄 Actualiser</span>
        </button>
      </div>

      {status && status.status === 'needs_data' && (
        <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md">
          <div className="flex items-start space-x-3">
            <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                Aucune donnée disponible
              </h3>
              <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                Lancez la collecte pour récupérer les données LeBonCoin. Le processus prend quelques minutes.
              </p>
            </div>
          </div>
        </div>
      )}

      {status && status.total_cars > 0 && (
        <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
          <div className="flex items-start space-x-3">
            <CheckCircleIcon className="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-green-800 dark:text-green-200">
                Données disponibles
              </h3>
              <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                {status.total_cars} voitures collectées. Le collecteur automatique fonctionne toutes les 30 minutes.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}