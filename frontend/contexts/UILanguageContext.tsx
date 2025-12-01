import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import i18n from '../i18n';

export type UILanguage = 'en' | 'th' | 'es' | 'fr' | 'de' | 'zh' | 'ja' | 'ko' | 'ar' | 'hi' | 'pt' | 'ru' | 'it' | 'vi';

interface UILanguageContextType {
  uiLanguage: UILanguage;
  setUILanguage: (lang: UILanguage) => Promise<void>;
  isLoading: boolean;
}

const UILanguageContext = createContext<UILanguageContextType | undefined>(undefined);

export function UILanguageProvider({ children }: { children: ReactNode }) {
  const [uiLanguage, setUILanguageState] = useState<UILanguage>('en');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadUILanguage();
  }, []);

  const loadUILanguage = async () => {
    try {
      const savedLang = await AsyncStorage.getItem('uiLanguage');
      if (savedLang) {
        setUILanguageState(savedLang as UILanguage);
        i18n.locale = savedLang;
      }
    } catch (error) {
      console.error('Error loading UI language:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const setUILanguage = async (lang: UILanguage) => {
    try {
      await AsyncStorage.setItem('uiLanguage', lang);
      i18n.locale = lang;
      setUILanguageState(lang); // This triggers re-render in components using uiLanguage
    } catch (error) {
      console.error('Error saving UI language:', error);
    }
  };

  return (
    <UILanguageContext.Provider value={{ uiLanguage, setUILanguage, isLoading }}>
      {children}
    </UILanguageContext.Provider>
  );
}

export function useUILanguage() {
  const context = useContext(UILanguageContext);
  if (!context) {
    throw new Error('useUILanguage must be used within UILanguageProvider');
  }
  return context;
}
