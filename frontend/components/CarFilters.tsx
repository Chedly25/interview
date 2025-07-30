'use client'

import { useState, useEffect } from 'react'
import { Filter, MapPin, DollarSign, Calendar, Gauge, Fuel, Settings, X, RotateCcw } from 'lucide-react'

interface FilterProps {
  onFiltersChange: (filters: {
    maxPrice: number
    minPrice: number
    department: string
    minYear: number
    maxYear: number
    minMileage: number
    maxMileage: number
    fuelTypes: string[]
    sellerTypes: string[]
  }) => void
}

const FRENCH_DEPARTMENTS = [
  { code: '', name: 'Tous les départements' },
  { code: '01', name: 'Ain' },
  { code: '02', name: 'Aisne' },
  { code: '03', name: 'Allier' },
  { code: '04', name: 'Alpes-de-Haute-Provence' },
  { code: '05', name: 'Hautes-Alpes' },
  { code: '06', name: 'Alpes-Maritimes' },
  { code: '07', name: 'Ardèche' },
  { code: '08', name: 'Ardennes' },
  { code: '09', name: 'Ariège' },
  { code: '10', name: 'Aube' },
  { code: '11', name: 'Aude' },
  { code: '12', name: 'Aveyron' },
  { code: '13', name: 'Bouches-du-Rhône' },
  { code: '14', name: 'Calvados' },
  { code: '15', name: 'Cantal' },
  { code: '16', name: 'Charente' },
  { code: '17', name: 'Charente-Maritime' },
  { code: '18', name: 'Cher' },
  { code: '19', name: 'Corrèze' },
  { code: '21', name: 'Côte-d\'Or' },
  { code: '22', name: 'Côtes-d\'Armor' },
  { code: '23', name: 'Creuse' },
  { code: '24', name: 'Dordogne' },
  { code: '25', name: 'Doubs' },
  { code: '26', name: 'Drôme' },
  { code: '27', name: 'Eure' },
  { code: '28', name: 'Eure-et-Loir' },
  { code: '29', name: 'Finistère' },
  { code: '30', name: 'Gard' },
  { code: '31', name: 'Haute-Garonne' },
  { code: '32', name: 'Gers' },
  { code: '33', name: 'Gironde' },
  { code: '34', name: 'Hérault' },
  { code: '35', name: 'Ille-et-Vilaine' },
  { code: '36', name: 'Indre' },
  { code: '37', name: 'Indre-et-Loire' },
  { code: '38', name: 'Isère' },
  { code: '39', name: 'Jura' },
  { code: '40', name: 'Landes' },
  { code: '41', name: 'Loir-et-Cher' },
  { code: '42', name: 'Loire' },
  { code: '43', name: 'Haute-Loire' },
  { code: '44', name: 'Loire-Atlantique' },
  { code: '45', name: 'Loiret' },
  { code: '46', name: 'Lot' },
  { code: '47', name: 'Lot-et-Garonne' },
  { code: '48', name: 'Lozère' },
  { code: '49', name: 'Maine-et-Loire' },
  { code: '50', name: 'Manche' },
  { code: '51', name: 'Marne' },
  { code: '52', name: 'Haute-Marne' },
  { code: '53', name: 'Mayenne' },
  { code: '54', name: 'Meurthe-et-Moselle' },
  { code: '55', name: 'Meuse' },
  { code: '56', name: 'Morbihan' },
  { code: '57', name: 'Moselle' },
  { code: '58', name: 'Nièvre' },
  { code: '59', name: 'Nord' },
  { code: '60', name: 'Oise' },
  { code: '61', name: 'Orne' },
  { code: '62', name: 'Pas-de-Calais' },
  { code: '63', name: 'Puy-de-Dôme' },
  { code: '64', name: 'Pyrénées-Atlantiques' },
  { code: '65', name: 'Hautes-Pyrénées' },
  { code: '66', name: 'Pyrénées-Orientales' },
  { code: '67', name: 'Bas-Rhin' },
  { code: '68', name: 'Haut-Rhin' },
  { code: '69', name: 'Rhône' },
  { code: '70', name: 'Haute-Saône' },
  { code: '71', name: 'Saône-et-Loire' },
  { code: '72', name: 'Sarthe' },
  { code: '73', name: 'Savoie' },
  { code: '74', name: 'Haute-Savoie' },
  { code: '75', name: 'Paris' },
  { code: '76', name: 'Seine-Maritime' },
  { code: '77', name: 'Seine-et-Marne' },
  { code: '78', name: 'Yvelines' },
  { code: '79', name: 'Deux-Sèvres' },
  { code: '80', name: 'Somme' },
  { code: '81', name: 'Tarn' },
  { code: '82', name: 'Tarn-et-Garonne' },
  { code: '83', name: 'Var' },
  { code: '84', name: 'Vaucluse' },
  { code: '85', name: 'Vendée' },
  { code: '86', name: 'Vienne' },
  { code: '87', name: 'Haute-Vienne' },
  { code: '88', name: 'Vosges' },
  { code: '89', name: 'Yonne' },
  { code: '90', name: 'Territoire de Belfort' },
  { code: '91', name: 'Essonne' },
  { code: '92', name: 'Hauts-de-Seine' },
  { code: '93', name: 'Seine-Saint-Denis' },
  { code: '94', name: 'Val-de-Marne' },
  { code: '95', name: 'Val-d\'Oise' }
]

