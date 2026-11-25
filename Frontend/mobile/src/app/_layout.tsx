import { DarkTheme, DefaultTheme, Stack, ThemeProvider, usePathname } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, Easing, Platform, useColorScheme, View } from 'react-native';

import { AuthProvider } from '@/lib/auth-context';
import { AppNavigation } from '@/components/app-navigation';

export default function RootLayout() {
  const scheme = useColorScheme();
  const pathname = usePathname();
  const [reduceMotion, setReduceMotion] = useState(true);
  const webPageOpacity = useRef(new Animated.Value(1)).current;
  const webPageTranslateY = useRef(new Animated.Value(0)).current;
  const previousPath = useRef(pathname);

  useEffect(() => {
    let active = true;
    void AccessibilityInfo.isReduceMotionEnabled().then((enabled) => {
      if (active) setReduceMotion(enabled);
    });
    const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', setReduceMotion);
    return () => {
      active = false;
      subscription.remove();
    };
  }, []);

  useEffect(() => {
    if (previousPath.current === pathname) return;
    previousPath.current = pathname;
    webPageOpacity.stopAnimation();
    webPageTranslateY.stopAnimation();
    if (Platform.OS !== 'web' || reduceMotion) {
      webPageOpacity.setValue(1);
      webPageTranslateY.setValue(0);
      return;
    }
    webPageOpacity.setValue(0.94);
    webPageTranslateY.setValue(6);
    const transition = Animated.parallel([
      Animated.timing(webPageOpacity, {
        toValue: 1,
        duration: 220,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: false,
      }),
      Animated.timing(webPageTranslateY, {
        toValue: 0,
        duration: 220,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: false,
      }),
    ]);
    transition.start();
    return () => transition.stop();
  }, [pathname, reduceMotion, webPageOpacity, webPageTranslateY]);

  return (
    <ThemeProvider value={scheme === 'dark' ? DarkTheme : DefaultTheme}>
      <AuthProvider>
        <View style={{ flex: 1 }}>
          <Animated.View
            style={{
              flex: 1,
              opacity: webPageOpacity,
              transform: [{ translateY: webPageTranslateY }],
            }}
          >
            <Stack screenOptions={{
              headerShown: false,
              contentStyle: { flex: 1 },
              animation: reduceMotion ? 'none' : Platform.select({ ios: 'fade_from_bottom', android: 'fade_from_bottom', default: 'none' }),
              animationDuration: reduceMotion ? 0 : 220,
              gestureEnabled: false,
            }} />
          </Animated.View>
          <AppNavigation />
        </View>
      </AuthProvider>
    </ThemeProvider>
  );
}
