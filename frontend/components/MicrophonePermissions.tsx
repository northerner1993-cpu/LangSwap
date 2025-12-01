import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  Linking,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Audio } from 'expo-av';

interface MicrophonePermissionsProps {
  colors: any;
}

export default function MicrophonePermissions({ colors }: MicrophonePermissionsProps) {
  const [permissionStatus, setPermissionStatus] = useState<'granted' | 'denied' | 'undetermined'>('undetermined');
  const [isChecking, setIsChecking] = useState(false);

  useEffect(() => {
    checkPermissions();
  }, []);

  const checkPermissions = async () => {
    try {
      const { status } = await Audio.getPermissionsAsync();
      if (status === 'granted') {
        setPermissionStatus('granted');
      } else if (status === 'denied') {
        setPermissionStatus('denied');
      } else {
        setPermissionStatus('undetermined');
      }
    } catch (error) {
      console.error('Error checking permissions:', error);
    }
  };

  const requestPermissions = async () => {
    setIsChecking(true);
    try {
      const { status } = await Audio.requestPermissionsAsync();
      
      if (status === 'granted') {
        setPermissionStatus('granted');
        Alert.alert(
          'Permission Granted',
          'Microphone access has been enabled. You can now use speech-to-translate and voice features.',
          [{ text: 'OK' }]
        );
      } else {
        setPermissionStatus('denied');
        Alert.alert(
          'Permission Denied',
          'Microphone access is required for voice translation. Please enable it in your device settings.',
          [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Open Settings', onPress: openSettings }
          ]
        );
      }
    } catch (error) {
      console.error('Error requesting permissions:', error);
      Alert.alert('Error', 'Failed to request microphone permissions. Please try again.');
    } finally {
      setIsChecking(false);
    }
  };

  const openSettings = () => {
    if (Platform.OS === 'ios') {
      Linking.openURL('app-settings:');
    } else {
      Linking.openURL('app-settings:');
    }
  };

  const getStatusColor = () => {
    switch (permissionStatus) {
      case 'granted':
        return colors.success;
      case 'denied':
        return colors.error;
      default:
        return colors.warning;
    }
  };

  const getStatusText = () => {
    switch (permissionStatus) {
      case 'granted':
        return 'Enabled';
      case 'denied':
        return 'Denied';
      default:
        return 'Not Set';
    }
  };

  const getStatusIcon = () => {
    switch (permissionStatus) {
      case 'granted':
        return 'checkmark-circle';
      case 'denied':
        return 'close-circle';
      default:
        return 'help-circle';
    }
  };

  return (
    <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
      <View style={styles.cardHeader}>
        <Ionicons name="mic" size={24} color={colors.primary} />
        <Text style={[styles.cardTitle, { color: colors.text }]}>Microphone & Audio Permissions</Text>
      </View>

      {/* Permission Info */}
      <View style={styles.infoSection}>
        <Text style={[styles.infoTitle, { color: colors.text }]}>
          Why we need microphone access:
        </Text>
        <Text style={[styles.infoText, { color: colors.textSecondary }]}>
          • Speech-to-translate feature for real-time voice translation{'\n'}
          • Voice input for language practice{'\n'}
          • Audio recording for pronunciation practice{'\n'}
          • Enhanced learning experience with voice interaction
        </Text>
      </View>

      {/* Privacy Notice */}
      <View style={[styles.privacyNotice, { backgroundColor: colors.primary + '10', borderColor: colors.primary + '30' }]}>
        <Ionicons name="shield-checkmark" size={18} color={colors.primary} />
        <Text style={[styles.privacyText, { color: colors.textSecondary }]}>
          Your privacy is protected. Audio is processed locally on your device and never stored without your permission.
        </Text>
      </View>

      {/* Current Status */}
      <View style={[styles.statusContainer, { backgroundColor: getStatusColor() + '15' }]}>
        <View style={styles.statusRow}>
          <Ionicons name={getStatusIcon()} size={24} color={getStatusColor()} />
          <View style={styles.statusTextContainer}>
            <Text style={[styles.statusLabel, { color: colors.textSecondary }]}>
              Current Status:
            </Text>
            <Text style={[styles.statusValue, { color: getStatusColor() }]}>
              {getStatusText()}
            </Text>
          </View>
        </View>
      </View>

      {/* Action Buttons */}
      <View style={styles.buttonContainer}>
        {permissionStatus !== 'granted' && (
          <TouchableOpacity
            style={[styles.button, styles.primaryButton, { backgroundColor: colors.primary }]}
            onPress={requestPermissions}
            disabled={isChecking}
            activeOpacity={0.7}
          >
            <Ionicons name="mic" size={20} color="#FFFFFF" />
            <Text style={styles.primaryButtonText}>
              {isChecking ? 'Requesting...' : 'Grant Permission'}
            </Text>
          </TouchableOpacity>
        )}

        {permissionStatus === 'denied' && (
          <TouchableOpacity
            style={[styles.button, styles.secondaryButton, { borderColor: colors.border }]}
            onPress={openSettings}
            activeOpacity={0.7}
          >
            <Ionicons name="settings" size={20} color={colors.text} />
            <Text style={[styles.secondaryButtonText, { color: colors.text }]}>
              Open Settings
            </Text>
          </TouchableOpacity>
        )}

        <TouchableOpacity
          style={[styles.button, styles.secondaryButton, { borderColor: colors.border }]}
          onPress={checkPermissions}
          activeOpacity={0.7}
        >
          <Ionicons name="refresh" size={20} color={colors.text} />
          <Text style={[styles.secondaryButtonText, { color: colors.text }]}>
            Refresh Status
          </Text>
        </TouchableOpacity>
      </View>

      {/* Device Info */}
      <View style={styles.deviceInfo}>
        <Text style={[styles.deviceInfoText, { color: colors.textSecondary }]}>
          Platform: {Platform.OS === 'ios' ? 'iOS' : Platform.OS === 'android' ? 'Android' : 'Web'} {Platform.Version}
        </Text>
      </View>

      {/* Legal Compliance */}
      <View style={styles.legalSection}>
        <Text style={[styles.legalTitle, { color: colors.textSecondary }]}>
          Global Privacy Compliance:
        </Text>
        <Text style={[styles.legalText, { color: colors.textSecondary }]}>
          ✓ GDPR Compliant (Europe){'\n'}
          ✓ CCPA Compliant (California){'\n'}
          ✓ PDPA Compliant (Thailand){'\n'}
          ✓ PIPEDA Compliant (Canada){'\n'}
          ✓ LGPD Compliant (Brazil)
        </Text>
        <Text style={[styles.legalFootnote, { color: colors.textSecondary }]}>
          You can revoke permissions anytime in your device settings.
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
    marginBottom: 16,
    gap: 12,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    flex: 1,
  },
  infoSection: {
    marginBottom: 16,
  },
  infoTitle: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    lineHeight: 22,
  },
  privacyNotice: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 12,
    borderRadius: 12,
    marginBottom: 16,
    borderWidth: 1,
    gap: 10,
  },
  privacyText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
  },
  statusContainer: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  statusTextContainer: {
    flex: 1,
  },
  statusLabel: {
    fontSize: 13,
    marginBottom: 2,
  },
  statusValue: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  buttonContainer: {
    gap: 12,
    marginBottom: 16,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    gap: 8,
  },
  primaryButton: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
  },
  secondaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  deviceInfo: {
    padding: 12,
    marginBottom: 12,
  },
  deviceInfoText: {
    fontSize: 12,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  legalSection: {
    marginTop: 8,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.1)',
  },
  legalTitle: {
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 8,
  },
  legalText: {
    fontSize: 12,
    lineHeight: 18,
    marginBottom: 8,
  },
  legalFootnote: {
    fontSize: 11,
    fontStyle: 'italic',
    marginTop: 4,
  },
});
