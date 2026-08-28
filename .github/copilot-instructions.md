# Frontend Guidelines (HTML + CSS + JavaScript)

You are working on a frontend project using only:
- HTML5
- CSS3
- Vanilla JavaScript (no frameworks)

---

## 🧱 General Principles
- Keep code simple, readable, and easy to maintain
- Avoid over-engineering
- Prefer clear structure over complex solutions
- Do not use frameworks or libraries (no React, no Vue, no jQuery)

---

## 🧩 HTML Guidelines
- Use semantic HTML5 elements:
  - `<header>`, `<main>`, `<section>`, `<footer>`, `<nav>`
- Avoid excessive `<div>` nesting
- Use meaningful class names (not generic like `box1`, `div2`)
- Ensure proper accessibility:
  - use `alt` for images
  - use `label` for inputs
  - use proper heading order (`h1 → h2 → h3`)

---

## 🎨 CSS Guidelines
- Use clean, modular CSS
- Prefer Flexbox and Grid for layout
- Mobile-first design approach
- Avoid inline styles unless absolutely necessary

### Rules:
- Use consistent spacing system (e.g. 4px / 8px / 16px scale)
- Avoid overly complex selectors
- Keep class names meaningful (e.g. `login-container`, not `box123`)

### Responsive Design:
- Always support mobile, tablet, and desktop
- Use media queries when needed:
