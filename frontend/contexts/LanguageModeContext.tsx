import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export type LanguageMode = 'learn-thai' | 'learn-english';

interface LanguageModeContextType {
  languageMode: LanguageMode | null;
  setLanguageMode: (mode: LanguageMode) => Promise<void>;
  isLoading: boolean;
}

const LanguageModeContext = createContext<LanguageModeContextType | undefined>(undefined);

export function LanguageModeProvider({ children }: { children: ReactNode }) {
  const [languageMode, setLanguageModeState] = useState<LanguageMode | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadLanguageMode();
  }, []);

  const loadLanguageMode = async () => {
    try {
      const savedMode = await AsyncStorage.getItem('languageMode');
      if (savedMode === 'learn-thai' || savedMode === 'learn-english') {
        setLanguageModeState(savedMode);
      }
    } catch (error) {
      console.error('Error loading language mode:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const setLanguageMode = async (mode: LanguageMode) => {
    try {
      await AsyncStorage.setItem('languageMode', mode);
      setLanguageModeState(mode);
    } catch (error) {
      console.error('Error saving language mode:', error);
    }
  };

  return (
    <LanguageModeContext.Provider value={{ languageMode, setLanguageMode, isLoading }}>
      {children}
    </LanguageModeContext.Provider>
  );
}

export function useLanguageMode() {
  const context = useContext(LanguageModeContext);
  if (!context) {
    throw new Error('useLanguageMode must be used within LanguageModeProvider');
  }
  return context;
}
