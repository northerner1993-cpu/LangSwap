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
import { LinearGradient } from 'expo-linear-gradient';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface Lesson {
  _id: string;
  title: string;
  category: string;
  subcategory: string;
  description: string;
  items: any[];
  order: number;
  language_mode: string;
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
      const response = await fetch(`${API_URL}/api/lessons?category=songs&language_mode=${languageMode}`);
      const data = await response.json();
      setSongs(data);
    } catch (error) {
      console.error('Error loading songs:', error);
    } finally {
      setLoading(false);
    }
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

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <LinearGradient
          colors={[colors.primary + '20', colors.background]}
          style={styles.header}
        >
          <View style={styles.headerContent}>
            <Ionicons name="musical-notes" size={48} color={colors.primary} />
            <Text style={[styles.title, { color: colors.text }]}>
              {languageMode === 'learn-english' ? '🇬🇧 English Songs' : '🇹🇭 Thai Songs'}
            </Text>
            <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
              Learn through music • {songs.length} songs available
            </Text>
          </View>
        </LinearGradient>

        {/* Songs List */}
        <View style={styles.songsContainer}>
          {songs.map((song, index) => (
            <TouchableOpacity
              key={song._id}
              style={[styles.songCard, { backgroundColor: colors.card }]}
              onPress={() => handleSongPress(song._id)}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={[
                  index % 4 === 0 ? '#F472B6' : 
                  index % 4 === 1 ? '#EC4899' : 
                  index % 4 === 2 ? '#DB2777' : '#BE185D',
                  index % 4 === 0 ? '#EC4899' : 
                  index % 4 === 1 ? '#DB2777' : 
                  index % 4 === 2 ? '#BE185D' : '#9F1239',
                ]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.songGradient}
              >
                <View style={styles.songIcon}>
                  <Ionicons name="musical-note" size={32} color="#FFFFFF" />
                </View>
                
                <View style={styles.songInfo}>
                  <Text style={styles.songTitle}>{song.title}</Text>
                  <Text style={styles.songDescription}>{song.description}</Text>
                  <View style={styles.songMeta}>
                    <Ionicons name="layers" size={14} color="rgba(255,255,255,0.8)" />
                    <Text style={styles.songMetaText}>{song.items.length} verses</Text>
                  </View>
                </View>

                <View style={styles.playButton}>
                  <Ionicons name="play-circle" size={48} color="#FFFFFF" />
                </View>
              </LinearGradient>
            </TouchableOpacity>
          ))}
        </View>

        {songs.length === 0 && (
          <View style={styles.emptyContainer}>
            <Ionicons name="musical-notes-outline" size={64} color={colors.textSecondary} />
            <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
              No songs available for this language
            </Text>
          </View>
        )}

        {/* Info Card */}
        <View style={[styles.infoCard, { backgroundColor: colors.primary + '10' }]}>
          <Ionicons name="information-circle" size={24} color={colors.primary} />
          <View style={styles.infoContent}>
            <Text style={[styles.infoTitle, { color: colors.text }]}>Learning Tips</Text>
            <Text style={[styles.infoText, { color: colors.textSecondary }]}>
              • Listen to songs multiple times{'
'}
              • Sing along to practice pronunciation{'
'}
              • Use the auto-play feature for continuous learning
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
    paddingVertical: 32,
    paddingHorizontal: 24,
    marginBottom: 8,
  },
  headerContent: {
    alignItems: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginTop: 12,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    textAlign: 'center',
  },
  songsContainer: {
    paddingHorizontal: 16,
    gap: 16,
  },
  songCard: {
    borderRadius: 20,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  songGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    gap: 16,
  },
  songIcon: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  songInfo: {
    flex: 1,
  },
  songTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 6,
  },
  songDescription: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.9)',
    marginBottom: 8,
  },
  songMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  songMetaText: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    fontWeight: '600',
  },
  playButton: {
    opacity: 0.9,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 64,
    gap: 16,
  },
  emptyText: {
    fontSize: 16,
    textAlign: 'center',
  },
  infoCard: {
    flexDirection: 'row',
    padding: 20,
    marginHorizontal: 16,
    marginTop: 24,
    borderRadius: 16,
    gap: 16,
  },
  infoContent: {
    flex: 1,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 13,
    lineHeight: 20,
  },
  bottomPadding: {
    height: 24,
  },
});
