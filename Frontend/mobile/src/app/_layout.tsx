import { DarkTheme, DefaultTheme, Stack, ThemeProvider } from 'expo-router';
import { useColorScheme, View } from 'react-native';

import { AuthProvider } from '@/lib/auth-context';
import { AppNavigation } from '@/components/app-navigation';

export default function RootLayout() {
  const scheme = useColorScheme();

  return (
    <ThemeProvider value={scheme === 'dark' ? DarkTheme : DefaultTheme}>
      <AuthProvider>
        <View style={{ flex: 1 }}>
          <Stack screenOptions={{ headerShown: false, contentStyle: { flex: 1 } }} />
          <AppNavigation />
        </View>
      </AuthProvider>
    </ThemeProvider>
  );
}
