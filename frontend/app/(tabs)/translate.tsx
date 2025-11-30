import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Speech from 'expo-speech';
import { useTheme } from '../../contexts/ThemeContext';
import { LinearGradient } from 'expo-linear-gradient';

interface Language {
  code: string;
  name: string;
  flag: string;
  ttsCode: string;
}

const LANGUAGES: Language[] = [
  { code: 'en', name: 'English', flag: '🇬🇧', ttsCode: 'en-GB' },
  { code: 'th', name: 'Thai', flag: '🇹🇭', ttsCode: 'th-TH' },
  { code: 'es', name: 'Spanish', flag: '🇪🇸', ttsCode: 'es-ES' },
  { code: 'fr', name: 'French', flag: '🇫🇷', ttsCode: 'fr-FR' },
  { code: 'de', name: 'German', flag: '🇩🇪', ttsCode: 'de-DE' },
  { code: 'zh', name: 'Chinese', flag: '🇨🇳', ttsCode: 'zh-CN' },
  { code: 'ja', name: 'Japanese', flag: '🇯🇵', ttsCode: 'ja-JP' },
  { code: 'ko', name: 'Korean', flag: '🇰🇷', ttsCode: 'ko-KR' },
  { code: 'ar', name: 'Arabic', flag: '🇸🇦', ttsCode: 'ar-SA' },
  { code: 'hi', name: 'Hindi', flag: '🇮🇳', ttsCode: 'hi-IN' },
  { code: 'pt', name: 'Portuguese', flag: '🇵🇹', ttsCode: 'pt-PT' },
  { code: 'ru', name: 'Russian', flag: '🇷🇺', ttsCode: 'ru-RU' },
  { code: 'it', name: 'Italian', flag: '🇮🇹', ttsCode: 'it-IT' },
  { code: 'vi', name: 'Vietnamese', flag: '🇻🇳', ttsCode: 'vi-VN' },
];

