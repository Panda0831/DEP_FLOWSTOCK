import { DarkTheme, DefaultTheme, Stack, ThemeProvider } from 'expo-router';
import { useColorScheme, View } from 'react-native';

import { AuthProvider } from '@/lib/auth-context';
import { AppNavigation } from '@/components/app-navigation';

export default function RootLayout() {
  const colorScheme = useColorScheme();
  return (
    <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <AuthProvider>
        <View style={{ flex: 1 }}>
          <AppNavigation />
          <Stack screenOptions={{ headerShown: false, contentStyle: { flex: 1 } }} />
        </View>
      </AuthProvider>
    </ThemeProvider>
  );
}
