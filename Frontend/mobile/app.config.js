const appJson = require('./app.json').expo;

module.exports = ({ config }) => {
  const googleMapsApiKey = process.env.GOOGLE_MAPS_API_KEY;

  return {
    ...config,
    ...appJson,
    android: googleMapsApiKey
      ? {
          ...appJson.android,
          config: {
            ...appJson.android?.config,
            googleMaps: { apiKey: googleMapsApiKey },
          },
        }
      : appJson.android,
  };
};
