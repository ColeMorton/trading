# Sensylate Style Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Brand Identity](#brand-identity)
3. [Color Palette](#color-palette)
4. [Typography](#typography)
5. [Components](#components)
6. [Layout & Grid](#layout--grid)
7. [Icons & Imagery](#icons--imagery)
8. [Data Visualization](#data-visualization)
9. [Responsive Design](#responsive-design)
10. [Accessibility](#accessibility)
11. [Code Standards](#code-standards)

## Introduction

This style guide establishes a design contract for the Sensylate application, a parameter sensitivity analysis tool for trading strategies. It defines the visual language and UI/UX principles that should be consistently applied across all Sensylate-related web applications to create a unified user experience.

## Brand Identity

### Logo
- The Sensylate logo combines a chart line icon with the Sensylate wordmark
- Primary logo uses the application's primary blue color on dark backgrounds
- Minimum clear space around the logo should be at least equal to the height of the "S" in Sensylate
- Logo should never be distorted, recolored outside the approved palette, or used below the minimum size of 32px height

### Brand Voice
- Professional but accessible
- Data-driven and analytical
- Clear and concise
- Educational without being overwhelming
- Focus on empowering users to make informed decisions

## Color Palette

### Primary Colors
- Primary Blue: `var(--bs-primary)` - #0d6efd
- Dark Background: `var(--bs-dark)` - #212529
- Secondary Gray: `var(--bs-secondary)` - #6c757d

### Secondary Colors
- Success Green: `var(--bs-success)` - #198754
- Danger Red: `var(--bs-danger)` - #dc3545
- Warning Yellow: `var(--bs-warning)` - #ffc107
- Info Teal: `var(--bs-info)` - #0dcaf0

### Neutral Colors
- Body Background: `var(--bs-body-bg)` - #121212
- Body Text: `var(--bs-body-color)` - #f8f9fa
- Border Color: `var(--bs-border-color)` - #495057

### Color Usage
- Primary Blue: Main actions, highlights, key metrics, and charts
- Success Green: Positive indicators, confirmations, profitable metrics
- Danger Red: Errors, warnings, negative metrics, deletions
- Warning Yellow: Cautions, mid-range indicators
- Info Teal: Informational elements, secondary actions
- Use dark mode color schemes consistently throughout the application

## Typography

### Font Family
- Primary Font: System fonts via Bootstrap's native stack
- Font stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`

### Font Sizes
- Base font size: 16px (1rem)
- Heading scales:
  - H1: 2.5rem (40px)
  - H2: 2rem (32px)
  - H3: 1.75rem (28px)
  - H4: 1.5rem (24px)
  - H5: 1.25rem (20px)
  - H6: 1rem (16px)
- Small text: 0.875rem (14px)

### Font Weights
- Regular: 400
- Bold: 700

### Line Heights
- Default body: 1.5
- Headings: 1.2

### Text Colors
- Primary text: `var(--bs-body-color)` - #f8f9fa
- Secondary text: `var(--bs-secondary-color)` - #adb5bd
- Muted text: `var(--bs-text-muted)` - #6c757d

## Components

### Cards
- Dark background: `var(--bs-dark)` - #212529
- Border: 1px solid `var(--bs-border-color)`
- Border radius: 0.375rem (6px)
- Shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075)
- Padding: 1.25rem (20px)
- Margin-bottom: 1.5rem (24px)
- Card headers should use flex layout for responsive title/action positioning

### Buttons
- Primary: Blue background, white text
- Secondary: Gray background, white text
- Outline variants: Transparent background with colored borders
- Border radius: 0.375rem (6px)
- Padding: 0.375rem 0.75rem (6px 12px)
- Button groups should have no gap between buttons
- Include icons where appropriate to enhance clarity

### Forms
- Dark inputs with light text
- Form background: `var(--bs-dark)` - #212529
- Text color: `var(--bs-body-color)` - #f8f9fa
- Border: 1px solid `var(--bs-border-color)`
- Border radius: 0.375rem (6px)
- Focus state: Blue glow with no change to background/text color
- Group related form elements with appropriate spacing
- Label positioning: Above inputs with 0.5rem spacing

### Tables
- Striped rows for better readability
- Hover effect to highlight rows
- Header background: Slightly darker than table body
- Responsive tables should horizontally scroll on small screens
- Column alignment:
  - Text data: Left-aligned
  - Numeric data: Right-aligned
  - Action buttons: Center-aligned

### Alerts & Notifications
- Success: Green background
- Error: Red background
- Warning: Yellow background
- Info: Teal background
- Border radius: 0.375rem (6px)
- Padding: 0.75rem 1.25rem (12px 20px)
- Include appropriate icons to reinforce message type
- Toast notifications should appear in the top right corner
- Toast animation: Fade in and slide from right

### Modals
- Centered on screen with dark overlay
- Dark background with light text
- Border radius: 0.375rem (6px)
- Header clearly separated from body content
- Close button in the top right
- Action buttons right-aligned in footer

## Layout & Grid

### Container System
- Max width: 1320px
- Padding: 1.5rem (24px) on desktop, 1rem (16px) on mobile
- Gutters: 1.5rem (24px) between columns

### Grid System
- 12-column layout using Bootstrap grid classes
- Breakpoints:
  - Extra small (xs): < 576px
  - Small (sm): ≥ 576px
  - Medium (md): ≥ 768px
  - Large (lg): ≥ 992px
  - Extra large (xl): ≥ 1200px
  - Extra extra large (xxl): ≥ 1400px

### Spacing
- Use Bootstrap spacing utilities:
  - m/p-0: 0
  - m/p-1: 0.25rem (4px)
  - m/p-2: 0.5rem (8px)
  - m/p-3: 1rem (16px)
  - m/p-4: 1.5rem (24px)
  - m/p-5: 3rem (48px)
- Consistent vertical rhythm: 1.5rem (24px) between major sections

### Z-index Layers
1. Default content: 1
2. Sticky headers: 1000
3. Dropdowns: 1050
4. Modals/Dialogs: 1060
5. Toasts/Notifications: 1070

## Icons & Imagery

### Icons
- Use Font Awesome for all icons
- Standard icon size: 1em (relative to text)
- Action icons: 1rem (16px)
- Navigation icons: 1.25rem (20px)
- Feature icons: 2rem (32px)
- Use `me-1` or `me-2` classes for spacing between icons and text

### Charts & Data Visualization
- Consistent color scheme across all charts
- Chart backgrounds: Dark with lighter grid lines
- Tooltip styling: Dark background with light text
- Legend position: Top or right side of charts
- Axes labels: Light gray text
- Use appropriate chart types for different data relationships:
  - Line charts for time series
  - Bar charts for comparisons
  - Pie/Donut charts for composition
  - Radar charts for multivariate data
  - Heatmaps for correlation data

## Data Visualization

### Charts
- Library: Chart.js
- Chart container height: 300px on desktop, 250px on mobile
- Chart padding: 20px
- Text colors: rgba(255, 255, 255, 0.7)
- Grid colors: rgba(255, 255, 255, 0.1)
- Interactive elements:
  - Hover tooltips with data details
  - Click actions where applicable

### Data Tables
- Library: DataTables
- Features:
  - Pagination
  - Sorting
  - Filtering
  - Row selection
- Table styling:
  - Header: Slightly darker than body
  - Alternating row colors for better readability
  - Selected row highlight: Primary color with reduced opacity

### Performance Metrics
- Consistent formatting for numeric values:
  - Percentages: 2 decimal places
  - Currency: 2 decimal places
  - Ratios: 2 decimal places
- Use appropriate indicators for positive/negative values:
  - Positive: Green, up arrows
  - Negative: Red, down arrows

## Responsive Design

### Mobile Adaptations
- Stack columns vertically on small screens
- Adjust font sizes down by 10-15%
- Reduce padding and margins by 25-50%
- Hide less important columns in tables
- Convert complex charts to simpler versions
- Card headers switch to vertical layout on mobile

### Touch Targets
- Minimum touch target size: 44px × 44px
- Adequate spacing between interactive elements
- Use larger button sizes on touch devices

### Navigation
- Collapse navbar into hamburger menu on mobile
- Ensure all main navigation is accessible with one thumb

## Accessibility

### Color Contrast
- Maintain minimum contrast ratios:
  - Normal text: 4.5:1
  - Large text: 3:1
- Avoid relying solely on color to convey information

### Focus States
- Visible focus indicators for keyboard navigation
- Focus styles should be distinct but not obtrusive

### Screen Readers
- Proper ARIA roles and labels
- Meaningful alt text for images
- Descriptive link text
- Announce dynamic content changes

### Keyboard Navigation
- All interactive elements must be keyboard accessible
- Logical tab order following visual layout
- Skip navigation links for screen readers

## Code Standards

### HTML
- Use semantic HTML5 elements
- Maintain proper heading hierarchy
- Include appropriate ARIA attributes
- Validate against HTML5 standards

### CSS
- Use Bootstrap utilities wherever possible
- Custom CSS follows BEM naming convention
- Minimize overrides of Bootstrap defaults
- CSS variables for theme customization

### JavaScript
- Unobtrusive JavaScript separated from HTML
- Event delegation for dynamically created elements
- Clear error handling and user feedback
- Consistent code style following ESLint standards

### Performance
- Minify and compress assets
- Lazy load non-critical resources
- Optimize images and limit file sizes
- Use caching strategies appropriately

---

This style guide serves as a comprehensive reference for maintaining consistency across all Sensylate applications. It should be regularly reviewed and updated as the design system evolves.