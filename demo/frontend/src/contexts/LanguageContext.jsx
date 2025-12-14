import React, { createContext, useContext, useState, useCallback } from 'react'
import { translations } from '../i18n/translations'

const LanguageContext = createContext()

export const LANGUAGES = {
    zh: '中文',
    en: 'English'
}

export function LanguageProvider({ children }) {
    const [language, setLanguage] = useState('zh') // Default to Chinese

    const toggleLanguage = useCallback(() => {
        setLanguage(prev => prev === 'zh' ? 'en' : 'zh')
    }, [])

    const t = useCallback((key) => {
        const keys = key.split('.')
        let value = translations[language]

        for (const k of keys) {
            if (value && typeof value === 'object') {
                value = value[k]
            } else {
                return key // Return the key if translation not found
            }
        }

        return value || key
    }, [language])

    return (
        <LanguageContext.Provider value={{ language, setLanguage, toggleLanguage, t }}>
            {children}
        </LanguageContext.Provider>
    )
}

export function useLanguage() {
    const context = useContext(LanguageContext)
    if (!context) {
        throw new Error('useLanguage must be used within a LanguageProvider')
    }
    return context
}

export default LanguageContext

