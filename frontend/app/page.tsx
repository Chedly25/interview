'use client'

import { useState, useEffect, useCallback } from 'react'
import CarCard from '../components/CarCard'
import CarFilters from '../components/CarFilters'
import ScraperControl from '../components/ScraperControl'
import { 
  Cpu, 
  Camera, 
  TrendingUp, 
  Clock, 
  BarChart3, 
  Zap,
  Sparkles,
  Brain,
  RefreshCw,
  Search,
  Filter,
  ArrowRight,
  Heart,
  Bell
} from 'lucide-react'
import Link from 'next/link'

interface Car {
  id: string
  title: string
  price: number | null
  year: number | null
  mileage: number | null
  fuel_type: string
  images: string[]
  department: string
  seller_type: string
}

interface ApiResponse {
  cars: Car[]
  total: number
}

export default function Home() {
  const [cars, setCars] = useState<Car[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ 
    maxPrice: 100000, 
    minPrice: 0,
    department: '',
    minYear: 1990,
    maxYear: new Date().getFullYear(),
    minMileage: 0,
    maxMileage: 300000,
    fuelTypes: [] as string[],
    sellerTypes: [] as string[]
  })
  const [sortBy, setSortBy] = useState('date_added')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalCars, setTotalCars] = useState(0)

  const CARS_PER_PAGE = 12

  const fetchCars = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        skip: ((currentPage - 1) * CARS_PER_PAGE).toString(),
        limit: CARS_PER_PAGE.toString(),
      })

      // Price filters
      if (filters.minPrice > 0) {
        params.append('min_price', filters.minPrice.toString())
      }
      if (filters.maxPrice < 100000) {
        params.append('max_price', filters.maxPrice.toString())
      }

      // Department filter
      if (filters.department) {
        params.append('department', filters.department)
      }

      // Year filters
      if (filters.minYear > 1990) {
        params.append('min_year', filters.minYear.toString())
      }
      if (filters.maxYear < new Date().getFullYear()) {
        params.append('max_year', filters.maxYear.toString())
      }

      // Mileage filters
      if (filters.minMileage > 0) {
        params.append('min_mileage', filters.minMileage.toString())
      }
      if (filters.maxMileage < 300000) {
        params.append('max_mileage', filters.maxMileage.toString())
      }

      // Fuel type filters
      if (filters.fuelTypes.length > 0) {
        filters.fuelTypes.forEach(fuel => params.append('fuel_type', fuel))
      }

      // Seller type filters
      if (filters.sellerTypes.length > 0) {
        filters.sellerTypes.forEach(seller => params.append('seller_type', seller))
      }

      // Sort parameter
      if (sortBy) {
        params.append('sort', sortBy)
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://interview-production-84f1.up.railway.app'
      const fullUrl = `${apiUrl}/api/cars?${params}`
      
      console.log('Fetching cars from:', fullUrl)
      console.log('Applied filters:', filters)
      
      const response = await fetch(fullUrl)
      console.log('Response status:', response.status)
      
      if (response.ok) {
        const data: ApiResponse = await response.json()
        console.log('API response data:', data)
        setCars(data.cars)
        setTotalCars(data.total)
      } else {
        console.error('Failed to fetch cars:', response.status, response.statusText)
        const errorText = await response.text()
        console.error('Error response:', errorText)
      }
    } catch (error) {
      console.error('Error fetching cars:', error)
    } finally {
      setLoading(false)
    }
  }, [currentPage, filters, sortBy])

  useEffect(() => {
    fetchCars()
  }, [fetchCars])

  const handleFiltersChange = (newFilters: {
    maxPrice: number
    minPrice: number
    department: string
    minYear: number
    maxYear: number
    minMileage: number
    maxMileage: number
    fuelTypes: string[]
    sellerTypes: string[]
  }) => {
    setFilters(newFilters)
    setCurrentPage(1)
  }

  const handleSortChange = (value: string) => {
    setSortBy(value)
    // Sort logic would be implemented here
  }

  const totalPages = Math.ceil(totalCars / CARS_PER_PAGE)

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-primary opacity-10"></div>
        <div className="relative px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center fade-in">
            <div className="inline-flex items-center justify-center p-4 bg-gradient-primary rounded-2xl mb-6 float shadow-2xl">
              <Brain className="w-8 h-8 text-white" strokeWidth={2} />
            </div>
            <h1 className="text-5xl md:text-6xl font-black text-gradient mb-6 leading-tight">
              Assistant Automobile IA
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
              Découvrez, analysez et négociez les meilleures voitures d'occasion grâce à notre intelligence artificielle avancée. 
              <span className="text-gradient-secondary font-semibold"> 10 fonctionnalités IA révolutionnaires</span> à votre service.
            </p>
            
            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-2xl mx-auto mb-12">
              <div className="glass-card p-6 rounded-2xl text-center scale-in">
                <div className="text-3xl font-bold text-gradient">10</div>
                <div className="text-sm text-gray-600 font-medium">Fonctionnalités IA</div>
              </div>
              <div className="glass-card p-6 rounded-2xl text-center scale-in" style={{animationDelay: '0.1s'}}>
                <div className="text-3xl font-bold text-gradient">{totalCars.toLocaleString('fr-FR')}</div>
                <div className="text-sm text-gray-600 font-medium">Voitures analysées</div>
              </div>
              <div className="glass-card p-6 rounded-2xl text-center scale-in" style={{animationDelay: '0.2s'}}>
                <div className="text-3xl font-bold text-gradient">24/7</div>
                <div className="text-sm text-gray-600 font-medium">Collecte automatique</div>
              </div>
            </div>
            
            {/* Quick Links */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center scale-in" style={{animationDelay: '0.3s'}}>
              <Link 
                href="/favorites" 
                className="inline-flex items-center space-x-3 glass-card p-4 rounded-2xl hover:bg-red-50/50 transition-all group"
              >
                <div className="w-12 h-12 bg-gradient-secondary rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform">
                  <Heart className="w-6 h-6 text-white" strokeWidth={2} />
                </div>
                <div className="text-left">
                  <div className="text-lg font-bold text-gray-900 group-hover:text-gradient transition-colors">
                    Mes Favoris
                  </div>
                  <div className="text-sm text-gray-600">
                    Vos voitures sauvegardées
                  </div>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-gradient group-hover:translate-x-1 transition-all" strokeWidth={2} />
              </Link>
              
              <Link 
                href="/alerts" 
                className="inline-flex items-center space-x-3 glass-card p-4 rounded-2xl hover:bg-yellow-50/50 transition-all group"
              >
                <div className="w-12 h-12 bg-gradient-warning rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform">
                  <Bell className="w-6 h-6 text-white" strokeWidth={2} />
                </div>
                <div className="text-left">
                  <div className="text-lg font-bold text-gray-900 group-hover:text-gradient transition-colors">
                    Alertes Prix
                  </div>
                  <div className="text-sm text-gray-600">
                    Notifications automatiques
                  </div>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-gradient group-hover:translate-x-1 transition-all" strokeWidth={2} />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="px-4 sm:px-6 lg:px-8 pb-20">
        {/* Scraper Control */}
        <div className="slide-up" style={{animationDelay: '0.3s'}}>
          <ScraperControl />
        </div>

        {/* Content Grid */}
        <div className="flex flex-col xl:flex-row gap-8 slide-up" style={{animationDelay: '0.4s'}}>
          {/* Sidebar */}
          <div className="xl:w-80 flex-shrink-0 space-y-6">
            <CarFilters onFiltersChange={handleFiltersChange} />
            
            {/* Sort Control */}
            <div className="glass-card p-6 rounded-2xl">
              <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                <div className="w-8 h-8 bg-gradient-secondary rounded-lg flex items-center justify-center mr-3">
                  <BarChart3 className="w-4 h-4 text-white" strokeWidth={2} />
                </div>
                Trier par
              </h3>
              <select
                value={sortBy}
                onChange={(e) => handleSortChange(e.target.value)}
                className="input-modern w-full"
              >
                <option value="date_added">Date d'ajout</option>
                <option value="price_asc">Prix croissant</option>
                <option value="price_desc">Prix décroissant</option>
                <option value="year_desc">Année décroissante</option>
                <option value="mileage_asc">Kilométrage croissant</option>
              </select>
            </div>

            {/* AI Features Showcase */}
            <div className="glass-card p-6 rounded-2xl">
              <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                <div className="w-8 h-8 bg-gradient-ai rounded-lg flex items-center justify-center mr-3">
                  <Cpu className="w-4 h-4 text-white" strokeWidth={2} />
                </div>
                Fonctionnalités IA
              </h3>
              <div className="space-y-3">
                {[
                  { icon: Sparkles, name: 'Détecteur de Pépites', desc: 'Trouve les bonnes affaires', color: 'text-yellow-500' },
                  { icon: Camera, name: 'Analyse Photos', desc: 'Détecte les défauts visuels', color: 'text-blue-500' },
                  { icon: Brain, name: 'Assistant Négociation', desc: 'Stratégies personnalisées', color: 'text-purple-500' },
                  { icon: TrendingUp, name: 'Prédicteur Marché', desc: 'Évolution des prix', color: 'text-green-500' },
                ].map((feature, idx) => {
                  const IconComponent = feature.icon
                  return (
                    <div key={idx} className="flex items-center space-x-3 p-3 rounded-lg hover:bg-white/20 transition-all cursor-pointer group">
                      <div className={`p-2 rounded-lg bg-white shadow-sm group-hover:shadow-md transition-all`}>
                        <IconComponent className={`w-4 h-4 ${feature.color}`} strokeWidth={2} />
                      </div>
                      <div>
                        <div className="font-semibold text-sm text-gray-900">{feature.name}</div>
                        <div className="text-xs text-gray-600">{feature.desc}</div>
                      </div>
                      <ArrowRight className="w-3 h-3 text-gray-400 group-hover:text-gray-600 ml-auto opacity-0 group-hover:opacity-100 transition-all" />
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Cars Grid */}
          <div className="flex-1">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="text-center">
                  <div className="loading-spinner mx-auto mb-4"></div>
                  <p className="text-gray-600 font-medium">Chargement des véhicules...</p>
                </div>
              </div>
            ) : (
              <>
                {/* Results Header */}
                <div className="glass-card p-6 rounded-2xl mb-6">
                  <div className="flex justify-between items-center">
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900 mb-1">
                        Véhicules disponibles
                      </h2>
                      <p className="text-gray-600">
                        <span className="font-semibold text-gradient">{totalCars.toLocaleString('fr-FR')}</span> voitures analysées par notre IA
                      </p>
                    </div>
                    <div className="hidden md:flex items-center space-x-2">
                      <div className="w-3 h-3 bg-gradient-success rounded-full pulse-glow"></div>
                      <Zap className="w-4 h-4 text-green-500" />
                      <span className="text-sm font-medium text-gray-600">Données en temps réel</span>
                    </div>
                  </div>
                </div>

                {/* Cars Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
                  {cars.map((car, index) => (
                    <div key={car.id} className="scale-in" style={{animationDelay: `${index * 0.1}s`}}>
                      <CarCard car={car} />
                    </div>
                  ))}
                </div>

                {/* Empty State */}
                {cars.length === 0 && (
                  <div className="text-center py-16">
                    <div className="glass-card p-12 rounded-2xl max-w-md mx-auto">
                      <div className="w-20 h-20 bg-gradient-secondary rounded-full flex items-center justify-center mx-auto mb-6">
                        <Search className="w-8 h-8 text-white" strokeWidth={2} />
                      </div>
                      <h3 className="text-xl font-bold text-gray-900 mb-2">
                        Aucune voiture trouvée
                      </h3>
                      <p className="text-gray-600 mb-6">
                        Vérifiez la console pour les erreurs API ou ajustez vos filtres.
                      </p>
                      <button 
                        onClick={() => {
                          setFilters({ 
                            maxPrice: 100000, 
                            minPrice: 0,
                            department: '',
                            minYear: 1990,
                            maxYear: new Date().getFullYear(),
                            minMileage: 0,
                            maxMileage: 300000,
                            fuelTypes: [],
                            sellerTypes: []
                          })
                          fetchCars()
                        }}
                        className="btn-primary flex items-center space-x-2 mx-auto"
                      >
                        <RefreshCw className="w-4 h-4" />
                        <span>Réinitialiser les filtres</span>
                      </button>
                    </div>
                  </div>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="glass-card p-6 rounded-2xl">
                    <div className="flex justify-center items-center space-x-4">
                      <button
                        onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                        disabled={currentPage === 1}
                        className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        ← Précédent
                      </button>
                      
                      <div className="flex items-center space-x-2">
                        {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                          const page = i + 1
                          return (
                            <button
                              key={page}
                              onClick={() => setCurrentPage(page)}
                              className={`w-10 h-10 rounded-lg font-semibold transition-all ${
                                page === currentPage
                                  ? 'bg-gradient-primary text-white shadow-lg'
                                  : 'hover:bg-white/20 text-gray-600'
                              }`}
                            >
                              {page}
                            </button>
                          )
                        })}
                        {totalPages > 5 && (
                          <>
                            <span className="text-gray-400">...</span>
                            <button
                              onClick={() => setCurrentPage(totalPages)}
                              className={`w-10 h-10 rounded-lg font-semibold transition-all ${
                                totalPages === currentPage
                                  ? 'bg-gradient-primary text-white shadow-lg'
                                  : 'hover:bg-white/20 text-gray-600'
                              }`}
                            >
                              {totalPages}
                            </button>
                          </>
                        )}
                      </div>
                      
                      <button
                        onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                        disabled={currentPage === totalPages}
                        className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Suivant →
                      </button>
                    </div>
                    
                    <div className="text-center mt-4">
                      <span className="text-sm text-gray-600">
                        Page <span className="font-semibold text-gradient">{currentPage}</span> sur <span className="font-semibold">{totalPages}</span>
                      </span>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}