# PWA Testing Checklist for Sensylate

This document provides a comprehensive checklist for testing the Progressive Web App (PWA) functionality of Sensylate.

## Prerequisites

Before testing, ensure you have:

- Created all the required icon files and placed them in the public/icons directory
- Created a favicon.ico file and placed it in the public directory
- Built the application with `npm run build`
- Served the built application with a proper web server

## Functionality Testing

### Offline Support

- [ ] Load the application while online
- [ ] Navigate through different views and load some CSV data
- [ ] Disconnect from the internet (turn off Wi-Fi or use browser DevTools to simulate offline)
- [ ] Verify the offline banner appears
- [ ] Verify previously loaded data is still accessible
- [ ] Verify new data cannot be loaded (appropriate error handling)
- [ ] Reconnect to the internet
- [ ] Verify the offline banner disappears
- [ ] Verify new data can be loaded again

### Installation

- [ ] Visit the application in Chrome
- [ ] Check if the install prompt appears (may need to visit multiple times)
- [ ] Click "Install" and verify the application installs correctly
- [ ] Verify the application icon appears on the desktop/home screen
- [ ] Launch the installed application
- [ ] Verify it opens in a standalone window without browser UI
- [ ] Verify all functionality works in the installed version

### Updates

- [ ] Install the application
- [ ] Make a change to the application code
- [ ] Build and deploy the new version
- [ ] Open the installed application
- [ ] Verify the update notification appears
- [ ] Click "Update" and verify the application updates correctly

## Lighthouse Audit

Run a Lighthouse audit in Chrome DevTools with the following categories:

- [ ] Progressive Web App
- [ ] Performance
- [ ] Accessibility
- [ ] Best Practices
- [ ] SEO

### PWA Checklist (from Lighthouse)

- [ ] Registers a service worker
- [ ] Responds with a 200 when offline
- [ ] Has a `<meta name="viewport">` tag with width or initial-scale
- [ ] Contains some content when JavaScript is not available
- [ ] Provides a valid `manifest.json`
- [ ] Manifest has a valid `name`
- [ ] Manifest has a valid `short_name`
- [ ] Manifest has a valid `start_url`
- [ ] Manifest has a valid `display` (should be `standalone` or `fullscreen`)
- [ ] Manifest has a valid `icons` array with 192px and 512px icons
- [ ] Page has the theme color meta tag

## Cross-Browser Testing

Test the application in the following browsers:

- [ ] Chrome (desktop)
- [ ] Firefox (desktop)
- [ ] Safari (desktop)
- [ ] Chrome (mobile)
- [ ] Safari (mobile)

## Device Testing

Test the application on the following devices:

- [ ] Desktop (Windows/Mac)
- [ ] Android phone
- [ ] iPhone
- [ ] Tablet (if available)

## Performance Testing

- [ ] Check initial load time
- [ ] Check time to interactive
- [ ] Check offline load time
- [ ] Check installed app launch time

## Troubleshooting Common Issues

If you encounter issues during testing, check the following:

1. **Service Worker Not Registering**

   - Ensure the application is served over HTTPS or localhost
   - Check browser console for errors
   - Verify the service worker path is correct

2. **Install Prompt Not Appearing**

   - Ensure the manifest.json is valid
   - Ensure all required icons are present
   - The user may have already dismissed the prompt (check Application tab in DevTools)

3. **Offline Support Not Working**

   - Check if the service worker is registered correctly
   - Verify the caching strategy in the service worker
   - Check if the cached resources are available in the Cache Storage (in Application tab of DevTools)

4. **Updates Not Detected**
   - Ensure the service worker update check is working
   - Try clearing the cache and reloading

## Final Checklist

- [ ] All PWA features work as expected
- [ ] Application works offline
- [ ] Application can be installed
- [ ] Application can be updated
- [ ] Lighthouse audit passes with a good score
- [ ] Application works on all tested browsers and devices
