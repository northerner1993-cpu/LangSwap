import React, { useEffect } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { useLanguageMode } from '../contexts/LanguageModeContext';
import { useTheme } from '../contexts/ThemeContext';

export default function Index() {
  const router = useRouter();
  const { languageMode, isLoading } = useLanguageMode();
  const { colors } = useTheme();

  useEffect(() => {
    if (!isLoading) {
      if (languageMode) {
        router.replace('/(tabs)' as any);
      } else {
        router.replace('/language-selection' as any);
      }
    }
  }, [isLoading, languageMode]);

  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.background }}>
      <ActivityIndicator size="large" color={colors.primary} />
    </View>
  );
}
