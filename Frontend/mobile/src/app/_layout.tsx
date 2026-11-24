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
    if (Platform.OS !== 'web' || reduceMotion) {
      webPageOpacity.setValue(1);
      return;
    }
    webPageOpacity.setValue(0.88);
    const transition = Animated.timing(webPageOpacity, {
      toValue: 1,
      duration: 160,
      easing: Easing.out(Easing.quad),
      useNativeDriver: false,
    });
    transition.start();
    return () => transition.stop();
  }, [pathname, reduceMotion, webPageOpacity]);

  return (
    <ThemeProvider value={scheme === 'dark' ? DarkTheme : DefaultTheme}>
      <AuthProvider>
        <View style={{ flex: 1 }}>
          <Animated.View style={{ flex: 1, opacity: webPageOpacity }}>
            <Stack screenOptions={{
              headerShown: false,
              contentStyle: { flex: 1 },
              animation: reduceMotion ? 'none' : 'fade',
              animationDuration: reduceMotion ? 0 : 180,
            }} />
          </Animated.View>
          <AppNavigation />
        </View>
      </AuthProvider>
    </ThemeProvider>
  );
}
