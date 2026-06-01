# ReelWrapped / Spotifyndr — AT3 Project TODO

Major workstreams for the assessment. Check items off as you complete them.

---

## 1. Secure Software Architecture

Harden the app against common vulnerabilities and align with secure design practice (OWASP).

- [ ] Run and triage security scans (e.g. Bandit, dependency checks); track fixes in version control
- [ ] Fix SQL injection risks — address Bandit **B608** (and similar) in `main.py`; use parameterised queries / ORM patterns consistently
- [ ] Review and fix **broken access control** — users must only access their own data; admin routes must require valid admin session
- [ ] Prevent **XSS** — escape or sanitise user-controlled output in templates; validate input on forms and APIs
- [ ] **Admin page hardening** — secure PIN flow, session expiry, CSRF where applicable, no admin UI leakage to regular users (see Admin Dashboard phases 1 & 6)
- [ ] OWASP alignment pass — document how the app addresses relevant Top 10 categories for AT3 evidence

---

## 2. Spotifyndr pivot

Adapt the Instagram-based ReelWrapped codebase to **Spotifyndr** (Spotify-based), where Spotify data and API access are more practical than Instagram.

- [ ] Define Spotify data model (listening history, artists, genres, playlists) vs current Instagram/reel fields
- [ ] Register app in Spotify Developer Dashboard; configure redirect URIs and scopes
- [ ] Replace or refactor Instagram auth / import flow with Spotify OAuth and token handling
- [ ] Update profile, trends, and mutuals logic to use Spotify-derived signals instead of reel metadata
- [ ] Refresh UI copy, branding, and empty states for Spotifyndr
- [ ] Update README and deployment notes for Spotify credentials and local testing

---

## 3. Software automation / machine learning

Integrate ML for matching and discovery features.

### Find Mutuals — percentage (%) match

- [ ] Collect or label training features for user–user similarity (shared artists, genres, listening overlap, etc.)
- [ ] Implement **K-Nearest Neighbour (KNN)** for neighbour-based similarity / match scoring
- [ ] Implement **Logistic Regression** for calibrated **% match** display on the Find Mutuals page
- [ ] Wire model output to the existing mutuals UI; handle cold-start users with sensible defaults

### For You page (FYP) — discovery algorithm

- [ ] Implement **Logistic Regression** (or incremental training) for FYP ranking / recommendation scores
- [ ] Connect **swipe left / swipe right on interests** to feature updates and model feedback
- [ ] Evaluate offline (hold-out set) and sanity-check recommendations in the app

---

## Admin Dashboard Implementation

Implementation checklist for the admin area. Security hardening for admin is also tracked under **§1 Secure Software Architecture** above.

### Phase 1: Authentication and Entry Point
- [ ] Add "Sign in as Admin" button to support.html
- [ ] Create floating popup modal for PIN input in support.html
- [ ] Add PIN authentication route in admin.py
- [ ] Implement admin session management

### Phase 2: Dashboard Structure
- [ ] Update admin.html template with tabbed interface (Admin View / User View)
- [ ] Implement User View tabs to display Trends and Mutuals pages identically to users
- [ ] Create Admin View with Manage Trend Page and Manage Profiles Page buttons

### Phase 3: Management Pages
- [ ] Create manage_trends.html template with table for trends data
- [ ] Create manage_profiles.html template with table for user profiles data
- [ ] Add checkboxes for bulk selection and three-dot menus per row
- [ ] Implement View, Edit, Delete options in three-dot menu

### Phase 4: CRUD Operations
- [ ] Add routes for trend management (view, edit, delete, bulk delete)
- [ ] Add routes for profile management (view, edit, delete, bulk delete)
- [ ] Implement edit modals with form fields mirroring profile edit
- [ ] Add confirmation popups for delete operations

### Phase 5: JavaScript and Interactions
- [ ] Update main.js for popup handling and PIN submission
- [ ] Add table interaction JS (bulk select, three-dot menu)
- [ ] Implement AJAX calls for admin actions
- [ ] Add loading states and success/error notifications

### Phase 6: Security and Polish
- [ ] Ensure admin sessions are invisible to regular users
- [ ] Add proper error handling and validation
- [ ] Make responsive and accessible
- [ ] Test all functionalities
