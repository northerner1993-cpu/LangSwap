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

export default function SongsScreen() {
  const [songs, setSongs] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const { colors } = useTheme();
  const { languageMode } = useLanguageMode();

  useEffect(() => {
    loadSongs();
  }, [languageMode]);

  const loadSongs = async () => {
    try {
      const modeParam = languageMode ? `?language_mode=${languageMode}` : '';
      const response = await fetch(`${API_URL}/api/lessons${modeParam}`);
      const data = await response.json();
      const songLessons = data.filter((lesson: Lesson) => lesson.category === 'songs');
      setSongs(songLessons);
    } catch (error) {
      console.error('Error loading songs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSongIcon = (subcategory: string) => {
    const iconMap: { [key: string]: string } = {
      'alphabet': 'text',
      'numbers': 'calculator',
      'daily': 'sunny',
      'vocabulary': 'color-palette',
      'colors': 'color-fill',
      'animals': 'paw',
      'family': 'people',
      'time': 'time',
      'anatomy': 'body',
    };
    return iconMap[subcategory] || 'musical-note';
  };

  const handleSongPress = (songId: string) => {
    router.push(`/lesson/${songId}`);
  };

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[styles.loadingText, { color: colors.textSecondary }]}>Loading songs...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <Ionicons name="musical-notes" size={48} color="#EC4899" />
          <Text style={[styles.title, { color: colors.text }]}>Learning Songs</Text>
          <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
            {songs.length} {languageMode === 'learn-thai' ? 'Thai' : 'English'} songs available
          </Text>
        </View>

        {/* Songs Grid */}
        <View style={styles.songsContainer}>
          {songs.map((song) => (
            <TouchableOpacity
              key={song._id}
              style={[styles.songCard, { backgroundColor: colors.card, borderColor: colors.border }]}
              onPress={() => handleSongPress(song._id)}
              activeOpacity={0.7}
            >
              <View style={[styles.songIconContainer, { backgroundColor: '#EC489920' }]}>
                <Ionicons name={getSongIcon(song.subcategory) as any} size={32} color="#EC4899" />
              </View>
              <View style={styles.songContent}>
                <Text style={[styles.songTitle, { color: colors.text }]}>{song.title}</Text>
                <Text style={[styles.songDescription, { color: colors.textSecondary }]} numberOfLines={2}>
                  {song.description}
                </Text>
                <View style={styles.songFooter}>
                  <View style={[styles.badge, { backgroundColor: '#EC489915' }]}>
                    <Text style={[styles.badgeText, { color: '#EC4899' }]}>{song.subcategory}</Text>
                  </View>
                  <View style={styles.itemCount}>
                    <Ionicons name="musical-note" size={14} color={colors.textSecondary} />
                    <Text style={[styles.itemCountText, { color: colors.textSecondary }]}>
                      {song.items.length} verses
                    </Text>
                  </View>
                </View>
              </View>
              <View style={styles.playIcon}>
                <Ionicons name="play-circle" size={40} color="#EC4899" />
              </View>
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
  },
  scrollView: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 16,
  },
  header: {
    padding: 24,
    alignItems: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginTop: 12,
  },
  subtitle: {
    fontSize: 15,
    marginTop: 4,
  },
  songsContainer: {
    padding: 16,
    gap: 16,
  },
  songCard: {
    flexDirection: 'row',
    alignItems: 'center',
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
    marginRight: 16,
  },
  songContent: {
    flex: 1,
  },
  songTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 6,
  },
  songDescription: {
    fontSize: 13,
    marginBottom: 10,
    lineHeight: 18,
  },
  songFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'capitalize',
  },
  itemCount: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  itemCountText: {
    fontSize: 12,
    fontWeight: '500',
  },
  playIcon: {
    marginLeft: 8,
  },
  bottomPadding: {
    height: 24,
  },
});
