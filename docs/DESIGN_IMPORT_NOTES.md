# Design Import Notes

Source archive: `Design system и прототип.zip` → extracted to `.design-import/` (git-ignored).

## Files found
| File | Purpose |
|---|---|
| `SteamHourBooster.dc.html` | Full design-system prototype (1313 lines, single-file, DesignCode-style export with `<sc-if>` conditionals) |
| `screenshots/landing-hero.png` | Hero preview reference |
| `support.js` | Prototype runtime (templating only — not ported) |
| `.thumbnail` | Thumbnail metadata |

The prototype is a **templating export** (`<x-dc>`, `<sc-if value="{{ showDashboard }}">`, `onClick="{{ goDashboard }}"`), not production React. It is the **visual source of truth**; it is not copied verbatim (no `dangerouslySetInnerHTML`, no inline-style dump).

## Design tokens (extracted)
| Token | Value | Mapped to |
|---|---|---|
| Background | `#05070D` | `--shb-bg` |
| Text primary | `#EAF0FA` | `--shb-text` |
| Text muted | `#9DAAC2` | `--shb-muted` |
| Text dim | `#7C8BA5` | `--shb-muted-dim` |
| Primary (electric blue) | `#2E8BFF` | `--shb-primary` |
| Primary strong | `#1E6FE0` | `--shb-primary-strong` |
| Primary soft | `#5BA6FF` | `--shb-primary-soft` |
| Violet | `#8B5CF6` / soft `#B79CFF` | `--shb-violet` / `--shb-violet-soft` |
| Neon green | `#3DF5A0` | `--shb-success` |
| Amber | `#F5B83D` | `--shb-warning` |
| Red | `#FF5C7A` | `--shb-danger` |
| CTA gradient | `linear-gradient(135deg,#2E8BFF,#1E6FE0)` | `--shb-cta-gradient` / `.cta-gradient` |
| Brand gradient | `linear-gradient(120deg,#5BA6FF,#8B5CF6 55%,#3DF5A0)` | `--shb-brand-gradient` / `.text-gradient` |
| Icon gradient | `linear-gradient(135deg,#2E8BFF,#8B5CF6)` | `--shb-icon-gradient` |
| Display font | `Satoshi` (700/900) | `h1,h2,h3,.font-display` |
| Body font | `General Sans` (400–700) | `body` |
| Page background | triple radial glow (blue TL / violet TR / green bottom) + masked 64px grid | `--shb-page-bg` |

Fonts loaded from Fontshare in `app/layout.tsx`. Surfaces: glass `linear-gradient(160deg, rgba(18,23,36,.94), rgba(10,13,22,.96))`, borders `rgba(255,255,255,.07–.1)`, radius 11–20px. Motion keyframes in prototype: pulse, float, reveal, shimmer, spin, drawer, modal, overlay.

## Screen inventory (from prototype)
- **Marketing:** Nav, Hero (+ dashboard preview), Problem, Solution, Features, How-it-works, Pricing, Security, FAQ, CTA, Footer.
- **App shell:** Dashboard, Accounts, Sessions, Games, Billing, Logs, Settings, Support (sidebar nav + topbar + command palette `cmdOpen`, add-account `addOpen`, detail drawer `drawerOpen`).
- **Admin:** Overview, Users, Subscriptions, Payments, Sessions, Audit.

## Component patterns (from prototype CSS)
`.shb-cta` (primary gradient button), `.shb-ghost` (ghost button), `.shb-card` (hover-lift glass card), `.shb-nav` (sidebar item + `.active`), `.shb-link`, `.shb-row` (table row hover), `.shb-ico` (icon button), `.shb-drawer`, `.shb-modal`, `.shb-ovl` (overlay), `.shb-fade`.

## What was implemented in this pass
- **Design tokens** retuned to the exact prototype palette in `app/globals.css` (`:root`) and `lib/design-tokens.ts` (added `gradient` + `font` groups).
- **Signature background** (triple radial glow + masked grid) applied to `body`.
- **Brand/CTA gradients** as reusable classes (`.text-gradient`, `.cta-gradient`).
- **Fonts** (Satoshi / General Sans) wired via Fontshare in `app/layout.tsx`.
- **Steam media components** `GameImage` and `SteamAvatar` (prototype `GameImage`/`SteamAvatar` requirements) added to `components/ui-kit/`.

## What remains (tracked in BETA_READINESS.md)
- Port the remaining marketing sections (Problem/Solution/How-it-works/FAQ/CTA) into `components/landing/*`.
- Adopt the `ui-kit` components in dashboard/admin screens (replace inline re-implementations — the audit flagged the kit as currently dead code).
- New routes from the prototype not yet present: `/onboarding`, `/sessions`, `/games`, `/logs`, `/support`, and split admin routes (`/admin/users`, `/admin/subscriptions`, `/admin/payments`, `/admin/sessions`, `/admin/audit`).
- Replace the hand-rolled Steam-Guard modal with a focus-trapped Radix dialog.
- Complete i18n coverage across the authenticated app (currently auth/nav/landing only).
