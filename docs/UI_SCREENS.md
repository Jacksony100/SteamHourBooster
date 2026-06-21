# DeckPilot UI Screens

## 1. Login

Goal: make returning users feel they are entering a secure premium control room.

Layout:

- two-column desktop, single-column mobile;
- left brand block with product name, safety mode, and trust notes;
- right glass auth panel with username/password, error state, submit, register link.

States:

- loading button while signing in;
- invalid credentials with human text;
- account banned message without exposing internals.

Primary CTA: `Sign in`.

## 2. Register

Goal: explain ownership and safety before account creation.

Layout:

- brand header;
- onboarding copy;
- glass form with username, password, password hints, ownership/safety notice.

Required details:

- password minimum requirements;
- terms-compatible notice;
- link to login.

Primary CTA: `Create account`.

## 3. Onboarding

Goal: take a new user from zero to first safe setup.

Steps:

1. Confirm account ownership and safety mode.
2. Add first Steam account.
3. Complete Steam Guard when requested.
4. Choose games.
5. Review dashboard.

UI pattern:

- horizontal stepper on desktop;
- vertical stepper on mobile;
- persistent "what happens next" panel.

## 4. No Subscription

Goal: explain why access is limited and direct to checkout.

Layout:

- concise access-blocked glass panel;
- current account state preview;
- pricing summary with recommended plan;
- comparison table below first fold.

Primary CTA: `Choose plan`.

## 5. Pricing And Checkout

Plans:

- Week;
- Month;
- 3 Months;
- 6 Months;
- Lifetime.

Layout:

- plan cards with duration, price, benefits;
- selected plan checkout panel;
- payment pending state;
- webhook/provider abstraction message.

States:

- loading plans;
- selected plan;
- checkout created;
- payment pending;
- checkout error.

## 6. Main Dashboard

Five-second answer:

- accounts count;
- online accounts;
- active sessions;
- selected games;
- subscription end date;
- risks/errors.

Layout:

- AppShell with sidebar/topbar;
- metric cards row;
- account grid/table hybrid;
- active sessions widget;
- ban/risk panel;
- recent activity log.

Primary actions:

- Add account;
- Open command palette;
- Start/stop session from account card.

## 7. Account Detail

Goal: show everything relevant to one Steam account without losing dashboard context.

Pattern: right drawer.

Sections:

- identity and status;
- selected games;
- active/current session;
- ban info;
- last logs;
- destructive zone.

Danger action: delete account through confirm modal only.

## 8. Add Steam Account Modal

Flow:

1. Credentials.
2. Steam Guard if needed.
3. Game selection.
4. Done.

Step 1 fields:

- label;
- Steam username;
- Steam password;
- ownership attestation checkbox.

Security note:

- credentials are encrypted;
- credentials are never displayed back;
- only user-owned accounts are allowed.

## 9. Steam Guard Modal

Goal: collect user-provided Steam Guard code when Steam asks for it.

Rules:

- never imply platform-rule circumvention;
- never store Steam Guard code;
- show timeout/retry state;
- allow cancel.

Copy:

- "Enter the Steam Guard code shown by Steam."
- "This completes the normal Steam Guard step requested by Steam."

## 10. Game Selector

Goal: choose games quickly and visibly.

Layout:

- search input;
- filter chips: selected, unselected, recently used;
- compact GameCard grid;
- selected count sticky footer;
- save/cancel buttons.

States:

- loading owned games;
- no games found;
- Steam API unavailable;
- selection saved.

## 11. Active Sessions

Goal: show current transparent activity sessions.

Layout:

- SessionCard list;
- uptime;
- current games;
- worker state;
- recent logs;
- stop controls.

Stop requires no destructive confirm, but should use clear feedback.

## 12. Ban Info Panel

Goal: surface risk honestly.

Fields:

- VAC bans;
- community ban;
- economy ban;
- days since last ban;
- fetched/cached timestamp.

States:

- clean;
- warning;
- error fetching;
- stale cache.

## 13. Settings

Sections:

- profile;
- security;
- theme;
- language;
- notification preferences;
- safety mode explanation.

Controls:

- ThemeToggle;
- LanguageToggle;
- active session revocation;
- account deletion confirmation.

## 14. Admin Users

Goal: find and manage users quickly.

Layout:

- admin metrics;
- search/filter bar;
- DataTable with username, role, status, subscription, last seen, actions;
- user detail drawer.

Filters:

- active/banned;
- subscribed/free;
- admin/user;
- recent activity.

## 15. Admin User Detail Drawer

Sections:

- profile and ids;
- subscription;
- accounts summary;
- recent audit events;
- admin controls.

Danger:

- ban user with confirm modal;
- revoke admin with confirm modal.

## 16. Admin Billing Controls

Goal: allow manual subscription override with audit trail.

Controls:

- grant/revoke subscription;
- plan selector;
- end date selector;
- reason field required;
- audit preview before confirm.

States:

- saved;
- validation error;
- audit log created.

## 17. Audit Log

Goal: make sensitive changes traceable.

Layout:

- filterable DataTable;
- actor, action, target, timestamp, metadata;
- detail drawer for metadata;
- data export action.

Required events:

- admin role changes;
- subscription overrides;
- user bans;
- account deletes;
- session start/stop.

## Responsive Rules

- Desktop: sidebar + topbar, 12-column grid, drawers for detail.
- Tablet: collapsible sidebar, two-column cards.
- Mobile: top navigation, single-column cards, bottom-safe modal actions.

## Copy Rules

- Use "session" or "activity session", not "farm".
- Use "account owner" and "visible controls".
- Avoid promises of ban avoidance, hidden behavior, or platform circumvention.
