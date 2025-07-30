'use client'

import { useState } from 'react'
import { Filter, MapPin, DollarSign } from 'lucide-react'

interface FilterProps {
  onFiltersChange: (filters: { maxPrice: number; department: string }) => void
}

const FRENCH_DEPARTMENTS = [
  { code: '', name: 'Tous les départements' },
  { code: '01', name: 'Ain' },
  { code: '69', name: 'Rhône' },
  { code: '75', name: 'Paris' },
  { code: '13', name: 'Bouches-du-Rhône' },
  { code: '33', name: 'Gironde' },
  { code: '59', name: 'Nord' },
  { code: '31', name: 'Haute-Garonne' },
  { code: '44', name: 'Loire-Atlantique' },
  { code: '67', name: 'Bas-Rhin' },
  { code: '06', name: 'Alpes-Maritimes' },
]

export default function CarFilters({ onFiltersChange }: FilterProps) {
  const [maxPrice, setMaxPrice] = useState(50000)
  const [department, setDepartment] = useState('')

  const handlePriceChange = (value: number) => {
    setMaxPrice(value)
    onFiltersChange({ maxPrice: value, department })
  }

  const handleDepartmentChange = (value: string) => {
    setDepartment(value)
    onFiltersChange({ maxPrice, department: value })
  }

  return (
    <div className="glass-card p-6 rounded-2xl">
      <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center">
        <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center mr-3">
          <Filter className="w-4 h-4 text-white" strokeWidth={2} />
        </div>
        Filtres de recherche
      </h3>
      
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-bold text-gray-900 mb-3 flex items-center">
            <DollarSign className="w-4 h-4 text-green-500 mr-2" strokeWidth={2} />
            Prix maximum: <span className="text-gradient ml-2">{new Intl.NumberFormat('fr-FR', {
              style: 'currency',
              currency: 'EUR',
              maximumFractionDigits: 0,
            }).format(maxPrice)}</span>
          </label>
          <div className="relative">
            <input
              type="range"
              min="0"
              max="100000"
              step="1000"
              value={maxPrice}
              onChange={(e) => handlePriceChange(Number(e.target.value))}
              className="slider-modern w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-2 font-medium">
              <span>0€</span>
              <span>100 000€</span>
            </div>
          </div>
        </div>

        <div>
          <label className="block text-sm font-bold text-gray-900 mb-3 flex items-center">
            <MapPin className="w-4 h-4 text-blue-500 mr-2" strokeWidth={2} />
            Département
          </label>
          <select
            value={department}
            onChange={(e) => handleDepartmentChange(e.target.value)}
            className="input-modern w-full"
          >
            {FRENCH_DEPARTMENTS.map((dept) => (
              <option key={dept.code} value={dept.code}>
                {dept.code && `${dept.code} - `}{dept.name}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  )
}