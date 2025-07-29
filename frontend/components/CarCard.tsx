'use client'

import Link from 'next/link'
import Image from 'next/image'

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
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 overflow-hidden cursor-pointer">
        <div className="relative h-48 w-full">
          <Image
            src={mainImage}
            alt={car.title}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
          <div className="absolute top-2 right-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-xs">
            {car.department}
          </div>
        </div>
        
        <div className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
            {car.title}
          </h3>
          
          <div className="flex justify-between items-center mb-2">
            <span className="text-2xl font-bold text-primary-600 dark:text-primary-400">
              {formatPrice(car.price)}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400 capitalize">
              {car.seller_type}
            </span>
          </div>
          
          <div className="flex justify-between text-sm text-gray-600 dark:text-gray-300">
            <span>{car.year || 'N/A'}</span>
            <span>{formatMileage(car.mileage)}</span>
            <span className="capitalize">{car.fuel_type || 'N/A'}</span>
          </div>
        </div>
      </div>
    </Link>
  )
}