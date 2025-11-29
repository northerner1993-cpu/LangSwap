import { Stack } from 'expo-router';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { ThemeProvider } from '../contexts/ThemeContext';
import { LanguageModeProvider } from '../contexts/LanguageModeContext';

export default function RootLayout() {
  return (
    <ThemeProvider>
      <LanguageModeProvider>
        <SafeAreaProvider>
          <Stack screenOptions={{ headerShown: false }}>
            <Stack.Screen name="index" options={{ headerShown: false }} />
            <Stack.Screen name="language-selection" options={{ headerShown: false }} />
            <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
            <Stack.Screen name="lesson/[id]" options={{ headerShown: false }} />
            <Stack.Screen name="songs-catalogue" options={{ headerShown: false }} />
          </Stack>
        </SafeAreaProvider>
      </LanguageModeProvider>
    </ThemeProvider>
  );
}