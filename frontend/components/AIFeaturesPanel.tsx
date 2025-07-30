'use client'

import { useState } from 'react'
import { 
  SparklesIcon, 
  CameraIcon, 
  DocumentTextIcon, 
  ChatBubbleLeftRightIcon,
  IdentificationIcon,
  TrendingUpIcon,
  HeartIcon,
  ScaleIcon,
  WrenchScrewdriverIcon,
  TrophyIcon
} from '@heroicons/react/24/outline'

interface AIFeaturesPanelProps {
  carId: string
}

interface FeatureData {
  [key: string]: any
}

const AI_FEATURES = [
  {
    id: 'gem',
    name: 'Détecteur de Pépites',
    icon: SparklesIcon,
    endpoint: 'gem-score',
    description: 'Identifie les bonnes affaires cachées',
    color: 'bg-yellow-500'
  },
  {
    id: 'photo',
    name: 'Analyse Photos IA',
    icon: CameraIcon,
    endpoint: 'photo-analysis',
    description: 'Analyse visuelle des dommages et équipements',
    color: 'bg-blue-500'
  },
  {
    id: 'description',
    name: 'Parser Intelligent',
    icon: DocumentTextIcon,
    endpoint: 'description-analysis',
    description: 'Analyse intelligente de la description',
    color: 'bg-green-500'
  },
  {
    id: 'negotiation',
    name: 'Assistant Négociation',
    icon: ChatBubbleLeftRightIcon,
    endpoint: 'negotiation-strategy',
    description: 'Stratégies de négociation personnalisées',
    color: 'bg-purple-500'
  },
  {
    id: 'vin',
    name: 'Décodeur VIN',
    icon: IdentificationIcon,
    endpoint: 'vin-analysis',
    description: 'Historique et analyse VIN complète',
    color: 'bg-indigo-500'
  },
  {
    id: 'market',
    name: 'Prédicteur Marché',
    icon: TrendingUpIcon,
    endpoint: 'market-pulse',
    description: 'Prédictions de prix et tendances',
    color: 'bg-red-500'
  },
  {
    id: 'sentiment',
    name: 'Analyse Sentiment',
    icon: HeartIcon,
    endpoint: 'social-sentiment',
    description: 'Sentiment social et réputation',
    color: 'bg-pink-500'
  },
  {
    id: 'comparison',
    name: 'Comparateur Intelligent',
    icon: ScaleIcon,
    endpoint: 'smart-comparison',
    description: 'Comparaison avec véhicules similaires',
    color: 'bg-teal-500'
  },
  {
    id: 'maintenance',
    name: 'Prophète Maintenance',
    icon: WrenchScrewdriverIcon,
    endpoint: 'maintenance-prediction',
    description: 'Prédiction des coûts de maintenance',
    color: 'bg-orange-500'
  },
  {
    id: 'investment',
    name: 'Score Investissement',
    icon: TrophyIcon,
    endpoint: 'investment-grade',
    description: 'Potentiel d\'investissement et appréciation',
    color: 'bg-amber-500'
  }
]

