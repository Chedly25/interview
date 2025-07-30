'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Image from 'next/image'
import Link from 'next/link'
import { 
  ArrowLeft, 
  Heart, 
  Share2, 
  ExternalLink, 
  Calendar, 
  Gauge, 
  Fuel, 
  MapPin, 
  User, 
  Clock, 
  Eye,
  ChevronLeft,
  ChevronRight,
  Download,
  Copy,
  Check,
  Star,
  DollarSign,
  Camera
} from 'lucide-react'
import ClaudeAnalysis from '../../../components/ClaudeAnalysis'
import AIFeaturesPanel from '../../../components/AIFeaturesPanel'
import PriceHistory from '../../../components/PriceHistory'

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
  const [isFavorite, setIsFavorite] = useState(false)
  const [showShareMenu, setShowShareMenu] = useState(false)
  const [copySuccess, setCopySuccess] = useState(false)

  useEffect(() => {
    if (carId) {
      fetchCar()
      checkFavoriteStatus()
    }
  }, [carId])

  const fetchCar = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://interview-production-84f1.up.railway.app'
      const response = await fetch(`${apiUrl}/api/cars/${carId}`)
      console.log('Fetching car details:', response.status)
      
      if (response.ok) {
        const carData = await response.json()
        console.log('Car data:', carData)
        setCar(carData)
      } else {
        console.error('Failed to fetch car:', response.status)
      }
    } catch (error) {
      console.error('Error fetching car:', error)
    } finally {
      setLoading(false)
    }
  }

  const checkFavoriteStatus = () => {
    const favorites = JSON.parse(localStorage.getItem('car-favorites') || '[]')
    setIsFavorite(favorites.includes(carId))
  }

  const toggleFavorite = () => {
    const favorites = JSON.parse(localStorage.getItem('car-favorites') || '[]')
    let updatedFavorites

    if (isFavorite) {
      updatedFavorites = favorites.filter((id: string) => id !== carId)
    } else {
      updatedFavorites = [...favorites, carId]
    }

    localStorage.setItem('car-favorites', JSON.stringify(updatedFavorites))
    setIsFavorite(!isFavorite)
  }

  const handleAnalyze = async () => {
    setAnalysisLoading(true)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://interview-production-84f1.up.railway.app'
      const response = await fetch(`${apiUrl}/api/cars/${carId}/analyze`, {
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

  const shareUrl = typeof window !== 'undefined' ? window.location.href : ''

  const handleShare = async (method: string) => {
    if (!car) return

    const shareData = {
      title: car.title,
      text: `Découvrez cette ${car.title} à ${formatPrice(car.price)} sur Assistant Automobile IA`,
      url: shareUrl
    }

    switch (method) {
      case 'copy':
        try {
          await navigator.clipboard.writeText(shareUrl)
          setCopySuccess(true)
          setTimeout(() => setCopySuccess(false), 2000)
        } catch (err) {
          console.error('Failed to copy link')
        }
        break
      case 'native':
        if (navigator.share) {
          try {
            await navigator.share(shareData)
          } catch (err) {
            console.error('Error sharing:', err)
          }
        }
        break
      case 'twitter':
        window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(shareData.text)}&url=${encodeURIComponent(shareUrl)}`, '_blank')
        break
      case 'facebook':
        window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`, '_blank')
        break
    }
    setShowShareMenu(false)
  }

  const nextImage = () => {
    if (car?.images) {
      setCurrentImageIndex((prev) => (prev + 1) % car.images.length)
    }
  }

  const prevImage = () => {
    if (car?.images) {
      setCurrentImageIndex((prev) => (prev - 1 + car.images.length) % car.images.length)
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
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    })
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Chargement des détails...</p>
        </div>
      </div>
    )
  }

  if (!car) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-20 h-20 bg-gradient-secondary rounded-full flex items-center justify-center mx-auto mb-6">
            <Eye className="w-8 h-8 text-white" strokeWidth={2} />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Voiture non trouvée
          </h1>
          <p className="text-gray-600 mb-6">Cette voiture n'existe pas ou a été supprimée.</p>
          <Link href="/" className="btn-primary">
            Retour à l'accueil
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <div className="px-4 sm:px-6 lg:px-8 py-6">
        <Link 
          href="/" 
          className="inline-flex items-center space-x-2 text-gradient hover:text-blue-700 transition-colors font-medium"
        >
          <ArrowLeft className="w-4 h-4" strokeWidth={2} />
          <span>Retour aux résultats</span>
        </Link>
      </div>

      {/* Main Content */}
      <div className="px-4 sm:px-6 lg:px-8 pb-20">
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          {/* Image Gallery */}
          <div className="xl:col-span-2">
            <div className="glass-card rounded-2xl overflow-hidden">
              {car.images && car.images.length > 0 ? (
                <div>
                  <div className="relative h-96 lg:h-[500px] w-full">
                    <Image
                      src={car.images[currentImageIndex]}
                      alt={car.title}
                      fill
                      className="object-cover"
                      sizes="(max-width: 1280px) 100vw, 66vw"
                      priority
                    />
                    
                    {/* Image Navigation */}
                    {car.images.length > 1 && (
                      <>
                        <button
                          onClick={prevImage}
                          className="absolute left-4 top-1/2 transform -translate-y-1/2 w-12 h-12 bg-black/50 backdrop-blur-sm rounded-full flex items-center justify-center text-white hover:bg-black/70 transition-all"
                        >
                          <ChevronLeft className="w-6 h-6" strokeWidth={2} />
                        </button>
                        <button
                          onClick={nextImage}
                          className="absolute right-4 top-1/2 transform -translate-y-1/2 w-12 h-12 bg-black/50 backdrop-blur-sm rounded-full flex items-center justify-center text-white hover:bg-black/70 transition-all"
                        >
                          <ChevronRight className="w-6 h-6" strokeWidth={2} />
                        </button>
                      </>
                    )}

                    {/* Image Counter */}
                    <div className="absolute top-4 right-4 glass-card px-3 py-1 rounded-full">
                      <div className="flex items-center space-x-1">
                        <Camera className="w-4 h-4 text-gray-600" strokeWidth={2} />
                        <span className="text-sm font-medium text-gray-700">
                          {currentImageIndex + 1}/{car.images.length}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Thumbnail Gallery */}
                  {car.images.length > 1 && (
                    <div className="p-4">
                      <div className="flex space-x-2 overflow-x-auto">
                        {car.images.map((image, index) => (
                          <button
                            key={index}
                            onClick={() => setCurrentImageIndex(index)}
                            className={`relative h-16 w-16 flex-shrink-0 rounded-lg overflow-hidden transition-all ${
                              index === currentImageIndex 
                                ? 'ring-2 ring-blue-500 transform scale-105' 
                                : 'hover:opacity-80'
                            }`}
                          >
                            <Image
                              src={image}
                              alt={`${car.title} - Image ${index + 1}`}
                              fill
                              className="object-cover"
                              sizes="64px"
                            />
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="h-96 bg-gradient-to-r from-gray-100 to-gray-200 flex items-center justify-center">
                  <div className="text-center">
                    <Camera className="w-16 h-16 text-gray-400 mx-auto mb-4" strokeWidth={1} />
                    <span className="text-gray-500 font-medium">Aucune image disponible</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Car Info Sidebar */}
          <div className="space-y-6">
            {/* Main Info Card */}
            <div className="glass-card p-8 rounded-2xl">
              {/* Title and Actions */}
              <div className="flex justify-between items-start mb-6">
                <h1 className="text-2xl font-black text-gradient leading-tight">
                  {car.title}
                </h1>
                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={toggleFavorite}
                    className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                      isFavorite 
                        ? 'bg-gradient-secondary text-white shadow-lg' 
                        : 'glass-card hover:bg-red-50'
                    }`}
                  >
                    <Heart 
                      className={`w-5 h-5 ${isFavorite ? 'fill-current' : ''}`} 
                      strokeWidth={2} 
                    />
                  </button>
                  <div className="relative">
                    <button
                      onClick={() => setShowShareMenu(!showShareMenu)}
                      className="w-12 h-12 glass-card rounded-full flex items-center justify-center hover:bg-blue-50 transition-all"
                    >
                      <Share2 className="w-5 h-5 text-gray-600" strokeWidth={2} />
                    </button>
                    
                    {showShareMenu && (
                      <div className="absolute right-0 top-14 glass-card rounded-2xl p-4 w-48 shadow-2xl z-10 slide-up">
                        <div className="space-y-2">
                          <button
                            onClick={() => handleShare('copy')}
                            className="w-full flex items-center space-x-3 p-2 rounded-lg hover:bg-white/50 transition-all"
                          >
                            {copySuccess ? (
                              <Check className="w-4 h-4 text-green-500" strokeWidth={2} />
                            ) : (
                              <Copy className="w-4 h-4 text-gray-600" strokeWidth={2} />
                            )}
                            <span className="text-sm font-medium">
                              {copySuccess ? 'Copié !' : 'Copier le lien'}
                            </span>
                          </button>
                          {navigator.share && (
                            <button
                              onClick={() => handleShare('native')}
                              className="w-full flex items-center space-x-3 p-2 rounded-lg hover:bg-white/50 transition-all"
                            >
                              <Share2 className="w-4 h-4 text-gray-600" strokeWidth={2} />
                              <span className="text-sm font-medium">Partager</span>
                            </button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Price and Seller */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="text-center p-4 bg-gradient-primary/10 rounded-2xl">
                  <DollarSign className="w-6 h-6 text-green-500 mx-auto mb-2" strokeWidth={2} />
                  <div className="text-2xl font-black text-gradient mb-1">
                    {formatPrice(car.price)}
                  </div>
                  <div className="text-xs text-gray-600 font-medium">Prix annoncé</div>
                </div>
                <div className="text-center p-4 bg-gradient-secondary/10 rounded-2xl">
                  <User className="w-6 h-6 text-blue-500 mx-auto mb-2" strokeWidth={2} />
                  <div className="text-lg font-bold text-gray-900 mb-1 capitalize">
                    {car.seller_type}
                  </div>
                  <div className="text-xs text-gray-600 font-medium">Type vendeur</div>
                </div>
              </div>

              {/* Car Details Grid */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="flex items-center space-x-3 p-3 glass-card rounded-xl">
                  <Calendar className="w-5 h-5 text-blue-500" strokeWidth={2} />
                  <div>
                    <div className="font-bold text-gray-900">{car.year || 'N/A'}</div>
                    <div className="text-xs text-gray-600">Année</div>
                  </div>
                </div>
                <div className="flex items-center space-x-3 p-3 glass-card rounded-xl">
                  <Gauge className="w-5 h-5 text-green-500" strokeWidth={2} />
                  <div>
                    <div className="font-bold text-gray-900">{formatMileage(car.mileage)}</div>
                    <div className="text-xs text-gray-600">Kilométrage</div>
                  </div>
                </div>
                <div className="flex items-center space-x-3 p-3 glass-card rounded-xl">
                  <Fuel className="w-5 h-5 text-orange-500" strokeWidth={2} />
                  <div>
                    <div className="font-bold text-gray-900 capitalize">{car.fuel_type || 'N/A'}</div>
                    <div className="text-xs text-gray-600">Carburant</div>
                  </div>
                </div>
                <div className="flex items-center space-x-3 p-3 glass-card rounded-xl">
                  <MapPin className="w-5 h-5 text-red-500" strokeWidth={2} />
                  <div>
                    <div className="font-bold text-gray-900">{car.department}</div>
                    <div className="text-xs text-gray-600">Département</div>
                  </div>
                </div>
              </div>

              {/* Tracking Info */}
              <div className="glass-card p-4 rounded-xl mb-6">
                <h3 className="text-sm font-bold text-gray-900 mb-3 flex items-center">
                  <Clock className="w-4 h-4 text-gray-500 mr-2" strokeWidth={2} />
                  Historique de suivi
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Première détection:</span>
                    <span className="font-medium text-gray-900">{formatDate(car.first_seen)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Dernière mise à jour:</span>
                    <span className="font-medium text-gray-900">{formatDate(car.last_seen)}</span>
                  </div>
                </div>
              </div>

              {/* Contact Button */}
              <a
                href={car.url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary w-full flex items-center justify-center space-x-2"
              >
                <ExternalLink className="w-5 h-5" strokeWidth={2} />
                <span>Contacter sur LeBonCoin</span>
              </a>
            </div>
          </div>
        </div>

        {/* Description */}
        {car.description && (
          <div className="glass-card rounded-2xl p-8 mt-8 slide-up">
            <h2 className="text-2xl font-bold text-gradient mb-6">
              Description du véhicule
            </h2>
            <div className="prose prose-gray max-w-none">
              <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                {car.description}
              </div>
            </div>
          </div>
        )}

        {/* Price History */}
        <div className="mt-8 slide-up" style={{animationDelay: '0.1s'}}>
          <PriceHistory 
            carId={carId} 
            currentPrice={car.price || 0} 
            title={car.title} 
          />
        </div>

        {/* AI Features Panel */}
        <div className="mt-8 slide-up" style={{animationDelay: '0.2s'}}>
          <AIFeaturesPanel carId={carId} />
        </div>

        {/* Claude Analysis */}
        <div className="mt-8 slide-up" style={{animationDelay: '0.3s'}}>
          <ClaudeAnalysis
            analysis={analysis}
            isLoading={analysisLoading}
            onAnalyze={handleAnalyze}
          />
        </div>
      </div>
    </div>
  )
}