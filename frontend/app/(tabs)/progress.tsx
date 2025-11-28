import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

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
  items: any[];
}

export default function ProgressScreen() {
  const [progress, setProgress] = useState<ProgressItem[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);

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
    const categories = ['alphabet', 'numbers', 'conversations'];
    return categories.map((cat) => {
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
      };
    });
  };

  const categoryIcons: { [key: string]: any } = {
    alphabet: 'language',
    numbers: 'calculator',
    conversations: 'chatbubbles',
  };

  const categoryColors: { [key: string]: string } = {
    alphabet: '#8B5CF6',
    numbers: '#10B981',
    conversations: '#F59E0B',
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#4F46E5" />
        </View>
      </SafeAreaView>
    );
  }

  const overallProgress = getOverallProgress();
  const categoryStats = getCategoryStats();

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.title}>Your Progress</Text>
          <Text style={styles.subtitle}>Keep up the great work!</Text>
        </View>

        {/* Overall Progress */}
        <View style={styles.overallCard}>
          <Text style={styles.overallTitle}>Overall Progress</Text>
          <View style={styles.progressCircle}>
            <Text style={styles.progressPercentage}>{overallProgress}%</Text>
            <Text style={styles.progressLabel}>Complete</Text>
          </View>
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Ionicons name="book" size={24} color="#4F46E5" />
              <Text style={styles.statValue}>{lessons.length}</Text>
              <Text style={styles.statLabel}>Lessons</Text>
            </View>
            <View style={styles.statItem}>
              <Ionicons name="checkmark-circle" size={24} color="#10B981" />
              <Text style={styles.statValue}>
                {progress.reduce((sum, p) => sum + p.completed_items.length, 0)}
              </Text>
              <Text style={styles.statLabel}>Items Learned</Text>
            </View>
          </View>
        </View>

        {/* Category Progress */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>By Category</Text>
          {categoryStats.map((stat) => (
            <View key={stat.category} style={styles.categoryCard}>
              <View style={styles.categoryHeader}>
                <View style={styles.categoryIconContainer}>
                  <Ionicons
                    name={categoryIcons[stat.category]}
                    size={24}
                    color={categoryColors[stat.category]}
                  />
                </View>
                <View style={styles.categoryInfo}>
                  <Text style={styles.categoryTitle}>{stat.title}</Text>
                  <Text style={styles.categorySubtitle}>
                    {stat.completed} of {stat.total} items
                  </Text>
                </View>
                <Text style={styles.categoryPercentage}>{stat.percentage}%</Text>
              </View>
              <View style={styles.progressBarContainer}>
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
  overallCard: {
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    marginBottom: 24,
    borderRadius: 20,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
  },
  overallTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 20,
    textAlign: 'center',
  },
  progressCircle: {
    alignItems: 'center',
    marginBottom: 24,
  },
  progressPercentage: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#4F46E5',
  },
  progressLabel: {
    fontSize: 14,
    color: '#9CA3AF',
    marginTop: 4,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 4,
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
  categoryCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  categoryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  categoryIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  categoryInfo: {
    flex: 1,
  },
  categoryTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 2,
  },
  categorySubtitle: {
    fontSize: 13,
    color: '#9CA3AF',
  },
  categoryPercentage: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#4F46E5',
  },
  progressBarContainer: {
    height: 8,
    backgroundColor: '#E5E7EB',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  bottomPadding: {
    height: 24,
  },
});