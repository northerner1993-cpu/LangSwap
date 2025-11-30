import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput, Alert, ScrollView, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import Constants from 'expo-constants';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

export default function PremiumScreen() {
  const [couponCode, setCouponCode] = useState('');
  const [couponValid, setCouponValid] = useState(false);
  const [discount, setDiscount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [subscription, setSubscription] = useState<any>(null);
  const { colors } = useTheme();
  const { user, token } = useAuth();
  const router = useRouter();

  useEffect(() => {
    checkSubscription();
  }, []);

  const checkSubscription = async () => {
    if (!token) return;
    
    try {
      const response = await fetch(`${API_URL}/api/my-subscription`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      if (data.has_subscription) {
        setSubscription(data);
      }
    } catch (error) {
      console.error('Error checking subscription:', error);
    }
  };

  const validateCoupon = async () => {
    if (!couponCode.trim()) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/coupons/validate/${couponCode}`);
      if (response.ok) {
        const data = await response.json();
        setCouponValid(true);
        setDiscount(data.discount_percent);
        Alert.alert('Valid Coupon!', `${data.discount_percent}% discount applied`);
      } else {
        setCouponValid(false);
        Alert.alert('Invalid Coupon', 'This coupon code is not valid');
      }
    } catch (error) {
      Alert.alert('Error', 'Could not validate coupon');
    } finally {
      setIsLoading(false);
    }
  };

  const purchaseSubscription = async (planType: string) => {
    if (!user) {
      Alert.alert('Login Required', 'Please login to purchase premium');
      router.push('/auth/login');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/subscribe?plan_type=${planType}&coupon_code=${couponCode}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();
      
      if (response.ok) {
        Alert.alert('Success!', 'Premium activated! Enjoy ad-free learning.');
        checkSubscription();
      } else {
        Alert.alert('Purchase Failed', data.detail || 'Please try again');
      }
    } catch (error) {
      Alert.alert('Error', 'Could not complete purchase');
    } finally {
      setIsLoading(false);
    }
  };

  if (subscription?.is_premium) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <View style={styles.premiumBadge}>
            <Ionicons name="star" size={64} color="#FFD700" />
            <Text style={[styles.premiumTitle, { color: colors.text }]}>You're Premium!</Text>
            <Text style={[styles.premiumSubtitle, { color: colors.textSecondary }]}>
              {subscription.plan_type === 'lifetime' ? 'Lifetime Access' : 'Monthly Subscription'}
            </Text>
          </View>

          <View style={[styles.featuresCard, { backgroundColor: colors.card }]}>
            <Text style={[styles.featuresTitle, { color: colors.text }]}>Your Benefits</Text>
            {['No Advertisements', 'Unlimited Translations', 'Offline Mode', 'Priority Support', 'Early Access to New Features'].map((feature, idx) => (
              <View key={idx} style={styles.featureItem}>
                <Ionicons name="checkmark-circle" size={24} color="#10B981" />
                <Text style={[styles.featureText, { color: colors.text }]}>{feature}</Text>
              </View>
            ))}
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }

  const lifetimePrice = couponValid ? (2.99 * (1 - discount / 100)).toFixed(2) : '2.99';
  const monthlyPrice = couponValid ? (5.99 * (1 - discount / 100)).toFixed(2) : '5.99';

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Ionicons name="diamond" size={64} color="#8B5CF6" />
          <Text style={[styles.title, { color: colors.text }]}>Go Premium</Text>
          <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
            Unlock the full LangSwap experience
          </Text>
        </View>

        <View style={[styles.couponSection, { backgroundColor: colors.card }]}>
          <Text style={[styles.couponTitle, { color: colors.text }]}>Have a coupon code?</Text>
          <View style={styles.couponInputRow}>
            <TextInput
              style={[styles.couponInput, { backgroundColor: colors.inputBackground, color: colors.text }]}
              placeholder="Enter code"
              placeholderTextColor={colors.textSecondary}
              value={couponCode}
              onChangeText={setCouponCode}
              autoCapitalize="characters"
            />
            <TouchableOpacity 
              style={[styles.validateButton, couponValid && styles.validatedButton]} 
              onPress={validateCoupon}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator color="#FFFFFF" size="small" />
              ) : (
                <Ionicons name={couponValid ? "checkmark" : "arrow-forward"} size={20} color="#FFFFFF" />
              )}
            </TouchableOpacity>
          </View>
          {couponValid && (
            <View style={styles.discountBadge}>
              <Ionicons name="pricetag" size={16} color="#10B981" />
              <Text style={styles.discountText}>{discount}% discount applied!</Text>
            </View>
          )}
        </View>

        <View style={styles.plansContainer}>
          <TouchableOpacity 
            style={[styles.planCard, styles.lifetimePlan]} 
            onPress={() => purchaseSubscription('lifetime')}
            disabled={isLoading}
          >
            <View style={styles.popularBadge}>
              <Text style={styles.popularText}>BEST VALUE</Text>
            </View>
            <View style={styles.planHeader}>
              <Text style={styles.planTitle}>Lifetime Access</Text>
              <Text style={styles.planDescription}>One-time payment, forever yours</Text>
            </View>
            <View style={styles.priceSection}>
              {couponValid && <Text style={styles.originalPrice}>£2.99</Text>}
              <Text style={styles.price}>£{lifetimePrice}</Text>
              <Text style={styles.priceNote}>Pay once, use forever</Text>
            </View>
            <View style={styles.features}>
              {['No Ads Ever', 'Unlimited Translations', 'Offline Mode', 'All Future Updates'].map((feature, idx) => (
                <View key={idx} style={styles.feature}>
                  <Ionicons name="checkmark-circle" size={20} color="#10B981" />
                  <Text style={styles.featureTextWhite}>{feature}</Text>
                </View>
              ))}
            </View>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.planCard, { backgroundColor: colors.card, borderColor: colors.border }]} 
            onPress={() => purchaseSubscription('monthly')}
            disabled={isLoading}
          >
            <View style={styles.planHeader}>
              <Text style={[styles.planTitle, { color: colors.text }]}>Monthly</Text>
              <Text style={[styles.planDescription, { color: colors.textSecondary }]}>Cancel anytime</Text>
            </View>
            <View style={styles.priceSection}>
              {couponValid && <Text style={[styles.originalPrice, { color: colors.textSecondary }]}>£5.99</Text>}
              <Text style={[styles.price, { color: colors.text }]}>£{monthlyPrice}</Text>
              <Text style={[styles.priceNote, { color: colors.textSecondary }]}>per month</Text>
            </View>
            <View style={styles.features}>
              {['No Ads', 'Unlimited Translations', 'Priority Support'].map((feature, idx) => (
                <View key={idx} style={styles.feature}>
                  <Ionicons name="checkmark-circle" size={20} color="#8B5CF6" />
                  <Text style={[styles.featureTextWhite, { color: colors.text }]}>{feature}</Text>
                </View>
              ))}
            </View>
          </TouchableOpacity>
        </View>

        <Text style={[styles.disclaimer, { color: colors.textSecondary }]}>
          Secure payment powered by Google Play • Cancel anytime
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scrollContent: { padding: 24, paddingBottom: 40 },
  header: { alignItems: 'center', marginBottom: 32 },
  title: { fontSize: 32, fontWeight: 'bold', marginTop: 16, marginBottom: 8 },
  subtitle: { fontSize: 16, textAlign: 'center' },
  couponSection: { borderRadius: 16, padding: 20, marginBottom: 24 },
  couponTitle: { fontSize: 16, fontWeight: '600', marginBottom: 12 },
  couponInputRow: { flexDirection: 'row', gap: 12 },
  couponInput: { flex: 1, borderRadius: 12, paddingHorizontal: 16, paddingVertical: 14, fontSize: 16 },
  validateButton: { backgroundColor: '#8B5CF6', borderRadius: 12, paddingHorizontal: 20, justifyContent: 'center', alignItems: 'center' },
  validatedButton: { backgroundColor: '#10B981' },
  discountBadge: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 12, backgroundColor: '#D1FAE5', padding: 12, borderRadius: 8 },
  discountText: { color: '#10B981', fontWeight: '700' },
  plansContainer: { gap: 16, marginBottom: 24 },
  planCard: { borderRadius: 20, padding: 24, borderWidth: 2 },
  lifetimePlan: { backgroundColor: '#8B5CF6', borderColor: '#6D28D9' },
  popularBadge: { backgroundColor: '#FFD700', alignSelf: 'flex-start', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 12, marginBottom: 16 },
  popularText: { color: '#000', fontSize: 12, fontWeight: '900' },
  planHeader: { marginBottom: 16 },
  planTitle: { fontSize: 24, fontWeight: 'bold', color: '#FFFFFF' },
  planDescription: { fontSize: 14, color: '#E9D5FF', marginTop: 4 },
  priceSection: { marginBottom: 20 },
  originalPrice: { fontSize: 16, textDecorationLine: 'line-through', color: '#E9D5FF' },
  price: { fontSize: 48, fontWeight: 'bold', color: '#FFFFFF' },
  priceNote: { fontSize: 14, color: '#E9D5FF' },
  features: { gap: 12 },
  feature: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  featureTextWhite: { fontSize: 15, color: '#FFFFFF', fontWeight: '500' },
  disclaimer: { fontSize: 12, textAlign: 'center', marginTop: 16 },
  premiumBadge: { alignItems: 'center', marginVertical: 40 },
  premiumTitle: { fontSize: 32, fontWeight: 'bold', marginTop: 16 },
  premiumSubtitle: { fontSize: 16, marginTop: 4 },
  featuresCard: { borderRadius: 16, padding: 20, marginTop: 24 },
  featuresTitle: { fontSize: 20, fontWeight: 'bold', marginBottom: 16 },
  featureItem: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 12 },
  featureText: { fontSize: 16 },
});
