import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import Constants from 'expo-constants';
import { useTheme } from '../../contexts/ThemeContext';
import { useLanguageMode } from '../../contexts/LanguageModeContext';
import SpeechToTranslate from '../../components/SpeechToTranslate';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface Lesson {
  _id: string;
  title: string;
  category: string;
  subcategory: string;
  description: string;
  items: any[];
  order: number;
}

interface Category {
  key: string;
  title: string;
  icon: any;
  color: string;
  description: string;
}

export default function HomeScreen() {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);
  const [initialized, setInitialized] = useState(false);
  const router = useRouter();
  const { colors } = useTheme();
  const { languageMode } = useLanguageMode();

  const categories: Category[] = [
    {
      key: 'alphabet',
      title: 'Alphabet',
      icon: 'language',
      color: '#8B5CF6',
      description: 'Thai consonants and vowels',
    },
    {
      key: 'numbers',
      title: 'Numbers',
      icon: 'calculator',
      color: '#10B981',
      description: 'Learn to count in Thai',
    },
    {
      key: 'conversations',
      title: 'Conversations',
      icon: 'chatbubbles',
      color: '#F59E0B',
      description: 'Common phrases and dialogues',
    },
    {
      key: 'vocabulary',
      title: 'Vocabulary',
      icon: 'book',
      color: '#EC4899',
      description: 'Colors, animals, family & more',
    },
    {
      key: 'time',
      title: 'Time & Days',
      icon: 'time',
      color: '#06B6D4',
      description: 'Days, time expressions',
    },
    {
      key: 'grammar',
      title: 'Grammar',
      icon: 'list',
      color: '#8B5CF6',
      description: 'Question words & sentence patterns',
    },
    {
      key: 'intermediate',
      title: 'Intermediate',
      icon: 'school',
      color: '#EF4444',
      description: 'Shopping, emergencies & more',
    },
    {
      key: 'songs',
      title: 'Learning Songs',
      icon: 'musical-notes',
      color: '#F472B6',
      description: 'Fun songs to learn Thai',
    },
  ];

  useEffect(() => {
    loadLessons();
    checkInitialization();
  }, [languageMode]);

  const loadLessons = async () => {
    try {
      const modeParam = languageMode ? `?language_mode=${languageMode}` : '';
      const response = await fetch(`${API_URL}/api/lessons${modeParam}`);
      const data = await response.json();
      setLessons(data);
    } catch (error) {
      console.error('Error loading lessons:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkInitialization = async () => {
    try {
      // First try to get lessons to check if data exists
      const response = await fetch(`${API_URL}/api/lessons`);
      const data = await response.json();

      if (data.length === 0 && !initialized) {
        // Initialize data if empty
        const initResponse = await fetch(`${API_URL}/api/init-data`, {
          method: 'POST',
        });
        const initResult = await initResponse.json();
        console.log('Data initialized:', initResult);
        setInitialized(true);
        
        // Reload lessons after initialization
        loadLessons();
      }
    } catch (error) {
      console.error('Error checking initialization:', error);
      Alert.alert('Error', 'Failed to initialize data. Please check your connection.');
    }
  };

  const getLessonsByCategory = (category: string) => {
    return lessons.filter((lesson) => lesson.category === category);
  };

  const getCategoryInfo = (category: string, subcategory?: string) => {
    // Map icons based on category and subcategory
    const iconMap: { [key: string]: { icon: string; color: string } } = {
      // Alphabet
      'alphabet-consonants': { icon: 'text', color: '#8B5CF6' },
      'alphabet-vowels': { icon: 'chatbox-ellipses', color: '#A78BFA' },
      
      // Numbers
      'numbers-basic': { icon: 'calculator', color: '#10B981' },
      'numbers-large': { icon: 'stats-chart', color: '#059669' },
      
      // Conversations
      'conversations-greetings': { icon: 'hand-left', color: '#F59E0B' },
      'conversations-common': { icon: 'chatbubbles', color: '#FBBF24' },
      'conversations-dining': { icon: 'restaurant', color: '#FB923C' },
      'conversations-travel': { icon: 'airplane', color: '#F97316' },
      
      // Vocabulary
      'vocabulary-colors': { icon: 'color-palette', color: '#EC4899' },
      'vocabulary-family': { icon: 'people', color: '#F472B6' },
      'vocabulary-animals': { icon: 'paw', color: '#E879F9' },
      'vocabulary-insects': { icon: 'bug', color: '#D946EF' },
      'vocabulary-plants': { icon: 'leaf', color: '#A855F7' },
      'vocabulary-automotive': { icon: 'car', color: '#C026D3' },
      'vocabulary-anatomy': { icon: 'body', color: '#9333EA' },
      'vocabulary-household': { icon: 'home', color: '#7C3AED' },
      'vocabulary-clothing': { icon: 'shirt', color: '#6366F1' },
      'vocabulary-emotions': { icon: 'happy', color: '#EC4899' },
      'vocabulary-adjectives': { icon: 'sparkles', color: '#F472B6' },
      'vocabulary-verbs': { icon: 'flash', color: '#E879F9' },
      
      // Time
      'time-days': { icon: 'calendar', color: '#06B6D4' },
      'time-expressions': { icon: 'time', color: '#0891B2' },
      
      // Grammar
      'grammar-questions': { icon: 'help-circle', color: '#8B5CF6' },
      'grammar-politeness': { icon: 'ribbon', color: '#A78BFA' },
      
      // Intermediate
      'intermediate-shopping': { icon: 'cart', color: '#EF4444' },
      'intermediate-emergency': { icon: 'medkit', color: '#DC2626' },
      
      // Songs
      'songs-alphabet': { icon: 'musical-note', color: '#F472B6' },
      'songs-numbers': { icon: 'musical-notes', color: '#EC4899' },
      'songs-daily': { icon: 'sunny', color: '#E879F9' },
      'songs-vocabulary': { icon: 'color-fill', color: '#D946EF' },
      'songs-animals': { icon: 'nutrition', color: '#C026D3' },
      'songs-family': { icon: 'heart', color: '#A855F7' },
      'songs-time': { icon: 'alarm', color: '#9333EA' },
      'songs-anatomy': { icon: 'fitness', color: '#7C3AED' },
    };

    const key = subcategory ? `${category}-${subcategory}` : category;
    return iconMap[key] || { icon: 'book', color: '#6B7280' };
  };

  const handleCategoryPress = (category: string) => {
    const categoryLessons = getLessonsByCategory(category);
    if (categoryLessons.length === 1) {
      // Navigate directly to the lesson if there's only one
      router.push(`/lesson/${categoryLessons[0]._id}`);
    } else if (categoryLessons.length > 1) {
      // For now, navigate to first lesson, later can show list
      router.push(`/lesson/${categoryLessons[0]._id}`);
    }
  };

  const handleLessonPress = (lessonId: string) => {
    router.push(`/lesson/${lessonId}`);
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#4F46E5" />
          <Text style={styles.loadingText}>Loading lessons...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>
            {languageMode === 'learn-thai' ? 'Learn Thai' : 'Learn English'}
          </Text>
          <Text style={styles.subtitle}>Choose a category to start learning</Text>
        </View>

        {/* Speech-to-Translate Feature */}
        <View style={styles.translateSection}>
          <View style={styles.translateHeader}>
            <Ionicons name="language" size={24} color="#4F46E5" />
            <Text style={styles.translateTitle}>Instant Translator</Text>
          </View>
          <SpeechToTranslate />
        </View>

        {/* Songs Catalogue Banner */}
        <TouchableOpacity
          style={styles.songsBanner}
          onPress={() => router.push('/songs-catalogue' as any)}
          activeOpacity={0.8}
        >
          <View style={styles.songsBannerLeft}>
            <View style={styles.songsBannerIcon}>
              <Ionicons name="musical-notes" size={32} color="#FFFFFF" />
            </View>
            <View style={styles.songsBannerContent}>
              <Text style={styles.songsBannerTitle}>🎵 Songs Catalogue</Text>
              <Text style={styles.songsBannerText}>
                8 learning songs • Learn through music
              </Text>
            </View>
          </View>
          <Ionicons name="chevron-forward" size={24} color="#FFFFFF" />
        </TouchableOpacity>

        {/* Featured Categories Grid */}
        <View style={styles.featuredGrid}>
          {categories.slice(0, 4).map((category) => {
            const categoryLessons = getLessonsByCategory(category.key);
            return (
              <TouchableOpacity
                key={category.key}
                style={[styles.featuredCard, { backgroundColor: category.color + '15' }]}
                onPress={() => handleCategoryPress(category.key)}
                activeOpacity={0.8}
              >
                <View style={[styles.featuredIconCircle, { backgroundColor: category.color }]}>
                  <Ionicons name={category.icon as any} size={28} color="#FFFFFF" />
                </View>
                <Text style={styles.featuredTitle}>{category.title}</Text>
                <Text style={styles.featuredCount}>
                  {categoryLessons.length} {categoryLessons.length === 1 ? 'lesson' : 'lessons'}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* All Categories */}
        <View style={styles.categoriesContainer}>
          <Text style={styles.sectionTitle}>All Categories</Text>
          {categories.map((category) => {
            const categoryLessons = getLessonsByCategory(category.key);
            return (
              <TouchableOpacity
                key={category.key}
                style={styles.categoryCard}
                onPress={() => handleCategoryPress(category.key)}
                activeOpacity={0.7}
              >
                <View style={[styles.iconContainer, { backgroundColor: category.color + '20' }]}>
                  <Ionicons name={category.icon as any} size={32} color={category.color} />
                </View>
                <View style={styles.categoryContent}>
                  <Text style={styles.categoryTitle}>{category.title}</Text>
                  <Text style={styles.categoryDescription}>{category.description}</Text>
                  <Text style={styles.lessonCount}>
                    {categoryLessons.length} lesson{categoryLessons.length !== 1 ? 's' : ''}
                  </Text>
                </View>
                <Ionicons name="chevron-forward" size={24} color="#9CA3AF" />
              </TouchableOpacity>
            );
          })}
        </View>

        {/* All Lessons */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>All Lessons</Text>
            <View style={styles.lessonCountBadge}>
              <Text style={styles.lessonCountText}>{lessons.length}</Text>
            </View>
          </View>
          {lessons.map((lesson) => {
            const categoryInfo = getCategoryInfo(lesson.category, lesson.subcategory);
            return (
              <TouchableOpacity
                key={lesson._id}
                style={[
                  styles.lessonCard,
                  { borderLeftColor: categoryInfo.color, borderLeftWidth: 4 }
                ]}
                onPress={() => handleLessonPress(lesson._id)}
                activeOpacity={0.7}
              >
                <View style={[
                  styles.lessonIconContainer,
                  { backgroundColor: categoryInfo.color + '20' }
                ]}>
                  <Ionicons 
                    name={categoryInfo.icon as any} 
                    size={24} 
                    color={categoryInfo.color} 
                  />
                </View>
                <View style={styles.lessonContent}>
                  <Text style={styles.lessonTitle}>{lesson.title}</Text>
                  <Text style={styles.lessonDescription} numberOfLines={2}>
                    {lesson.description}
                  </Text>
                  <View style={styles.lessonFooter}>
                    <View style={[styles.badge, { backgroundColor: categoryInfo.color + '15' }]}>
                      <Text style={[styles.badgeText, { color: categoryInfo.color }]}>
                        {lesson.category}
                      </Text>
                    </View>
                    <View style={styles.itemCountContainer}>
                      <Ionicons name="layers" size={14} color="#9CA3AF" />
                      <Text style={styles.itemCount}>{lesson.items.length} items</Text>
                    </View>
                  </View>
                </View>
                <View style={styles.arrowContainer}>
                  <Ionicons name="chevron-forward" size={20} color="#9CA3AF" />
                </View>
              </TouchableOpacity>
            );
          })}
        </View>

        <View style={styles.bottomPadding} />
      </ScrollView>
      
      {/* Language Swap FAB */}
      <LanguageSwapFAB />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  scrollView: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6B7280',
  },
  header: {
    padding: 24,
    paddingTop: 16,
    paddingBottom: 8,
  },
  title: {
    fontSize: 34,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 15,
    color: '#6B7280',
    lineHeight: 22,
  },
  translateSection: {
    marginHorizontal: 16,
    marginBottom: 24,
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
  },
  translateHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  translateTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  songsBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginHorizontal: 16,
    marginBottom: 20,
    padding: 20,
    borderRadius: 20,
    background: 'linear-gradient(135deg, #F472B6 0%, #EC4899 100%)',
    backgroundColor: '#EC4899',
    shadowColor: '#EC4899',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 6,
  },
  songsBannerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 14,
  },
  songsBannerIcon: {
    width: 56,
    height: 56,
    borderRadius: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.25)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  songsBannerContent: {
    flex: 1,
  },
  songsBannerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  songsBannerText: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.9)',
    lineHeight: 18,
  },
  featuredGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 16,
    gap: 12,
    marginBottom: 24,
  },
  featuredCard: {
    width: '48%',
    aspectRatio: 1,
    borderRadius: 20,
    padding: 20,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
  },
  featuredIconCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  featuredTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
    textAlign: 'center',
  },
  featuredCount: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '500',
  },
  categoriesContainer: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  categoryCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 18,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.08,
    shadowRadius: 10,
    elevation: 3,
  },
  iconContainer: {
    width: 60,
    height: 60,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  categoryContent: {
    flex: 1,
  },
  categoryTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 4,
  },
  categoryDescription: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 4,
  },
  lessonCount: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 2,
  },
  section: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#111827',
  },
  lessonCountBadge: {
    backgroundColor: '#4F46E5',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    minWidth: 36,
    alignItems: 'center',
  },
  lessonCountText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  lessonCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  lessonIconContainer: {
    width: 52,
    height: 52,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  lessonContent: {
    flex: 1,
    paddingRight: 8,
  },
  lessonTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 5,
  },
  lessonDescription: {
    fontSize: 13,
    color: '#6B7280',
    marginBottom: 10,
    lineHeight: 18,
  },
  lessonFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'capitalize',
  },
  itemCountContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  itemCount: {
    fontSize: 12,
    color: '#9CA3AF',
    fontWeight: '500',
  },
  arrowContainer: {
    padding: 4,
  },
  bottomPadding: {
    height: 24,
  },
});