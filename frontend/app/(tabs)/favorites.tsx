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
    paddingHorizontal: 40,
    paddingTop: 60,
  },
  emptyIconCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#FEE2E2',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  emptyTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 12,
  },
  emptyText: {
    fontSize: 15,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 22,
  },
  favoritesContainer: {
    paddingHorizontal: 16,
  },
  favoriteCard: {
    position: 'relative',
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#EF4444',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
    borderWidth: 1,
    borderColor: '#FEE2E2',
  },
  favoriteIconBadge: {
    position: 'absolute',
    top: 12,
    left: 12,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#EF4444',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  favoriteContent: {
    flex: 1,
    paddingLeft: 32,
  },
  thaiText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 10,
  },
  romanText: {
    fontSize: 17,
    color: '#6366F1',
    fontWeight: '600',
    marginBottom: 6,
  },
  englishText: {
    fontSize: 16,
    color: '#374151',
    marginBottom: 8,
  },
  exampleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFBEB',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 10,
    marginTop: 4,
    gap: 6,
  },
  exampleText: {
    flex: 1,
    fontSize: 13,
    color: '#92400E',
    lineHeight: 18,
  },
  heartButton: {
    padding: 10,
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
  },
  bottomPadding: {
    height: 24,
  },
});