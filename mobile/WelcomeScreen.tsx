import { useEffect, useState } from 'react';
import { Animated, Image, StyleSheet, Text, View } from 'react-native';
import { colors, space } from './theme';
import { useReducedMotion } from './ui';

export default function WelcomeScreen({ ready }: { ready: boolean }) {
  const reduced = useReducedMotion();
  const [rise] = useState(() => new Animated.Value(0));

  useEffect(() => {
    if (reduced) return;
    const motion = Animated.loop(Animated.sequence([
      Animated.timing(rise, { toValue: -8, duration: 450, useNativeDriver: true }),
      Animated.timing(rise, { toValue: 0, duration: 450, useNativeDriver: true }),
    ]));
    motion.start();
    return () => motion.stop();
  }, [reduced, rise]);

  return <View style={styles.page}>
    <Animated.View style={{ transform: [{ translateY: rise }] }}>
      <Image source={require('./assets/pulso-icon.png')} style={styles.logo} accessible={false} />
    </Animated.View>
    <Text style={styles.name}>PULSO URBANO</Text>
    <Text style={styles.tagline}>Danos tu reporte, te estamos escuchando</Text>
    {!ready ? <Text style={styles.waiting}>Preparando el formulario…</Text> : null}
  </View>;
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: colors.canvas, alignItems: 'center', justifyContent: 'center', padding: space.lg },
  logo: { width: 150, height: 150, borderRadius: 32 },
  name: { color: colors.primaryDark, fontWeight: '800', fontSize: 26, letterSpacing: 1.5, marginTop: space.lg, textAlign: 'center' },
  tagline: { color: colors.ink, fontSize: 18, lineHeight: 26, textAlign: 'center', marginTop: space.md, maxWidth: 300 },
  waiting: { color: colors.muted, fontSize: 15, marginTop: space.lg },
});
