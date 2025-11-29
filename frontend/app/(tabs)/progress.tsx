import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import Constants from 'expo-constants';
import { useTheme } from '../../contexts/ThemeContext';
import { useLanguageMode } from '../../contexts/LanguageModeContext';
import { LinearGradient } from 'expo-linear-gradient';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;
const { width } = Dimensions.get('window');

interface ProgressItem {
  _id: string;
  lesson_id: string;
  completed: boolean;
  completed_items: number[];
  last_accessed: string;
}

interface Lesson {
  _id: string;
  title: string;
  category: string;
  subcategory: string;
  description: string;
  items: any[];
  order: number;
}

export default function ProgressScreen() {
  const [progress, setProgress] = useState<ProgressItem[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);
  const { colors } = useTheme();
  const { languageMode } = useLanguageMode();
  const router = useRouter();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [progressRes, lessonsRes] = await Promise.all([
        fetch(`${API_URL}/api/progress?user_id=default_user`),
        fetch(`${API_URL}/api/lessons`),
      ]);
      
      const progressData = await progressRes.json();
      const lessonsData = await lessonsRes.json();
      
      setProgress(progressData);
      setLessons(lessonsData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getLessonProgress = (lessonId: string) => {
    const prog = progress.find((p) => p.lesson_id === lessonId);
    const lesson = lessons.find((l) => l._id === lessonId);
    
    if (!prog || !lesson) return 0;
    
    return Math.round((prog.completed_items.length / lesson.items.length) * 100);
  };

  const getOverallProgress = () => {
    if (lessons.length === 0) return 0;
    
    let totalItems = 0;
    let completedItems = 0;
    
    lessons.forEach((lesson) => {
      totalItems += lesson.items.length;
      const prog = progress.find((p) => p.lesson_id === lesson._id);
      if (prog) {
        completedItems += prog.completed_items.length;
      }
    });
    
    return totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;
  };

  const getCategoryStats = () => {
    const allCategories = ['alphabet', 'numbers', 'conversations', 'vocabulary', 'time', 'grammar', 'intermediate', 'songs'];
    return allCategories.map((cat) => {
      const categoryLessons = lessons.filter((l) => l.category === cat);
      let totalItems = 0;
      let completedItems = 0;
      
      categoryLessons.forEach((lesson) => {
        totalItems += lesson.items.length;
        const prog = progress.find((p) => p.lesson_id === lesson._id);
        if (prog) {
          completedItems += prog.completed_items.length;
        }
      });
      
      const percentage = totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;
      
      return {
        category: cat,
        title: cat.charAt(0).toUpperCase() + cat.slice(1),
        percentage,
        completed: completedItems,
        total: totalItems,
        lessonsCount: categoryLessons.length,
      };
    }).filter(stat => stat.total > 0);
  };

  const getProgressStatus = (percentage: number): 'not-started' | 'in-progress' | 'completed' => {
    if (percentage === 0) return 'not-started';
    if (percentage === 100) return 'completed';
    return 'in-progress';
  };

  const getProgressIcon = (percentage: number) => {
    const status = getProgressStatus(percentage);
    if (status === 'completed') return 'checkmark-circle';
    if (status === 'in-progress') return 'hourglass';
    return 'ellipse-outline';
  };

  const getProgressColor = (percentage: number) => {
    const status = getProgressStatus(percentage);
    if (status === 'completed') return colors.success;
    if (status === 'in-progress') return colors.warning;
    return colors.textSecondary;
  };

  const categoryIcons: { [key: string]: any } = {
    alphabet: 'language',
    numbers: 'calculator',
    conversations: 'chatbubbles',
    vocabulary: 'book',
    time: 'time',
    grammar: 'list',
    intermediate: 'school',
    songs: 'musical-notes',
  };

  const categoryColors: { [key: string]: string } = {
    alphabet: '#8B5CF6',
    numbers: '#10B981',
    conversations: '#F59E0B',
    vocabulary: '#EC4899',
    time: '#06B6D4',
    grammar: '#8B5CF6',
    intermediate: '#EF4444',
    songs: '#F472B6',
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
            Loading your progress...
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  const overallProgress = getOverallProgress();
  const categoryStats = getCategoryStats();
  const totalCompleted = progress.reduce((sum, p) => sum + p.completed_items.length, 0);
  const totalItems = lessons.reduce((sum, l) => sum + l.items.length, 0);

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={[styles.title, { color: colors.text }]}>
            {languageMode === 'learn-english' ? '🇬🇧 Your Progress' : '🇹🇭 Your Progress'}
          </Text>
          <Text style={[styles.subtitle, { color: colors.textSecondary }]}>Keep up the great work!</Text>
        </View>

        {/* Overall Progress Card */}
        <View style={[styles.overallCard, { backgroundColor: colors.card, borderColor: colors.border }]}>
          <LinearGradient
            colors={[colors.primary + '15', colors.primary + '05']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.gradientOverlay}
          >
            <View style={styles.overallHeader}>
              <Ionicons name="trophy" size={32} color={colors.primary} />
              <Text style={[styles.overallTitle, { color: colors.text }]}>Overall Progress</Text>
            </View>
            
            <View style={styles.progressCircleContainer}>
              <View style={[styles.progressCircle, { borderColor: colors.primary }]}>
                <Text style={[styles.progressPercentage, { color: colors.primary }]}>{overallProgress}%</Text>
                <Text style={[styles.progressLabel, { color: colors.textSecondary }]}>Complete</Text>
              </View>
            </View>
            
            <View style={styles.statsRow}>
              <View style={styles.statItem}>
                <View style={[styles.statIconContainer, { backgroundColor: colors.primary + '20' }]}>
                  <Ionicons name="book" size={24} color={colors.primary} />
                </View>
                <Text style={[styles.statValue, { color: colors.text }]}>{lessons.length}</Text>
                <Text style={[styles.statLabel, { color: colors.textSecondary }]}>Lessons</Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <View style={[styles.statIconContainer, { backgroundColor: colors.success + '20' }]}>
                  <Ionicons name="checkmark-circle" size={24} color={colors.success} />
                </View>
                <Text style={[styles.statValue, { color: colors.text }]}>{totalCompleted}</Text>
                <Text style={[styles.statLabel, { color: colors.textSecondary }]}>Items Learned</Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <View style={[styles.statIconContainer, { backgroundColor: colors.warning + '20' }]}>
                  <Ionicons name="layers" size={24} color={colors.warning} />
                </View>
                <Text style={[styles.statValue, { color: colors.text }]}>{totalItems}</Text>
                <Text style={[styles.statLabel, { color: colors.textSecondary }]}>Total Items</Text>
              </View>
            </View>
          </LinearGradient>
        </View>

        {/* Category Progress */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>Progress by Category</Text>
          {categoryStats.map((stat) => (
            <View key={stat.category} style={[styles.categoryCard, { backgroundColor: colors.card, borderColor: colors.border }]}>
              <View style={styles.categoryHeader}>
                <View style={[styles.categoryIconContainer, { backgroundColor: categoryColors[stat.category] + '20' }]}>
                  <Ionicons
                    name={categoryIcons[stat.category]}
                    size={28}
                    color={categoryColors[stat.category]}
                  />
                </View>
                <View style={styles.categoryInfo}>
                  <Text style={[styles.categoryTitle, { color: colors.text }]}>{stat.title}</Text>
                  <Text style={[styles.categorySubtitle, { color: colors.textSecondary }]}>
                    {stat.completed} of {stat.total} items • {stat.lessonsCount} lessons
                  </Text>
                </View>
                <View style={styles.categoryRight}>
                  <Ionicons 
                    name={getProgressIcon(stat.percentage)} 
                    size={24} 
                    color={getProgressColor(stat.percentage)} 
                  />
                  <Text style={[styles.categoryPercentage, { color: categoryColors[stat.category] }]}>
                    {stat.percentage}%
                  </Text>
                </View>
              </View>
              <View style={[styles.progressBarContainer, { backgroundColor: colors.border }]}>
                <View
                  style={[
                    styles.progressBarFill,
                    {
                      width: `${stat.percentage}%`,
                      backgroundColor: categoryColors[stat.category],
                    },
                  ]}
                />
              </View>
            </View>
          ))}
        </View>

        {/* Lesson List with Quick Access */}
        <View style={styles.section}>
          <View style={styles.sectionHeaderRow}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>All Lessons</Text>
            <TouchableOpacity 
              style={[styles.viewAllButton, { backgroundColor: colors.primary + '15' }]}
              onPress={() => router.push('/(tabs)/all-lessons' as any)}
            >
              <Text style={[styles.viewAllText, { color: colors.primary }]}>View All</Text>
              <Ionicons name="arrow-forward" size={16} color={colors.primary} />
            </TouchableOpacity>
          </View>
          
          {lessons.slice(0, 5).map((lesson) => {
            const percentage = getLessonProgress(lesson._id);
            const status = getProgressStatus(percentage);
            
            return (
              <TouchableOpacity
                key={lesson._id}
                style={[styles.lessonCard, { backgroundColor: colors.card, borderColor: colors.border }]}
                onPress={() => handleLessonPress(lesson._id)}
                activeOpacity={0.7}
              >
                <View style={styles.lessonLeft}>
                  <View style={[styles.lessonIconCircle, { backgroundColor: categoryColors[lesson.category] + '20' }]}>
                    <Ionicons
                      name={categoryIcons[lesson.category]}
                      size={24}
                      color={categoryColors[lesson.category]}
                    />
                  </View>
                  <View style={styles.lessonInfo}>
                    <Text style={[styles.lessonTitle, { color: colors.text }]} numberOfLines={1}>
                      {lesson.title}
                    </Text>
                    <View style={styles.lessonMeta}>
                      <Ionicons 
                        name={getProgressIcon(percentage)} 
                        size={14} 
                        color={getProgressColor(percentage)} 
                      />
                      <Text style={[styles.lessonMetaText, { color: colors.textSecondary }]}>
                        {status === 'completed' ? 'Completed' : status === 'in-progress' ? 'In Progress' : 'Not Started'}
                      </Text>
                    </View>
                  </View>
                </View>
                <View style={styles.lessonRight}>
                  <Text style={[styles.lessonPercentage, { color: categoryColors[lesson.category] }]}>
                    {percentage}%
                  </Text>
                  <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
                </View>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* Achievements Badge */}
        <View style={[styles.achievementCard, { backgroundColor: colors.card, borderColor: colors.border }]}>
          <View style={styles.achievementHeader}>
            <Ionicons name="ribbon" size={32} color={colors.warning} />
            <Text style={[styles.achievementTitle, { color: colors.text }]}>Keep Going!</Text>
          </View>
          <Text style={[styles.achievementText, { color: colors.textSecondary }]}>
            {overallProgress < 25 
              ? "You're just getting started. Every lesson counts!"
              : overallProgress < 50
              ? "Great progress! You're building momentum!"
              : overallProgress < 75
              ? "You're more than halfway there. Keep pushing!"
              : overallProgress < 100
              ? "Almost there! Finish strong!"
              : "Amazing! You've completed everything!"}
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
    fontSize: 16,
  },
  overallCard: {
    marginHorizontal: 16,
    marginBottom: 24,
    borderRadius: 24,
    borderWidth: 1,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 20,
    elevation: 8,
  },
  gradientOverlay: {
    padding: 24,
  },
  overallHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 24,
  },
  overallTitle: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  progressCircleContainer: {
    alignItems: 'center',
    marginBottom: 32,
  },
  progressCircle: {
    width: 140,
    height: 140,
    borderRadius: 70,
    borderWidth: 8,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.5)',
  },
  progressPercentage: {
    fontSize: 40,
    fontWeight: 'bold',
  },
  progressLabel: {
    fontSize: 14,
    marginTop: 4,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  statItem: {
    alignItems: 'center',
    flex: 1,
  },
  statIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 4,
  },
  statLabel: {
    fontSize: 12,
    marginTop: 4,
    textAlign: 'center',
  },
  statDivider: {
    width: 1,
    height: 60,
    backgroundColor: 'rgba(0,0,0,0.1)',
  },
  section: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  viewAllButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 4,
  },
  viewAllText: {
    fontSize: 14,
    fontWeight: '600',
  },
  categoryCard: {
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  categoryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  categoryIconContainer: {
    width: 56,
    height: 56,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  categoryInfo: {
    flex: 1,
  },
  categoryTitle: {
    fontSize: 17,
    fontWeight: '700',
    marginBottom: 4,
  },
  categorySubtitle: {
    fontSize: 13,
  },
  categoryRight: {
    alignItems: 'center',
    gap: 4,
  },
  categoryPercentage: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  progressBarContainer: {
    height: 10,
    borderRadius: 5,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 5,
  },
  lessonCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
  },
  lessonLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 12,
  },
  lessonIconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  lessonInfo: {
    flex: 1,
  },
  lessonTitle: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 4,
  },
  lessonMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  lessonMetaText: {
    fontSize: 12,
  },
  lessonRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  lessonPercentage: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  achievementCard: {
    marginHorizontal: 16,
    padding: 20,
    borderRadius: 20,
    borderWidth: 1,
    alignItems: 'center',
  },
  achievementHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  achievementTitle: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  achievementText: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
  bottomPadding: {
    height: 24,
  },
});
