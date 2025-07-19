
# 🧑‍💻 Frontend Developer Instructions – SingleBrief UI

---

## 🎯 Objective


Create a professional, modern, and enterprise-grade interface for the **SingleBrief** product. Combine the **layout structure** from `SingleBrief - Dashboard.png` with **visual polish, typography, and spacing** seen in `Hashnode Web`.

---

## ⚙️ Frameworks & Stack

- **Frontend Framework:** Next.js 14+ (App Router)
- **Styling:** Tailwind CSS
- **State Management:** React Context API + React Query
- **Charts:** Recharts or D3.js
- **Icons:** Lucide
- **Typography:** Inter (preferred) or Satoshi
- **Design Tokens:** Follow 8px spacing system, brand colors, and shadows as below

---

## 🎨 Visual Identity

### 🎯 Brand Color Palette

| Color Role           | Hex Value   | Notes                           |
|----------------------|-------------|---------------------------------|
| **Primary Blue**     | `#1A2D64`   | Used in logo + main CTA button  |
| **Highlight Orange** | `#F57C00`   | Used in logo icon & progress    |
| **Soft Orange**      | `#FFE3C3`   | Background gradient tint        |
| **Neutral Gray**     | `#6B7280`   | For secondary text              |
| **Success Green**    | `#2BAE66`   | Used in status indicators       |
| **White**            | `#FFFFFF`   | Background and card base        |

### Design Guidelines

| Element            | Direction                                                  |
|--------------------|------------------------------------------------------------|
| **Typography**     | Inter/Satoshi with hierarchy (e.g. `text-xl font-semibold`)|
| **Corner Radius**  | 8px across all components                                  |
| **Elevation**      | Use soft shadows (e.g. `shadow-md`) where hierarchy demands|
| **Animations**     | Subtle transitions (hover effects, expandable panels)      |

---

## 📐 Layout Plan

### `app/layout.tsx`

- Persistent **Sidebar** on desktop (`lg:flex`) with icons + labels
- Collapsible sidebar for mobile
- Top navbar with:
  - Search bar
  - Profile icon
  - Notifications bell
- Layout wraps `children` content grid

---

## 🧩 Key Pages & Components

### ✅ `app/page.tsx` – Dashboard

- **Daily Brief Card**
- **Recent Queries** sidebar
- **Team Status Card**
- **Data Sources Health**
- **Quick Actions**
- **Team Performance Metrics Chart**
- **Trending Topics**

---

### 💬 `app/query/page.tsx` – Intelligence Interface

- Query Builder
- Synthesized Answer Panel
- Sidebar: Query History + Suggestions

---

### 🧠 `app/memory/page.tsx` – Memory Manager

- Timeline view
- Search + Filter
- Edit/Delete
- Privacy settings toggle

---

### ⚙️ `app/settings/page.tsx` – Settings

Tabs for:
- Profile & Preferences
- Team Config
- Integrations
- Privacy & Data
- Display / Accessibility

---

## 🧱 Component Directory

| Path | Purpose |
|------|---------|
| `components/ui/` | Reusable: buttons, tags, cards, toggles, inputs |
| `components/dashboard/` | Brief card, team chart, query panel |
| `components/query/` | Query form, result viewer |
| `components/memory/` | Timeline, edit/delete |
| `components/trust/` | Source visualizer, confidence indicator |

---

## 📱 Mobile UX Enhancements

- Bottom tab bar
- Horizontal scrolling cards
- Expand/collapse sections
- Touch-friendly controls

---

## 🛡️ Trust Layer Design

- Confidence Score
- Source Attribution
- “Raw Data” Toggle
- Tooltips

---

## 🧪 Sample Test Instructions

- Dark mode
- Responsive breakpoints
- Live state indicators
- Simulated API loop

---

## 🧩 Optional Enhancements (Stretch)

- Keyboard shortcuts
- Click-to-copy
- Editable Briefs
- Draggable dashboard layout
