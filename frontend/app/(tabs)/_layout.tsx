import React from 'react';
import { Text, TouchableOpacity, View, StyleSheet } from 'react-native';
import { Tabs, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useLanguageMode } from '../../contexts/LanguageModeContext';
import { useTheme } from '../../contexts/ThemeContext';

export default function TabLayout() {
  const { languageMode } = useLanguageMode();
  const { colors, theme } = useTheme();
  const router = useRouter();
  
  const getLearnTitle = () => {
    if (languageMode === 'learn-english') return '🇬🇧 English';
    if (languageMode === 'learn-thai') return '🇹🇭 Thai';
    return 'Learn';
  };

  const handleLanguageSwap = () => {
    router.push('/language-selection' as any);
  };

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textSecondary,
        headerShown: false,
        tabBarStyle: {
          backgroundColor: colors.card,
          borderTopWidth: 1,
          borderTopColor: colors.border,
          height: 70,
          paddingBottom: 8,
          paddingTop: 8,
        },
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: '600',
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: getLearnTitle(),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="book" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="all-lessons"
        options={{
          title: 'Lessons',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="list-circle" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="progress"
        options={{
          title: 'Progress',
          tabBarIcon: ({ color, size, focused }) => (
            <Ionicons name="analytics" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="favorites"
        options={{
          title: 'Favorites',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="heart" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: 'Settings',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="settings" size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}