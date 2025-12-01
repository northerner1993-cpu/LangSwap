import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Switch,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Slider from '@react-native-community/slider';

interface AccessibilitySettingsProps {
  colors: any;
}

type ColorBlindMode = 'none' | 'protanopia' | 'deuteranopia' | 'tritanopia' | 'achromatopsia';

export default function AccessibilitySettings({ colors }: AccessibilitySettingsProps) {
  const [textScale, setTextScale] = useState(1.0);
  const [cardScale, setCardScale] = useState(1.0);
  const [highContrast, setHighContrast] = useState(false);
  const [colorBlindMode, setColorBlindMode] = useState<ColorBlindMode>('none');
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    loadAccessibilitySettings();
  }, []);

  const loadAccessibilitySettings = async () => {
    try {
      const settings = await AsyncStorage.multiGet([
        'accessibility_text_scale',
        'accessibility_card_scale',
        'accessibility_high_contrast',
        'accessibility_colorblind_mode',
        'accessibility_reduced_motion',
      ]);

      settings.forEach(([key, value]) => {
        if (value) {
          switch (key) {
            case 'accessibility_text_scale':
              setTextScale(parseFloat(value));
              break;
            case 'accessibility_card_scale':
              setCardScale(parseFloat(value));
              break;
            case 'accessibility_high_contrast':
              setHighContrast(value === 'true');
              break;
            case 'accessibility_colorblind_mode':
              setColorBlindMode(value as ColorBlindMode);
              break;
            case 'accessibility_reduced_motion':
              setReducedMotion(value === 'true');
              break;
          }
        }
      });
    } catch (error) {
      console.error('Error loading accessibility settings:', error);
    }
  };

  const saveTextScale = async (value: number) => {
    setTextScale(value);
    await AsyncStorage.setItem('accessibility_text_scale', value.toString());
  };

  const saveCardScale = async (value: number) => {
    setCardScale(value);
    await AsyncStorage.setItem('accessibility_card_scale', value.toString());
  };

  const saveHighContrast = async (value: boolean) => {
    setHighContrast(value);
    await AsyncStorage.setItem('accessibility_high_contrast', value.toString());
  };

  const saveColorBlindMode = async (mode: ColorBlindMode) => {
    setColorBlindMode(mode);
    await AsyncStorage.setItem('accessibility_colorblind_mode', mode);
  };

  const saveReducedMotion = async (value: boolean) => {
    setReducedMotion(value);
    await AsyncStorage.setItem('accessibility_reduced_motion', value.toString());
  };

  const colorBlindModes = [
    { id: 'none', name: 'None', icon: 'eye-outline', description: 'Standard colors' },
    { id: 'protanopia', name: 'Protanopia', icon: 'color-filter-outline', description: 'Red-blind (1% of males)' },
    { id: 'deuteranopia', name: 'Deuteranopia', icon: 'color-filter-outline', description: 'Green-blind (1% of males)' },
    { id: 'tritanopia', name: 'Tritanopia', icon: 'color-filter-outline', description: 'Blue-blind (rare)' },
    { id: 'achromatopsia', name: 'Achromatopsia', icon: 'contrast-outline', description: 'Total color blindness (very rare)' },
  ];

  const getColorBlindColor = (originalColor: string, mode: ColorBlindMode): string => {
    if (mode === 'none') return originalColor;
    
    // Simplified color mapping for colorblind modes
    const colorMappings: { [key in ColorBlindMode]: { [key: string]: string } } = {
      none: {},
      protanopia: {
        '#10B981': '#8B8B00', // green -> yellow-brown
        '#EF4444': '#7B7B00', // red -> dark yellow
        '#4F46E5': '#4F46E5', // blue unchanged
      },
      deuteranopia: {
        '#10B981': '#8B8B00',
        '#EF4444': '#8B6914',
        '#4F46E5': '#4F46E5',
      },
      tritanopia: {
        '#10B981': '#00A0A0',
        '#EF4444': '#FF6B6B',
        '#4F46E5': '#00A0A0',
      },
      achromatopsia: {
        '#10B981': '#888888',
        '#EF4444': '#666666',
        '#4F46E5': '#999999',
      },
    };

    return colorMappings[mode][originalColor] || originalColor;
  };

  return (
    <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
      <View style={styles.cardHeader}>
        <Ionicons name="accessibility" size={24} color={colors.primary} />
        <Text style={[styles.cardTitle, { color: colors.text }]}>Accessibility Features</Text>
      </View>

      {/* Text Size */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Ionicons name="text" size={20} color={colors.text} />
          <Text style={[styles.sectionTitle, { color: colors.text }]}>Text Size</Text>
        </View>
        <Text style={[styles.description, { color: colors.textSecondary }]}>
          Adjust text size throughout the app ({Math.round(textScale * 100)}%)
        </Text>
        <View style={styles.sliderContainer}>
          <Text style={[styles.sliderLabel, { color: colors.textSecondary }]}>A</Text>
          <Slider
            style={styles.slider}
            minimumValue={0.8}
            maximumValue={1.5}
            step={0.1}
            value={textScale}
            onValueChange={saveTextScale}
            minimumTrackTintColor={colors.primary}
            maximumTrackTintColor={colors.border}
            thumbTintColor={colors.primary}
          />
          <Text style={[styles.sliderLabel, { color: colors.textSecondary, fontSize: 20 }]}>A</Text>
        </View>
        <Text 
          style={[
            styles.previewText, 
            { color: colors.text, fontSize: 16 * textScale }
          ]}
        >
          Preview: Hello สวัสดี 你好
        </Text>
      </View>

      {/* Card Size */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Ionicons name="resize" size={20} color={colors.text} />
          <Text style={[styles.sectionTitle, { color: colors.text }]}>Card Size</Text>
        </View>
        <Text style={[styles.description, { color: colors.textSecondary }]}>
          Adjust flashcard size for better readability ({Math.round(cardScale * 100)}%)
        </Text>
        <View style={styles.sliderContainer}>
          <Text style={[styles.sliderLabel, { color: colors.textSecondary }]}>Small</Text>
          <Slider
            style={styles.slider}
            minimumValue={0.8}
            maximumValue={1.3}
            step={0.1}
            value={cardScale}
            onValueChange={saveCardScale}
            minimumTrackTintColor={colors.primary}
            maximumTrackTintColor={colors.border}
            thumbTintColor={colors.primary}
          />
          <Text style={[styles.sliderLabel, { color: colors.textSecondary }]}>Large</Text>
        </View>
      </View>

      {/* High Contrast */}
      <View style={styles.section}>
        <View style={styles.optionRow}>
          <View style={styles.optionLeft}>
            <Ionicons name="contrast" size={20} color={colors.text} />
            <View style={styles.optionTextContainer}>
              <Text style={[styles.optionTitle, { color: colors.text }]}>High Contrast Mode</Text>
              <Text style={[styles.optionDescription, { color: colors.textSecondary }]}>
                Increase contrast for better visibility
              </Text>
            </View>
          </View>
          <Switch
            value={highContrast}
            onValueChange={saveHighContrast}
            trackColor={{ false: colors.border, true: colors.primary + '80' }}
            thumbColor={highContrast ? colors.primary : '#f4f3f4'}
          />
        </View>
      </View>

      {/* Colorblind Mode */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Ionicons name="color-palette" size={20} color={colors.text} />
          <Text style={[styles.sectionTitle, { color: colors.text }]}>Colorblind Mode</Text>
        </View>
        <Text style={[styles.description, { color: colors.textSecondary }]}>
          Adjust colors for different types of color vision deficiency
        </Text>
        
        {colorBlindModes.map((mode) => (
          <TouchableOpacity
            key={mode.id}
            style={[
              styles.modeOption,
              { 
                backgroundColor: colorBlindMode === mode.id ? colors.primary + '15' : 'transparent',
                borderColor: colors.border
              }
            ]}
            onPress={() => saveColorBlindMode(mode.id as ColorBlindMode)}
            activeOpacity={0.7}
          >
            <View style={styles.modeLeft}>
              <Ionicons 
                name={mode.icon as any} 
                size={20} 
                color={colorBlindMode === mode.id ? colors.primary : colors.text} 
              />
              <View style={styles.modeTextContainer}>
                <Text style={[
                  styles.modeTitle, 
                  { 
                    color: colorBlindMode === mode.id ? colors.primary : colors.text,
                    fontWeight: colorBlindMode === mode.id ? '600' : '400'
                  }
                ]}>
                  {mode.name}
                </Text>
                <Text style={[styles.modeDescription, { color: colors.textSecondary }]}>
                  {mode.description}
                </Text>
              </View>
            </View>
            {colorBlindMode === mode.id && (
              <Ionicons name="checkmark-circle" size={24} color={colors.primary} />
            )}
          </TouchableOpacity>
        ))}

        {/* Color Preview */}
        {colorBlindMode !== 'none' && (
          <View style={styles.colorPreview}>
            <Text style={[styles.previewLabel, { color: colors.textSecondary }]}>
              Color Preview:
            </Text>
            <View style={styles.colorSamples}>
              <View style={styles.colorSample}>
                <View style={[
                  styles.colorBox, 
                  { backgroundColor: getColorBlindColor('#10B981', colorBlindMode) }
                ]} />
                <Text style={[styles.colorLabel, { color: colors.textSecondary }]}>Success</Text>
              </View>
              <View style={styles.colorSample}>
                <View style={[
                  styles.colorBox, 
                  { backgroundColor: getColorBlindColor('#EF4444', colorBlindMode) }
                ]} />
                <Text style={[styles.colorLabel, { color: colors.textSecondary }]}>Error</Text>
              </View>
              <View style={styles.colorSample}>
                <View style={[
                  styles.colorBox, 
                  { backgroundColor: getColorBlindColor('#4F46E5', colorBlindMode) }
                ]} />
                <Text style={[styles.colorLabel, { color: colors.textSecondary }]}>Primary</Text>
              </View>
            </View>
          </View>
        )}
      </View>

      {/* Reduced Motion */}
      <View style={styles.section}>
        <View style={styles.optionRow}>
          <View style={styles.optionLeft}>
            <Ionicons name="play-skip-forward" size={20} color={colors.text} />
            <View style={styles.optionTextContainer}>
              <Text style={[styles.optionTitle, { color: colors.text }]}>Reduce Motion</Text>
              <Text style={[styles.optionDescription, { color: colors.textSecondary }]}>
                Minimize animations and transitions
              </Text>
            </View>
          </View>
          <Switch
            value={reducedMotion}
            onValueChange={saveReducedMotion}
            trackColor={{ false: colors.border, true: colors.primary + '80' }}
            thumbColor={reducedMotion ? colors.primary : '#f4f3f4'}
          />
        </View>
      </View>

      {/* Info */}
      <View style={[styles.infoBox, { backgroundColor: colors.primary + '10', borderColor: colors.primary + '30' }]}>
        <Ionicons name="information-circle" size={18} color={colors.primary} />
        <Text style={[styles.infoText, { color: colors.textSecondary }]}>
          These settings apply throughout the app. Restart the app if changes don't appear immediately.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    gap: 12,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    flex: 1,
  },
  section: {
    marginBottom: 24,
    paddingBottom: 24,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0,0,0,0.05)',
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  description: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  sliderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginVertical: 8,
  },
  slider: {
    flex: 1,
    height: 40,
  },
  sliderLabel: {
    fontSize: 14,
    fontWeight: '500',
  },
  previewText: {
    marginTop: 12,
    padding: 12,
    borderRadius: 8,
    backgroundColor: 'rgba(0,0,0,0.03)',
    textAlign: 'center',
  },
  optionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  optionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  optionTextContainer: {
    flex: 1,
  },
  optionTitle: {
    fontSize: 15,
    fontWeight: '500',
    marginBottom: 4,
  },
  optionDescription: {
    fontSize: 13,
    lineHeight: 18,
  },
  modeOption: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
  },
  modeLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  modeTextContainer: {
    flex: 1,
  },
  modeTitle: {
    fontSize: 15,
    marginBottom: 2,
  },
  modeDescription: {
    fontSize: 12,
  },
  colorPreview: {
    marginTop: 16,
    padding: 12,
    borderRadius: 12,
    backgroundColor: 'rgba(0,0,0,0.03)',
  },
  previewLabel: {
    fontSize: 13,
    marginBottom: 12,
    fontWeight: '500',
  },
  colorSamples: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  colorSample: {
    alignItems: 'center',
    gap: 8,
  },
  colorBox: {
    width: 50,
    height: 50,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  colorLabel: {
    fontSize: 12,
  },
  infoBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 12,
    borderRadius: 12,
    marginTop: 8,
    borderWidth: 1,
    gap: 10,
  },
  infoText: {
    flex: 1,
    fontSize: 12,
    lineHeight: 18,
  },
});
