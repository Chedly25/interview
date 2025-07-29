'use client'

import { useState } from 'react'

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
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Filtres
      </h2>
      
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Prix maximum: {new Intl.NumberFormat('fr-FR', {
              style: 'currency',
              currency: 'EUR',
              maximumFractionDigits: 0,
            }).format(maxPrice)}
          </label>
          <input
            type="range"
            min="0"
            max="100000"
            step="1000"
            value={maxPrice}
            onChange={(e) => handlePriceChange(Number(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
            <span>0€</span>
            <span>100 000€</span>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Département
          </label>
          <select
            value={department}
            onChange={(e) => handleDepartmentChange(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
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