import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Linking,
  Alert,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';
import { useLanguageMode } from '../../contexts/LanguageModeContext';
import MicrophonePermissions from '../../components/MicrophonePermissions';
import WorldLanguagesSelector from '../../components/WorldLanguagesSelector';
import AccessibilitySettings from '../../components/AccessibilitySettings';

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
            LangSwap
          </Text>
          <Text style={[styles.appVersion, { color: colors.textSecondary }]}>
            Version 1.0.0 • Bidirectional Learning
          </Text>
        </View>

        {/* Language Mode Card */}
        <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
          <View style={styles.cardHeader}>
            <Ionicons name="globe" size={24} color={colors.primary} />
            <Text style={[styles.cardTitle, { color: colors.text }]}>Learning Mode</Text>
          </View>
          <TouchableOpacity
            style={[styles.optionRow, { borderTopColor: colors.border }]}
            onPress={() => router.push('/language-selection' as any)}
            activeOpacity={0.7}
          >
            <View style={styles.optionLeft}>
              <Text style={styles.flagLarge}>
                {languageMode === 'learn-english' ? '🇬🇧' : '🇹🇭'}
              </Text>
              <View style={styles.optionTextContainer}>
                <Text style={[styles.optionText, { color: colors.text }]}>
                  {languageMode === 'learn-english' ? 'Learning English' : 'Learning Thai'}
                </Text>
                <Text style={[styles.optionSubtext, { color: colors.textSecondary }]}>
                  Tap to switch language
                </Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
          </TouchableOpacity>
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

        {/* World Languages Selector */}
        <WorldLanguagesSelector colors={colors} />

        {/* Microphone Permissions */}
        <MicrophonePermissions colors={colors} />

        {/* App Features Card - Enhanced */}
        <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
          <View style={styles.cardHeader}>
            <Ionicons name="star" size={24} color={colors.primary} />
            <Text style={[styles.cardTitle, { color: colors.text }]}>App Features</Text>
          </View>
          <View style={styles.infoContent}>
            <Text style={[styles.infoText, { color: colors.textSecondary }]}>
              LangSwap is a comprehensive, bidirectional language learning platform for Thai and English speakers.
            </Text>
            
            {/* Core Features */}
            <View style={[styles.featureSection, { borderLeftColor: colors.primary }]}>
              <Text style={[styles.featureSectionTitle, { color: colors.text }]}>
                🎯 Core Learning Features
              </Text>
              <View style={styles.featureList}>
                <View style={styles.featureItem}>
                  <Ionicons name="swap-horizontal" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    Bidirectional Learning (Thai ⇄ English)
                  </Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="card" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    Interactive Flashcards with Swipe Gestures
                  </Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="volume-high" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    Native Text-to-Speech (TTS) Audio
                  </Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="play" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    Play All Mode for Continuous Learning
                  </Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="trophy" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    Difficulty Levels (Beginner/Intermediate)
                  </Text>
                </View>
              </View>
            </View>

            {/* Voice Features */}
            <View style={[styles.featureSection, { borderLeftColor: colors.error }]}>
              <Text style={[styles.featureSectionTitle, { color: colors.text }]}>
                🎤 Voice Translation Features
              </Text>
              <View style={styles.featureList}>
                <View style={styles.featureItem}>
                  <Ionicons name="mic" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    Speech-to-Translate (Real-time)
                  </Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="globe" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    Voice Recognition for Practice
                  </Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="chatbubbles" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    Conversation Practice Tools
                  </Text>
                </View>
              </View>
            </View>

            {/* Content */}
            <View style={[styles.featureSection, { borderLeftColor: colors.warning }]}>
              <Text style={[styles.featureSectionTitle, { color: colors.text }]}>
                📚 Rich Content Library
              </Text>
              <View style={styles.featureList}>
                <View style={styles.featureItem}>
                  <Ionicons name="library" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    350+ Comprehensive Lessons
                  </Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="musical-notes" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    100+ Song-Based Lessons
                  </Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="restaurant" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    Day-to-Day Conversations (Restaurant, Shopping, Travel)
                  </Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="school" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    Alphabet, Numbers, Grammar & Vocabulary
                  </Text>
                </View>
              </View>
            </View>

            {/* User Experience */}
            <View style={[styles.featureSection, { borderLeftColor: colors.primary }]}>
              <Text style={[styles.featureSectionTitle, { color: colors.text }]}>
                ✨ User Experience
              </Text>
              <View style={styles.featureList}>
                <View style={styles.featureItem}>
                  <Ionicons name="moon" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    Dark/Light Mode Support
                  </Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="heart" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    Favorites & Progress Tracking
                  </Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="analytics" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    Visual Progress Dashboard
                  </Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="language" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    30+ UI Language Options
                  </Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="phone-portrait" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    iOS & Android Compatible
                  </Text>
                </View>
              </View>
            </View>

            {/* Account & Management */}
            <View style={[styles.featureSection, { borderLeftColor: colors.success }]}>
              <Text style={[styles.featureSectionTitle, { color: colors.text }]}>
                🔐 Account & Management
              </Text>
              <View style={styles.featureList}>
                <View style={styles.featureItem}>
                  <Ionicons name="person" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    User Accounts with Progress Sync
                  </Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="people" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    Staff & Admin Management System
                  </Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="shield-checkmark" size={18} color={colors.success} />
                  <Text style={[styles.featureText, { color: colors.textSecondary }]}>
                    Secure Authentication (JWT)
                  </Text>
                </View>
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
            <View style={styles.profileImageContainer}>
              <Image
                source={{ uri: 'https://customer-assets.emergentagent.com/job_thai-buddy/artifacts/fzgug7nw_IMG_5979.jpg' }}
                style={styles.profileImage}
                resizeMode="cover"
              />
            </View>
            <Text style={[styles.developerName, { color: colors.text }]}>
              Jake Adamson
            </Text>
            <Text style={[styles.developerRole, { color: colors.textSecondary }]}>
              Full-Stack Developer
            </Text>
            <Text style={[styles.developerDescription, { color: colors.textSecondary }]}>
              Creator of LangSwap - Bidirectional Language Learning
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

        {/* Legal & Copyright Information */}
        <View style={[styles.legalCard, { backgroundColor: colors.card, borderColor: colors.border }]}>
          <View style={styles.legalHeader}>
            <Ionicons name="shield-checkmark" size={24} color={colors.primary} />
            <Text style={[styles.legalTitle, { color: colors.text }]}>Legal Information</Text>
          </View>
          
          <View style={styles.legalContent}>
            <Text style={[styles.copyrightText, { color: colors.text }]}>
              © 2025 Jake Adamson
            </Text>
            <Text style={[styles.copyrightSubtext, { color: colors.textSecondary }]}>
              All Rights Reserved Worldwide
            </Text>
            
            <View style={styles.divider} />
            
            <Text style={[styles.legalNotice, { color: colors.textSecondary }]}>
              LangSwap™ is a registered trademark of Jake Adamson. This application, including all content, features, and functionality, is protected by international copyright, trademark, and other intellectual property laws.
            </Text>
            
            <Text style={[styles.legalNotice, { color: colors.textSecondary }]}>
              Created, Developed, and Owned by Jake Adamson.
            </Text>
            
            <View style={styles.divider} />
            
            <View style={styles.protectionBadges}>
              <View style={[styles.badge, { backgroundColor: colors.success + '15' }]}>
                <Ionicons name="shield-checkmark" size={14} color={colors.success} />
                <Text style={[styles.badgeText, { color: colors.success }]}>Copyright Protected</Text>
              </View>
              <View style={[styles.badge, { backgroundColor: colors.primary + '15' }]}>
                <Ionicons name="globe" size={14} color={colors.primary} />
                <Text style={[styles.badgeText, { color: colors.primary }]}>Global Rights</Text>
              </View>
            </View>
          </View>
        </View>

        {/* Footer Love Message */}
        <View style={styles.footer}>
          <Text style={[styles.loveText, { color: colors.textSecondary }]}>
            Made with ❤️ for Language Learners Worldwide
          </Text>
          <Text style={[styles.smallText, { color: colors.textSecondary }]}>
            Empowering communication across cultures
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
  flagLarge: {
    fontSize: 32,
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
    flex: 1,
  },
  featureSection: {
    marginTop: 16,
    paddingLeft: 16,
    borderLeftWidth: 3,
  },
  featureSectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 12,
  },
  developerContent: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  profileImageContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    overflow: 'hidden',
    marginBottom: 16,
    borderWidth: 4,
    borderColor: '#4F46E5',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 8,
  },
  profileImage: {
    width: '100%',
    height: '100%',
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
  legalCard: {
    marginHorizontal: 16,
    marginTop: 24,
    borderRadius: 16,
    borderWidth: 1,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  legalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  legalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  legalContent: {
    gap: 12,
  },
  copyrightText: {
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  copyrightSubtext: {
    fontSize: 13,
    textAlign: 'center',
    marginTop: 4,
  },
  legalNotice: {
    fontSize: 12,
    lineHeight: 18,
    textAlign: 'center',
  },
  divider: {
    height: 1,
    backgroundColor: 'rgba(0,0,0,0.1)',
    marginVertical: 8,
  },
  protectionBadges: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 12,
    marginTop: 8,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    gap: 6,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  footer: {
    alignItems: 'center',
    paddingVertical: 24,
    paddingHorizontal: 32,
  },
  loveText: {
    fontSize: 14,
    textAlign: 'center',
    fontWeight: '500',
  },
  smallText: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 4,
    fontStyle: 'italic',
  },
  bottomPadding: {
    height: 24,
  },
});
