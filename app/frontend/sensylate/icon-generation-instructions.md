# Icon Generation Instructions for Sensylate PWA

This document provides instructions for creating the necessary icons for the Sensylate Progressive Web App.

## Required Icon Sizes

Create the following icon sizes with a simple design featuring the letter "S" for Sensylate:

- 72x72 (icon-72x72.png)
- 96x96 (icon-96x96.png)
- 128x128 (icon-128x128.png)
- 144x144 (icon-144x144.png)
- 152x152 (icon-152x152.png)
- 192x192 (icon-192x192.png)
- 384x384 (icon-384x384.png)
- 512x512 (icon-512x512.png)
- 192x192 with safe area for maskable icon (maskable-icon.png)
- 180x180 for Apple Touch Icon (apple-touch-icon.png)

## Design Guidelines

1. Use the indigo color (#6366f1) as the background
2. Use white (#ffffff) for the "S" letter
3. Use a simple, clean font for the "S"
4. For the maskable icon, ensure the "S" is within the safe area (central 80% of the image)
5. Save all icons in PNG format
6. Place all icons in the `public/icons/` directory

## Tools for Icon Creation

You can use any of the following tools to create these icons:

- Adobe Illustrator or Photoshop
- Figma
- Sketch
- GIMP (free and open-source)
- Inkscape (free and open-source)
- Online tools like Canva or Favicon.io

## Quick Method Using Online Tools

1. Go to https://favicon.io/favicon-generator/
2. Enter "S" as the text
3. Select a font style (preferably sans-serif)
4. Set the background color to #6366f1
5. Set the text color to #ffffff
6. Download the generated icons
7. Resize them to the required dimensions using an image editor

## Testing Icons

After creating and placing the icons in the `public/icons/` directory, run the application and check:

1. The icons appear correctly in the browser tab
2. The app can be installed on desktop and mobile devices
3. The installed app shows the correct icon on the home screen/desktop
