import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView,
  Alert,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Speech from 'expo-speech';
import Voice from '@react-native-voice/voice';
import Constants from 'expo-constants';
import { useTheme } from '../contexts/ThemeContext';
import { useLanguageMode } from '../contexts/LanguageModeContext';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface TranslationHistory {
  id: string;
  original: string;
  translated: string;
  sourceLang: string;
  targetLang: string;
  timestamp: Date;
}

export default function SpeechToTranslate() {
  const { colors } = useTheme();
  const { languageMode } = useLanguageMode();
  const [inputText, setInputText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [isTranslating, setIsTranslating] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [history, setHistory] = useState<TranslationHistory[]>([]);

  const sourceLang = languageMode === 'learn-thai' ? 'en' : 'th';
  const targetLang = languageMode === 'learn-thai' ? 'th' : 'en';

  useEffect(() => {
    // Request microphone permissions immediately on mount
    const requestPermissions = async () => {
      try {
        if (Platform.OS !== 'web') {
          // Check if permissions are available
          const hasPermission = await Voice.isAvailable();
          if (!hasPermission) {
            Alert.alert(
              'Microphone Required',
              'LangSwap needs microphone access for voice translation. Please enable it in your device settings.',
              [
                { text: 'Cancel', style: 'cancel' },
                { text: 'Open Settings', onPress: () => {
                  // On mobile, this would open settings
                  console.log('Open device settings for microphone');
                }}
              ]
            );
          }
        }
      } catch (error) {
        console.error('Permission check error:', error);
      }
    };

    requestPermissions();

    // Setup voice recognition
    Voice.onSpeechStart = () => setIsRecording(true);
    Voice.onSpeechEnd = () => setIsRecording(false);
    Voice.onSpeechResults = (e: any) => {
      if (e.value && e.value.length > 0) {
        setInputText(e.value[0]);
      }
    };
    Voice.onSpeechError = (e: any) => {
      console.error('Speech error:', e);
      setIsRecording(false);
      Alert.alert(
        'Microphone Access Needed',
        'Please enable microphone permissions in your device settings to use voice translation.',
        [{ text: 'OK' }]
      );
    };

    return () => {
      Voice.destroy().then(Voice.removeAllListeners);
    };
  }, []);

  const handleTranslate = async () => {
    if (!inputText.trim()) {
      Alert.alert('Empty Input', 'Please enter text to translate');
      return;
    }

    setIsTranslating(true);
    try {
      const response = await fetch(`${API_URL}/api/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: inputText,
          source_lang: sourceLang,
          target_lang: targetLang,
        }),
      });

      const data = await response.json();
      setTranslatedText(data.translated);

      // Add to history
      const newEntry: TranslationHistory = {
        id: Date.now().toString(),
        original: inputText,
        translated: data.translated,
        sourceLang,
        targetLang,
        timestamp: new Date(),
      };
      setHistory([newEntry, ...history.slice(0, 9)]); // Keep last 10
    } catch (error) {
      console.error('Translation error:', error);
      Alert.alert('Error', 'Failed to translate. Please try again.');
    } finally {
      setIsTranslating(false);
    }
  };

  const handleSpeak = async (text: string, language: string) => {
    if (!text) return;

    try {
      const available = await Speech.isSpeakingAsync();
      if (available) {
        await Speech.stop();
      }

      setIsSpeaking(true);
      const langCode = language === 'th' ? 'th-TH' : 'en-GB';

      Speech.speak(text, {
        language: langCode,
        pitch: 1.0,
        rate: 0.75,
        onDone: () => setIsSpeaking(false),
        onStopped: () => setIsSpeaking(false),
        onError: () => {
          setIsSpeaking(false);
          Alert.alert('TTS Not Available', 'Text-to-speech works best on mobile devices.');
        },
      });
    } catch (error) {
      console.error('Speech error:', error);
      setIsSpeaking(false);
    }
  };

  const handleSwapLanguages = () => {
    const temp = inputText;
    setInputText(translatedText);
    setTranslatedText(temp);
  };

  const startRecording = async () => {
    try {
      setIsRecording(true);
      
      // Determine language for recognition
      const recognitionLang = sourceLang; // 'th' or 'en'
      
      // Start speech recognition
      const started = await Voice.start(recognitionLang === 'th' ? 'th-TH' : 'en-US');
      
      if (!started) {
        setIsRecording(false);
        Alert.alert('Error', 'Could not start speech recognition. Please check microphone permissions.');
      }
    } catch (error) {
      console.error('Failed to start recording:', error);
      setIsRecording(false);
      Alert.alert('Microphone Error', 'Please enable microphone permissions in your device settings.');
    }
  };

  const stopRecording = async () => {
    try {
      await Voice.stop();
      setIsRecording(false);
    } catch (error) {
      console.error('Failed to stop recording:', error);
      setIsRecording(false);
    }
  };

  const handleClear = () => {
    setInputText('');
    setTranslatedText('');
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Input Section */}
      <View style={[styles.card, { backgroundColor: colors.card }]}>
        <View style={styles.header}>
          <Text style={[styles.headerText, { color: colors.text }]}>
            {sourceLang === 'en' ? 'English' : 'ไทย'}
          </Text>
          <View style={styles.headerActions}>
            <TouchableOpacity 
              onPress={isRecording ? stopRecording : startRecording}
              style={[styles.micButton, isRecording && styles.micButtonActive]}
            >
              <Ionicons 
                name={isRecording ? "stop-circle" : "mic"} 
                size={24} 
                color={isRecording ? "#EF4444" : colors.primary} 
              />
            </TouchableOpacity>
            <TouchableOpacity onPress={() => handleSpeak(inputText, sourceLang)} disabled={!inputText || isSpeaking}>
              <Ionicons name="volume-high" size={24} color={inputText ? colors.primary : colors.textSecondary} />
            </TouchableOpacity>
          </View>
        </View>
        <TextInput
          style={[styles.input, { color: colors.text, backgroundColor: colors.inputBackground || colors.background }]}
          placeholder={`Enter ${sourceLang === 'en' ? 'English' : 'Thai'} text...`}
          placeholderTextColor={colors.textSecondary}
          value={inputText}
          onChangeText={setInputText}
          multiline
          maxLength={500}
        />
        {isRecording && (
          <View style={styles.recordingIndicator}>
            <View style={styles.recordingDot} />
            <Text style={[styles.recordingText, { color: '#EF4444' }]}>Recording...</Text>
          </View>
        )}
      </View>

      {/* Swap Button */}
      <View style={styles.swapContainer}>
        <TouchableOpacity style={[styles.swapButton, { backgroundColor: colors.primary }]} onPress={handleSwapLanguages}>
          <Ionicons name="swap-vertical" size={24} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      {/* Output Section */}
      <View style={[styles.card, { backgroundColor: colors.card }]}>
        <View style={styles.header}>
          <Text style={[styles.headerText, { color: colors.text }]}>
            {targetLang === 'en' ? 'English' : 'ไทย'}
          </Text>
          <TouchableOpacity onPress={() => handleSpeak(translatedText, targetLang)} disabled={!translatedText || isSpeaking}>
            <Ionicons name="volume-high" size={24} color={translatedText ? colors.primary : colors.textSecondary} />
          </TouchableOpacity>
        </View>
        <View style={[styles.output, { backgroundColor: colors.inputBackground || colors.background }]}>
          <Text style={[styles.outputText, { color: translatedText ? colors.text : colors.textSecondary }]}>
            {translatedText || 'Translation will appear here...'}
          </Text>
        </View>
      </View>

      {/* Action Buttons */}
      <View style={styles.actionButtons}>
        <TouchableOpacity style={[styles.button, styles.clearButton, { borderColor: colors.border }]} onPress={handleClear}>
          <Ionicons name="close-circle" size={20} color={colors.textSecondary} />
          <Text style={[styles.buttonText, { color: colors.textSecondary }]}>Clear</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.button, styles.translateButton, { backgroundColor: colors.primary }]}
          onPress={handleTranslate}
          disabled={isTranslating || !inputText}
        >
          {isTranslating ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <>
              <Ionicons name="language" size={20} color="#FFFFFF" />
              <Text style={styles.translateButtonText}>Translate</Text>
            </>
          )}
        </TouchableOpacity>
      </View>

      {/* Translation History */}
      {history.length > 0 && (
        <View style={[styles.historyContainer, { backgroundColor: colors.card }]}>
          <Text style={[styles.historyTitle, { color: colors.text }]}>Recent Translations</Text>
          <ScrollView style={styles.historyScroll} showsVerticalScrollIndicator={false}>
            {history.map((item) => (
              <TouchableOpacity
                key={item.id}
                style={[styles.historyItem, { borderBottomColor: colors.border }]}
                onPress={() => {
                  setInputText(item.original);
                  setTranslatedText(item.translated);
                }}
              >
                <Text style={[styles.historyOriginal, { color: colors.text }]}>{item.original}</Text>
                <Ionicons name="arrow-forward" size={16} color={colors.textSecondary} />
                <Text style={[styles.historyTranslated, { color: colors.textSecondary }]}>{item.translated}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  card: {
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  headerText: {
    fontSize: 16,
    fontWeight: '700',
  },
  input: {
    minHeight: 120,
    padding: 12,
    borderRadius: 12,
    fontSize: 16,
    textAlignVertical: 'top',
  },
  output: {
    minHeight: 120,
    padding: 12,
    borderRadius: 12,
    justifyContent: 'center',
  },
  outputText: {
    fontSize: 16,
    lineHeight: 24,
  },
  swapContainer: {
    alignItems: 'center',
    marginVertical: -8,
    zIndex: 10,
  },
  swapButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 5,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  button: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    gap: 8,
  },
  clearButton: {
    borderWidth: 1.5,
  },
  translateButton: {
    flex: 2,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  translateButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  historyContainer: {
    marginTop: 16,
    borderRadius: 16,
    padding: 16,
    maxHeight: 200,
  },
  historyTitle: {
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 12,
    textTransform: 'uppercase',
  },
  historyScroll: {
    maxHeight: 150,
  },
  historyItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    gap: 8,
  },
  historyOriginal: {
    flex: 1,
    fontSize: 14,
  },
  historyTranslated: {
    flex: 1,
    fontSize: 14,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  micButton: {
    padding: 4,
    borderRadius: 8,
  },
  micButtonActive: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
  },
  recordingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
    gap: 8,
  },
  recordingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#EF4444',
  },
  recordingText: {
    fontSize: 14,
    fontWeight: '600',
  },
});