const FUEL_TYPES = [
  { value: 'essence', label: 'Essence', color: 'bg-orange-500' },
  { value: 'diesel', label: 'Diesel', color: 'bg-blue-500' },
  { value: 'électrique', label: 'Électrique', color: 'bg-green-500' },
  { value: 'hybride', label: 'Hybride', color: 'bg-purple-500' },
  { value: 'gpl', label: 'GPL', color: 'bg-yellow-500' },
  { value: 'autre', label: 'Autre', color: 'bg-gray-500' }
]

const SELLER_TYPES = [
  { value: 'particulier', label: 'Particulier', icon: '👤' },
  { value: 'professionnel', label: 'Professionnel', icon: '🏢' }
]

export default function CarFilters({ onFiltersChange }: FilterProps) {
  const [minPrice, setMinPrice] = useState(0)
  const [maxPrice, setMaxPrice] = useState(100000)
  const [department, setDepartment] = useState('')
  const [minYear, setMinYear] = useState(1990)
  const [maxYear, setMaxYear] = useState(new Date().getFullYear())
  const [minMileage, setMinMileage] = useState(0)
  const [maxMileage, setMaxMileage] = useState(300000)
  const [selectedFuelTypes, setSelectedFuelTypes] = useState<string[]>([])
  const [selectedSellerTypes, setSelectedSellerTypes] = useState<string[]>([])
  const [showAdvanced, setShowAdvanced] = useState(false)

  // Trigger filters change when any filter updates
  useEffect(() => {
    onFiltersChange({
      minPrice,
      maxPrice,
      department,
      minYear,
      maxYear,
      minMileage,
      maxMileage,
      fuelTypes: selectedFuelTypes,
      sellerTypes: selectedSellerTypes
    })
  }, [minPrice, maxPrice, department, minYear, maxYear, minMileage, maxMileage, selectedFuelTypes, selectedSellerTypes, onFiltersChange])

  const toggleFuelType = (fuelType: string) => {
    setSelectedFuelTypes(prev => 
      prev.includes(fuelType) 
        ? prev.filter(type => type !== fuelType)
        : [...prev, fuelType]
    )
  }

  const toggleSellerType = (sellerType: string) => {
    setSelectedSellerTypes(prev => 
      prev.includes(sellerType) 
        ? prev.filter(type => type !== sellerType)
        : [...prev, sellerType]
    )
  }

  const resetFilters = () => {
    setMinPrice(0)
    setMaxPrice(100000)
    setDepartment('')
    setMinYear(1990)
    setMaxYear(new Date().getFullYear())
    setMinMileage(0)
    setMaxMileage(300000)
    setSelectedFuelTypes([])
    setSelectedSellerTypes([])
  }

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(price)
  }

  const formatMileage = (mileage: number) => {
    return new Intl.NumberFormat('fr-FR').format(mileage) + ' km'
  }

  const activeFiltersCount = [
    minPrice > 0 || maxPrice < 100000,
    department !== '',
    minYear > 1990 || maxYear < new Date().getFullYear(),
    minMileage > 0 || maxMileage < 300000,
    selectedFuelTypes.length > 0,
    selectedSellerTypes.length > 0
  ].filter(Boolean).length

  return (
    <div className="glass-card p-6 rounded-2xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
            <Filter className="w-4 h-4 text-white" strokeWidth={2} />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">Filtres de recherche</h3>
            {activeFiltersCount > 0 && (
              <p className="text-xs text-gradient font-medium">{activeFiltersCount} filtre{activeFiltersCount > 1 ? 's' : ''} actif{activeFiltersCount > 1 ? 's' : ''}</p>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className={`p-2 rounded-lg transition-all ${showAdvanced ? 'bg-blue-100 text-blue-600' : 'glass-card hover:bg-blue-50'}`}
          >
            <Settings className="w-4 h-4" strokeWidth={2} />
          </button>
          {activeFiltersCount > 0 && (
            <button
              onClick={resetFilters}
              className="p-2 glass-card rounded-lg hover:bg-red-50 transition-all"
              title="Réinitialiser les filtres"
            >
              <RotateCcw className="w-4 h-4 text-gray-600" strokeWidth={2} />
            </button>
          )}
        </div>
      </div>

      <div className="space-y-6">
        {/* Price Range */}
        <div>
          <label className="block text-sm font-bold text-gray-900 mb-3 flex items-center">
            <DollarSign className="w-4 h-4 text-green-500 mr-2" strokeWidth={2} />
            Prix: <span className="text-gradient ml-2">{formatPrice(minPrice)} - {formatPrice(maxPrice)}</span>
          </label>
          <div className="space-y-3">
            <div className="relative">
              <input
                type="range"
                min="0"
                max="100000"
                step="1000"
                value={minPrice}
                onChange={(e) => setMinPrice(Math.min(Number(e.target.value), maxPrice - 1000))}
                className="slider-modern w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1 font-medium">
                <span>Min: {formatPrice(minPrice)}</span>
                <span>0€ - 100 000€</span>
              </div>
            </div>
            <div className="relative">
              <input
                type="range"
                min="0"
                max="100000"
                step="1000"
                value={maxPrice}
                onChange={(e) => setMaxPrice(Math.max(Number(e.target.value), minPrice + 1000))}
                className="slider-modern w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1 font-medium">
                <span>Max: {formatPrice(maxPrice)}</span>
                <span>0€ - 100 000€</span>
              </div>
            </div>
          </div>
        </div>

        {/* Department */}
        <div>
          <label className="block text-sm font-bold text-gray-900 mb-3 flex items-center">
            <MapPin className="w-4 h-4 text-blue-500 mr-2" strokeWidth={2} />
            Département
          </label>
          <select
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            className="input-modern w-full"
          >
            {FRENCH_DEPARTMENTS.map((dept) => (
              <option key={dept.code} value={dept.code}>
                {dept.code && `${dept.code} - `}{dept.name}
              </option>
            ))}
          </select>
        </div>

        {/* Advanced Filters */}
        {showAdvanced && (
          <div className="space-y-6 border-t pt-6">
            {/* Year Range */}
            <div>
              <label className="block text-sm font-bold text-gray-900 mb-3 flex items-center">
                <Calendar className="w-4 h-4 text-blue-500 mr-2" strokeWidth={2} />
                Année: <span className="text-gradient ml-2">{minYear} - {maxYear}</span>
              </label>
              <div className="space-y-3">
                <div className="relative">
                  <input
                    type="range"
                    min="1990"
                    max={new Date().getFullYear()}
                    step="1"
                    value={minYear}
                    onChange={(e) => setMinYear(Math.min(Number(e.target.value), maxYear - 1))}
                    className="slider-modern w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1 font-medium">
                    <span>Min: {minYear}</span>
                    <span>1990 - {new Date().getFullYear()}</span>
                  </div>
                </div>
                <div className="relative">
                  <input
                    type="range"
                    min="1990"
                    max={new Date().getFullYear()}
                    step="1"
                    value={maxYear}
                    onChange={(e) => setMaxYear(Math.max(Number(e.target.value), minYear + 1))}
                    className="slider-modern w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1 font-medium">
                    <span>Max: {maxYear}</span>
                    <span>1990 - {new Date().getFullYear()}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Mileage Range */}
            <div>
              <label className="block text-sm font-bold text-gray-900 mb-3 flex items-center">
                <Gauge className="w-4 h-4 text-green-500 mr-2" strokeWidth={2} />
                Kilométrage: <span className="text-gradient ml-2">{formatMileage(minMileage)} - {formatMileage(maxMileage)}</span>
              </label>
              <div className="space-y-3">
                <div className="relative">
                  <input
                    type="range"
                    min="0"
                    max="300000"
                    step="5000"
                    value={minMileage}
                    onChange={(e) => setMinMileage(Math.min(Number(e.target.value), maxMileage - 5000))}
                    className="slider-modern w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1 font-medium">
                    <span>Min: {formatMileage(minMileage)}</span>
                    <span>0 - 300 000 km</span>
                  </div>
                </div>
                <div className="relative">
                  <input
                    type="range"
                    min="0"
                    max="300000"
                    step="5000"
                    value={maxMileage}
                    onChange={(e) => setMaxMileage(Math.max(Number(e.target.value), minMileage + 5000))}
                    className="slider-modern w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1 font-medium">
                    <span>Max: {formatMileage(maxMileage)}</span>
                    <span>0 - 300 000 km</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Fuel Types */}
            <div>
              <label className="block text-sm font-bold text-gray-900 mb-3 flex items-center">
                <Fuel className="w-4 h-4 text-orange-500 mr-2" strokeWidth={2} />
                Types de carburant
                {selectedFuelTypes.length > 0 && (
                  <span className="ml-2 px-2 py-1 bg-gradient-primary/10 text-gradient text-xs rounded-full font-bold">
                    {selectedFuelTypes.length}
                  </span>
                )}
              </label>
              <div className="grid grid-cols-2 gap-2">
                {FUEL_TYPES.map((fuel) => (
                  <button
                    key={fuel.value}
                    onClick={() => toggleFuelType(fuel.value)}
                    className={`p-3 rounded-xl text-left transition-all ${
                      selectedFuelTypes.includes(fuel.value)
                        ? 'bg-gradient-primary text-white shadow-lg'
                        : 'glass-card hover:bg-white/50'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <div className={`w-3 h-3 rounded-full ${fuel.color}`}></div>
                      <span className="text-sm font-medium">{fuel.label}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Seller Types */}
            <div>
              <label className="block text-sm font-bold text-gray-900 mb-3">
                Types de vendeurs
                {selectedSellerTypes.length > 0 && (
                  <span className="ml-2 px-2 py-1 bg-gradient-secondary/10 text-gradient-secondary text-xs rounded-full font-bold">
                    {selectedSellerTypes.length}
                  </span>
                )}
              </label>
              <div className="grid grid-cols-2 gap-2">
                {SELLER_TYPES.map((seller) => (
                  <button
                    key={seller.value}
                    onClick={() => toggleSellerType(seller.value)}
                    className={`p-3 rounded-xl text-left transition-all ${
                      selectedSellerTypes.includes(seller.value)
                        ? 'bg-gradient-secondary text-white shadow-lg'
                        : 'glass-card hover:bg-white/50'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{seller.icon}</span>
                      <span className="text-sm font-medium">{seller.label}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}