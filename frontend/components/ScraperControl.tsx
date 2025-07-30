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
    if (!status) return <ChartBarIcon className="w-6 h-6 text-white" />
    if (status.status === 'healthy') return <CheckCircleIcon className="w-6 h-6 text-white" />
    if (status.status === 'needs_data') return <ExclamationTriangleIcon className="w-6 h-6 text-white" />
    return <ChartBarIcon className="w-6 h-6 text-white" />
  }

  return (
    <div className="glass-card rounded-2xl p-8 mb-8 fade-in">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-gradient-primary rounded-2xl flex items-center justify-center float">
            {getStatusIcon()}
          </div>
          <div>
            <h2 className="text-2xl font-black text-gradient mb-1">
              Collecteur LeBonCoin
            </h2>
            <p className="text-gray-600 font-medium">Système de collecte automatique • Temps réel</p>
          </div>
        </div>
        
        {scraperRunning && (
          <div className="glass-card px-4 py-2 rounded-xl flex items-center space-x-2">
            <div className="loading-spinner"></div>
            <span className="text-sm font-bold text-gradient">Collecte en cours...</span>
          </div>
        )}
      </div>

      {status && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="glass-card p-6 rounded-2xl text-center scale-in">
            <div className="w-12 h-12 bg-gradient-primary rounded-2xl flex items-center justify-center mx-auto mb-3">
              <span className="text-white text-xl font-bold">🚗</span>
            </div>
            <div className="text-3xl font-black text-gradient mb-1">
              {status.total_cars.toLocaleString('fr-FR')}
            </div>
            <div className="text-sm text-gray-600 font-medium">
              Total voitures
            </div>
          </div>
          
          <div className="glass-card p-6 rounded-2xl text-center scale-in" style={{animationDelay: '0.1s'}}>
            <div className="w-12 h-12 bg-gradient-success rounded-2xl flex items-center justify-center mx-auto mb-3">
              <span className="text-white text-xl font-bold">✓</span>
            </div>
            <div className="text-3xl font-black text-gradient mb-1">
              {status.active_cars.toLocaleString('fr-FR')}
            </div>
            <div className="text-sm text-gray-600 font-medium">
              Actives
            </div>
          </div>
          
          <div className="glass-card p-6 rounded-2xl text-center scale-in" style={{animationDelay: '0.2s'}}>
            <div className="w-12 h-12 bg-gradient-secondary rounded-2xl flex items-center justify-center mx-auto mb-3">
              <span className="text-white text-xl font-bold">⭐</span>
            </div>
            <div className="text-3xl font-black text-gradient mb-1">
              {status.recent_cars_24h.toLocaleString('fr-FR')}
            </div>
            <div className="text-sm text-gray-600 font-medium">
              Nouvelles (24h)
            </div>
          </div>
          
          <div className="glass-card p-6 rounded-2xl text-center scale-in" style={{animationDelay: '0.3s'}}>
            <div className={`w-12 h-12 ${status.status === 'healthy' ? 'bg-gradient-success' : status.status === 'needs_data' ? 'bg-gradient-warning' : 'bg-gradient-primary'} rounded-2xl flex items-center justify-center mx-auto mb-3`}>
              <span className="text-white text-xl font-bold">
                {status.status === 'healthy' ? '✅' : status.status === 'needs_data' ? '⚠️' : '🔄'}
              </span>
            </div>
            <div className="text-lg font-bold text-gradient mb-1">
              {status.status === 'healthy' ? 'Opérationnel' : 
               status.status === 'needs_data' ? 'Données requises' : 'En cours'}
            </div>
            <div className="text-sm text-gray-600 font-medium">
              Statut
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-4">
        <button
          onClick={runScraper}
          disabled={loading || scraperRunning}
          className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
        >
          {loading || scraperRunning ? (
            <>
              <div className="loading-spinner"></div>
              <span>Lancement...</span>
            </>
          ) : (
            <>
              <PlayIcon className="w-5 h-5" />
              <span>🚀 Lancer Collecte Complète</span>
            </>
          )}
        </button>

        <button
          onClick={testScrapfly}
          disabled={loading}
          className="btn-secondary flex-1 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
        >
          <ChartBarIcon className="w-5 h-5" />
          <span>🧪 Test Scrapfly</span>
        </button>

        <button
          onClick={fetchStatus}
          className="btn-secondary flex items-center justify-center space-x-2 px-8"
        >
          <span>🔄 Actualiser</span>
        </button>
      </div>

      {status && status.status === 'needs_data' && (
        <div className="mt-6 glass-card p-6 rounded-2xl border-l-4 border-yellow-500 slide-up">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-gradient-warning rounded-2xl flex items-center justify-center flex-shrink-0">
              <ExclamationTriangleIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">
                Aucune donnée disponible
              </h3>
              <p className="text-gray-700 leading-relaxed">
                Lancez la collecte pour récupérer les données LeBonCoin. Le processus prend quelques minutes et utilise notre technologie Scrapfly avancée.
              </p>
            </div>
          </div>
        </div>
      )}

      {status && status.total_cars > 0 && (
        <div className="mt-6 glass-card p-6 rounded-2xl border-l-4 border-green-500 slide-up">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-gradient-success rounded-2xl flex items-center justify-center flex-shrink-0 pulse-glow">
              <CheckCircleIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">
                Système opérationnel
              </h3>
              <p className="text-gray-700 leading-relaxed">
                <span className="font-bold text-gradient">{status.total_cars.toLocaleString('fr-FR')}</span> voitures collectées avec succès. 
                Le collecteur automatique fonctionne toutes les 30 minutes pour maintenir les données à jour.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}