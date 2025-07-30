'use client'

import { useState } from 'react'
import { 
  Sparkles, 
  Camera, 
  FileText, 
  MessageSquare,
  CreditCard,
  TrendingUp,
  Heart,
  Scale,
  Wrench,
  Trophy,
  Brain,
  CheckCircle,
  AlertTriangle,
  DollarSign,
  Cpu
} from 'lucide-react'

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
    icon: Sparkles,
    endpoint: 'gem-score',
    description: 'Identifie les bonnes affaires cachées',
    color: 'bg-yellow-500'
  },
  {
    id: 'photo',
    name: 'Analyse Photos IA',
    icon: Camera,
    endpoint: 'photo-analysis',
    description: 'Analyse visuelle des dommages et équipements',
    color: 'bg-blue-500'
  },
  {
    id: 'description',
    name: 'Parser Intelligent',
    icon: FileText,
    endpoint: 'description-analysis',
    description: 'Analyse intelligente de la description',
    color: 'bg-green-500'
  },
  {
    id: 'negotiation',
    name: 'Assistant Négociation',
    icon: MessageSquare,
    endpoint: 'negotiation-strategy',
    description: 'Stratégies de négociation personnalisées',
    color: 'bg-purple-500'
  },
  {
    id: 'vin',
    name: 'Décodeur VIN',
    icon: CreditCard,
    endpoint: 'vin-analysis',
    description: 'Historique et analyse VIN complète',
    color: 'bg-indigo-500'
  },
  {
    id: 'market',
    name: 'Prédicteur Marché',
    icon: TrendingUp,
    endpoint: 'market-pulse',
    description: 'Prédictions de prix et tendances',
    color: 'bg-red-500'
  },
  {
    id: 'sentiment',
    name: 'Analyse Sentiment',
    icon: Heart,
    endpoint: 'social-sentiment',
    description: 'Sentiment social et réputation',
    color: 'bg-pink-500'
  },
  {
    id: 'comparison',
    name: 'Comparateur Intelligent',
    icon: Scale,
    endpoint: 'smart-comparison',
    description: 'Comparaison avec véhicules similaires',
    color: 'bg-teal-500'
  },
  {
    id: 'maintenance',
    name: 'Prophète Maintenance',
    icon: Wrench,
    endpoint: 'maintenance-prediction',
    description: 'Prédiction des coûts de maintenance',
    color: 'bg-orange-500'
  },
  {
    id: 'investment',
    name: 'Score Investissement',
    icon: Trophy,
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
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://interview-production-84f1.up.railway.app'
      const fullUrl = `${apiUrl}/api/cars/${carId}/${feature.endpoint}`
      
      console.log(`Triggering ${feature.name} analysis:`, fullUrl)
      
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })
      
      console.log(`${feature.name} response status:`, response.status)
      
      if (response.ok) {
        const data = await response.json()
        console.log(`${feature.name} data:`, data)
        setFeaturesData(prev => ({ ...prev, [feature.id]: data }))
        setActiveFeature(feature.id)
      } else {
        const errorText = await response.text()
        console.error(`Failed to analyze ${feature.name}:`, response.status, errorText)
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
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://interview-production-84f1.up.railway.app'
      const fullUrl = `${apiUrl}/api/cars/${carId}/full-ai-analysis`
      
      console.log('Triggering full AI analysis:', fullUrl)
      
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })
      
      console.log('Full analysis response status:', response.status)
      
      if (response.ok) {
        const result = await response.json()
        console.log('Full analysis result:', result)
        
        // Refresh all feature data after full analysis
        setTimeout(async () => {
          for (const feature of AI_FEATURES) {
            try {
              const featureResponse = await fetch(`${apiUrl}/api/cars/${carId}/${feature.endpoint}-insights`)
              if (featureResponse.ok) {
                const data = await featureResponse.json()
                setFeaturesData(prev => ({ ...prev, [feature.id]: data }))
              }
            } catch (error) {
              console.error(`Error fetching ${feature.name} insights:`, error)
            }
          }
        }, 3000) // Wait 3 seconds for processing
      } else {
        const errorText = await response.text()
        console.error('Failed to run full analysis:', response.status, errorText)
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
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-24 h-24 bg-gradient-warning rounded-full flex items-center justify-center mx-auto mb-4">
                <div className="text-3xl font-black text-white">
                  {data.gem_score}
                </div>
              </div>
              <div className="text-lg font-bold text-gradient">Score Pépite: {data.gem_score}/100</div>
            </div>
            <div className="glass-card p-4 rounded-xl">
              <h4 className="font-bold mb-3 text-gray-900 flex items-center">
                <Sparkles className="w-4 h-4 text-yellow-500 mr-2" strokeWidth={2} /> Raisons:
              </h4>
              <div className="space-y-2">
                {(data.reasons || []).map((reason: string, idx: number) => (
                  <div key={idx} className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-gradient-warning rounded-full mt-2 flex-shrink-0"></div>
                    <span className="text-sm text-gray-700">{reason}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="glass-card p-4 rounded-xl text-center">
                <div className="text-2xl font-bold text-gradient mb-1">{data.profit_potential}€</div>
                <div className="text-sm text-gray-600 font-medium">Potentiel profit</div>
              </div>
              <div className="glass-card p-4 rounded-xl text-center">
                <div className="text-2xl font-bold text-gradient mb-1">{Math.round((data.confidence_level || 0) * 100)}%</div>
                <div className="text-sm text-gray-600 font-medium">Confiance</div>
              </div>
            </div>
          </div>
        )

      case 'photo':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="glass-card p-4 rounded-xl text-center">
                <div className="w-16 h-16 bg-gradient-primary rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-xl font-black text-white">{data.overall_condition_score}</span>
                </div>
                <div className="text-sm text-gray-600 font-medium">État général /10</div>
              </div>
              <div className="glass-card p-4 rounded-xl text-center">
                <div className="w-16 h-16 bg-gradient-success rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-xl font-black text-white">{data.honesty_score}</span>
                </div>
                <div className="text-sm text-gray-600 font-medium">Honnêteté photos /10</div>
              </div>
            </div>
            
            {data.detected_damage && data.detected_damage.length > 0 && (
              <div className="glass-card p-4 rounded-xl border-l-4 border-red-500">
                <h4 className="font-bold mb-3 text-red-600 flex items-center">
                  <AlertTriangle className="w-4 h-4 text-red-500 mr-2" strokeWidth={2} /> Dommages détectés:
                </h4>
                <div className="space-y-2">
                  {data.detected_damage.map((damage: string, idx: number) => (
                    <div key={idx} className="flex items-start space-x-2">
                      <div className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                      <span className="text-sm text-gray-700">{damage}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {data.detected_features && data.detected_features.length > 0 && (
              <div className="glass-card p-4 rounded-xl border-l-4 border-green-500">
                <h4 className="font-bold mb-3 text-green-600 flex items-center">
                  <CheckCircle className="w-4 h-4 text-green-500 mr-2" strokeWidth={2} /> Équipements détectés:
                </h4>
                <div className="flex flex-wrap gap-2">
                  {data.detected_features.map((feature: string, idx: number) => (
                    <span key={idx} className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
                      {feature}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {data.estimated_repair_costs && (
              <div className="glass-card p-4 rounded-xl bg-red-50/50">
                <h4 className="font-bold mb-3 text-red-600 flex items-center">
                  <DollarSign className="w-4 h-4 text-red-500 mr-2" strokeWidth={2} /> Coûts de réparation estimés:
                </h4>
                <div className="text-center">
                  <div className="text-3xl font-black text-gradient-secondary mb-1">
                    {data.estimated_repair_costs.total_estimated}€
                  </div>
                  <div className="text-sm text-gray-600">Estimation totale</div>
                </div>
              </div>
            )}
          </div>
        )

      case 'description':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-20 h-20 bg-gradient-success rounded-full flex items-center justify-center mx-auto mb-4">
                <div className="text-2xl font-black text-white">
                  {data.seller_credibility}%
                </div>
              </div>
              <div className="text-lg font-bold text-gradient">Crédibilité vendeur</div>
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
    <div className="glass-card rounded-2xl p-8 fade-in">
      <div className="flex justify-between items-center mb-8">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-gradient-ai rounded-2xl flex items-center justify-center float">
            <Brain className="w-6 h-6 text-white" strokeWidth={2} />
          </div>
          <div>
            <h2 className="text-3xl font-black text-gradient mb-1">
              Analyse IA Complète
            </h2>
            <p className="text-gray-600 font-medium">Intelligence artificielle avancée • 10 fonctionnalités</p>
          </div>
        </div>
        <button
          onClick={triggerFullAnalysis}
          disabled={loadingFeatures.full}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loadingFeatures.full ? (
            <>
              <div className="loading-spinner inline-block mr-2"></div>
              Analyse en cours...
            </>
          ) : (
            <>
              <Cpu className="w-4 h-4 mr-2" strokeWidth={2} />
              Analyse Complète
            </>
          )}
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        {AI_FEATURES.map((feature, index) => {
          const IconComponent = feature.icon
          const isLoading = loadingFeatures[feature.id]
          const hasData = featuresData[feature.id]
          
          return (
            <button
              key={feature.id}
              onClick={() => hasData ? setActiveFeature(feature.id) : triggerFeatureAnalysis(feature)}
              disabled={isLoading}
              className={`relative glass-card p-4 rounded-2xl transition-all text-center scale-in card-hover group ${
                activeFeature === feature.id
                  ? 'ring-2 ring-blue-500 bg-blue-50/80'
                  : ''
              } ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
              style={{animationDelay: `${index * 0.1}s`}}
            >
              {hasData && (
                <div className="absolute -top-2 -right-2 w-6 h-6 bg-gradient-success rounded-full flex items-center justify-center pulse-glow">
                  <CheckCircle className="w-3 h-3 text-white" strokeWidth={2} />
                </div>
              )}
              
              <div className={`w-12 h-12 bg-gradient-primary rounded-2xl flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform`}>
                {isLoading ? (
                  <div className="loading-spinner"></div>
                ) : (
                  <IconComponent className="w-6 h-6 text-white" />
                )}
              </div>
              
              <div className="text-sm font-bold text-gray-900 mb-1">
                {feature.name}
              </div>
              <div className="text-xs text-gray-600 leading-tight">
                {feature.description}
              </div>
            </button>
          )
        })}
      </div>

      {activeFeature && (
        <div className="glass-card rounded-2xl p-8 slide-up">
          <div className="flex items-center mb-6">
            {(() => {
              const feature = AI_FEATURES.find(f => f.id === activeFeature)
              if (!feature) return null
              const IconComponent = feature.icon
              return (
                <>
                  <div className={`w-16 h-16 bg-gradient-primary rounded-2xl flex items-center justify-center mr-4 float`}>
                    <IconComponent className="w-8 h-8 text-white" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-gradient mb-2">
                      {feature.name}
                    </h3>
                    <p className="text-gray-600 font-medium">
                      {feature.description}
                    </p>
                  </div>
                </>
              )
            })()}
          </div>
          
          <div className="bg-white/50 rounded-2xl p-6">
            {(() => {
              const feature = AI_FEATURES.find(f => f.id === activeFeature)
              return feature ? renderFeatureContent(feature) : null
            })()}
          </div>
        </div>
      )}
    </div>
  )
}