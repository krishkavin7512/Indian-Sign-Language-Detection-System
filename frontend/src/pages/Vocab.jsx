import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, BookMarked } from 'lucide-react'
import { getVocabulary } from '../services/api'
import { useRecognitionStore } from '../store/recognitionStore'
import en from '../translations/en'
import hi from '../translations/hi'

export default function Vocab() {
  const [search, setSearch] = useState('')
  const language = useRecognitionStore(s => s.language)
  const t = language === 'hi' ? hi : en

  const { data, isLoading } = useQuery({
    queryKey: ['vocab', search],
    queryFn: () => getVocabulary({ search: search || undefined, limit: 263 }),
    staleTime: 60000,
  })

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">{t.vocab.title}</h1>
        <p className="text-slate-400 text-sm mt-1">{t.vocab.subtitle}</p>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          placeholder={t.vocab.search}
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-4 py-2.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
        />
      </div>

      {/* Stats */}
      {data && (
        <p className="text-sm text-slate-400 mb-4">
          {t.vocab.total}: <span className="text-slate-200 font-medium">{data.total}</span>
        </p>
      )}

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-7 gap-2">
          {Array.from({ length: 35 }).map((_, i) => (
            <div key={i} className="h-12 bg-slate-800 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-7 gap-2">
          {data?.words?.map(word => (
            <div
              key={word.id}
              className="card px-2 py-3 text-center hover:border-blue-500/50 transition-colors cursor-default"
            >
              <span className="text-sm font-medium text-slate-200">{word.label}</span>
            </div>
          ))}
        </div>
      )}

      {!isLoading && !data?.words?.length && (
        <div className="text-center py-16 text-slate-500">
          <BookMarked className="w-10 h-10 mx-auto mb-3 opacity-50" />
          <p>No signs found. Train the dynamic model first.</p>
        </div>
      )}
    </div>
  )
}