export default function AIFeaturesPanel({ carId }: AIFeaturesPanelProps) {
  const [activeFeature, setActiveFeature] = useState<string | null>(null)
  const [featuresData, setFeaturesData] = useState<{[key: string]: FeatureData}>({})
  const [loadingFeatures, setLoadingFeatures] = useState<{[key: string]: boolean}>({})

  const triggerFeatureAnalysis = async (feature: typeof AI_FEATURES[0]) => {
    setLoadingFeatures(prev => ({ ...prev, [feature.id]: true }))
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/cars/${carId}/${feature.endpoint}`, {
        method: 'POST'
      })
      
      if (response.ok) {
        const data = await response.json()
        setFeaturesData(prev => ({ ...prev, [feature.id]: data }))
        setActiveFeature(feature.id)
      } else {
        console.error(`Failed to analyze ${feature.name}`)
      }
    } catch (error) {
      console.error(`Error analyzing ${feature.name}:`, error)
    } finally {
      setLoadingFeatures(prev => ({ ...prev, [feature.id]: false }))
    }
  }

  const triggerFullAnalysis = async () => {
    setLoadingFeatures({ full: true })
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/cars/${carId}/full-ai-analysis`, {
        method: 'POST'
      })
      
      if (response.ok) {
        // Refresh all feature data after full analysis
        setTimeout(async () => {
          for (const feature of AI_FEATURES) {
            try {
              const featureResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/cars/${carId}/${feature.endpoint}-insights`)
              if (featureResponse.ok) {
                const data = await featureResponse.json()
                setFeaturesData(prev => ({ ...prev, [feature.id]: data }))
              }
            } catch (error) {
              console.error(`Error fetching ${feature.name} insights:`, error)
            }
          }
        }, 3000) // Wait 3 seconds for processing
      }
    } catch (error) {
      console.error('Error running full analysis:', error)
    } finally {
      setLoadingFeatures({ full: false })
    }
  }

  const renderFeatureContent = (feature: typeof AI_FEATURES[0]) => {
    const data = featuresData[feature.id]
    if (!data) return null

    switch (feature.id) {
      case 'gem':
        return (
          <div className="space-y-4">
            <div className="text-center">
              <div className="text-4xl font-bold text-yellow-600">
                {data.gem_score}/100
              </div>
              <div className="text-sm text-gray-600">Score Pépite</div>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Raisons:</h4>
              <ul className="list-disc list-inside space-y-1">
                {(data.reasons || []).map((reason: string, idx: number) => (
                  <li key={idx} className="text-sm">{reason}</li>
                ))}
              </ul>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium">Potentiel profit:</span>
                <span className="ml-2">{data.profit_potential}€</span>
              </div>
              <div>
                <span className="font-medium">Confiance:</span>
                <span className="ml-2">{Math.round((data.confidence_level || 0) * 100)}%</span>
              </div>
            </div>
          </div>
        )

      case 'photo':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {data.overall_condition_score}/10
                </div>
                <div className="text-sm text-gray-600">État général</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {data.honesty_score}/10
                </div>
                <div className="text-sm text-gray-600">Honnêteté photos</div>
              </div>
            </div>
            
            {data.detected_damage && data.detected_damage.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2 text-red-600">Dommages détectés:</h4>
                <ul className="list-disc list-inside space-y-1">
                  {data.detected_damage.map((damage: string, idx: number) => (
                    <li key={idx} className="text-sm">{damage}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {data.detected_features && data.detected_features.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2 text-green-600">Équipements détectés:</h4>
                <ul className="list-disc list-inside space-y-1">
                  {data.detected_features.map((feature: string, idx: number) => (
                    <li key={idx} className="text-sm">{feature}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {data.estimated_repair_costs && (
              <div className="bg-gray-50 p-3 rounded">
                <h4 className="font-semibold mb-2">Coûts de réparation estimés:</h4>
                <div className="text-lg font-bold text-red-600">
                  {data.estimated_repair_costs.total_estimated}€
                </div>
              </div>
            )}
          </div>
        )

      case 'description':
        return (
          <div className="space-y-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {data.seller_credibility}%
              </div>
              <div className="text-sm text-gray-600">Crédibilité vendeur</div>
            </div>
            
            {data.detected_options && data.detected_options.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">Options détectées:</h4>
                <div className="flex flex-wrap gap-2">
                  {data.detected_options.map((option: string, idx: number) => (
                    <span key={idx} className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">
                      {option}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {data.red_flags && data.red_flags.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2 text-red-600">Signaux d'alarme:</h4>
                <ul className="list-disc list-inside space-y-1">
                  {data.red_flags.map((flag: any, idx: number) => (
                    <li key={idx} className="text-sm">{flag.type}: {flag.context}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {data.positive_signals && data.positive_signals.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2 text-green-600">Signaux positifs:</h4>
                <div className="flex flex-wrap gap-2">
                  {data.positive_signals.map((signal: string, idx: number) => (
                    <span key={idx} className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">
                      {signal}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )

      case 'negotiation':
        return (
          <div className="space-y-4">
            {data.recommended_approach && (
              <div className="bg-purple-50 p-4 rounded">
                <h4 className="font-semibold mb-2">Approche recommandée:</h4>
                <p className="text-sm">{data.recommended_approach}</p>
              </div>
            )}
            
            {data.price_points && (
              <div>
                <h4 className="font-semibold mb-2">Points de prix:</h4>
                <div className="grid grid-cols-3 gap-2 text-sm">
                  <div className="text-center">
                    <div className="font-bold text-green-600">{data.price_points.opening_offer}€</div>
                    <div className="text-xs">Offre initiale</div>
                  </div>
                  <div className="text-center">
                    <div className="font-bold text-blue-600">{data.price_points.target_price}€</div>
                    <div className="text-xs">Prix cible</div>
                  </div>
                  <div className="text-center">
                    <div className="font-bold text-red-600">{data.price_points.walk_away}€</div>
                    <div className="text-xs">Prix limite</div>
                  </div>
                </div>
              </div>
            )}
            
            {data.negotiation_scripts && data.negotiation_scripts.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">Scripts de négociation:</h4>
                <div className="space-y-2">
                  {data.negotiation_scripts.map((script: any, idx: number) => (
                    <div key={idx} className="bg-gray-50 p-3 rounded">
                      <div className="font-medium text-sm">{script.phase}:</div>
                      <div className="text-sm text-gray-700">{script.script}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )

      case 'investment':
        return (
          <div className="space-y-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-amber-600">
                {data.investment_grade}
              </div>
              <div className="text-sm text-gray-600">Grade d'investissement</div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium">Appréciation:</span>
                <span className="ml-2">{data.appreciation_potential}%</span>
              </div>
              <div>
                <span className="font-medium">Liquidité:</span>
                <span className="ml-2">{data.liquidity_score}/10</span>
              </div>
            </div>
            
            {data.hold_recommendation && (
              <div className="bg-amber-50 p-3 rounded">
                <h4 className="font-semibold mb-1">Recommandation:</h4>
                <p className="text-sm capitalize">{data.hold_recommendation} terme</p>
              </div>
            )}
          </div>
        )

      default:
        return (
          <div className="text-center text-gray-500">
            <p>Données disponibles pour {feature.name}</p>
            <pre className="text-xs mt-2 bg-gray-100 p-2 rounded overflow-auto max-h-40">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        )
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          🤖 Analyse IA Complète
        </h2>
        <button
          onClick={triggerFullAnalysis}
          disabled={loadingFeatures.full}
          className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-medium py-2 px-4 rounded-md transition-all disabled:opacity-50"
        >
          {loadingFeatures.full ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white inline-block mr-2"></div>
              Analyse en cours...
            </>
          ) : (
            '🚀 Analyse Complète'
          )}
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        {AI_FEATURES.map((feature) => {
          const IconComponent = feature.icon
          const isLoading = loadingFeatures[feature.id]
          const hasData = featuresData[feature.id]
          
          return (
            <button
              key={feature.id}
              onClick={() => hasData ? setActiveFeature(feature.id) : triggerFeatureAnalysis(feature)}
              disabled={isLoading}
              className={`relative p-3 rounded-lg border-2 transition-all text-center ${
                activeFeature === feature.id
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'
              } ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              {hasData && (
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full"></div>
              )}
              
              <div className={`w-8 h-8 ${feature.color} rounded-lg flex items-center justify-center mx-auto mb-2`}>
                {isLoading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  <IconComponent className="w-4 h-4 text-white" />
                )}
              </div>
              
              <div className="text-xs font-medium text-gray-900 dark:text-white">
                {feature.name}
              </div>
            </button>
          )
        })}
      </div>

      {activeFeature && (
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
          <div className="flex items-center mb-4">
            {(() => {
              const feature = AI_FEATURES.find(f => f.id === activeFeature)
              if (!feature) return null
              const IconComponent = feature.icon
              return (
                <>
                  <div className={`w-8 h-8 ${feature.color} rounded-lg flex items-center justify-center mr-3`}>
                    <IconComponent className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {feature.name}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {feature.description}
                    </p>
                  </div>
                </>
              )
            })()}
          </div>
          
          {(() => {
            const feature = AI_FEATURES.find(f => f.id === activeFeature)
            return feature ? renderFeatureContent(feature) : null
          })()}
        </div>
      )}
    </div>
  )
}