# Sensylate Accessibility Guide

## Introduction

This accessibility guide provides comprehensive standards and best practices to ensure the Sensylate application is usable by people of all abilities. Following these guidelines will help meet WCAG 2.1 AA standards and create an inclusive experience for all users.

## Table of Contents

1. [Principles](#principles)
2. [Visual Design](#visual-design)
3. [Keyboard Navigation](#keyboard-navigation)
4. [Screen Readers](#screen-readers)
5. [Forms and Inputs](#forms-and-inputs)
6. [Interactive Elements](#interactive-elements)
7. [Data Tables and Charts](#data-tables-and-charts)
8. [Error Handling](#error-handling)
9. [Testing](#testing)
10. [Resources](#resources)

## Principles

Sensylate follows the four core principles of accessibility:

1. **Perceivable**: Information and user interface components must be presentable to users in ways they can perceive.
2. **Operable**: User interface components and navigation must be operable.
3. **Understandable**: Information and the operation of the user interface must be understandable.
4. **Robust**: Content must be robust enough to be interpreted reliably by a wide variety of user agents, including assistive technologies.

## Visual Design

### Color and Contrast

- Maintain a minimum contrast ratio of 4.5:1 for normal text and 3:1 for large text (18pt or 14pt bold).
- Do not rely solely on color to convey information.
- Provide additional indicators such as icons, patterns, or text labels alongside color.

```html
<!-- Good example: Color and icon together -->
<div class="alert alert-danger">
  <i class="fas fa-exclamation-circle me-2" aria-hidden="true"></i>
  Error: Unable to load data.
</div>

<!-- Good example: Sufficient contrast -->
<button class="btn btn-primary">Primary action</button> <!-- Blue on white, contrast ratio: 4.5:1 -->
```

### Text and Typography

- Use relative units (rem, em) rather than absolute units (px) to support text resizing.
- Ensure text can be resized up to 200% without loss of content or functionality.
- Maintain appropriate line height (1.5 for body text) for readability.
- Avoid justified text alignment, which can create uneven spacing.

```css
/* Good example: Using relative units */
body {
  font-size: 1rem;
  line-height: 1.5;
}

h1 {
  font-size: 2.5rem;
  line-height: 1.2;
}
```

### Focus Indicators

- Ensure all interactive elements have a visible focus indicator.
- Do not remove the default focus outline unless replacing it with an equally or more visible alternative.
- Make focus indicators high contrast (at least 3:1 against adjacent colors).

```css
/* Good example: Enhanced focus styles */
:focus {
  outline: 3px solid var(--bs-primary);
  outline-offset: 2px;
}

/* Bad example: Removing focus without replacement */
:focus {
  outline: none; /* Don't do this without a replacement */
}
```

## Keyboard Navigation

### Focus Order

- Ensure logical tab order that follows the visual layout.
- Tab order should follow a natural reading sequence (left to right, top to bottom).
- Use tabindex="0" to include elements in the natural tab order.
- Avoid using tabindex values greater than 0.

```html
<!-- Good example: Natural tab order -->
<div class="form-group">
  <label for="name">Name</label>
  <input id="name" type="text" class="form-control">
  
  <label for="email">Email</label>
  <input id="email" type="email" class="form-control">
  
  <button type="submit">Submit</button>
</div>
```

### Keyboard Shortcuts

- Provide keyboard shortcuts for common actions where appropriate.
- Ensure keyboard shortcuts don't conflict with browser or screen reader shortcuts.
- Allow users to customize or disable keyboard shortcuts.

```javascript
// Good example: Keyboard shortcut with option to customize
document.addEventListener('keydown', function(event) {
  // Alt+S to submit form
  if (event.altKey && event.key === 's' && userPreferences.enableShortcuts) {
    event.preventDefault();
    document.getElementById('submit-button').click();
  }
});
```

### Skip Navigation

- Provide a "Skip to main content" link at the beginning of the page.
- Make the skip link visible when focused.

```html
<!-- Good example: Skip navigation link -->
<a href="#main-content" class="skip-link">Skip to main content</a>

<!-- Later in the document -->
<main id="main-content">
  <!-- Main content here -->
</main>
```

## Screen Readers

### Semantic HTML

- Use appropriate HTML elements for their intended purpose.
- Use heading elements (h1-h6) to create a logical document outline.
- Use lists (ul, ol, dl) for groups of related items.
- Use tables for tabular data with proper headers.

```html
<!-- Good example: Semantic HTML -->
<header>
  <h1>Sensylate</h1>
  <nav>
    <!-- Navigation content -->
  </nav>
</header>

<main>
  <section>
    <h2>Parameter Sensitivity Testing</h2>
    <!-- Section content -->
  </section>
</main>

<footer>
  <!-- Footer content -->
</footer>
```

### ARIA Attributes

- Use ARIA attributes to enhance accessibility when HTML semantics are insufficient.
- Follow the first rule of ARIA: "No ARIA is better than bad ARIA."
- Use aria-label, aria-labelledby, and aria-describedby to provide additional context.

```html
<!-- Good example: ARIA to enhance semantics -->
<div role="alert" aria-live="assertive">
  Form submitted successfully!
</div>

<button aria-expanded="false" aria-controls="advancedConfig">
  Toggle Advanced Config
</button>
<div id="advancedConfig" class="d-none">
  <!-- Advanced configuration options -->
</div>
```

### Dynamic Content

- Use aria-live regions for dynamic content updates.
- Set appropriate aria-live values: "polite" for non-critical updates, "assertive" for important alerts.
- Announce loading states and completion of operations.

```html
<!-- Good example: Aria-live region for loading state -->
<div aria-live="polite" id="loadingStatus">
  Loading results, please wait...
</div>

<script>
  // After loading completes
  document.getElementById('loadingStatus').textContent = 'Results loaded successfully.';
</script>
```

## Forms and Inputs

### Labels and Instructions

- Provide visible labels for all form controls.
- Use the `<label>` element with the "for" attribute matching the input's ID.
- Provide clear instructions and error messages.
- Group related form elements with `<fieldset>` and `<legend>`.

```html
<!-- Good example: Proper form labeling -->
<div class="form-group">
  <label for="ticker-input">Ticker Symbol</label>
  <input type="text" id="ticker-input" class="form-control">
  <div class="form-text">Enter stock ticker symbols separated by commas (e.g., AAPL, MSFT, GOOGL)</div>
</div>

<!-- Good example: Fieldset for related inputs -->
<fieldset>
  <legend>Strategy Type</legend>
  <div class="form-check">
    <input class="form-check-input" type="radio" name="strategy" id="strategy-sma" checked>
    <label class="form-check-label" for="strategy-sma">SMA</label>
  </div>
  <div class="form-check">
    <input class="form-check-input" type="radio" name="strategy" id="strategy-ema">
    <label class="form-check-label" for="strategy-ema">EMA</label>
  </div>
</fieldset>
```

### Form Validation

- Provide real-time validation when possible.
- Display clear error messages that explain the issue and how to fix it.
- Associate error messages with the appropriate form control using aria-describedby.
- Use both color and text/icons to indicate validation status.

```html
<!-- Good example: Accessible form validation -->
<div class="form-group">
  <label for="win-rate">Minimum Win Rate</label>
  <input type="number" id="win-rate" class="form-control is-invalid" aria-describedby="win-rate-error" min="0" max="1" step="0.01">
  <div id="win-rate-error" class="invalid-feedback">
    <i class="fas fa-exclamation-circle" aria-hidden="true"></i>
    Win rate must be between 0 and 1.
  </div>
</div>
```

## Interactive Elements

### Buttons

- Use the `<button>` element for interactive controls.
- Provide descriptive text that indicates the action.
- Include both icon and text for clarity.

```html
<!-- Good example: Descriptive button -->
<button type="button" class="btn btn-primary">
  <i class="fas fa-save" aria-hidden="true"></i>
  Save Portfolio
</button>

<!-- Bad example: Icon-only button without accessible label -->
<button type="button" class="btn btn-primary">
  <i class="fas fa-save"></i>
  <!-- Missing text label -->
</button>
```

### Modals and Dialogs

- Use appropriate ARIA roles and attributes for modals.
- Trap focus within the modal when open.
- Ensure modals can be closed with the Escape key.
- Return focus to the triggering element when closed.

```html
<!-- Good example: Accessible modal -->
<div class="modal fade" id="exampleModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true" role="dialog" aria-modal="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="exampleModalLabel">Modal Title</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
        <!-- Modal content -->
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
        <button type="button" class="btn btn-primary">Save changes</button>
      </div>
    </div>
  </div>
</div>
```

### Dropdown Menus

- Use appropriate ARIA attributes for dropdown menus.
- Ensure dropdowns can be operated with keyboard.
- Provide visual indication of the current selection.

```html
<!-- Good example: Accessible dropdown -->
<div class="dropdown">
  <button class="btn btn-secondary dropdown-toggle" type="button" id="sortDropdown" data-bs-toggle="dropdown" aria-expanded="false">
    Sort By
  </button>
  <ul class="dropdown-menu" aria-labelledby="sortDropdown">
    <li><a class="dropdown-item" href="#" role="menuitem">Score</a></li>
    <li><a class="dropdown-item" href="#" role="menuitem">Win Rate</a></li>
    <li><a class="dropdown-item" href="#" role="menuitem">Profit Factor</a></li>
  </ul>
</div>
```

## Data Tables and Charts

### Data Tables

- Use the `<table>` element with proper structure.
- Include `<caption>` and appropriate header cells.
- Use scope attributes on header cells.
- Consider responsive table solutions for mobile.

```html
<!-- Good example: Accessible data table -->
<table class="table">
  <caption>Performance Metrics for Selected Strategies</caption>
  <thead>
    <tr>
      <th scope="col">Strategy</th>
      <th scope="col">Win Rate</th>
      <th scope="col">Profit Factor</th>
      <th scope="col">Expectancy</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">SMA (10, 20)</th>
      <td>58.3%</td>
      <td>2.14</td>
      <td>3.42</td>
    </tr>
    <!-- More rows -->
  </tbody>
</table>
```

### Charts and Visualizations

- Provide text alternatives for charts.
- Include descriptive titles and legends.
- Use patterns in addition to colors.
- Make interactive charts keyboard accessible.
- Consider providing the data in an accessible table format as an alternative.

```html
<!-- Good example: Accessible chart -->
<figure>
  <figcaption id="chart-title">Portfolio Performance by Strategy Type</figcaption>
  <div aria-labelledby="chart-title">
    <canvas id="performanceChart"></canvas>
  </div>
  <p id="chart-description">
    The chart shows performance metrics across different strategy types. SMA strategies show the highest win rate at 62%, while EMA strategies show the highest profit factor at 2.8.
  </p>
  <a href="#dataTable" class="btn btn-sm btn-outline-secondary">View as data table</a>
</figure>
```

## Error Handling

### Error Messages

- Provide clear, specific error messages.
- Use both visual and programmatic means to indicate errors.
- Suggest solutions when possible.
- Maintain focus on or near the error message.

```html
<!-- Good example: Helpful error message -->
<div role="alert" class="alert alert-danger">
  <h4 class="alert-heading">Unable to run analysis</h4>
  <p>The following issues need to be addressed:</p>
  <ul>
    <li>At least one ticker symbol is required</li>
    <li>At least one strategy type must be selected</li>
  </ul>
  <p>Please correct these issues and try again.</p>
</div>
```

### Timeouts

- Warn users before session timeouts.
- Provide ample time to extend the session.
- Allow users to request more time if needed.

```html
<!-- Good example: Session timeout warning -->
<div role="alert" class="alert alert-warning" id="timeout-alert" aria-live="assertive">
  <p>Your session will expire in <span id="timeout-countdown">5:00</span> minutes.</p>
  <button class="btn btn-primary" id="extend-session">Extend Session</button>
</div>
```

## Testing

### Automated Testing

- Integrate accessibility testing tools into the development workflow.
- Use tools like axe, WAVE, or Lighthouse for automated checks.
- Address all critical and serious issues before release.

### Manual Testing

- Test with keyboard-only navigation.
- Test with screen readers (NVDA, JAWS, VoiceOver).
- Test with browser zoom and text resizing.
- Test with high contrast mode.

### User Testing

- Conduct testing with users who have disabilities.
- Include users with various assistive technologies.
- Address feedback in a timely manner.

## Resources

### Tools

- [WAVE Web Accessibility Evaluation Tool](https://wave.webaim.org/)
- [axe DevTools](https://www.deque.com/axe/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [Color Contrast Analyzer](https://developer.paciellogroup.com/resources/contrastanalyser/)

### Guidelines and Standards

- [Web Content Accessibility Guidelines (WCAG) 2.1](https://www.w3.org/TR/WCAG21/)
- [WAI-ARIA Authoring Practices](https://www.w3.org/TR/wai-aria-practices-1.1/)
- [WebAIM: Web Accessibility In Mind](https://webaim.org/)

---

By following these accessibility guidelines, Sensylate will provide an inclusive experience for all users, regardless of their abilities or the assistive technologies they use. Accessibility is not just a checkbox but an ongoing commitment to ensuring everyone can access and use our application effectively.