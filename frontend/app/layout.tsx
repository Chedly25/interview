import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Assistant Automobile Français',
  description: 'Trouvez et analysez les meilleures voitures d\'occasion avec l\'IA',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="fr" className="h-full">
      <body className={`${inter.className} h-full bg-gray-50 dark:bg-gray-900`}>
        <div className="min-h-full">
          <nav className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                      🚗 Assistant Automobile
                    </h1>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <button className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                    🌙
                  </button>
                </div>
              </div>
            </div>
          </nav>
          <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}