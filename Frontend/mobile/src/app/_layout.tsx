import { DefaultTheme, Stack, ThemeProvider } from 'expo-router';
import { View } from 'react-native';

import { AuthProvider } from '@/lib/auth-context';
import { AppNavigation } from '@/components/app-navigation';

export default function RootLayout() {
  return (
    <ThemeProvider value={DefaultTheme}>
      <AuthProvider>
        <View style={{ flex: 1 }}>
          <Stack screenOptions={{ headerShown: false, contentStyle: { flex: 1 } }} />
          <AppNavigation />
        </View>
      </AuthProvider>
    </ThemeProvider>
  );
}
