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
import { useTheme } from '../contexts/ThemeContext';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface Song {
  _id: string;
  title: string;
  category: string;
  subcategory: string;
  description: string;
  items: any[];
  order: number;
}

interface SongCategory {
  key: string;
  title: string;
  icon: string;
  color: string;
  description: string;
}

export default function SongsCatalogueScreen() {
  const [songs, setSongs] = useState<Song[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const router = useRouter();
  const { colors } = useTheme();

  const songCategories: SongCategory[] = [
    {
      key: 'all',
      title: 'All Songs',
      icon: 'musical-notes',
      color: '#F472B6',
      description: 'Browse all learning songs',
    },
    {
      key: 'alphabet',
      title: 'Alphabet',
      icon: 'text',
      color: '#8B5CF6',
      description: 'Learn letters through song',
    },
    {
      key: 'numbers',
      title: 'Numbers',
      icon: 'calculator',
      color: '#10B981',
      description: 'Count with music',
    },
    {
      key: 'daily',
      title: 'Daily Life',
      icon: 'sunny',
      color: '#F59E0B',
      description: 'Everyday routines',
    },
    {
      key: 'vocabulary',
      title: 'Vocabulary',
      icon: 'color-palette',
      color: '#EC4899',
      description: 'Words & objects',
    },
    {
      key: 'animals',
      title: 'Animals',
      icon: 'paw',
      color: '#06B6D4',
      description: 'Animal sounds & names',
    },
    {
      key: 'family',
      title: 'Family',
      icon: 'people',
      color: '#A855F7',
      description: 'Family members',
    },
    {
      key: 'time',
      title: 'Time',
      icon: 'time',
      color: '#3B82F6',
      description: 'Days & time',
    },
    {
      key: 'anatomy',
      title: 'Body Parts',
      icon: 'body',
      color: '#EF4444',
      description: 'Learn body parts',
    },
  ];

  useEffect(() => {
    loadSongs();
  }, []);

  const loadSongs = async () => {
    try {
      const response = await fetch(`${API_URL}/api/lessons?category=songs`);
      const data = await response.json();
      setSongs(data);
    } catch (error) {
      console.error('Error loading songs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFilteredSongs = () => {
    if (selectedCategory === 'all') {
      return songs;
    }
    return songs.filter(song => song.subcategory === selectedCategory);
  };

  const getSongIcon = (subcategory: string) => {
    const category = songCategories.find(c => c.key === subcategory);
    return category?.icon || 'musical-note';
  };

  const getSongColor = (subcategory: string) => {
    const category = songCategories.find(c => c.key === subcategory);
    return category?.color || '#F472B6';
  };

  const handleSongPress = (songId: string) => {
    router.push(`/lesson/${songId}`);
  };

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[styles.loadingText, { color: colors.textSecondary }]}>
            Loading songs...
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  const filteredSongs = getFilteredSongs();

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color={colors.text} />
          </TouchableOpacity>
          <View style={styles.headerContent}>
            <Text style={[styles.title, { color: colors.text }]}>🎵 Songs Catalogue</Text>
            <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
              Learn Thai through music
            </Text>
          </View>
        </View>

        {/* Category Filters */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.categoriesScroll}
          contentContainerStyle={styles.categoriesContainer}
        >
          {songCategories.map((category) => {
            const isSelected = selectedCategory === category.key;
            const categoryCount = category.key === 'all' 
              ? songs.length 
              : songs.filter(s => s.subcategory === category.key).length;

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
                  size={20}
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
                {categoryCount > 0 && (
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
                      {categoryCount}
                    </Text>
                  </View>
                )}
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {/* Songs Grid */}
        <View style={styles.songsSection}>
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>
              {selectedCategory === 'all' ? 'All Songs' : songCategories.find(c => c.key === selectedCategory)?.title}
            </Text>
            <View style={[styles.songCountBadge, { backgroundColor: colors.primary }]}>
              <Text style={styles.songCountText}>{filteredSongs.length}</Text>
            </View>
          </View>

          {filteredSongs.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Ionicons name="musical-notes-outline" size={64} color={colors.textSecondary} />
              <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
                No songs in this category yet
              </Text>
            </View>
          ) : (
            <View style={styles.songsGrid}>
              {filteredSongs.map((song) => {
                const songColor = getSongColor(song.subcategory);
                const songIcon = getSongIcon(song.subcategory);
                
                return (
                  <TouchableOpacity
                    key={song._id}
                    style={[
                      styles.songCard,
                      { backgroundColor: colors.card, borderColor: colors.border },
                    ]}
                    onPress={() => handleSongPress(song._id)}
                    activeOpacity={0.8}
                  >
                    <View style={[styles.songIconContainer, { backgroundColor: songColor + '20' }]}>
                      <Ionicons name={songIcon as any} size={32} color={songColor} />
                    </View>
                    <Text style={[styles.songTitle, { color: colors.text }]} numberOfLines={2}>
                      {song.title}
                    </Text>
                    <Text style={[styles.songDescription, { color: colors.textSecondary }]} numberOfLines={2}>
                      {song.description}
                    </Text>
                    <View style={styles.songFooter}>
                      <View style={[styles.verseBadge, { backgroundColor: songColor + '15' }]}>
                        <Ionicons name="musical-note" size={12} color={songColor} />
                        <Text style={[styles.verseText, { color: songColor }]}>
                          {song.items.length} verses
                        </Text>
                      </View>
                      <Ionicons name="play-circle" size={24} color={songColor} />
                    </View>
                  </TouchableOpacity>
                );
              })}
            </View>
          )}
        </View>

        {/* Info Banner */}
        <View style={[styles.infoBanner, { backgroundColor: colors.card, borderColor: colors.border }]}>
          <Ionicons name="information-circle" size={24} color={colors.primary} />
          <View style={styles.infoBannerContent}>
            <Text style={[styles.infoBannerTitle, { color: colors.text }]}>
              Learning Through Songs
            </Text>
            <Text style={[styles.infoBannerText, { color: colors.textSecondary }]}>
              Songs help improve memory retention by 40%! Tap any song to start learning with auto-play pronunciation.
            </Text>
          </View>
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
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    paddingTop: 16,
    gap: 12,
  },
  backButton: {
    padding: 8,
  },
  headerContent: {
    flex: 1,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 15,
  },
  categoriesScroll: {
    marginBottom: 24,
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
    fontSize: 14,
    fontWeight: '600',
  },
  countBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    minWidth: 24,
    alignItems: 'center',
  },
  countBadgeText: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  songsSection: {
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
  songCountBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    minWidth: 36,
    alignItems: 'center',
  },
  songCountText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 60,
    gap: 16,
  },
  emptyText: {
    fontSize: 16,
  },
  songsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 24,
  },
  songCard: {
    width: '48%',
    borderRadius: 20,
    padding: 16,
    borderWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
  },
  songIconContainer: {
    width: 64,
    height: 64,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  songTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 6,
    lineHeight: 20,
  },
  songDescription: {
    fontSize: 12,
    marginBottom: 12,
    lineHeight: 16,
  },
  songFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  verseBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    gap: 4,
  },
  verseText: {
    fontSize: 11,
    fontWeight: '600',
  },
  infoBanner: {
    flexDirection: 'row',
    marginHorizontal: 20,
    padding: 16,
    borderRadius: 16,
    borderWidth: 1,
    gap: 12,
  },
  infoBannerContent: {
    flex: 1,
  },
  infoBannerTitle: {
    fontSize: 15,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  infoBannerText: {
    fontSize: 13,
    lineHeight: 18,
  },
  bottomPadding: {
    height: 24,
  },
});
