'use client'

import Link from 'next/link'
import Image from 'next/image'
import { Calendar, Gauge, Fuel, MapPin, Eye } from 'lucide-react'

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

interface CarCardProps {
  car: Car
}

export default function CarCard({ car }: CarCardProps) {
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

  const mainImage = car.images && car.images.length > 0 ? car.images[0] : '/placeholder-car.jpg'

  return (
    <Link href={`/cars/${car.id}`}>
      <div className="glass-card rounded-2xl overflow-hidden card-hover group transition-all duration-300">
        <div className="relative h-48 w-full overflow-hidden">
          <Image
            src={mainImage}
            alt={car.title}
            fill
            className="object-cover transition-transform duration-300 group-hover:scale-110"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <div className="absolute top-3 right-3 glass-card px-3 py-1 rounded-full flex items-center space-x-1">
            <MapPin className="w-3 h-3 text-blue-500" strokeWidth={2} />
            <span className="text-xs font-medium text-gray-700">{car.department}</span>
          </div>
          <div className="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-y-2 group-hover:translate-y-0">
            <div className="w-10 h-10 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-lg">
              <Eye className="w-5 h-5 text-gray-700" strokeWidth={2} />
            </div>
          </div>
        </div>
        
        <div className="p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-3 line-clamp-2 group-hover:text-gradient transition-colors duration-200">
            {car.title}
          </h3>
          
          <div className="flex justify-between items-center mb-4">
            <span className="text-2xl font-black text-gradient">
              {formatPrice(car.price)}
            </span>
            <span className="px-3 py-1 bg-gradient-secondary/10 text-gradient-secondary text-xs font-bold rounded-full capitalize">
              {car.seller_type}
            </span>
          </div>
          
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div className="flex items-center space-x-2 text-gray-600">
              <Calendar className="w-4 h-4 text-blue-500" strokeWidth={2} />
              <span className="font-medium">{car.year || 'N/A'}</span>
            </div>
            <div className="flex items-center space-x-2 text-gray-600">
              <Gauge className="w-4 h-4 text-green-500" strokeWidth={2} />
              <span className="font-medium">{formatMileage(car.mileage)}</span>
            </div>
            <div className="flex items-center space-x-2 text-gray-600">
              <Fuel className="w-4 h-4 text-orange-500" strokeWidth={2} />
              <span className="font-medium capitalize">{car.fuel_type || 'N/A'}</span>
            </div>
          </div>
        </div>
      </div>
    </Link>
  )
}