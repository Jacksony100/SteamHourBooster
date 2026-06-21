# DeckPilot Design System

## Purpose

DeckPilot should feel like a premium gaming SaaS control room: calm, dark, technical, readable, and safe. The interface is built for personal account/session management, not hidden automation. Every control should make state, ownership, risk, and next action obvious.

## Design Principles

1. Dark-first, not gloomy. Use deep navy and graphite as the base, with electric blue and neon green as controlled accents.
2. Glass with restraint. Surfaces use blur, translucent fill, and thin borders, but content must remain sharp and scannable.
3. Status over decoration. Glow is reserved for live status, primary CTAs, and focused controls.
4. Five-second dashboard. A user should immediately understand accounts, online state, active sessions, selected games, subscription health, and risks.
5. Safety by design. Risky actions use confirm modals, destructive buttons are visually distinct, and Steam Guard is treated as a user-driven verification step.
6. No Bootstrap residue. Avoid generic admin tables as the main experience; use dense but polished cards, drawers, command palette, and focused data tables.

## Core Tokens

### Color

| Token | Value | Usage |
| --- | --- | --- |
| `--shb-bg` | `#05070D` | App background |
| `--shb-bg-2` | `#080B12` | Secondary background band |
| `--shb-surface` | `rgba(255,255,255,0.06)` | Default glass card |
| `--shb-surface-strong` | `rgba(255,255,255,0.10)` | Active surface, selected cards |
| `--shb-border` | `rgba(255,255,255,0.12)` | Card and input border |
| `--shb-border-strong` | `rgba(255,255,255,0.20)` | Focused/hover border |
| `--shb-text` | `#F4F8FF` | Main text |
| `--shb-muted` | `#8EA0B8` | Secondary text |
| `--shb-primary` | `#38BDF8` | Electric blue primary |
| `--shb-primary-strong` | `#0EA5E9` | Primary hover/pressed |
| `--shb-success` | `#46F2A6` | Online/success |
| `--shb-warning` | `#FBBF24` | Risk, subscription warning |
| `--shb-danger` | `#FB3F7A` | Errors/destructive actions |

### Gradients

- App background: deep navy layered with a subtle technical grid.
- Primary glow: transparent blue wash around selected cards and primary CTAs.
- Success glow: small controlled glow around online/farming status dots.
- Danger glow: only for critical error states or destructive confirmation.

### Radius

| Token | Value | Usage |
| --- | --- | --- |
| `radius-sm` | `8px` | Inputs, compact pills |
| `radius-md` | `12px` | Buttons, badges, table rows |
| `radius-lg` | `16px` | Cards and modals |
| `radius-xl` | `22px` | Large dashboard panels |

Cards should not become bubbly. Use 12-22px depending on scale, and keep inner elements tighter than outer panels.

### Shadow And Depth

- `shadow-glass`: large soft drop shadow for elevated panels.
- `shadow-card-3d`: subtle top highlight plus low shadow for premium cards.
- `shadow-glow-primary`: electric blue glow for primary interactive focus.
- `shadow-glow-success`: neon green status glow, only for active/online.
- `shadow-glow-danger`: destructive or critical error glow.

Use depth to communicate hierarchy:

1. Background grid.
2. Passive glass cards.
3. Hovered/selected cards.
4. Modals/drawers.
5. Toasts and command palette.

## Typography

Use system UI fonts for performance and native feel. Keep the type compact and dashboard-native.

| Role | Class Guidance | Usage |
| --- | --- | --- |
| Hero title | `text-4xl md:text-5xl font-black` | Login/register brand block only |
| Page title | `text-2xl md:text-3xl font-black` | Dashboard, Admin, Settings |
| Section title | `text-lg font-semibold` | Card headers |
| Body | `text-sm leading-6` | Tables, descriptions |
| Meta | `text-xs uppercase tracking-[0.14em]` | Metric labels, badges |

Do not scale type with viewport width. Keep letter spacing at zero except small uppercase metadata.

## Component Language

### AppShell

- Left sidebar on desktop, compact top navigation on mobile.
- Product mark, primary navigation, safety mode notice, account menu.
- Sidebar must always leave enough width for labels and badges.

### Topbar

- Page title, search/command palette trigger, subscription status, user menu.
- The command palette is the fastest path to accounts, sessions, billing, and admin.

### MetricCard

- One metric per card.
- Include label, value, delta/context, status variant.
- Use skeletons while loading.

### StatusBadge

Variants:

- `online`: green dot, success border.
- `offline`: muted dot.
- `session`: blue dot.
- `warning`: amber dot.
- `error`: danger dot.
- `admin`: violet/blue neutral admin state.

### AccountCard

Required fields:

- label;
- SteamID or "not connected";
- online/offline/error status;
- selected games count;
- active session state;
- last activity;
- visible action buttons: Detail, Games, Start/Stop, Delete.

Delete is never a direct action. It opens a confirm modal with account label.

### SessionCard

Required fields:

- account label;
- status;
- uptime;
- current games;
- worker state;
- recent logs;
- stop button only when active.

### GameCard

- Compact selectable card.
- Shows game name, app id, selected state, optional session indicator.
- Search and multi-select must stay fast.

### PricingCard

- Plan name, price, duration, limits, CTA.
- Highlight recommended plan with primary glow.
- Lifetime plan should feel premium but not visually overpower the page.

### EmptyState

Required fields:

- title;
- helpful explanation;
- primary CTA;
- optional secondary link.

Empty states should reduce anxiety: explain why the area is empty and what happens next.

### ErrorState

Human language. Avoid raw exception text. Include:

- what failed;
- likely reason;
- next action;
- support/audit hint when relevant.

### LoadingSkeleton

- Use shimmer blocks shaped like the final content.
- Do not resize layout after loading.

### Modal And Drawer

- Modal: focused confirmation or step in a flow.
- Drawer: rich detail view without leaving the table/dashboard.
- Both include accessible title, close button, and keyboard escape behavior.

### DataTable

- Used for admin users and audit logs.
- Sticky header, compact rows, clear filters, visible status badges.
- Avoid making the user scroll horizontally for primary actions on desktop.

## Motion

Use subtle micro-motion:

- card reveal: 120-180ms;
- hover lift: 120ms;
- button press: 80ms scale to `0.98`;
- skeleton shimmer: 1.6s;
- modal/drawer entrance: 160-220ms.

Avoid constant decorative movement. Motion must explain state or improve feedback.

## Accessibility

- Minimum contrast for body text: WCAG AA.
- Keyboard focus uses visible blue ring.
- Icon-only controls need `aria-label`.
- Modal/drawer focus must stay inside overlay.
- Error text must be programmatically associated with fields where possible.

## Safety And Compliance UI

The product must not present platform-rule circumvention, network-routing evasion, or hidden automation as features. The interface should say:

- "Only add accounts you own."
- "Sessions are visible and user-controlled."
- "Steam Guard is entered by the user when Steam requests it."
- "Risk/bans are displayed, not hidden."

## Implementation Notes

- Tailwind tokens live in `apps/web/tailwind.config.ts`.
- Runtime CSS variables live in `apps/web/app/globals.css`.
- React UI-kit skeletons live in `apps/web/components/ui-kit`.
- Legacy Flask compatibility variables live in `legacy/flask/steam_hour_booster/static/css/design-system.css`.
