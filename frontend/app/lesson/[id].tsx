import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter, useLocalSearchParams } from 'expo-router';
import Constants from 'expo-constants';
import * as Speech from 'expo-speech';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;
const { width } = Dimensions.get('window');

interface LessonItem {
  thai: string;
  romanization: string;
  english: string;
  example?: string;
}

interface Lesson {
  _id: string;
  title: string;
  category: string;
  subcategory: string;
  description: string;
  items: LessonItem[];
}

export default function LessonScreen() {
  const { id } = useLocalSearchParams();
  const router = useRouter();
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [favorites, setFavorites] = useState<Set<number>>(new Set());
  const [completedItems, setCompletedItems] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLesson();
    loadFavorites();
    loadProgress();
  }, [id]);

  const loadLesson = async () => {
    try {
      const response = await fetch(`${API_URL}/api/lessons/${id}`);
      const data = await response.json();
      setLesson(data);
    } catch (error) {
      console.error('Error loading lesson:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFavorites = async () => {
    try {
      const response = await fetch(`${API_URL}/api/favorites?user_id=default_user`);
      const data = await response.json();
      const lessonFavorites = data.filter((f: any) => f.lesson_id === id);
      setFavorites(new Set(lessonFavorites.map((f: any) => f.item_index)));
    } catch (error) {
      console.error('Error loading favorites:', error);
    }
  };

  const loadProgress = async () => {
    try {
      const response = await fetch(`${API_URL}/api/progress?user_id=default_user`);
      const data = await response.json();
      const lessonProgress = data.find((p: any) => p.lesson_id === id);
      if (lessonProgress) {
        setCompletedItems(new Set(lessonProgress.completed_items));
      }
    } catch (error) {
      console.error('Error loading progress:', error);
    }
  };

  const saveProgress = async () => {
    try {
      await fetch(`${API_URL}/api/progress`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'default_user',
          lesson_id: id,
          completed_items: Array.from(completedItems),
          completed: lesson ? completedItems.size === lesson.items.length : false,
        }),
      });
    } catch (error) {
      console.error('Error saving progress:', error);
    }
  };

  const speakThai = async (text: string) => {
    try {
      // Stop any ongoing speech
      await Speech.stop();
      
      // Speak the Thai text with Thai language settings
      Speech.speak(text, {
        language: 'th-TH', // Thai language
        pitch: 1.0,
        rate: 0.75, // Slightly slower for learning
      });
    } catch (error) {
      console.error('Error speaking:', error);
      Alert.alert('Error', 'Text-to-speech is not available');
    }
  };

  const toggleFavorite = async () => {
    if (!lesson) return;
    
    const item = lesson.items[currentIndex];
    try {
      await fetch(`${API_URL}/api/favorites`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'default_user',
          lesson_id: id,
          item_index: currentIndex,
          item_data: item,
        }),
      });
      
      const newFavorites = new Set(favorites);
      if (favorites.has(currentIndex)) {
        newFavorites.delete(currentIndex);
      } else {
        newFavorites.add(currentIndex);
      }
      setFavorites(newFavorites);
    } catch (error) {
      console.error('Error toggling favorite:', error);
    }
  };

  const handleNext = () => {
    if (!lesson) return;
    
    // Mark current item as completed
    const newCompleted = new Set(completedItems);
    newCompleted.add(currentIndex);
    setCompletedItems(newCompleted);
    
    if (currentIndex < lesson.items.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setShowAnswer(false);
    } else {
      // Lesson completed
      saveProgress();
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setShowAnswer(false);
    }
  };

  useEffect(() => {
    if (completedItems.size > 0) {
      saveProgress();
    }
  }, [completedItems]);

  if (loading || !lesson) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#4F46E5" />
        </View>
      </SafeAreaView>
    );
  }

  const currentItem = lesson.items[currentIndex];
  const progress = Math.round(((currentIndex + 1) / lesson.items.length) * 100);

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#111827" />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>{lesson.title}</Text>
          <Text style={styles.headerSubtitle}>
            {currentIndex + 1} / {lesson.items.length}
          </Text>
        </View>
        <TouchableOpacity onPress={toggleFavorite} style={styles.favoriteButton}>
          <Ionicons
            name={favorites.has(currentIndex) ? 'heart' : 'heart-outline'}
            size={24}
            color={favorites.has(currentIndex) ? '#EF4444' : '#9CA3AF'}
          />
        </TouchableOpacity>
      </View>

      {/* Progress Bar */}
      <View style={styles.progressContainer}>
        <View style={[styles.progressBar, { width: `${progress}%` }]} />
      </View>

      {/* Flashcard */}
      <View style={styles.cardContainer}>
        <TouchableOpacity
          style={styles.card}
          onPress={() => setShowAnswer(!showAnswer)}
          activeOpacity={0.9}
        >
          <View style={styles.cardContent}>
            {!showAnswer ? (
              <>
                <Text style={styles.thaiText}>{currentItem.thai}</Text>
                <Text style={styles.tapHint}>Tap to reveal</Text>
              </>
            ) : (
              <>
                <Text style={styles.thaiTextSmall}>{currentItem.thai}</Text>
                <Text style={styles.romanText}>{currentItem.romanization}</Text>
                <Text style={styles.englishText}>{currentItem.english}</Text>
                {currentItem.example && (
                  <View style={styles.exampleContainer}>
                    <Text style={styles.exampleLabel}>Example:</Text>
                    <Text style={styles.exampleText}>{currentItem.example}</Text>
                  </View>
                )}
              </>
            )}
          </View>
          
          {completedItems.has(currentIndex) && (
            <View style={styles.checkmarkBadge}>
              <Ionicons name="checkmark-circle" size={32} color="#10B981" />
            </View>
          )}
        </TouchableOpacity>
      </View>

      {/* Navigation Buttons */}
      <View style={styles.navigation}>
        <TouchableOpacity
          style={[styles.navButton, currentIndex === 0 && styles.navButtonDisabled]}
          onPress={handlePrevious}
          disabled={currentIndex === 0}
        >
          <Ionicons
            name="chevron-back"
            size={24}
            color={currentIndex === 0 ? '#D1D5DB' : '#4F46E5'}
          />
          <Text
            style={[
              styles.navButtonText,
              currentIndex === 0 && styles.navButtonTextDisabled,
            ]}
          >
            Previous
          </Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.revealButton} onPress={() => setShowAnswer(!showAnswer)}>
          <Ionicons name={showAnswer ? 'eye-off' : 'eye'} size={20} color="#FFFFFF" />
          <Text style={styles.revealButtonText}>
            {showAnswer ? 'Hide' : 'Reveal'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.navButton} onPress={handleNext}>
          <Text style={styles.navButtonText}>
            {currentIndex === lesson.items.length - 1 ? 'Complete' : 'Next'}
          </Text>
          <Ionicons name="chevron-forward" size={24} color="#4F46E5" />
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    padding: 8,
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#9CA3AF',
    marginTop: 2,
  },
  favoriteButton: {
    padding: 8,
  },
  progressContainer: {
    height: 4,
    backgroundColor: '#E5E7EB',
    marginHorizontal: 16,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    backgroundColor: '#4F46E5',
    borderRadius: 2,
  },
  cardContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  card: {
    width: width - 48,
    minHeight: 400,
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 32,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 16,
    elevation: 8,
  },
  cardContent: {
    alignItems: 'center',
    width: '100%',
  },
  thaiText: {
    fontSize: 64,
    fontWeight: 'bold',
    color: '#111827',
    textAlign: 'center',
  },
  thaiTextSmall: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 16,
    textAlign: 'center',
  },
  tapHint: {
    fontSize: 16,
    color: '#9CA3AF',
    marginTop: 24,
  },
  romanText: {
    fontSize: 24,
    color: '#6366F1',
    marginBottom: 12,
    textAlign: 'center',
  },
  englishText: {
    fontSize: 20,
    color: '#374151',
    textAlign: 'center',
    marginBottom: 16,
  },
  exampleContainer: {
    marginTop: 16,
    padding: 16,
    backgroundColor: '#F3F4F6',
    borderRadius: 12,
    width: '100%',
  },
  exampleLabel: {
    fontSize: 12,
    color: '#9CA3AF',
    fontWeight: '600',
    marginBottom: 4,
  },
  exampleText: {
    fontSize: 14,
    color: '#6B7280',
    fontStyle: 'italic',
  },
  checkmarkBadge: {
    position: 'absolute',
    top: 16,
    right: 16,
  },
  navigation: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingBottom: 24,
    paddingTop: 16,
  },
  navButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
  },
  navButtonDisabled: {
    opacity: 0.4,
  },
  navButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#4F46E5',
    marginHorizontal: 4,
  },
  navButtonTextDisabled: {
    color: '#D1D5DB',
  },
  revealButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#4F46E5',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
  },
  revealButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginLeft: 8,
  },
});