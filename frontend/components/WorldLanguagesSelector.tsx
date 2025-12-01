import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Modal,
  Dimensions,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useUILanguage } from '../contexts/UILanguageContext';
import i18n from '../i18n';

interface Language {
  code: string;
  name: string;
  nativeName: string;
  flag: string;
}

interface WorldLanguagesSelectorProps {
  colors: any;
}

const AVAILABLE_LANGUAGES: Language[] = [
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇬🇧' },
  { code: 'th', name: 'Thai', nativeName: 'ไทย', flag: '🇹🇭' },
  { code: 'zh', name: 'Chinese', nativeName: '中文', flag: '🇨🇳' },
  { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
  { code: 'ja', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵' },
  { code: 'ko', name: 'Korean', nativeName: '한국어', flag: '🇰🇷' },
  { code: 'ru', name: 'Russian', nativeName: 'Русский', flag: '🇷🇺' },
  { code: 'pt', name: 'Portuguese', nativeName: 'Português', flag: '🇵🇹' },
  { code: 'it', name: 'Italian', nativeName: 'Italiano', flag: '🇮🇹' },
  { code: 'nl', name: 'Dutch', nativeName: 'Nederlands', flag: '🇳🇱' },
  { code: 'pl', name: 'Polish', nativeName: 'Polski', flag: '🇵🇱' },
  { code: 'tr', name: 'Turkish', nativeName: 'Türkçe', flag: '🇹🇷' },
  { code: 'vi', name: 'Vietnamese', nativeName: 'Tiếng Việt', flag: '🇻🇳' },
  { code: 'id', name: 'Indonesian', nativeName: 'Bahasa Indonesia', flag: '🇮🇩' },
  { code: 'ar', name: 'Arabic', nativeName: 'العربية', flag: '🇸🇦' },
  { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', flag: '🇮🇳' },
  { code: 'bn', name: 'Bengali', nativeName: 'বাংলা', flag: '🇧🇩' },
  { code: 'sw', name: 'Swahili', nativeName: 'Kiswahili', flag: '🇰🇪' },
  { code: 'fi', name: 'Finnish', nativeName: 'Suomi', flag: '🇫🇮' },
  { code: 'sv', name: 'Swedish', nativeName: 'Svenska', flag: '🇸🇪' },
  { code: 'no', name: 'Norwegian', nativeName: 'Norsk', flag: '🇳🇴' },
  { code: 'da', name: 'Danish', nativeName: 'Dansk', flag: '🇩🇰' },
  { code: 'he', name: 'Hebrew', nativeName: 'עברית', flag: '🇮🇱' },
  { code: 'el', name: 'Greek', nativeName: 'Ελληνικά', flag: '🇬🇷' },
  { code: 'cs', name: 'Czech', nativeName: 'Čeština', flag: '🇨🇿' },
  { code: 'hu', name: 'Hungarian', nativeName: 'Magyar', flag: '🇭🇺' },
  { code: 'ro', name: 'Romanian', nativeName: 'Română', flag: '🇷🇴' },
  { code: 'uk', name: 'Ukrainian', nativeName: 'Українська', flag: '🇺🇦' },
];

export default function WorldLanguagesSelector({ colors }: WorldLanguagesSelectorProps) {
  const [currentLanguage, setCurrentLanguage] = useState<Language>(AVAILABLE_LANGUAGES[0]);
  const [modalVisible, setModalVisible] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [, forceUpdate] = useState(0);
  const { uiLanguage, setUILanguage } = useUILanguage();
  
  // Force re-render when language changes
  useEffect(() => {
    forceUpdate(prev => prev + 1);
  }, [uiLanguage]);
  
  // Helper function for translations
  const t = (key: string) => i18n.t(key);

  useEffect(() => {
    loadLanguagePreference();
  }, [uiLanguage]);

  const loadLanguagePreference = async () => {
    try {
      const savedLanguage = AVAILABLE_LANGUAGES.find(lang => lang.code === uiLanguage);
      if (savedLanguage) {
        setCurrentLanguage(savedLanguage);
      }
    } catch (error) {
      console.error('Error loading language preference:', error);
    }
  };

  const saveLanguagePreference = async (language: Language) => {
    try {
      await setUILanguage(language.code as any);
      setCurrentLanguage(language);
      setModalVisible(false);
      
      // Show confirmation
      Alert.alert(
        'Language Changed',
        `App language has been changed to ${language.name}. The app will reload to apply changes.`,
        [
          {
            text: 'OK',
            onPress: () => {
              // Force reload to apply language changes
              if (typeof window !== 'undefined') {
                window.location.reload();
              }
            }
          }
        ]
      );
    } catch (error) {
      console.error('Error saving language preference:', error);
      Alert.alert('Error', 'Failed to change language. Please try again.');
    }
  };

  const filteredLanguages = AVAILABLE_LANGUAGES.filter(lang =>
    lang.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    lang.nativeName.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
      <View style={styles.cardHeader}>
        <Ionicons name="globe-outline" size={24} color={colors.primary} />
        <Text style={[styles.cardTitle, { color: colors.text }]}>{t('settings.appLanguagePreference')}</Text>
      </View>

      <Text style={[styles.description, { color: colors.textSecondary }]}>
        {t('settings.choosePreferredLanguage')}
      </Text>

      {/* Current Selection */}
      <TouchableOpacity
        style={[styles.currentSelection, { backgroundColor: colors.primary + '10', borderColor: colors.primary + '30' }]}
        onPress={() => setModalVisible(true)}
        activeOpacity={0.7}
      >
        <View style={styles.languageInfo}>
          <Text style={styles.flag}>{currentLanguage.flag}</Text>
          <View style={styles.languageText}>
            <Text style={[styles.languageName, { color: colors.text }]}>
              {currentLanguage.name}
            </Text>
            <Text style={[styles.nativeName, { color: colors.textSecondary }]}>
              {currentLanguage.nativeName}
            </Text>
          </View>
        </View>
        <Ionicons name="chevron-forward" size={24} color={colors.textSecondary} />
      </TouchableOpacity>

      {/* Language Count */}
      <View style={styles.infoRow}>
        <Ionicons name="information-circle-outline" size={16} color={colors.textSecondary} />
        <Text style={[styles.infoText, { color: colors.textSecondary }]}>
          {AVAILABLE_LANGUAGES.length} languages available
        </Text>
      </View>

      {/* Language Selection Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={modalVisible}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalContainer}>
          <View style={[styles.modalContent, { backgroundColor: colors.card }]}>
            {/* Modal Header */}
            <View style={[styles.modalHeader, { borderBottomColor: colors.border }]}>
              <Text style={[styles.modalTitle, { color: colors.text }]}>
                Select Language
              </Text>
              <TouchableOpacity
                onPress={() => setModalVisible(false)}
                style={styles.closeButton}
              >
                <Ionicons name="close" size={28} color={colors.text} />
              </TouchableOpacity>
            </View>

            {/* Language List */}
            <ScrollView 
              style={styles.languageList}
              showsVerticalScrollIndicator={false}
            >
              {filteredLanguages.map((language) => (
                <TouchableOpacity
                  key={language.code}
                  style={[
                    styles.languageItem,
                    currentLanguage.code === language.code && { backgroundColor: colors.primary + '15' },
                    { borderBottomColor: colors.border }
                  ]}
                  onPress={() => saveLanguagePreference(language)}
                  activeOpacity={0.7}
                >
                  <Text style={styles.languageFlag}>{language.flag}</Text>
                  <View style={styles.languageDetails}>
                    <Text style={[styles.languageItemName, { color: colors.text }]}>
                      {language.name}
                    </Text>
                    <Text style={[styles.languageItemNative, { color: colors.textSecondary }]}>
                      {language.nativeName}
                    </Text>
                  </View>
                  {currentLanguage.code === language.code && (
                    <Ionicons name="checkmark-circle" size={24} color={colors.primary} />
                  )}
                </TouchableOpacity>
              ))}
            </ScrollView>

            {/* Note */}
            <View style={[styles.modalFooter, { borderTopColor: colors.border }]}>
              <Text style={[styles.footerNote, { color: colors.textSecondary }]}>
                ℹ️ This changes the app's interface language only. Your learning language (Thai/English) remains the same.
              </Text>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const { height } = Dimensions.get('window');

const styles = StyleSheet.create({
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
    marginBottom: 12,
    gap: 12,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    flex: 1,
  },
  description: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 16,
  },
  currentSelection: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
  },
  languageInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  flag: {
    fontSize: 36,
  },
  languageText: {
    flex: 1,
  },
  languageName: {
    fontSize: 16,
    fontWeight: '600',
  },
  nativeName: {
    fontSize: 14,
    marginTop: 2,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  infoText: {
    fontSize: 12,
  },
  modalContainer: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  modalContent: {
    height: height * 0.7,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
    elevation: 10,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 20,
    borderBottomWidth: 1,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  closeButton: {
    padding: 4,
  },
  languageList: {
    flex: 1,
  },
  languageItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    gap: 12,
  },
  languageFlag: {
    fontSize: 28,
  },
  languageDetails: {
    flex: 1,
  },
  languageItemName: {
    fontSize: 16,
    fontWeight: '500',
  },
  languageItemNative: {
    fontSize: 14,
    marginTop: 2,
  },
  modalFooter: {
    padding: 16,
    borderTopWidth: 1,
  },
  footerNote: {
    fontSize: 12,
    lineHeight: 18,
    textAlign: 'center',
  },
});
