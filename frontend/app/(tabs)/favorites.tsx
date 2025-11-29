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
import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface FavoriteItem {
  _id: string;
  lesson_id: string;
  item_index: number;
  item_data: {
    thai: string;
    romanization: string;
    english: string;
    example?: string;
  };
  created_at: string;
}

export default function FavoritesScreen() {
  const [favorites, setFavorites] = useState<FavoriteItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFavorites();
  }, []);

  const loadFavorites = async () => {
    try {
      const response = await fetch(`${API_URL}/api/favorites?user_id=default_user`);
      const data = await response.json();
      setFavorites(data);
    } catch (error) {
      console.error('Error loading favorites:', error);
    } finally {
      setLoading(false);
    }
  };

  const removeFavorite = async (favorite: FavoriteItem) => {
    try {
      await fetch(`${API_URL}/api/favorites`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'default_user',
          lesson_id: favorite.lesson_id,
          item_index: favorite.item_index,
          item_data: favorite.item_data,
        }),
      });
      // Refresh favorites
      loadFavorites();
    } catch (error) {
      console.error('Error removing favorite:', error);
    }
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

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.title}>Favorites</Text>
          <Text style={styles.subtitle}>
            {favorites.length} saved item{favorites.length !== 1 ? 's' : ''}
          </Text>
        </View>

        {favorites.length === 0 ? (
          <View style={styles.emptyContainer}>
            <View style={styles.emptyIconCircle}>
              <Ionicons name="heart-outline" size={48} color="#EF4444" />
            </View>
            <Text style={styles.emptyTitle}>No favorites yet</Text>
            <Text style={styles.emptyText}>
              Tap the ❤️ icon while learning to save your favorite Thai words and phrases here
            </Text>
          </View>
        ) : (
          <View style={styles.favoritesContainer}>
            {favorites.map((favorite) => (
              <View key={favorite._id} style={styles.favoriteCard}>
                <View style={styles.favoriteIconBadge}>
                  <Ionicons name="heart" size={16} color="#FFFFFF" />
                </View>
                <View style={styles.favoriteContent}>
                  <Text style={styles.thaiText}>{favorite.item_data.thai}</Text>
                  <Text style={styles.romanText}>{favorite.item_data.romanization}</Text>
                  <Text style={styles.englishText}>{favorite.item_data.english}</Text>
                  {favorite.item_data.example && (
                    <View style={styles.exampleContainer}>
                      <Ionicons name="bulb-outline" size={14} color="#F59E0B" />
                      <Text style={styles.exampleText}>{favorite.item_data.example}</Text>
                    </View>
                  )}
                </View>
                <TouchableOpacity
                  onPress={() => removeFavorite(favorite)}
                  style={styles.heartButton}
                  activeOpacity={0.7}
                >
                  <Ionicons name="heart-dislike" size={22} color="#9CA3AF" />
                </TouchableOpacity>
              </View>
            ))}
          </View>
        )}

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
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
    paddingTop: 80,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#374151',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: '#9CA3AF',
    textAlign: 'center',
    lineHeight: 20,
  },
  favoritesContainer: {
    paddingHorizontal: 16,
  },
  favoriteCard: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  favoriteContent: {
    flex: 1,
  },
  thaiText: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 8,
  },
  romanText: {
    fontSize: 16,
    color: '#6366F1',
    marginBottom: 4,
  },
  englishText: {
    fontSize: 16,
    color: '#374151',
    marginBottom: 4,
  },
  exampleText: {
    fontSize: 14,
    color: '#9CA3AF',
    fontStyle: 'italic',
    marginTop: 4,
  },
  heartButton: {
    padding: 8,
  },
  bottomPadding: {
    height: 24,
  },
});