'use client'

interface AnalysisData {
  price_assessment: string
  red_flags: string[]
  negotiation_tips: string[]
  overall_score: number
  recommendation: string
}

interface ClaudeAnalysisProps {
  analysis: AnalysisData | null
  isLoading: boolean
  onAnalyze: () => void
}

export default function ClaudeAnalysis({ analysis, isLoading, onAnalyze }: ClaudeAnalysisProps) {
  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-600 dark:text-green-400'
    if (score >= 6) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const getScoreBackground = (score: number) => {
    if (score >= 8) return 'bg-green-100 dark:bg-green-900'
    if (score >= 6) return 'bg-yellow-100 dark:bg-yellow-900'
    return 'bg-red-100 dark:bg-red-900'
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Analyse IA Claude
        </h2>
        <button
          onClick={onAnalyze}
          disabled={isLoading}
          className="bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white px-4 py-2 rounded-md transition-colors"
        >
          {isLoading ? 'Analyse en cours...' : 'Analyser avec Claude'}
        </button>
      </div>

      {analysis && (
        <div className="space-y-6">
          <div className="flex items-center space-x-4">
            <div className={`px-4 py-2 rounded-full ${getScoreBackground(analysis.overall_score)}`}>
              <span className={`text-lg font-bold ${getScoreColor(analysis.overall_score)}`}>
                {analysis.overall_score}/10
              </span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">Note globale</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">{analysis.recommendation}</p>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Évaluation du prix
            </h3>
            <p className="text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 p-3 rounded-md">
              {analysis.price_assessment}
            </p>
          </div>

          {analysis.red_flags && analysis.red_flags.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-red-600 dark:text-red-400 mb-2">
                ⚠️ Signaux d'alarme
              </h3>
              <ul className="space-y-2">
                {analysis.red_flags.map((flag, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <span className="text-red-500 mt-1">•</span>
                    <span className="text-gray-700 dark:text-gray-300">{flag}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {analysis.negotiation_tips && analysis.negotiation_tips.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-green-600 dark:text-green-400 mb-2">
                💡 Conseils de négociation
              </h3>
              <ul className="space-y-2">
                {analysis.negotiation_tips.map((tip, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <span className="text-green-500 mt-1">•</span>
                    <span className="text-gray-700 dark:text-gray-300">{tip}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {!analysis && !isLoading && (
        <div className="text-center py-8">
          <div className="text-gray-400 dark:text-gray-500 mb-4">
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Aucune analyse disponible pour cette voiture
          </p>
          <p className="text-sm text-gray-400 dark:text-gray-500">
            Cliquez sur "Analyser avec Claude" pour obtenir une évaluation détaillée
          </p>
        </div>
      )}
    </div>
  )
}