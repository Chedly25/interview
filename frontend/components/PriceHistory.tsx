'use client'

import { useState, useEffect } from 'react'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Calendar, 
  Bell, 
  BellOff,
  BarChart3,
  Activity,
  AlertTriangle,
  CheckCircle,
  Minus
} from 'lucide-react'

interface PricePoint {
  date: string
  price: number
  change?: number
  changePercent?: number
}

interface PriceAlert {
  id: string
  carId: string
  targetPrice: number
  condition: 'below' | 'above'
  isActive: boolean
  createdAt: string
}

interface PriceHistoryProps {
  carId: string
  currentPrice: number
  title: string
}

export default function PriceHistory({ carId, currentPrice, title }: PriceHistoryProps) {
  const [priceHistory, setPriceHistory] = useState<PricePoint[]>([])
  const [alerts, setAlerts] = useState<PriceAlert[]>([])
  const [newAlertPrice, setNewAlertPrice] = useState<string>('')
  const [newAlertCondition, setNewAlertCondition] = useState<'below' | 'above'>('below')
  const [loading, setLoading] = useState(true)
  const [showAlertForm, setShowAlertForm] = useState(false)

  useEffect(() => {
    fetchPriceHistory()
    loadAlerts()
  }, [carId])

  const fetchPriceHistory = async () => {
    setLoading(true)
    try {
      // For now, we'll simulate price history data since the API doesn't have this yet
      // In a real implementation, this would call the API
      const simulatedHistory = generateSimulatedPriceHistory(currentPrice)
      setPriceHistory(simulatedHistory)
    } catch (error) {
      console.error('Error fetching price history:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateSimulatedPriceHistory = (currentPrice: number): PricePoint[] => {
    const history: PricePoint[] = []
    const basePrice = currentPrice
    const days = 30
    
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date()
      date.setDate(date.getDate() - i)
      
      // Simulate price fluctuations
      const volatility = Math.random() * 0.1 - 0.05 // ±5% volatility
      const trendFactor = (days - i) / days * 0.02 // Slight downward trend over time
      const price = Math.round(basePrice * (1 + volatility - trendFactor))
      
      const prevPrice = history.length > 0 ? history[history.length - 1].price : price
      const change = price - prevPrice
      const changePercent = prevPrice > 0 ? (change / prevPrice) * 100 : 0
      
      history.push({
        date: date.toISOString(),
        price,
        change: history.length > 0 ? change : 0,
        changePercent: history.length > 0 ? changePercent : 0
      })
    }
    
    return history
  }

  const loadAlerts = () => {
    const storedAlerts = JSON.parse(localStorage.getItem('price-alerts') || '[]')
    const carAlerts = storedAlerts.filter((alert: PriceAlert) => alert.carId === carId)
    setAlerts(carAlerts)
  }

  const saveAlerts = (updatedAlerts: PriceAlert[]) => {
    const allAlerts = JSON.parse(localStorage.getItem('price-alerts') || '[]')
    const otherCarAlerts = allAlerts.filter((alert: PriceAlert) => alert.carId !== carId)
    const newAllAlerts = [...otherCarAlerts, ...updatedAlerts]
    localStorage.setItem('price-alerts', JSON.stringify(newAllAlerts))
  }

  const createAlert = () => {
    const price = parseFloat(newAlertPrice)
    if (isNaN(price) || price <= 0) return

    const newAlert: PriceAlert = {
      id: Date.now().toString(),
      carId,
      targetPrice: price,
      condition: newAlertCondition,
      isActive: true,
      createdAt: new Date().toISOString()
    }

    const updatedAlerts = [...alerts, newAlert]
    setAlerts(updatedAlerts)
    saveAlerts(updatedAlerts)
    setNewAlertPrice('')
    setShowAlertForm(false)
  }

  const toggleAlert = (alertId: string) => {
    const updatedAlerts = alerts.map(alert =>
      alert.id === alertId ? { ...alert, isActive: !alert.isActive } : alert
    )
    setAlerts(updatedAlerts)
    saveAlerts(updatedAlerts)
  }

  const deleteAlert = (alertId: string) => {
    const updatedAlerts = alerts.filter(alert => alert.id !== alertId)
    setAlerts(updatedAlerts)
    saveAlerts(updatedAlerts)
  }

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(price)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short'
    })
  }

  const getCurrentTrend = () => {
    if (priceHistory.length < 2) return null
    
    const recent = priceHistory.slice(-7) // Last 7 days
    const firstPrice = recent[0].price
    const lastPrice = recent[recent.length - 1].price
    const change = lastPrice - firstPrice
    const changePercent = (change / firstPrice) * 100
    
    return {
      change,
      changePercent,
      trend: change > 0 ? 'up' : change < 0 ? 'down' : 'stable'
    }
  }

  const getMinMaxPrices = () => {
    if (priceHistory.length === 0) return { min: 0, max: 0 }
    
    const prices = priceHistory.map(p => p.price)
    return {
      min: Math.min(...prices),
      max: Math.max(...prices)
    }
  }

  const trend = getCurrentTrend()
  const { min: minPrice, max: maxPrice } = getMinMaxPrices()

  if (loading) {
    return (
      <div className="glass-card rounded-2xl p-8">
        <div className="flex items-center justify-center h-32">
          <div className="loading-spinner"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="glass-card rounded-2xl p-8 fade-in">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-gradient-success rounded-2xl flex items-center justify-center">
            <BarChart3 className="w-6 h-6 text-white" strokeWidth={2} />
          </div>
          <div>
            <h2 className="text-2xl font-black text-gradient mb-1">
              Historique des Prix
            </h2>
            <p className="text-gray-600 font-medium">Évolution sur les 30 derniers jours</p>
          </div>
        </div>
        
        <button
          onClick={() => setShowAlertForm(!showAlertForm)}
          className="btn-secondary flex items-center space-x-2"
        >
          <Bell className="w-4 h-4" strokeWidth={2} />
          <span>Alerte Prix</span>
        </button>
      </div>

      {/* Price Trend Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="glass-card p-4 rounded-xl text-center">
          <DollarSign className="w-5 h-5 text-blue-500 mx-auto mb-2" strokeWidth={2} />
          <div className="text-lg font-bold text-gray-900 mb-1">
            {formatPrice(currentPrice)}
          </div>
          <div className="text-xs text-gray-600">Prix actuel</div>
        </div>
        
        <div className="glass-card p-4 rounded-xl text-center">
          <TrendingDown className="w-5 h-5 text-green-500 mx-auto mb-2" strokeWidth={2} />
          <div className="text-lg font-bold text-gray-900 mb-1">
            {formatPrice(minPrice)}
          </div>
          <div className="text-xs text-gray-600">Prix minimum</div>
        </div>
        
        <div className="glass-card p-4 rounded-xl text-center">
          <TrendingUp className="w-5 h-5 text-red-500 mx-auto mb-2" strokeWidth={2} />
          <div className="text-lg font-bold text-gray-900 mb-1">
            {formatPrice(maxPrice)}
          </div>
          <div className="text-xs text-gray-600">Prix maximum</div>
        </div>
        
        <div className="glass-card p-4 rounded-xl text-center">
          {trend && (
            <>
              {trend.trend === 'up' && <TrendingUp className="w-5 h-5 text-red-500 mx-auto mb-2" strokeWidth={2} />}
              {trend.trend === 'down' && <TrendingDown className="w-5 h-5 text-green-500 mx-auto mb-2" strokeWidth={2} />}
              {trend.trend === 'stable' && <Minus className="w-5 h-5 text-gray-500 mx-auto mb-2" strokeWidth={2} />}
              <div className={`text-lg font-bold mb-1 ${
                trend.trend === 'up' ? 'text-red-600' : 
                trend.trend === 'down' ? 'text-green-600' : 'text-gray-600'
              }`}>
                {trend.changePercent > 0 ? '+' : ''}{trend.changePercent.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-600">Tendance 7j</div>
            </>
          )}
        </div>
      </div>

      {/* Simple Price Chart */}
      <div className="glass-card p-6 rounded-xl mb-8">
        <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
          <Activity className="w-5 h-5 text-blue-500 mr-2" strokeWidth={2} />
          Évolution des prix
        </h3>
        
        <div className="relative h-48 flex items-end space-x-1">
          {priceHistory.map((point, index) => {
            const height = ((point.price - minPrice) / (maxPrice - minPrice)) * 100
            const isRecent = index >= priceHistory.length - 7
            
            return (
              <div
                key={index}
                className="flex-1 flex flex-col items-center group"
              >
                <div
                  className={`w-full rounded-t transition-all group-hover:opacity-75 ${
                    isRecent ? 'bg-gradient-primary' : 'bg-gradient-secondary'
                  }`}
                  style={{ height: `${Math.max(height, 5)}%` }}
                  title={`${formatDate(point.date)}: ${formatPrice(point.price)}`}
                ></div>
                {index % 5 === 0 && (
                  <div className="text-xs text-gray-500 mt-2 transform -rotate-45 origin-left">
                    {formatDate(point.date)}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Price Alerts */}
      <div>
        <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
          <Bell className="w-5 h-5 text-orange-500 mr-2" strokeWidth={2} />
          Alertes Prix ({alerts.length})
        </h3>

        {/* Alert Form */}
        {showAlertForm && (
          <div className="glass-card p-6 rounded-xl mb-4 border-l-4 border-blue-500">
            <h4 className="font-bold text-gray-900 mb-4">Créer une nouvelle alerte</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prix cible
                </label>
                <input
                  type="number"
                  value={newAlertPrice}
                  onChange={(e) => setNewAlertPrice(e.target.value)}
                  placeholder="Prix en €"
                  className="input-modern w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Condition
                </label>
                <select
                  value={newAlertCondition}
                  onChange={(e) => setNewAlertCondition(e.target.value as 'below' | 'above')}
                  className="input-modern w-full"
                >
                  <option value="below">Passe en dessous de</option>
                  <option value="above">Passe au dessus de</option>
                </select>
              </div>
              <div className="flex items-end space-x-2">
                <button
                  onClick={createAlert}
                  className="btn-primary flex-1"
                  disabled={!newAlertPrice || parseFloat(newAlertPrice) <= 0}
                >
                  Créer l'alerte
                </button>
                <button
                  onClick={() => setShowAlertForm(false)}
                  className="btn-secondary px-3"
                >
                  ✕
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Active Alerts */}
        {alerts.length > 0 ? (
          <div className="space-y-3">
            {alerts.map((alert) => {
              const isTriggered = alert.condition === 'below' 
                ? currentPrice <= alert.targetPrice 
                : currentPrice >= alert.targetPrice

              return (
                <div
                  key={alert.id}
                  className={`glass-card p-4 rounded-xl flex items-center justify-between border-l-4 ${
                    isTriggered 
                      ? 'border-red-500 bg-red-50/50' 
                      : alert.isActive 
                        ? 'border-green-500' 
                        : 'border-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-4">
                    {isTriggered ? (
                      <AlertTriangle className="w-5 h-5 text-red-500" strokeWidth={2} />
                    ) : alert.isActive ? (
                      <CheckCircle className="w-5 h-5 text-green-500" strokeWidth={2} />
                    ) : (
                      <BellOff className="w-5 h-5 text-gray-400" strokeWidth={2} />
                    )}
                    
                    <div>
                      <div className="font-medium text-gray-900">
                        {alert.condition === 'below' ? 'Prix inférieur à' : 'Prix supérieur à'} {formatPrice(alert.targetPrice)}
                      </div>
                      <div className="text-sm text-gray-600">
                        Créée le {formatDate(alert.createdAt)} • 
                        {alert.isActive ? (
                          <span className="text-green-600 ml-1">Active</span>
                        ) : (
                          <span className="text-gray-500 ml-1">Désactivée</span>
                        )}
                        {isTriggered && <span className="text-red-600 ml-1">• DÉCLENCHÉE</span>}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => toggleAlert(alert.id)}
                      className={`p-2 rounded-lg transition-all ${
                        alert.isActive ? 'bg-yellow-100 text-yellow-600' : 'bg-green-100 text-green-600'
                      }`}
                      title={alert.isActive ? 'Désactiver' : 'Activer'}
                    >
                      {alert.isActive ? <BellOff className="w-4 h-4" strokeWidth={2} /> : <Bell className="w-4 h-4" strokeWidth={2} />}
                    </button>
                    <button
                      onClick={() => deleteAlert(alert.id)}
                      className="p-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition-all"
                      title="Supprimer"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-gradient-warning/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <Bell className="w-6 h-6 text-gray-400" strokeWidth={2} />
            </div>
            <p className="text-gray-600 mb-4">Aucune alerte configurée</p>
            <p className="text-sm text-gray-500">
              Créez une alerte pour être notifié des changements de prix
            </p>
          </div>
        )}
      </div>
    </div>
  )
}