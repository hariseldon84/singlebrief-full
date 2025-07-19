# 🎨 SingleBrief UI Design Guide & Frontend Generation

This document provides comprehensive guidance for designing and generating the SingleBrief user interface, consolidating information from the product requirements and architecture specifications.

## 🎯 Objective

Create a professional, modern, and enterprise-grade interface for the **SingleBrief** product. Combine the **layout structure** from `SingleBrief - Dashboard.png` with **visual polish, typography, and spacing** seen in `Hashnode Web`.

## 📋 Product Overview Context

SingleBrief is an AI-powered intelligence operative designed for managers and team leads. It consolidates team intelligence, document data, and personal sources (email, calendar, cloud files) into one unified AI interface. Rather than users chasing updates, SingleBrief proactively collects, synthesizes, and delivers the final answer. It learns over time, remembers decisions, and adapts to how each user and team operates.

**Tagline**: "Answers from everyone. Delivered by one."

## 🧩 Core Features to Implement in UI

### 1. 🧠 Team Interrogation AI  
- Actively queries team members for responses to a lead's question  
- Uses adaptive tone, memory, and context
- **UI Needs**: Query builder interface, response viewer, conversation history

### 2. 🔁 Memory Engine  
- Tracks decisions, conversation threads, and task outcomes  
- Improves accuracy and personalization over time  
- Optional per-user memory opt-in settings
- **UI Needs**: Memory management interface, preferences controls, decision history visualization

### 3. 🗂️ Data Streams Layer  
- Integrates with Slack, Email, Docs, Calendar, GitHub, CRM, and more  
- Fetches relevant content in real-time with contextual filters
- **UI Needs**: Source connection management, data source health indicators, filtering controls

### 4. 📊 Daily Brief Generator  
- Personalized, TL;DR summaries for leaders (wins, risks, actions)  
- Customizable frequency and data focus
- **UI Needs**: Brief display cards, customization controls, scheduling interface

### 5. 👁️ Trust & Transparency System  
- Displays confidence scores  
- Shows "who said what" + traceable synthesis chain  
- Raw data toggle for auditing or override
- **UI Needs**: Confidence visualizations, source attribution UI, raw/synthesized data toggle

## 👤 Target User Personas

Design with these specific user personas in mind:

### Maya – Marketing Manager
- **Needs**: Daily updates from 4 functions, campaign performance metrics
- **Wants**: Blockers surfaced quickly, visual presentation of data
- **UI Focus**: Dashboard with campaign metrics, cross-functional blocker alerts

### Ravi – Remote Tech Lead
- **Needs**: Consolidated view of async teams across time zones
- **Wants**: Single coherent view of status and risks
- **UI Focus**: Status board, risk indicators, timezone-aware notifications

### Neha – Founder/CEO
- **Needs**: Ultra-efficient information processing
- **Wants**: 3-line briefing with memory and decision recall
- **UI Focus**: Executive summary view, decision history, minimal UI with high value density

### Sahil – Sales Ops Head
- **Needs**: Knowledge distribution to sales team
- **Wants**: Pattern detection from pipeline data
- **UI Focus**: CRM integration dashboards, pattern visualization, knowledge base

### Asha – HR Business Partner
- **Needs**: Team sentiment monitoring without surveys
- **Wants**: Early detection of burnout signs
- **UI Focus**: Sentiment analysis visualization, confidential reporting, wellness metrics

## ⚙️ Technical Architecture Context

### Frameworks & Stack
- **Frontend Framework:** Next.js 14+ (App Router)
- **Styling:** Tailwind CSS
- **State Management:** React Context API + React Query
- **Charts:** Recharts or D3.js
- **Icons:** Lucide
- **Typography:** Inter (preferred) or Satoshi
- **Authentication**: OAuth 2.0 + Role-based access
- **Design Tokens:** Follow 8px spacing system, brand colors, and shadows
- **Hosting**: Vercel (Frontend)

### 🎨 Visual Identity

#### Brand Color Palette

