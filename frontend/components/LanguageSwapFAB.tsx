import React from 'react';
import { TouchableOpacity, StyleSheet, Animated, View, Text } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useTheme } from '../contexts/ThemeContext';
import { useLanguageMode } from '../contexts/LanguageModeContext';
import { LinearGradient } from 'expo-linear-gradient';

export default function LanguageSwapFAB() {
  const router = useRouter();
  const { colors } = useTheme();
  const { languageMode } = useLanguageMode();

  const handlePress = () => {
    router.push('/language-selection' as any);
  };

  const getCurrentFlag = () => {
    return languageMode === 'learn-english' ? '🇬🇧' : '🇹🇭';
  };

  const getTargetFlag = () => {
    return languageMode === 'learn-english' ? '🇹🇭' : '🇬🇧';
  };

  return (
    <TouchableOpacity
      style={styles.fab}
      onPress={handlePress}
      activeOpacity={0.8}
    >
      <LinearGradient
        colors={[colors.primary, colors.primary + 'DD']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.gradient}
      >
        <View style={styles.flagContainer}>
          <Text style={styles.currentFlag}>{getCurrentFlag()}</Text>
          <Ionicons name="swap-horizontal" size={20} color="#FFFFFF" />
          <Text style={styles.targetFlag}>{getTargetFlag()}</Text>
        </View>
      </LinearGradient>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  fab: {
    position: 'absolute',
    bottom: 90,
    right: 20,
    width: 100,
    height: 56,
    borderRadius: 28,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
    overflow: 'hidden',
  },
  gradient: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  flagContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  currentFlag: {
    fontSize: 22,
  },
  targetFlag: {
    fontSize: 22,
  },
});
