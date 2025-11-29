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
  ];

  useEffect(() => {
    initializeData();
  }, []);

  const initializeData = async () => {
    try {
      // First try to get lessons
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
        
        // Fetch lessons again
        const newResponse = await fetch(`${API_URL}/api/lessons`);
        const newData = await newResponse.json();
        setLessons(newData);
      } else {
        setLessons(data);
      }
    } catch (error) {
      console.error('Error fetching lessons:', error);
      Alert.alert('Error', 'Failed to load lessons. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const getLessonsByCategory = (category: string) => {
    return lessons.filter((lesson) => lesson.category === category);
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
          <Text style={styles.title}>Learn Thai</Text>
          <Text style={styles.subtitle}>Choose a category to start learning</Text>
        </View>

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
          <Text style={styles.sectionTitle}>All Lessons</Text>
          {lessons.map((lesson) => (
            <TouchableOpacity
              key={lesson._id}
              style={styles.lessonCard}
              onPress={() => handleLessonPress(lesson._id)}
              activeOpacity={0.7}
            >
              <View style={styles.lessonContent}>
                <Text style={styles.lessonTitle}>{lesson.title}</Text>
                <Text style={styles.lessonDescription}>{lesson.description}</Text>
                <View style={styles.lessonFooter}>
                  <View style={styles.badge}>
                    <Text style={styles.badgeText}>{lesson.category}</Text>
                  </View>
                  <Text style={styles.itemCount}>{lesson.items.length} items</Text>
                </View>
              </View>
              <Ionicons name="arrow-forward" size={20} color="#4F46E5" />
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.bottomPadding} />
      </ScrollView>
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
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6B7280',
  },
  categoriesContainer: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  categoryCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  iconContainer: {
    width: 64,
    height: 64,
    borderRadius: 16,
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
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 16,
  },
  lessonCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1,
  },
  lessonContent: {
    flex: 1,
  },
  lessonTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  lessonDescription: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 8,
  },
  lessonFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  badge: {
    backgroundColor: '#EEF2FF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  badgeText: {
    fontSize: 12,
    color: '#4F46E5',
    fontWeight: '600',
  },
  itemCount: {
    fontSize: 12,
    color: '#9CA3AF',
  },
  bottomPadding: {
    height: 24,
  },
});