| Color Role           | Hex Value   | Notes                           |
|----------------------|-------------|---------------------------------|
| **Primary Blue**     | `#1A2D64`   | Used in logo + main CTA button  |
| **Highlight Orange** | `#F57C00`   | Used in logo icon & progress    |
| **Soft Orange**      | `#FFE3C3`   | Background gradient tint        |
| **Neutral Gray**     | `#6B7280`   | For secondary text              |
| **Success Green**    | `#2BAE66`   | Used in status indicators       |
| **White**            | `#FFFFFF`   | Background and card base        |

#### Design Guidelines

| Element            | Direction                                                  |
|--------------------|------------------------------------------------------------|
| **Typography**     | Inter/Satoshi with hierarchy (e.g. `text-xl font-semibold`)|
| **Corner Radius**  | 8px across all components                                  |
| **Elevation**      | Use soft shadows (e.g. `shadow-md`) where hierarchy demands|
| **Animations**     | Subtle transitions (hover effects, expandable panels)      |

### Core UX/UI Principles
1. **User-Centric Above All**: Every design decision must serve user needs
2. **Simplicity Through Iteration**: Start simple, refine based on feedback
3. **Delight in the Details**: Thoughtful micro-interactions create memorable experiences
4. **Design for Real Scenarios**: Consider edge cases, errors, and loading states
5. **Collaborate, Don't Dictate**: Best solutions emerge from cross-functional work

## � Layout Plan

### `app/layout.tsx`

- Persistent **Sidebar** on desktop (`lg:flex`) with icons + labels
- Collapsible sidebar for mobile
- Top navbar with:
  - Search bar
  - Profile icon
  - Notifications bell
- Layout wraps `children` content grid

## 🧩 Key Pages & Components

### ✅ `app/page.tsx` – Dashboard

- **Daily Brief Card**
- **Recent Queries** sidebar
- **Team Status Card**
- **Data Sources Health**
- **Quick Actions**
- **Team Performance Metrics Chart**
- **Trending Topics**

### 💬 `app/query/page.tsx` – Intelligence Interface

- Query Builder
- Synthesized Answer Panel
- Sidebar: Query History + Suggestions

### 🧠 `app/memory/page.tsx` – Memory Manager

- Timeline view
- Search + Filter
- Edit/Delete
- Privacy settings toggle

### ⚙️ `app/settings/page.tsx` – Settings

Tabs for:
- Profile & Preferences
- Team Config
- Integrations
- Privacy & Data
- Display / Accessibility

## 🧱 Component Directory

| Path | Purpose |
|------|---------|
| `components/ui/` | Reusable: buttons, tags, cards, toggles, inputs |
| `components/dashboard/` | Brief card, team chart, query panel |
| `components/query/` | Query form, result viewer |
| `components/memory/` | Timeline, edit/delete |
| `components/trust/` | Source visualizer, confidence indicator |

## 📱 Mobile UX Enhancements

- Bottom tab bar
- Horizontal scrolling cards
- Expand/collapse sections
- Touch-friendly controls (min 44x44px tap targets)

## 🛡️ Trust Layer Design

- Confidence Score visualization (color-coded: red to green)
- Source Attribution panels
- "Raw Data" Toggle
- Tooltips explaining synthesized answers
- Visual "Source Chain" diagram

## 📊 Data Structures & API Contracts

Implement frontends that expect these API response structures:

### 1. Daily Brief Data:
```json
{
  "brief_id": "string",
  "generated_at": "ISO-date",
  "updated_at": "ISO-date",
  "confidence_score": 85,
  "sections": [
    {
      "type": "wins",
      "items": [
        {
          "title": "string",
          "description": "string",
          "sources": ["string"],
          "confidence": 90
        }
      ]
    },
    {
      "type": "risks",
      "items": [...]
    },
    {
      "type": "actions",
      "items": [...]
    }
  ]
}
```

### 2. Query Response Data:
```json
{
  "query_id": "string",
  "question": "string",
  "synthesized_answer": "string",
  "confidence_score": 75,
  "sources": [
    {
      "source_type": "team_member",
      "source_name": "string",
      "content": "string",
      "timestamp": "ISO-date",
      "confidence": 80
    },
    {
      "source_type": "document",
      "source_name": "string",
      "content": "string",
      "timestamp": "ISO-date",
      "confidence": 70
    }
  ],
  "related_queries": ["string"]
}
```

