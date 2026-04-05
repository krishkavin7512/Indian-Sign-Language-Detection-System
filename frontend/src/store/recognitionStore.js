import { create } from 'zustand'

export const useRecognitionStore = create((set, get) => ({
  // Current prediction
  prediction: null,
  confidence: 0,
  landmarks: null,
  modelUsed: null,
  alternatives: [],

  // Session
  history: [],
  sentence: [],
  isConnected: false,
  isStreaming: false,
  mode: 'auto',

  // Language
  language: 'en',  // 'en' | 'hi'

  // Actions
  setPrediction: (result) => set({
    prediction: result,
    confidence: result?.confidence ?? 0,
    modelUsed: result?.model_used ?? null,
    alternatives: result?.alternatives ?? [],
  }),

  addToHistory: (item) => set((state) => ({
    history: [{ ...item, id: Date.now() }, ...state.history].slice(0, 50),
  })),

  addToSentence: (word) => set((state) => {
    const last = state.sentence[state.sentence.length - 1]
    if (last === word) return {}  // deduplicate consecutive
    return { sentence: [...state.sentence, word] }
  }),

  clearSentence: () => set({ sentence: [] }),
  clearHistory: () => set({ history: [] }),

  setLandmarks: (data) => set({ landmarks: data }),
  setConnected: (v) => set({ isConnected: v }),
  setStreaming: (v) => set({ isStreaming: v }),
  setMode: (m) => set({ mode: m }),
  toggleLanguage: () => set((state) => ({
    language: state.language === 'en' ? 'hi' : 'en',
  })),
}))
