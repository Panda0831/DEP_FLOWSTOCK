// https://docs.expo.dev/guides/using-eslint/
const { defineConfig } = require('eslint/config');
const expoConfig = require('eslint-config-expo/flat');

module.exports = defineConfig([
  { ignores: ['dist/**'] },
  expoConfig,
  {
    rules: {
      // Existing React Native animated values and initial data loads are safe,
      // but trigger React Compiler migration rules that are not build errors.
      'react-hooks/refs': 'off',
      'react-hooks/set-state-in-effect': 'off',
    },
  },
]);