## 🧪 Testing & Requirements

### Accessibility Requirements
- Ensure all components meet WCAG 2.1 AA standards
- Implement keyboard navigation throughout the application
- Include proper ARIA attributes and semantic HTML
- Maintain adequate color contrast (minimum 4.5:1 for text)

### Performance Requirements
- Page load time under 1.5 seconds
- Time to interactive under 3 seconds
- Implement code splitting and lazy loading for optimal performance
- Use efficient rendering practices (virtualization for long lists)

### Sample Test Instructions
- Dark mode functionality
- Responsive breakpoints verification
- Live state indicators
- Simulated API loop

## 📱 UI Component Specifications

### Key Interface Components

#### 1. Daily Brief Card
- **Purpose**: Summarize key updates for leaders in a concise, scannable format
- **Key Elements**:
  - Wins section with success metrics
  - Risks section with potential blockers
  - Actions section with recommended next steps
  - Confidence score indicator
  - Last updated timestamp
  - Source information toggle
- **Styling**: Primary card with shadow-md, rounded-lg (8px), prominent position in dashboard

#### 2. Query Builder
- **Purpose**: Allow users to formulate questions to the intelligence system
- **Key Elements**:
  - Natural language input field
  - Team member selector
  - Data source filters
  - Priority level indicator
  - Submit button (Primary Blue #1A2D64)
  - Quick query templates/suggestions
- **Styling**: Clean input with focus state, consistent with brand colors

#### 3. Memory Manager
- **Purpose**: Review and control what the system has learned
- **Key Elements**:
  - Memory timeline view
  - Category filters
  - Search functionality
  - Delete/edit controls
  - Export options
  - Privacy toggles
- **Styling**: Timeline with Highlight Orange (#F57C00) progress indicators

#### 4. Trust Indicators
- **Purpose**: Provide transparency into data reliability
- **Key Elements**:
  - Confidence score visualization (0-100%)
  - Source attribution panels
  - Synthesis method explainers
  - Raw/processed data toggle
  - Feedback mechanism
- **Styling**: Color scale from red (low confidence) through Highlight Orange to Success Green (#2BAE66)

## 🧠 UX Design Best Practices

1. **Progressive Disclosure**: Start with high-level summaries, allow drill-down for details
2. **Contextual Help**: Provide tooltips and guidance without overwhelming the interface
3. **Consistent Feedback**: Always show system status and confirmation of actions
4. **Efficient Workflows**: Minimize clicks for common tasks
5. **Adaptive Interface**: Personalize the experience based on user role and preferences
6. **Error Prevention**: Design interfaces that guide users away from mistakes
7. **Recovery Options**: Make it easy to undo actions or correct mistakes
8. **Loading States**: Design thoughtful loading states and placeholders

## 📊 UI Evaluation Checklist

- [ ] Does the UI clearly communicate the core value proposition?
- [ ] Are all primary actions immediately discoverable?
- [ ] Does the interface work well across devices (desktop, tablet, mobile)?
- [ ] Are accessibility standards met (contrast, keyboard navigation, screen reader support)?
- [ ] Do confidence scores and trust indicators provide appropriate transparency?
- [ ] Is information density appropriate for the target users?
- [ ] Are all persona-specific needs addressed in the interface?
- [ ] Does the UI reflect the brand personality and tone?
- [ ] Are loading, empty, and error states designed thoughtfully?
- [ ] Does the interface scale appropriately as content grows?

## 🧩 Optional Enhancements (Stretch Goals)

- Keyboard shortcuts for power users
- Click-to-copy functionality for sharing insights
- Editable Briefs for collaborative refinement
- Draggable dashboard layout for personalization
- Integration of ambient intelligence notifications
- Personalized AI interface adaption based on usage patterns
- Advanced visualization options for data relationships
- Voice and natural language interaction layer

---

*This document serves as a comprehensive guide for designing and generating the SingleBrief user interface, aligning with product requirements, technical architecture, and UX best practices. Follow the brand color palette and visual identity guidelines for consistent implementation.*
