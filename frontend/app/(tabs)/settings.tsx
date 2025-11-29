import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Linking,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';
import { useLanguageMode } from '../../contexts/LanguageModeContext';

export default function SettingsScreen() {
  const { theme, toggleTheme, colors } = useTheme();
  const { languageMode, setLanguageMode } = useLanguageMode();
  const router = useRouter();

  const handleEmailSupport = () => {
    const email = 'jakemadamson2k14@gmail.com';
    const subject = 'Thai Language Learning App - Support Request';
    const body = 'Hi Jake,\n\nI need help with:\n\n';
    
    Linking.openURL(`mailto:${email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`)
      .catch(() => {
        Alert.alert('Email Not Available', `Please email us at: ${email}`);
      });
  };

  const handleWebsite = () => {
    Linking.openURL('https://github.com/jakeadamson')
      .catch(() => Alert.alert('Cannot open link'));
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <View style={[styles.appIconContainer, { backgroundColor: colors.primary + '20' }]}>
            <Ionicons name="language" size={48} color={colors.primary} />
          </View>
          <Text style={[styles.appTitle, { color: colors.text }]}>
            Thai Language Learning
          </Text>
          <Text style={[styles.appVersion, { color: colors.textSecondary }]}>
            Version 1.0.0
          </Text>
        </View>

        {/* Theme Toggle Card */}
        <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
          <View style={styles.cardHeader}>
            <Ionicons name="color-palette" size={24} color={colors.primary} />
            <Text style={[styles.cardTitle, { color: colors.text }]}>Appearance</Text>
          </View>
          <TouchableOpacity
            style={[styles.optionRow, { borderTopColor: colors.border }]}
            onPress={toggleTheme}
            activeOpacity={0.7}
          >
            <View style={styles.optionLeft}>
              <Ionicons 
                name={theme === 'dark' ? 'moon' : 'sunny'} 
                size={22} 
                color={colors.warning} 
              />
              <Text style={[styles.optionText, { color: colors.text }]}>
                {theme === 'dark' ? 'Dark Mode' : 'Light Mode'}
              </Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
          </TouchableOpacity>
        </View>

        {/* App Info Card */}
        <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
          <View style={styles.cardHeader}>
            <Ionicons name="information-circle" size={24} color={colors.primary} />
            <Text style={[styles.cardTitle, { color: colors.text }]}>About This App</Text>
          </View>
          <View style={styles.infoContent}>
            <Text style={[styles.infoText, { color: colors.textSecondary }]}>
              A comprehensive Thai language learning application with 575+ learning items, 
              including alphabet, numbers, conversations, vocabulary, and educational songs.
            </Text>
            <View style={styles.featureList}>
              <View style={styles.featureItem}>
                <Ionicons name="checkmark-circle" size={18} color={colors.success} />
                <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                  575 Learning Items
                </Text>
              </View>
              <View style={styles.featureItem}>
                <Ionicons name="checkmark-circle" size={18} color={colors.success} />
                <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                  34 Comprehensive Lessons
                </Text>
              </View>
              <View style={styles.featureItem}>
                <Ionicons name="checkmark-circle" size={18} color={colors.success} />
                <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                  8 Learning Songs
                </Text>
              </View>
              <View style={styles.featureItem}>
                <Ionicons name="checkmark-circle" size={18} color={colors.success} />
                <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                  Native Thai Audio (TTS)
                </Text>
              </View>
              <View style={styles.featureItem}>
                <Ionicons name="checkmark-circle" size={18} color={colors.success} />
                <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                  Dark/Light Mode
                </Text>
              </View>
            </View>
          </View>
        </View>

        {/* Developer Credit Card */}
        <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
          <View style={styles.cardHeader}>
            <Ionicons name="code-slash" size={24} color={colors.primary} />
            <Text style={[styles.cardTitle, { color: colors.text }]}>Developer</Text>
          </View>
          <View style={styles.developerContent}>
            <View style={[styles.developerBadge, { backgroundColor: colors.primary + '15' }]}>
              <Ionicons name="person-circle" size={64} color={colors.primary} />
            </View>
            <Text style={[styles.developerName, { color: colors.text }]}>
              Jake Adamson
            </Text>
            <Text style={[styles.developerRole, { color: colors.textSecondary }]}>
              Full-Stack Developer
            </Text>
            <Text style={[styles.developerDescription, { color: colors.textSecondary }]}>
              Creator of Thai Language Learning App
            </Text>
          </View>
        </View>

        {/* Support Card */}
        <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
          <View style={styles.cardHeader}>
            <Ionicons name="help-circle" size={24} color={colors.primary} />
            <Text style={[styles.cardTitle, { color: colors.text }]}>Support & Contact</Text>
          </View>
          
          <TouchableOpacity
            style={[styles.optionRow, { borderTopColor: colors.border }]}
            onPress={handleEmailSupport}
            activeOpacity={0.7}
          >
            <View style={styles.optionLeft}>
              <View style={[styles.iconCircle, { backgroundColor: colors.error + '15' }]}>
                <Ionicons name="mail" size={20} color={colors.error} />
              </View>
              <View style={styles.optionTextContainer}>
                <Text style={[styles.optionText, { color: colors.text }]}>Email Support</Text>
                <Text style={[styles.optionSubtext, { color: colors.textSecondary }]}>
                  jakemadamson2k14@gmail.com
                </Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.optionRow, { borderTopColor: colors.border }]}
            onPress={handleWebsite}
            activeOpacity={0.7}
          >
            <View style={styles.optionLeft}>
              <View style={[styles.iconCircle, { backgroundColor: colors.primary + '15' }]}>
                <Ionicons name="globe" size={20} color={colors.primary} />
              </View>
              <View style={styles.optionTextContainer}>
                <Text style={[styles.optionText, { color: colors.text }]}>Visit Website</Text>
                <Text style={[styles.optionSubtext, { color: colors.textSecondary }]}>
                  github.com/jakeadamson
                </Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
          </TouchableOpacity>
        </View>

        {/* Copyright */}
        <View style={styles.footer}>
          <Text style={[styles.copyrightText, { color: colors.textSecondary }]}>
            © 2025 Jake Adamson
          </Text>
          <Text style={[styles.copyrightText, { color: colors.textSecondary }]}>
            All Rights Reserved
          </Text>
          <Text style={[styles.loveText, { color: colors.textSecondary }]}>
            Made with ❤️ for Thai Language Learners
          </Text>
        </View>

        <View style={styles.bottomPadding} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  header: {
    alignItems: 'center',
    padding: 32,
    paddingTop: 24,
  },
  appIconContainer: {
    width: 100,
    height: 100,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  appTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
    textAlign: 'center',
  },
  appVersion: {
    fontSize: 14,
  },
  card: {
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 12,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  optionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
    borderTopWidth: 1,
  },
  optionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 12,
  },
  optionText: {
    fontSize: 16,
    fontWeight: '500',
  },
  optionTextContainer: {
    flex: 1,
  },
  optionSubtext: {
    fontSize: 13,
    marginTop: 2,
  },
  iconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  infoContent: {
    gap: 16,
  },
  infoText: {
    fontSize: 15,
    lineHeight: 22,
  },
  featureList: {
    gap: 12,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  featureText: {
    fontSize: 14,
  },
  developerContent: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  developerBadge: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  developerName: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  developerRole: {
    fontSize: 15,
    marginBottom: 8,
  },
  developerDescription: {
    fontSize: 14,
    textAlign: 'center',
  },
  footer: {
    alignItems: 'center',
    paddingVertical: 24,
    gap: 4,
  },
  copyrightText: {
    fontSize: 13,
  },
  loveText: {
    fontSize: 13,
    marginTop: 8,
    fontStyle: 'italic',
  },
  bottomPadding: {
    height: 24,
  },
});
