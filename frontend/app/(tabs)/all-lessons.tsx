import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import Constants from 'expo-constants';
import { useTheme } from '../../contexts/ThemeContext';
import { useLanguageMode } from '../../contexts/LanguageModeContext';

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

export default function AllLessonsScreen() {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const router = useRouter();
  const { colors } = useTheme();
  const { languageMode } = useLanguageMode();

  const categories = [
    { key: 'all', title: 'All', icon: 'grid', color: colors.primary },
    { key: 'alphabet', title: 'Alphabet', icon: 'language', color: '#8B5CF6' },
    { key: 'numbers', title: 'Numbers', icon: 'calculator', color: '#10B981' },
    { key: 'conversations', title: 'Conversations', icon: 'chatbubbles', color: '#F59E0B' },
    { key: 'vocabulary', title: 'Vocabulary', icon: 'book', color: '#EC4899' },
    { key: 'time', title: 'Time', icon: 'time', color: '#06B6D4' },
    { key: 'grammar', title: 'Grammar', icon: 'list', color: '#8B5CF6' },
    { key: 'intermediate', title: 'Intermediate', icon: 'school', color: '#EF4444' },
    { key: 'songs', title: 'Songs', icon: 'musical-notes', color: '#F472B6' },
  ];

  useEffect(() => {
    loadLessons();
  }, []);

  const loadLessons = async () => {
    try {
      const response = await fetch(`${API_URL}/api/lessons`);
      const data = await response.json();
      setLessons(data);
    } catch (error) {
      console.error('Error loading lessons:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFilteredLessons = () => {
    if (selectedCategory === 'all') {
      return lessons;
    }
    return lessons.filter(lesson => lesson.category === selectedCategory);
  };

  const getCategoryInfo = (category: string, subcategory?: string) => {
    const iconMap: { [key: string]: { icon: string; color: string } } = {
      'alphabet-consonants': { icon: 'text', color: '#8B5CF6' },
      'alphabet-vowels': { icon: 'chatbox-ellipses', color: '#A78BFA' },
      'numbers-basic': { icon: 'calculator', color: '#10B981' },
      'numbers-large': { icon: 'stats-chart', color: '#059669' },
      'conversations-greetings': { icon: 'hand-left', color: '#F59E0B' },
      'conversations-common': { icon: 'chatbubbles', color: '#FBBF24' },
      'conversations-dining': { icon: 'restaurant', color: '#FB923C' },
      'conversations-travel': { icon: 'airplane', color: '#F97316' },
      'vocabulary-colors': { icon: 'color-palette', color: '#EC4899' },
      'vocabulary-family': { icon: 'people', color: '#F472B6' },
      'vocabulary-animals': { icon: 'paw', color: '#E879F9' },
      'songs-alphabet': { icon: 'musical-note', color: '#F472B6' },
      'songs-numbers': { icon: 'musical-notes', color: '#EC4899' },
    };

    const key = subcategory ? `${category}-${subcategory}` : category;
    return iconMap[key] || { icon: 'book', color: colors.primary };
  };

  const handleLessonPress = (lessonId: string) => {
    router.push(`/lesson/${lessonId}`);
  };

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[styles.loadingText, { color: colors.textSecondary }]}>
            Loading lessons...
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  const filteredLessons = getFilteredLessons();

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={[styles.title, { color: colors.text }]}>
            {languageMode === 'learn-english' ? '🇬🇧 All English Lessons' : '🇹🇭 All Thai Lessons'}
          </Text>
          <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
            Browse all available learning content
          </Text>
        </View>

        {/* Category Filters */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.categoriesScroll}
          contentContainerStyle={styles.categoriesContainer}
        >
          {categories.map((category) => {
            const isSelected = selectedCategory === category.key;
            const count = category.key === 'all' 
              ? lessons.length 
              : lessons.filter(l => l.category === category.key).length;

            return (
              <TouchableOpacity
                key={category.key}
                style={[
                  styles.categoryChip,
                  isSelected && { backgroundColor: category.color },
                  !isSelected && { 
                    backgroundColor: colors.card,
                    borderWidth: 1,
                    borderColor: colors.border,
                  },
                ]}
                onPress={() => setSelectedCategory(category.key)}
                activeOpacity={0.7}
              >
                <Ionicons
                  name={category.icon as any}
                  size={18}
                  color={isSelected ? '#FFFFFF' : category.color}
                />
                <Text
                  style={[
                    styles.categoryChipText,
                    { color: isSelected ? '#FFFFFF' : colors.text },
                  ]}
                >
                  {category.title}
                </Text>
                <View
                  style={[
                    styles.countBadge,
                    { backgroundColor: isSelected ? 'rgba(255,255,255,0.3)' : category.color + '20' },
                  ]}
                >
                  <Text
                    style={[
                      styles.countBadgeText,
                      { color: isSelected ? '#FFFFFF' : category.color },
                    ]}
                  >
                    {count}
                  </Text>
                </View>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {/* Lessons List */}
        <View style={styles.lessonsSection}>
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>
              {selectedCategory === 'all' 
                ? 'All Lessons' 
                : categories.find(c => c.key === selectedCategory)?.title}
            </Text>
            <View style={[styles.lessonCountBadge, { backgroundColor: colors.primary }]}>
              <Text style={styles.lessonCountText}>{filteredLessons.length}</Text>
            </View>
          </View>

          {filteredLessons.map((lesson) => {
            const categoryInfo = getCategoryInfo(lesson.category, lesson.subcategory);
            
            return (
              <TouchableOpacity
                key={lesson._id}
                style={[
                  styles.lessonCard,
                  { backgroundColor: colors.card, borderColor: colors.border, borderLeftColor: categoryInfo.color }
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
                  <Text style={[styles.lessonTitle, { color: colors.text }]}>{lesson.title}</Text>
                  <Text style={[styles.lessonDescription, { color: colors.textSecondary }]} numberOfLines={2}>
                    {lesson.description}
                  </Text>
                  <View style={styles.lessonFooter}>
                    <View style={[styles.badge, { backgroundColor: categoryInfo.color + '15' }]}>
                      <Text style={[styles.badgeText, { color: categoryInfo.color }]}>
                        {lesson.category}
                      </Text>
                    </View>
                    <View style={styles.itemCountContainer}>
                      <Ionicons name="layers" size={14} color={colors.textSecondary} />
                      <Text style={[styles.itemCount, { color: colors.textSecondary }]}>
                        {lesson.items.length} items
                      </Text>
                    </View>
                  </View>
                </View>
                <View style={styles.arrowContainer}>
                  <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
                </View>
              </TouchableOpacity>
            );
          })}
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 16,
  },
  header: {
    padding: 24,
    paddingTop: 16,
    paddingBottom: 16,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 15,
  },
  categoriesScroll: {
    marginBottom: 20,
  },
  categoriesContainer: {
    paddingHorizontal: 20,
    gap: 10,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    gap: 8,
  },
  categoryChipText: {
    fontSize: 13,
    fontWeight: '600',
  },
  countBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    minWidth: 22,
    alignItems: 'center',
  },
  countBadgeText: {
    fontSize: 11,
    fontWeight: 'bold',
  },
  lessonsSection: {
    paddingHorizontal: 20,
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
  },
  lessonCountBadge: {
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
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderLeftWidth: 4,
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
    marginBottom: 5,
  },
  lessonDescription: {
    fontSize: 13,
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
    fontWeight: '500',
  },
  arrowContainer: {
    padding: 4,
  },
  bottomPadding: {
    height: 24,
  },
});
