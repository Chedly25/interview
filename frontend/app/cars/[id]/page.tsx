'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Image from 'next/image'
import Link from 'next/link'
import ClaudeAnalysis from '../../../components/ClaudeAnalysis'
import AIFeaturesPanel from '../../../components/AIFeaturesPanel'

interface Car {
  id: string
  title: string
  price: number | null
  year: number | null
  mileage: number | null
  fuel_type: string
  description: string
  images: string[]
  url: string
  seller_type: string
  department: string
  first_seen: string
  last_seen: string
}

interface AnalysisData {
  price_assessment: string
  red_flags: string[]
  negotiation_tips: string[]
  overall_score: number
  recommendation: string
}

export default function CarDetail() {
  const params = useParams()
  const carId = params.id as string

  const [car, setCar] = useState<Car | null>(null)
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null)
  const [loading, setLoading] = useState(true)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [currentImageIndex, setCurrentImageIndex] = useState(0)

  useEffect(() => {
    if (carId) {
      fetchCar()
    }
  }, [carId])

  const fetchCar = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/cars/${carId}`)
      if (response.ok) {
        const carData = await response.json()
        setCar(carData)
      } else {
        console.error('Failed to fetch car')
      }
    } catch (error) {
      console.error('Error fetching car:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyze = async () => {
    setAnalysisLoading(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/cars/${carId}/analyze`, {
        method: 'POST',
      })
      if (response.ok) {
        const analysisData = await response.json()
        setAnalysis(analysisData)
      } else {
        console.error('Failed to analyze car')
      }
    } catch (error) {
      console.error('Error analyzing car:', error)
    } finally {
      setAnalysisLoading(false)
    }
  }

  const formatPrice = (price: number | null) => {
    if (!price) return 'Prix non spécifié'
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(price)
  }

  const formatMileage = (mileage: number | null) => {
    if (!mileage) return 'N/A'
    return new Intl.NumberFormat('fr-FR').format(mileage) + ' km'
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!car) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Voiture non trouvée
        </h1>
        <Link href="/" className="text-primary-600 hover:text-primary-700">
          Retour à l'accueil
        </Link>
      </div>
    )
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="mb-6">
        <Link href="/" className="text-primary-600 hover:text-primary-700 text-sm">
          ← Retour aux résultats
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div>
          {car.images && car.images.length > 0 ? (
            <div>
              <div className="relative h-96 w-full mb-4">
                <Image
                  src={car.images[currentImageIndex]}
                  alt={car.title}
                  fill
                  className="object-cover rounded-lg"
                  sizes="(max-width: 1024px) 100vw, 50vw"
                />
              </div>
              
              {car.images.length > 1 && (
                <div className="flex space-x-2 overflow-x-auto">
                  {car.images.map((image, index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentImageIndex(index)}
                      className={`relative h-20 w-20 flex-shrink-0 rounded-md overflow-hidden ${
                        index === currentImageIndex ? 'ring-2 ring-primary-500' : ''
                      }`}
                    >
                      <Image
                        src={image}
                        alt={`${car.title} - Image ${index + 1}`}
                        fill
                        className="object-cover"
                        sizes="80px"
                      />
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="h-96 bg-gray-200 dark:bg-gray-700 rounded-lg flex items-center justify-center">
              <span className="text-gray-500 dark:text-gray-400">Aucune image disponible</span>
            </div>
          )}
        </div>

        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            {car.title}
          </h1>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <span className="text-sm text-gray-500 dark:text-gray-400">Prix</span>
                <p className="text-2xl font-bold text-primary-600 dark:text-primary-400">
                  {formatPrice(car.price)}
                </p>
              </div>
              <div>
                <span className="text-sm text-gray-500 dark:text-gray-400">Vendeur</span>
                <p className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
                  {car.seller_type}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500 dark:text-gray-400">Année:</span>
                <span className="ml-2 font-medium text-gray-900 dark:text-white">
                  {car.year || 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Kilométrage:</span>
                <span className="ml-2 font-medium text-gray-900 dark:text-white">
                  {formatMileage(car.mileage)}
                </span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Carburant:</span>
                <span className="ml-2 font-medium text-gray-900 dark:text-white capitalize">
                  {car.fuel_type || 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Département:</span>
                <span className="ml-2 font-medium text-gray-900 dark:text-white">
                  {car.department}
                </span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Vue pour la première fois:</span>
                <span className="ml-2 font-medium text-gray-900 dark:text-white">
                  {formatDate(car.first_seen)}
                </span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Dernière mise à jour:</span>
                <span className="ml-2 font-medium text-gray-900 dark:text-white">
                  {formatDate(car.last_seen)}
                </span>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-600">
              <a
                href={car.url}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-md transition-colors inline-block text-center"
              >
                Contacter le vendeur sur LeBonCoin
              </a>
            </div>
          </div>
        </div>
      </div>

      {car.description && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Description
          </h2>
          <div className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
            {car.description}
          </div>
        </div>
      )}

      <AIFeaturesPanel carId={carId} />

      <div className="mt-8">
        <ClaudeAnalysis
          analysis={analysis}
          isLoading={analysisLoading}
          onAnalyze={handleAnalyze}
        />
      </div>
    </div>
  )
}