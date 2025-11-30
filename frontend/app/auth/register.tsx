import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, ActivityIndicator, Alert, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';

export default function RegisterScreen() {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { register } = useAuth();
  const { colors } = useTheme();
  const router = useRouter();

  const handleRegister = async () => {
    if (!email || !username || !password) {
      Alert.alert('Error', 'Please fill all fields');
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }

    if (password.length < 6) {
      Alert.alert('Error', 'Password must be at least 6 characters');
      return;
    }

    setIsLoading(true);
    try {
      await register(email, username, password);
      router.replace('/(tabs)');
    } catch (error: any) {
      Alert.alert('Registration Failed', error.message || 'Please try again');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.keyboardView}>
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          <View style={styles.header}>
            <View style={styles.logoContainer}>
              <Ionicons name="person-add" size={64} color="#10B981" />
            </View>
            <Text style={[styles.title, { color: colors.text }]}>Create Account</Text>
            <Text style={[styles.subtitle, { color: colors.textSecondary }]}>Join LangSwap today</Text>
          </View>

          <View style={styles.form}>
            <View style={[styles.inputWrapper, { backgroundColor: colors.inputBackground, borderColor: colors.border }]}>
              <Ionicons name="person-outline" size={20} color={colors.textSecondary} />
              <TextInput style={[styles.input, { color: colors.text }]} placeholder="Username" placeholderTextColor={colors.textSecondary} value={username} onChangeText={setUsername} autoCapitalize="words" />
            </View>

            <View style={[styles.inputWrapper, { backgroundColor: colors.inputBackground, borderColor: colors.border }]}>
              <Ionicons name="mail-outline" size={20} color={colors.textSecondary} />
              <TextInput style={[styles.input, { color: colors.text }]} placeholder="Email" placeholderTextColor={colors.textSecondary} value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" />
            </View>

            <View style={[styles.inputWrapper, { backgroundColor: colors.inputBackground, borderColor: colors.border }]}>
              <Ionicons name="lock-closed-outline" size={20} color={colors.textSecondary} />
              <TextInput style={[styles.input, { color: colors.text }]} placeholder="Password" placeholderTextColor={colors.textSecondary} value={password} onChangeText={setPassword} secureTextEntry={!showPassword} />
              <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
                <Ionicons name={showPassword ? 'eye-off-outline' : 'eye-outline'} size={20} color={colors.textSecondary} />
              </TouchableOpacity>
            </View>

            <View style={[styles.inputWrapper, { backgroundColor: colors.inputBackground, borderColor: colors.border }]}>
              <Ionicons name="lock-closed-outline" size={20} color={colors.textSecondary} />
              <TextInput style={[styles.input, { color: colors.text }]} placeholder="Confirm Password" placeholderTextColor={colors.textSecondary} value={confirmPassword} onChangeText={setConfirmPassword} secureTextEntry={!showPassword} />
            </View>

            <TouchableOpacity style={[styles.registerButton, isLoading && styles.registerButtonDisabled]} onPress={handleRegister} disabled={isLoading}>
              {isLoading ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.registerButtonText}>Create Account</Text>}
            </TouchableOpacity>

            <TouchableOpacity style={styles.loginLink} onPress={() => router.back()}>
              <Text style={[styles.loginLinkText, { color: colors.textSecondary }]}>Already have an account? <Text style={{ color: colors.primary, fontWeight: '700' }}>Sign In</Text></Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  keyboardView: { flex: 1 },
  scrollContent: { flexGrow: 1, padding: 24, justifyContent: 'center' },
  header: { alignItems: 'center', marginBottom: 48 },
  logoContainer: { width: 120, height: 120, borderRadius: 60, backgroundColor: '#D1FAE5', justifyContent: 'center', alignItems: 'center', marginBottom: 24 },
  title: { fontSize: 32, fontWeight: 'bold', marginBottom: 8 },
  subtitle: { fontSize: 16 },
  form: { gap: 16 },
  inputWrapper: { flexDirection: 'row', alignItems: 'center', borderWidth: 1.5, borderRadius: 12, paddingHorizontal: 16, paddingVertical: 14, gap: 12 },
  input: { flex: 1, fontSize: 16 },
  registerButton: { backgroundColor: '#10B981', paddingVertical: 16, borderRadius: 12, alignItems: 'center', marginTop: 8 },
  registerButtonDisabled: { opacity: 0.6 },
  registerButtonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
  loginLink: { alignItems: 'center', marginTop: 16 },
  loginLinkText: { fontSize: 14 },
});
