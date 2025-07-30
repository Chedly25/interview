'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Heart, Trash2, ArrowLeft, Search, Filter, SortAsc, SortDesc, Calendar, DollarSign, Eye } from 'lucide-react'
import CarCard from '../../components/CarCard'

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
  first_seen: string
  last_seen: string
}

export default function FavoritesPage() {
  const [favorites, setFavorites] = useState<string[]>([])
  const [favoriteCars, setFavoriteCars] = useState<Car[]>([])
  const [loading, setLoading] = useState(true)
  const [sortBy, setSortBy] = useState<'date_added' | 'price_asc' | 'price_desc' | 'year_desc' | 'title'>('date_added')
  const [filterText, setFilterText] = useState('')

  useEffect(() => {
    loadFavorites()
  }, [])

  useEffect(() => {
    if (favorites.length > 0) {
      fetchFavoriteCars()
    } else {
      setFavoriteCars([])
      setLoading(false)
    }
  }, [favorites])

  const loadFavorites = () => {
    const storedFavorites = JSON.parse(localStorage.getItem('car-favorites') || '[]')
    setFavorites(storedFavorites)
  }

  const fetchFavoriteCars = async () => {
    setLoading(true)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://interview-production-84f1.up.railway.app'
      const carPromises = favorites.map(async (carId) => {
        try {
          const response = await fetch(`${apiUrl}/api/cars/${carId}`)
          if (response.ok) {
            return await response.json()
          }
          return null
        } catch (error) {
          console.error(`Error fetching car ${carId}:`, error)
          return null
        }
      })

      const cars = await Promise.all(carPromises)
      const validCars = cars.filter(car => car !== null)
      setFavoriteCars(validCars)
    } catch (error) {
      console.error('Error fetching favorite cars:', error)
    } finally {
      setLoading(false)
    }
  }

  const removeFavorite = (carId: string) => {
    const updatedFavorites = favorites.filter(id => id !== carId)
    setFavorites(updatedFavorites)
    localStorage.setItem('car-favorites', JSON.stringify(updatedFavorites))
    setFavoriteCars(prev => prev.filter(car => car.id !== carId))
  }

  const clearAllFavorites = () => {
    setFavorites([])
    setFavoriteCars([])
    localStorage.removeItem('car-favorites')
  }

  const sortedAndFilteredCars = favoriteCars
    .filter(car => 
      car.title.toLowerCase().includes(filterText.toLowerCase()) ||
      car.department.toLowerCase().includes(filterText.toLowerCase()) ||
      car.fuel_type.toLowerCase().includes(filterText.toLowerCase())
    )
    .sort((a, b) => {
      switch (sortBy) {
        case 'price_asc':
          return (a.price || 0) - (b.price || 0)
        case 'price_desc':
          return (b.price || 0) - (a.price || 0)
        case 'year_desc':
          return (b.year || 0) - (a.year || 0)
        case 'title':
          return a.title.localeCompare(b.title)
        case 'date_added':
        default:
          // For date_added, we maintain the original order (most recently added first)
          return 0
      }
    })

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    })
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <Link 
              href="/" 
              className="inline-flex items-center space-x-2 text-gradient hover:text-blue-700 transition-colors font-medium"
            >
              <ArrowLeft className="w-4 h-4" strokeWidth={2} />
              <span>Retour à l'accueil</span>
            </Link>
          </div>
        </div>

        {/* Title and Stats */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center p-4 bg-gradient-secondary rounded-2xl mb-6 float shadow-2xl">
            <Heart className="w-8 h-8 text-white fill-current" strokeWidth={2} />
          </div>
          <h1 className="text-5xl md:text-6xl font-black text-gradient mb-6 leading-tight">
            Mes Favoris
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto leading-relaxed">
            Retrouvez toutes les voitures que vous avez sauvegardées. 
            <span className="text-gradient-secondary font-semibold"> {favorites.length} véhicule{favorites.length !== 1 ? 's' : ''} sauvegardé{favorites.length !== 1 ? 's' : ''}</span>
          </p>
        </div>

        {/* Controls */}
        {favorites.length > 0 && (
          <div className="glass-card p-6 rounded-2xl mb-8">
            <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
              {/* Search */}
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" strokeWidth={2} />
                <input
                  type="text"
                  placeholder="Rechercher dans mes favoris..."
                  value={filterText}
                  onChange={(e) => setFilterText(e.target.value)}
                  className="input-modern w-full pl-10"
                />
              </div>

              {/* Sort */}
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Filter className="w-4 h-4 text-gray-600" strokeWidth={2} />
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as any)}
                    className="input-modern"
                  >
                    <option value="date_added">Date d'ajout</option>
                    <option value="price_asc">Prix croissant</option>
                    <option value="price_desc">Prix décroissant</option>
                    <option value="year_desc">Année décroissante</option>
                    <option value="title">Nom A-Z</option>
                  </select>
                </div>

                {/* Clear All */}
                <button
                  onClick={clearAllFavorites}
                  className="btn-secondary text-red-600 hover:bg-red-50 flex items-center space-x-2"
                >
                  <Trash2 className="w-4 h-4" strokeWidth={2} />
                  <span>Tout supprimer</span>
                </button>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-200">
              <div className="text-center p-4 glass-card rounded-xl">
                <div className="text-2xl font-black text-gradient mb-1">{sortedAndFilteredCars.length}</div>
                <div className="text-sm text-gray-600 font-medium">Véhicules affichés</div>
              </div>
              <div className="text-center p-4 glass-card rounded-xl">
                <div className="text-2xl font-black text-gradient mb-1">
                  {sortedAndFilteredCars.length > 0 
                    ? Math.round(sortedAndFilteredCars.reduce((sum, car) => sum + (car.price || 0), 0) / sortedAndFilteredCars.length).toLocaleString('fr-FR')
                    : '0'
                  }€
                </div>
                <div className="text-sm text-gray-600 font-medium">Prix moyen</div>
              </div>
              <div className="text-center p-4 glass-card rounded-xl">
                <div className="text-2xl font-black text-gradient mb-1">
                  {sortedAndFilteredCars.length > 0 
                    ? Math.round(sortedAndFilteredCars.reduce((sum, car) => sum + (car.year || 0), 0) / sortedAndFilteredCars.length)
                    : new Date().getFullYear()
                  }
                </div>
                <div className="text-sm text-gray-600 font-medium">Année moyenne</div>
              </div>
            </div>

            {filterText && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-600">
                  <span className="font-semibold">{sortedAndFilteredCars.length}</span> résultat{sortedAndFilteredCars.length !== 1 ? 's' : ''} 
                  pour "<span className="font-medium text-gradient">{filterText}</span>"
                </p>
              </div>
            )}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="loading-spinner mx-auto mb-4"></div>
              <p className="text-gray-600 font-medium">Chargement de vos favoris...</p>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && favorites.length === 0 && (
          <div className="text-center py-16">
            <div className="glass-card p-12 rounded-2xl max-w-md mx-auto">
              <div className="w-20 h-20 bg-gradient-secondary/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <Heart className="w-8 h-8 text-gray-400" strokeWidth={2} />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                Aucun favori pour le moment
              </h3>
              <p className="text-gray-600 mb-6">
                Ajoutez des voitures à vos favoris en cliquant sur le cœur lors de vos recherches.
              </p>
              <Link href="/" className="btn-primary">
                Découvrir des voitures
              </Link>
            </div>
          </div>
        )}

        {/* No Results State */}
        {!loading && favorites.length > 0 && sortedAndFilteredCars.length === 0 && (
          <div className="text-center py-16">
            <div className="glass-card p-12 rounded-2xl max-w-md mx-auto">
              <div className="w-20 h-20 bg-gradient-warning/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <Search className="w-8 h-8 text-gray-400" strokeWidth={2} />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                Aucun résultat trouvé
              </h3>
              <p className="text-gray-600 mb-6">
                Aucune voiture ne correspond à votre recherche "{filterText}".
              </p>
              <button 
                onClick={() => setFilterText('')}
                className="btn-secondary"
              >
                Effacer la recherche
              </button>
            </div>
          </div>
        )}

        {/* Cars Grid */}
        {!loading && sortedAndFilteredCars.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {sortedAndFilteredCars.map((car, index) => (
              <div key={car.id} className="relative scale-in" style={{animationDelay: `${index * 0.1}s`}}>
                <CarCard car={car} />
                {/* Remove Button */}
                <button
                  onClick={(e) => {
                    e.preventDefault()
                    removeFavorite(car.id)
                  }}
                  className="absolute top-3 left-3 w-10 h-10 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center shadow-lg transition-all hover:scale-110 z-10"
                  title="Retirer des favoris"
                >
                  <Trash2 className="w-4 h-4" strokeWidth={2} />
                </button>
                {/* Added Date */}
                <div className="absolute bottom-3 left-3 glass-card px-2 py-1 rounded-full">
                  <div className="flex items-center space-x-1">
                    <Calendar className="w-3 h-3 text-gray-600" strokeWidth={2} />
                    <span className="text-xs font-medium text-gray-700">
                      Ajouté le {formatDate(car.first_seen)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}