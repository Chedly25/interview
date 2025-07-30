'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { 
  Bell, 
  BellOff, 
  ArrowLeft, 
  AlertTriangle, 
  CheckCircle, 
  Trash2,
  Settings,
  TrendingUp,
  TrendingDown,
  Car,
  Calendar,
  DollarSign
} from 'lucide-react'

interface PriceAlert {
  id: string
  carId: string
  carTitle?: string
  currentPrice?: number
  targetPrice: number
  condition: 'below' | 'above'
  isActive: boolean
  createdAt: string
  triggeredAt?: string
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<PriceAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [carDetails, setCarDetails] = useState<{[key: string]: any}>({})

  useEffect(() => {
    loadAlerts()
  }, [])

  const loadAlerts = async () => {
    setLoading(true)
    try {
      const storedAlerts = JSON.parse(localStorage.getItem('price-alerts') || '[]')
      setAlerts(storedAlerts)
      
      // Fetch car details for each alert
      const carIds = [...new Set(storedAlerts.map((alert: PriceAlert) => alert.carId))]
      const carDetailsMap: {[key: string]: any} = {}
      
      await Promise.all(
        carIds.map(async (carId) => {
          try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://interview-production-84f1.up.railway.app'
            const response = await fetch(`${apiUrl}/api/cars/${carId}`)
            if (response.ok) {
              const carData = await response.json()
              carDetailsMap[carId] = carData
            }
          } catch (error) {
            console.error(`Error fetching car ${carId}:`, error)
          }
        })
      )
      
      setCarDetails(carDetailsMap)
    } catch (error) {
      console.error('Error loading alerts:', error)
    } finally {
      setLoading(false)
    }
  }

  const saveAlerts = (updatedAlerts: PriceAlert[]) => {
    localStorage.setItem('price-alerts', JSON.stringify(updatedAlerts))
    setAlerts(updatedAlerts)
  }

  const toggleAlert = (alertId: string) => {
    const updatedAlerts = alerts.map(alert =>
      alert.id === alertId ? { ...alert, isActive: !alert.isActive } : alert
    )
    saveAlerts(updatedAlerts)
  }

  const deleteAlert = (alertId: string) => {
    const updatedAlerts = alerts.filter(alert => alert.id !== alertId)
    saveAlerts(updatedAlerts)
  }

  const clearAllAlerts = () => {
    saveAlerts([])
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
      month: 'long',
      year: 'numeric'
    })
  }

  const getAlertStatus = (alert: PriceAlert) => {
    const car = carDetails[alert.carId]
    if (!car) return { status: 'unknown', triggered: false }
    
    const currentPrice = car.price || 0
    const triggered = alert.condition === 'below' 
      ? currentPrice <= alert.targetPrice 
      : currentPrice >= alert.targetPrice
    
    return { 
      status: triggered ? 'triggered' : 'active', 
      triggered,
      currentPrice 
    }
  }

  const activeAlerts = alerts.filter(alert => alert.isActive)
  const triggeredAlerts = alerts.filter(alert => {
    const status = getAlertStatus(alert)
    return status.triggered && alert.isActive
  })

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Chargement des alertes...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <Link 
            href="/" 
            className="inline-flex items-center space-x-2 text-gradient hover:text-blue-700 transition-colors font-medium"
          >
            <ArrowLeft className="w-4 h-4" strokeWidth={2} />
            <span>Retour à l'accueil</span>
          </Link>
        </div>

        {/* Title and Stats */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center p-4 bg-gradient-warning rounded-2xl mb-6 float shadow-2xl">
            <Bell className="w-8 h-8 text-white" strokeWidth={2} />
          </div>
          <h1 className="text-5xl md:text-6xl font-black text-gradient mb-6 leading-tight">
            Alertes Prix
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto leading-relaxed">
            Gérez vos alertes de prix et ne manquez jamais une bonne affaire.
            <span className="text-gradient-secondary font-semibold"> {alerts.length} alerte{alerts.length !== 1 ? 's' : ''} configurée{alerts.length !== 1 ? 's' : ''}</span>
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="glass-card p-6 rounded-2xl text-center">
            <div className="w-12 h-12 bg-gradient-primary rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Bell className="w-6 h-6 text-white" strokeWidth={2} />
            </div>
            <div className="text-3xl font-black text-gradient mb-2">{alerts.length}</div>
            <div className="text-sm text-gray-600 font-medium">Total alertes</div>
          </div>
          
          <div className="glass-card p-6 rounded-2xl text-center">
            <div className="w-12 h-12 bg-gradient-success rounded-2xl flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-6 h-6 text-white" strokeWidth={2} />
            </div>
            <div className="text-3xl font-black text-gradient mb-2">{activeAlerts.length}</div>
            <div className="text-sm text-gray-600 font-medium">Alertes actives</div>
          </div>
          
          <div className="glass-card p-6 rounded-2xl text-center">
            <div className="w-12 h-12 bg-gradient-warning rounded-2xl flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-6 h-6 text-white" strokeWidth={2} />
            </div>
            <div className="text-3xl font-black text-gradient mb-2">{triggeredAlerts.length}</div>
            <div className="text-sm text-gray-600 font-medium">Alertes déclenchées</div>
          </div>
          
          <div className="glass-card p-6 rounded-2xl text-center">
            <div className="w-12 h-12 bg-gradient-secondary rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Car className="w-6 h-6 text-white" strokeWidth={2} />
            </div>
            <div className="text-3xl font-black text-gradient mb-2">
              {new Set(alerts.map(a => a.carId)).size}
            </div>
            <div className="text-sm text-gray-600 font-medium">Voitures surveillées</div>
          </div>
        </div>

        {/* Controls */}
        {alerts.length > 0 && (
          <div className="glass-card p-6 rounded-2xl mb-8">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-1">Gestion des alertes</h3>
                <p className="text-sm text-gray-600">Activez, désactivez ou supprimez vos alertes</p>
              </div>
              <button
                onClick={clearAllAlerts}
                className="btn-secondary text-red-600 hover:bg-red-50 flex items-center space-x-2"
              >
                <Trash2 className="w-4 h-4" strokeWidth={2} />
                <span>Tout supprimer</span>
              </button>
            </div>
          </div>
        )}

        {/* Empty State */}
        {alerts.length === 0 && (
          <div className="text-center py-16">
            <div className="glass-card p-12 rounded-2xl max-w-md mx-auto">
              <div className="w-20 h-20 bg-gradient-warning/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <Bell className="w-8 h-8 text-gray-400" strokeWidth={2} />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                Aucune alerte configurée
              </h3>
              <p className="text-gray-600 mb-6">
                Visitez les pages de détail des voitures pour créer des alertes de prix.
              </p>
              <Link href="/" className="btn-primary">
                Parcourir les voitures
              </Link>
            </div>
          </div>
        )}

        {/* Alerts List */}
        {alerts.length > 0 && (
          <div className="space-y-4">
            {alerts.map((alert) => {
              const car = carDetails[alert.carId]
              const status = getAlertStatus(alert)
              
              return (
                <div
                  key={alert.id}
                  className={`glass-card p-6 rounded-2xl border-l-4 ${
                    status.triggered 
                      ? 'border-red-500 bg-red-50/20' 
                      : alert.isActive 
                        ? 'border-green-500' 
                        : 'border-gray-300'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      {/* Status Icon */}
                      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${
                        status.triggered 
                          ? 'bg-red-100' 
                          : alert.isActive 
                            ? 'bg-green-100' 
                            : 'bg-gray-100'
                      }`}>
                        {status.triggered ? (
                          <AlertTriangle className="w-6 h-6 text-red-500" strokeWidth={2} />
                        ) : alert.isActive ? (
                          <Bell className="w-6 h-6 text-green-500" strokeWidth={2} />
                        ) : (
                          <BellOff className="w-6 h-6 text-gray-400" strokeWidth={2} />
                        )}
                      </div>

                      {/* Alert Details */}
                      <div className="flex-1">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h3 className="text-lg font-bold text-gray-900 mb-1">
                              {car ? car.title : 'Voiture inconnue'}
                            </h3>
                            <div className="flex items-center space-x-4 text-sm text-gray-600">
                              <div className="flex items-center space-x-1">
                                <Calendar className="w-4 h-4" strokeWidth={2} />
                                <span>Créée le {formatDate(alert.createdAt)}</span>
                              </div>
                              <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                                alert.isActive ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                              }`}>
                                {alert.isActive ? 'Active' : 'Désactivée'}
                              </div>
                              {status.triggered && (
                                <div className="px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium">
                                  DÉCLENCHÉE
                                </div>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Price Information */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                          <div className="glass-card p-3 rounded-lg">
                            <div className="flex items-center space-x-2 mb-1">
                              {alert.condition === 'below' ? (
                                <TrendingDown className="w-4 h-4 text-green-500" strokeWidth={2} />
                              ) : (
                                <TrendingUp className="w-4 h-4 text-red-500" strokeWidth={2} />
                              )}
                              <span className="text-sm font-medium text-gray-600">
                                {alert.condition === 'below' ? 'Alerte si < à' : 'Alerte si > à'}
                              </span>
                            </div>
                            <div className="text-lg font-bold text-gray-900">
                              {formatPrice(alert.targetPrice)}
                            </div>
                          </div>

                          {car && (
                            <div className="glass-card p-3 rounded-lg">
                              <div className="flex items-center space-x-2 mb-1">
                                <DollarSign className="w-4 h-4 text-blue-500" strokeWidth={2} />
                                <span className="text-sm font-medium text-gray-600">Prix actuel</span>
                              </div>
                              <div className="text-lg font-bold text-gray-900">
                                {formatPrice(car.price || 0)}
                              </div>
                            </div>
                          )}

                          {car && (
                            <div className="glass-card p-3 rounded-lg">
                              <div className="flex items-center space-x-2 mb-1">
                                <Settings className="w-4 h-4 text-purple-500" strokeWidth={2} />
                                <span className="text-sm font-medium text-gray-600">Différence</span>
                              </div>
                              <div className={`text-lg font-bold ${
                                status.triggered ? 'text-red-600' : 'text-gray-900'
                              }`}>
                                {car.price ? formatPrice(Math.abs(car.price - alert.targetPrice)) : 'N/A'}
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Action Buttons */}
                        <div className="flex items-center space-x-3">
                          {car && (
                            <Link
                              href={`/cars/${alert.carId}`}
                              className="btn-secondary text-sm"
                            >
                              Voir la voiture
                            </Link>
                          )}
                          <button
                            onClick={() => toggleAlert(alert.id)}
                            className={`btn-secondary text-sm ${
                              alert.isActive ? 'text-yellow-600' : 'text-green-600'
                            }`}
                          >
                            {alert.isActive ? 'Désactiver' : 'Activer'}
                          </button>
                          <button
                            onClick={() => deleteAlert(alert.id)}
                            className="btn-secondary text-sm text-red-600"
                          >
                            Supprimer
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}