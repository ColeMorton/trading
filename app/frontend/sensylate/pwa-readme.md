# Sensylate PWA Implementation

This document provides an overview of the Progressive Web App (PWA) implementation for Sensylate.

## Features

The Sensylate PWA includes the following features:

1. **Offline Support**: The application can work offline with cached data
2. **Installability**: The application can be installed on desktop and mobile devices
3. **App-like Experience**: The application provides a native-like experience
4. **Automatic Updates**: The application can be updated automatically

## Implementation Details

### Service Worker

The service worker is implemented using Workbox through the vite-plugin-pwa package. It provides:

- Precaching of static assets
- Runtime caching of API responses
- Offline fallback
- Update notification

### Manifest

The web app manifest (`manifest.json`) provides metadata about the application, including:

- Name and description
- Icons in various sizes
- Theme color
- Display mode (standalone)

### Components

The following React components were created for the PWA functionality:

- `OfflineContext.tsx`: Context provider for tracking online/offline status
- `OfflineBanner.tsx`: Banner displayed when the user is offline
- `PWAUpdateNotification.tsx`: Notification displayed when an update is available
- `InstallPrompt.tsx`: Prompt displayed when the app can be installed

### API Modifications

The API service was modified to support offline functionality:

- Caching of API responses
- Fallback to cached data when offline
- Error handling for offline scenarios

## Directory Structure

```
app/sensylate/
├── public/
│   ├── icons/              # App icons in various sizes
│   ├── manifest.json       # Web app manifest
│   └── robots.txt          # Robots file
├── src/
│   ├── components/
│   │   ├── OfflineBanner.tsx
│   │   ├── PWAUpdateNotification.tsx
│   │   └── InstallPrompt.tsx
│   ├── context/
│   │   └── OfflineContext.tsx
│   └── services/
│       └── api.ts          # Modified for offline support
└── vite.config.ts          # Configured for PWA
```

## Usage

### Development

```bash
npm run dev
```

### Building for Production

```bash
npm run build:pwa
```

### Serving the PWA

```bash
npm run serve:pwa
```

## Testing

See the `pwa-testing-checklist.md` file for a comprehensive testing checklist.

## Icon Generation

See the `icon-generation-instructions.md` file for instructions on generating the required icons.

## Troubleshooting

### Service Worker Not Registering

- Ensure the application is served over HTTPS or localhost
- Check browser console for errors
- Verify the service worker path is correct

### Install Prompt Not Appearing

- Ensure the manifest.json is valid
- Ensure all required icons are present
- The user may have already dismissed the prompt

### Offline Support Not Working

- Check if the service worker is registered correctly
- Verify the caching strategy in the service worker
- Check if the cached resources are available in the Cache Storage

## Resources

- [Vite PWA Plugin Documentation](https://vite-pwa-org.netlify.app/)
- [Workbox Documentation](https://developer.chrome.com/docs/workbox/)
- [Web App Manifest Documentation](https://developer.mozilla.org/en-US/docs/Web/Manifest)
- [Service Worker API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
