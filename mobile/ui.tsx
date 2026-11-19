import { useEffect, useState } from 'react';
import { AccessibilityInfo, ActivityIndicator, Animated, Easing, Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, space } from './theme';

export function ActionButton({ title, onPress, variant = 'primary', disabled = false, busy = false }: {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  disabled?: boolean;
  busy?: boolean;
}) {
  return <Pressable accessibilityRole="button" accessibilityLabel={title} accessibilityState={{ disabled: disabled || busy, busy }}
    onPress={onPress} disabled={disabled || busy}
    style={({ pressed }) => [styles.button, styles[variant], (disabled || busy) && styles.disabled, pressed && styles.pressed]}>
    {busy ? <ActivityIndicator color={variant === 'primary' ? colors.surface : colors.primary} /> : null}
    <Text style={[styles.buttonText, variant !== 'primary' && styles.secondaryText, variant === 'danger' && styles.dangerText]}>{title}</Text>
  </Pressable>;
}

export function useReducedMotion() {
  const [reduced, setReduced] = useState(true);

  useEffect(() => {
    const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', setReduced);
    void AccessibilityInfo.isReduceMotionEnabled().then(setReduced);
    return () => subscription.remove();
  }, []);
  return reduced;
}

export function LoadingMark({ label }: { label: string }) {
  const [lift] = useState(() => new Animated.Value(0));
  const reduced = useReducedMotion();

  useEffect(() => {
    if (reduced) { lift.setValue(0); return; }
    const motion = Animated.loop(Animated.sequence([
      Animated.timing(lift, { toValue: -5, duration: 480, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      Animated.timing(lift, { toValue: 0, duration: 480, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
    ]));
    motion.start();
    return () => motion.stop();
  }, [lift, reduced]);

  return <View style={styles.loading} accessibilityRole="progressbar" accessibilityLabel={label}>
    <Animated.View style={{ transform: [{ translateY: lift }] }} accessibilityElementsHidden>
      <Image source={require('./assets/pulso-icon.png')} style={styles.loadingLogo} />
    </Animated.View>
    <Text style={styles.loadingText}>{label}</Text>
  </View>;
}

const styles = StyleSheet.create({
  button: { minHeight: 54, borderRadius: 14, paddingHorizontal: space.md, paddingVertical: 12,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: space.sm },
  primary: { backgroundColor: colors.primary },
  secondary: { backgroundColor: colors.softBlue, borderWidth: 1, borderColor: colors.line },
  danger: { backgroundColor: colors.dangerBg, borderWidth: 1, borderColor: '#E7B7C0' },
  disabled: { opacity: 0.55 }, pressed: { opacity: 0.82 },
  buttonText: { color: colors.surface, fontSize: 16, fontWeight: '700', textAlign: 'center' },
  secondaryText: { color: colors.primaryDark }, dangerText: { color: colors.danger },
  loading: { alignItems: 'center', justifyContent: 'center', padding: space.lg, gap: space.sm },
  loadingText: { color: colors.muted, fontSize: 16, fontWeight: '600', textAlign: 'center' },
  loadingLogo: { width: 54, height: 54, borderRadius: 12 },
});