export default function TranslateScreen() {
  const { colors } = useTheme();
  const [sourceLanguage, setSourceLanguage] = useState<Language>(LANGUAGES[0]);
  const [targetLanguage, setTargetLanguage] = useState<Language>(LANGUAGES[1]);
  const [sourceText, setSourceText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [isTranslating, setIsTranslating] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const swapLanguages = () => {
    const temp = sourceLanguage;
    setSourceLanguage(targetLanguage);
    setTargetLanguage(temp);
    setSourceText(translatedText);
    setTranslatedText(sourceText);
  };

  const translate = async () => {
    if (!sourceText.trim()) return;
    
    setIsTranslating(true);
    try {
      // Mock translation - In production, use Google Translate API or similar
      // For now, just echo back with language indicator
      await new Promise(resolve => setTimeout(resolve, 1000));
      setTranslatedText(`[${targetLanguage.name}] ${sourceText}`);
    } catch (error) {
      console.error('Translation error:', error);
    } finally {
      setIsTranslating(false);
    }
  };

  const speakText = async (text: string, language: Language, isSource: boolean) => {
    if (!text.trim()) return;
    
    try {
      const available = await Speech.isSpeakingAsync();
      if (available) await Speech.stop();
      
      setIsSpeaking(true);
      
      Speech.speak(text, {
        language: language.ttsCode,
        pitch: 1.0,
        rate: 0.85,
        onDone: () => setIsSpeaking(false),
        onStopped: () => setIsSpeaking(false),
        onError: () => setIsSpeaking(false),
      });
    } catch (error) {
      console.error('TTS error:', error);
      setIsSpeaking(false);
    }
  };

  const startVoiceRecognition = async () => {
    // Web Speech API for web platform
    if (Platform.OS === 'web' && 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      
      recognition.lang = sourceLanguage.ttsCode;
      recognition.continuous = false;
      recognition.interimResults = false;
      
      recognition.onstart = () => setIsRecording(true);
      recognition.onend = () => setIsRecording(false);
      
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setSourceText(transcript);
        setIsRecording(false);
      };
      
      recognition.onerror = () => setIsRecording(false);
      
      recognition.start();
    } else {
      // Mobile - would need react-native-voice or similar
      alert('Voice recognition is available on web platform. On mobile, please type your text.');
    }
  };

  useEffect(() => {
    if (sourceText) {
      const debounce = setTimeout(() => {
        translate();
      }, 500);
      return () => clearTimeout(debounce);
    }
  }, [sourceText, sourceLanguage, targetLanguage]);

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <LinearGradient
        colors={[colors.primary + '15', colors.background]}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <Ionicons name="language" size={32} color={colors.primary} />
          <Text style={[styles.headerTitle, { color: colors.text }]}>Universal Translator</Text>
          <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]}>14 Languages Supported</Text>
        </View>
      </LinearGradient>

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Source Language Selector */}
        <View style={[styles.card, { backgroundColor: colors.card }]}>
          <Text style={[styles.cardLabel, { color: colors.textSecondary }]}>From</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.languageScroll}>
            {LANGUAGES.map((lang) => (
              <TouchableOpacity
                key={lang.code}
                style={[
                  styles.languageButton,
                  sourceLanguage.code === lang.code && { backgroundColor: colors.primary + '20' },
                ]}
                onPress={() => setSourceLanguage(lang)}
              >
                <Text style={styles.flagEmoji}>{lang.flag}</Text>
                <Text
                  style={[
                    styles.languageName,
                    { color: sourceLanguage.code === lang.code ? colors.primary : colors.text },
                  ]}
                >
                  {lang.name}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          {/* Source Text Input */}
          <View style={[styles.inputContainer, { backgroundColor: colors.inputBackground }]}>
            <TextInput
              style={[styles.textInput, { color: colors.text }]}
              placeholder="Type or speak to translate..."
              placeholderTextColor={colors.textSecondary}
              value={sourceText}
              onChangeText={setSourceText}
              multiline
              maxLength={500}
            />
          </View>

          {/* Source Controls */}
          <View style={styles.controlsRow}>
            <TouchableOpacity
              style={[styles.controlButton, { backgroundColor: colors.primary + '15' }]}
              onPress={startVoiceRecognition}
            >
              <Ionicons
                name={isRecording ? "mic" : "mic-outline"}
                size={20}
                color={isRecording ? colors.error : colors.primary}
              />
              <Text style={[styles.controlText, { color: colors.primary }]}>
                {isRecording ? 'Listening...' : 'Voice'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.controlButton, { backgroundColor: colors.success + '15' }]}
              onPress={() => speakText(sourceText, sourceLanguage, true)}
              disabled={!sourceText || isSpeaking}
            >
              <Ionicons name="volume-high" size={20} color={colors.success} />
              <Text style={[styles.controlText, { color: colors.success }]}>Listen</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.controlButton, { backgroundColor: colors.error + '15' }]}
              onPress={() => setSourceText('')}
            >
              <Ionicons name="close-circle" size={20} color={colors.error} />
              <Text style={[styles.controlText, { color: colors.error }]}>Clear</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Swap Button */}
        <View style={styles.swapContainer}>
          <TouchableOpacity
            style={[styles.swapButton, { backgroundColor: colors.primary }]}
            onPress={swapLanguages}
          >
            <Ionicons name="swap-vertical" size={28} color="#FFFFFF" />
          </TouchableOpacity>
        </View>

        {/* Target Language Selector */}
        <View style={[styles.card, { backgroundColor: colors.card }]}>
          <Text style={[styles.cardLabel, { color: colors.textSecondary }]}>To</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.languageScroll}>
            {LANGUAGES.map((lang) => (
              <TouchableOpacity
                key={lang.code}
                style={[
                  styles.languageButton,
                  targetLanguage.code === lang.code && { backgroundColor: colors.primary + '20' },
                ]}
                onPress={() => setTargetLanguage(lang)}
              >
                <Text style={styles.flagEmoji}>{lang.flag}</Text>
                <Text
                  style={[
                    styles.languageName,
                    { color: targetLanguage.code === lang.code ? colors.primary : colors.text },
                  ]}
                >
                  {lang.name}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          {/* Translation Output */}
          <View style={[styles.outputContainer, { backgroundColor: colors.inputBackground }]}>
            {isTranslating ? (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="small" color={colors.primary} />
                <Text style={[styles.loadingText, { color: colors.textSecondary }]}>Translating...</Text>
              </View>
            ) : (
              <Text style={[styles.translatedText, { color: colors.text }]}>
                {translatedText || 'Translation will appear here...'}
              </Text>
            )}
          </View>

          {/* Target Controls */}
          <View style={styles.controlsRow}>
            <TouchableOpacity
              style={[styles.controlButton, { backgroundColor: colors.success + '15' }]}
              onPress={() => speakText(translatedText, targetLanguage, false)}
              disabled={!translatedText || isSpeaking}
            >
              <Ionicons name="volume-high" size={20} color={colors.success} />
              <Text style={[styles.controlText, { color: colors.success }]}>Listen</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.controlButton, { backgroundColor: colors.warning + '15' }]}
              onPress={() => {
                // Copy to clipboard functionality
                if (Platform.OS === 'web') {
                  navigator.clipboard.writeText(translatedText);
                }
              }}
              disabled={!translatedText}
            >
              <Ionicons name="copy" size={20} color={colors.warning} />
              <Text style={[styles.controlText, { color: colors.warning }]}>Copy</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Info Card */}
        <View style={[styles.infoCard, { backgroundColor: colors.primary + '10' }]}>
          <Ionicons name="information-circle" size={24} color={colors.primary} />
          <Text style={[styles.infoText, { color: colors.text }]}>
            Powered by AI Translation • Voice recognition available on web
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
  header: {
    paddingVertical: 24,
    paddingHorizontal: 20,
  },
  headerContent: {
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 8,
  },
  headerSubtitle: {
    fontSize: 14,
    marginTop: 4,
  },
  scrollView: {
    flex: 1,
    paddingHorizontal: 16,
  },
  card: {
    borderRadius: 20,
    padding: 20,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 5,
  },
  cardLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 12,
    textTransform: 'uppercase',
  },
  languageScroll: {
    marginBottom: 16,
  },
  languageButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    marginRight: 8,
    gap: 8,
  },
  flagEmoji: {
    fontSize: 20,
  },
  languageName: {
    fontSize: 14,
    fontWeight: '600',
  },
  inputContainer: {
    borderRadius: 16,
    padding: 16,
    minHeight: 120,
    marginBottom: 16,
  },
  textInput: {
    fontSize: 16,
    lineHeight: 24,
    minHeight: 100,
  },
  outputContainer: {
    borderRadius: 16,
    padding: 16,
    minHeight: 120,
    marginBottom: 16,
    justifyContent: 'center',
  },
  translatedText: {
    fontSize: 16,
    lineHeight: 24,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
  },
  controlsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  controlButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 12,
    gap: 6,
  },
  controlText: {
    fontSize: 13,
    fontWeight: '600',
  },
  swapContainer: {
    alignItems: 'center',
    marginVertical: 16,
  },
  swapButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 6,
  },
  infoCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 16,
    marginTop: 16,
    gap: 12,
  },
  infoText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
  },
  bottomPadding: {
    height: 24,
  },
});
