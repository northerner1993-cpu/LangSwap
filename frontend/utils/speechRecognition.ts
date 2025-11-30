// Speech Recognition Utility for Web and Mobile
import Voice from '@react-native-voice/voice';
import { Platform, Alert } from 'react-native';

export class SpeechRecognitionService {
  private static isListening = false;
  
  static async startListening(language: string, onResult: (text: string) => void, onError?: (error: string) => void): Promise<boolean> {
    try {
      if (Platform.OS === 'web') {
        // Web Speech Recognition
        return this.startWebSpeechRecognition(language, onResult, onError);
      } else {
        // Mobile Voice Recognition
        return this.startMobileSpeechRecognition(language, onResult, onError);
      }
    } catch (error) {
      console.error('Speech recognition error:', error);
      if (onError) onError(String(error));
      return false;
    }
  }

  private static async startMobileSpeechRecognition(language: string, onResult: (text: string) => void, onError?: (error: string) => void): Promise<boolean> {
    try {
      const available = await Voice.isAvailable();
      if (!available) {
        Alert.alert('Not Available', 'Speech recognition is not available on this device');
        return false;
      }

      // Set language code
      const langCode = language === 'th' ? 'th-TH' : 'en-US';
      
      // Start recognition
      await Voice.start(langCode);
      this.isListening = true;

      // Setup listeners
      Voice.onSpeechResults = (event: any) => {
        if (event.value && event.value.length > 0) {
          onResult(event.value[0]);
        }
      };

      Voice.onSpeechError = (event: any) => {
        console.error('Speech error:', event);
        if (onError) onError('Speech recognition failed');
        this.isListening = false;
      };

      return true;
    } catch (error) {
      console.error('Mobile speech recognition error:', error);
      if (onError) onError(String(error));
      return false;
    }
  }

  private static startWebSpeechRecognition(language: string, onResult: (text: string) => void, onError?: (error: string) => void): Promise<boolean> {
    return new Promise((resolve) => {
      try {
        // @ts-ignore - Web Speech API
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
          Alert.alert('Not Supported', 'Speech recognition is not supported in this browser. Try Chrome, Edge, or Safari.');
          resolve(false);
          return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = language === 'th' ? 'th-TH' : 'en-US';
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        recognition.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          onResult(transcript);
          this.isListening = false;
        };

        recognition.onerror = (event: any) => {
          console.error('Web speech error:', event.error);
          if (onError) onError(`Speech recognition error: ${event.error}`);
          this.isListening = false;
        };

        recognition.onend = () => {
          this.isListening = false;
        };

        recognition.start();
        this.isListening = true;
        resolve(true);
      } catch (error) {
        console.error('Web speech recognition setup error:', error);
        if (onError) onError(String(error));
        resolve(false);
      }
    });
  }

  static async stopListening(): Promise<void> {
    try {
      if (Platform.OS === 'web') {
        // Web speech stops automatically
        this.isListening = false;
      } else {
        await Voice.stop();
        this.isListening = false;
      }
    } catch (error) {
      console.error('Error stopping speech recognition:', error);
    }
  }

  static isCurrentlyListening(): boolean {
    return this.isListening;
  }

  static cleanup(): void {
    if (Platform.OS !== 'web') {
      Voice.destroy().then(Voice.removeAllListeners);
    }
    this.isListening = false;
  }
}
