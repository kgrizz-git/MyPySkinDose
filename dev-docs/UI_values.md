# UI Values — MyPySkinDose

This document maps the primary design tokens (colors, gradients, effects) used in the MyPySkinDose GUI. All values are defined in [src/mypyskindose/gui/app.py](file:///d:/MyCodes_SD/MyPySkinDose/src/mypyskindose/gui/app.py) within the `AURORA_CSS` constant.

## 🎨 Color Palette (CSS Variables)

| Variable | Value | Purpose |
| :--- | :--- | :--- |
| `--bg-primary` | `#090909` | Lifted black background |
| `--bg-secondary` | `#101010` | Card/Panel background |
| `--aurora-purple` | `#4338CA` | Navigation, Primary actions, & Sidebar glow (Darker Indigo) |
| `--aurora-teal` | `#0D9488` | Input & Load accents (True Teal) |
| `--aurora-pink` | `#831843` | Status & Highlights (Deep Pink) |
| `--text-main` | `#F8FAFC` | Primary text (White/Off-white) |
| `--border-brutal` | `rgba(139, 148, 158, 0.2)` | Low-contrast separators (Grey-purple) |

## ✨ Aurora Effects (Gradients)

Defined in the `body` and `.q-drawer` styles.

### Main Window Gradients
*   **Pink (Top-Right):** `rgba(160, 135, 150, 0.18)` (60% radius)
*   **Indigo (Top-Left):** `rgba(120, 135, 195, 0.17)` (60% radius)
*   **Blue-Cyan (Bottom-Right):** `rgba(105, 120, 135, 0.17)` (60% radius)

### Navigation Drawer
*   **Indigo Glow (Bottom-Left):** `rgba(120, 135, 195, 0.12)` (70% radius)

## 🔘 Component Styling

### Buttons (`.brutal-btn`)
*   **Border:** `1px solid` with `50%` color opacity.
*   **Background:** `15%` (Purple) or `20%` (Teal) opacity tint.
*   **Hover Glow:** `15px` blur with `30%` color opacity.

### Special Components
*   **Upload (RDSR):** Uses Quasar `deep-purple` to distinguish from blue buttons.
*   **PSD Status:** Uses `text-h6` and `text-pink-5` for high visibility.
*   **View Toggles:** Custom `.brutal-toggle` with `rgba(0,0,0,0.4)` background and subtle border.

### Cards (`.brutal-card`)
*   **Border:** `1px solid rgba(255, 255, 255, 0.1)`
*   **Effects:** `blur(12px)` backdrop and soft teal glow (`0 0 10px rgba(45, 212, 191, 0.1)`).

### Notifications (`.q-notification--positive`)
*   **Background:** `#022c22` (Ultra-dark emerald)
*   **Text:** `#d1fae5` (Light mint)
*   **Border:** `#065f46`

## 📊 Summary Card (Tab 5)
*   **Labels:** `font-normal`, `text-[11px]`, `opacity-70`.
*   **Values:** `font-bold`, `text-[13px]`, `100% opacity`.
