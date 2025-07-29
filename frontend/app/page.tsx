'use client'

import { useState, useEffect, useCallback } from 'react'
import CarCard from '../components/CarCard'
import CarFilters from '../components/CarFilters'

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
  const [filters, setFilters] = useState({ maxPrice: 50000, department: '' })
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

      if (filters.maxPrice < 50000) {
        params.append('max_price', filters.maxPrice.toString())
      }
      if (filters.department) {
        params.append('department', filters.department)
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/cars?${params}`)
      if (response.ok) {
        const data: ApiResponse = await response.json()
        setCars(data.cars)
        setTotalCars(data.total)
      } else {
        console.error('Failed to fetch cars')
      }
    } catch (error) {
      console.error('Error fetching cars:', error)
    } finally {
      setLoading(false)
    }
  }, [currentPage, filters])

  useEffect(() => {
    fetchCars()
  }, [fetchCars])

  const handleFiltersChange = (newFilters: { maxPrice: number; department: string }) => {
    setFilters(newFilters)
    setCurrentPage(1)
  }

  const handleSortChange = (value: string) => {
    setSortBy(value)
    // Sort logic would be implemented here
  }

  const totalPages = Math.ceil(totalCars / CARS_PER_PAGE)

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Voitures d'occasion
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Découvrez notre sélection de voitures analysées par l'IA
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        <div className="lg:w-80 flex-shrink-0">
          <CarFilters onFiltersChange={handleFiltersChange} />
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Trier par
            </h3>
            <select
              value={sortBy}
              onChange={(e) => handleSortChange(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            >
              <option value="date_added">Date d'ajout</option>
              <option value="price_asc">Prix croissant</option>
              <option value="price_desc">Prix décroissant</option>
              <option value="year_desc">Année décroissante</option>
              <option value="mileage_asc">Kilométrage croissant</option>
            </select>
          </div>
        </div>

        <div className="flex-1">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
            </div>
          ) : (
            <>
              <div className="mb-4 flex justify-between items-center">
                <p className="text-gray-600 dark:text-gray-400">
                  {totalCars} voitures trouvées
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
                {cars.map((car) => (
                  <CarCard key={car.id} car={car} />
                ))}
              </div>

              {cars.length === 0 && (
                <div className="text-center py-12">
                  <div className="text-gray-400 dark:text-gray-500 mb-4">
                    <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </div>
                  <p className="text-gray-500 dark:text-gray-400">
                    Aucune voiture trouvée avec ces filtres
                  </p>
                </div>
              )}

              {totalPages > 1 && (
                <div className="flex justify-center space-x-2">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700"
                  >
                    Précédent
                  </button>
                  
                  <span className="px-4 py-2 text-gray-700 dark:text-gray-300">
                    Page {currentPage} sur {totalPages}
                  </span>
                  
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700"
                  >
                    Suivant
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}