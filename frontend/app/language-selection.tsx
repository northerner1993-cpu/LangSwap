import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
  StatusBar,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useLanguageMode } from '../contexts/LanguageModeContext';
import { useTheme } from '../contexts/ThemeContext';

const { width } = Dimensions.get('window');

export default function LanguageSelectionScreen() {
  const router = useRouter();
  const { setLanguageMode } = useLanguageMode();
  const { colors, theme } = useTheme();

  const handleSelectMode = async (mode: 'learn-thai' | 'learn-english') => {
    await setLanguageMode(mode);
    router.replace('/(tabs)' as any);
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar barStyle={theme === 'dark' ? 'light-content' : 'dark-content'} />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.appName, { color: colors.text }]}>LangSwap</Text>
        <Text style={[styles.tagline, { color: colors.textSecondary }]}>🌍 Your Bilingual Journey Starts Here</Text>
      </View>

      {/* Selection Cards */}
      <View style={styles.cardsContainer}>
        <Text style={[styles.instruction, { color: colors.text }]}>Choose Your Learning Path</Text>

        {/* Learn English Card */}
        <TouchableOpacity
          style={styles.cardWrapper}
          onPress={() => handleSelectMode('learn-english')}
          activeOpacity={0.9}
        >
          <LinearGradient
            colors={['#1E40AF', '#3B82F6', '#60A5FA']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.card}
          >
            <View style={styles.flagContainer}>
              <Text style={styles.flagEmoji}>🇬🇧</Text>
            </View>
            <Text style={styles.cardTitle}>Learn English</Text>
            <Text style={styles.cardSubtitle}>Perfect Your British English</Text>
            <Text style={styles.cardDescription}>with Thai language support</Text>
            <View style={styles.features}>
              <View style={styles.featureItem}>
                <Ionicons name="checkmark-circle" size={16} color="#FFFFFF" />
                <Text style={styles.featureText}>575+ Learning Items</Text>
              </View>
              <View style={styles.featureItem}>
                <Ionicons name="musical-notes" size={16} color="#FFFFFF" />
                <Text style={styles.featureText}>8 Learning Songs</Text>
              </View>
              <View style={styles.featureItem}>
                <Ionicons name="chatbubbles" size={16} color="#FFFFFF" />
                <Text style={styles.featureText}>Real Conversations</Text>
              </View>
            </View>
            <View style={styles.arrow}>
              <Ionicons name="arrow-forward" size={24} color="#FFFFFF" />
            </View>
          </LinearGradient>
        </TouchableOpacity>

        {/* Learn Thai Card */}
        <TouchableOpacity
          style={styles.cardWrapper}
          onPress={() => handleSelectMode('learn-thai')}
          activeOpacity={0.9}
        >
          <LinearGradient
            colors={['#BE123C', '#E11D48', '#FB7185']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.card}
          >
            <View style={styles.flagContainer}>
              <Text style={styles.flagEmoji}>🇹🇭</Text>
            </View>
            <Text style={styles.cardTitle}>Learn Thai</Text>
            <Text style={styles.cardSubtitle}>Master Thai Language</Text>
            <Text style={styles.cardDescription}>with English language support</Text>
            <View style={styles.features}>
              <View style={styles.featureItem}>
                <Ionicons name="checkmark-circle" size={16} color="#FFFFFF" />
                <Text style={styles.featureText}>575+ Learning Items</Text>
              </View>
              <View style={styles.featureItem}>
                <Ionicons name="musical-notes" size={16} color="#FFFFFF" />
                <Text style={styles.featureText}>8 Learning Songs</Text>
              </View>
              <View style={styles.featureItem}>
                <Ionicons name="chatbubbles" size={16} color="#FFFFFF" />
                <Text style={styles.featureText}>Real Conversations</Text>
              </View>
            </View>
            <View style={styles.arrow}>
              <Ionicons name="arrow-forward" size={24} color="#FFFFFF" />
            </View>
          </LinearGradient>
        </TouchableOpacity>
      </View>

      {/* Footer */}
      <View style={styles.footer}>
        <Text style={[styles.footerText, { color: colors.textSecondary }]}>
          You can switch languages anytime in Settings
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    alignItems: 'center',
    paddingTop: 40,
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  appName: {
    fontSize: 42,
    fontWeight: 'bold',
    marginBottom: 8,
    letterSpacing: -0.5,
  },
  tagline: {
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 22,
  },
  cardsContainer: {
    flex: 1,
    paddingHorizontal: 20,
    justifyContent: 'center',
  },
  instruction: {
    fontSize: 22,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 32,
  },
  cardWrapper: {
    marginBottom: 20,
    borderRadius: 28,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  card: {
    borderRadius: 28,
    padding: 28,
    minHeight: 280,
    justifyContent: 'space-between',
  },
  flagContainer: {
    alignSelf: 'flex-start',
    marginBottom: 12,
  },
  flagEmoji: {
    fontSize: 64,
  },
  cardTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 6,
  },
  cardSubtitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  cardDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.85)',
    marginBottom: 20,
  },
  features: {
    gap: 10,
    marginBottom: 12,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  featureText: {
    fontSize: 14,
    color: '#FFFFFF',
    fontWeight: '500',
  },
  arrow: {
    alignSelf: 'flex-end',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  footer: {
    paddingHorizontal: 20,
    paddingBottom: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 13,
    textAlign: 'center',
  },
});
