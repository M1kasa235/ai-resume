# Frontend Improvement Plan

## Context
The AI Job Assistant frontend has 9 pages (Dashboard, Jobs, JobDetail, Questions, Workbench, AIInterview, AIAdvisor, Profile, Settings) built with React + Ant Design. The user wants improvements across three axes: **功能完善** (feature completion), **交互体验增强** (interaction experience), and **界面视觉优化** (visual polish). This plan targets specific, high-impact improvements per page while maintaining the existing architecture.

---

## I. Global Improvements

### 1. Document Title Per Route
Set `document.title` on route change via a hook or the router meta.

**Files:**
- `frontend/src/App.tsx` — add `useEffect` watching `location.pathname` to set title from route meta
- `frontend/src/router/index.tsx` — meta already has `title` field, just need to wire it up

### 2. Loading Skeleton for Lazy Routes
Enhance the `LoadingFallback` in `App.tsx` to be more visually pleasing (a skeleton of the main layout instead of a centered spin).

**Files:**
- `frontend/src/App.tsx` — enhance `LoadingFallback` component

### 3. Error Handling Consistency
Standardize error display across pages (consistent toast style, retry buttons on failure).

**Files:**
- `frontend/src/components/ErrorBoundary/index.tsx` — review and enhance
- All page components — unify error handling pattern

---

## II. Dashboard (仪表盘)

### 1. Entry Animation for Stat Cards
Add staggered `fadeInUp` animation for the 4 stat cards when the page loads, using CSS `@keyframes` with `animation-delay`.

### 2. Dynamic Activity List Height
Replace `max-height: 320px` with a height that fills available space using flex.

### 3. Quick Action Ripple Effect
Add a subtle ripple/scale effect on click for quick action items.

**Files:**
- `frontend/src/features/dashboard/index.tsx`
- `frontend/src/features/dashboard/Dashboard.module.scss`

---

## III. Jobs (岗位搜索) — Major Improvements

### 1. Collapsible Filter Bar
The filter row is too tall. Make it collapsible — show only keyword search + 2-3 essential filters by default, with a "展开筛选" toggle button.

### 2. Fix Empty Search Button
Line 394: `onClick={() => {}}` — the search button does nothing. Wire it to trigger a search refetch.

### 3. Persistent Favorites
Favorites are stored in memory only (lost on page refresh). Load user's favorited job IDs from `jobApi.getMyFavorites` on mount, and sync add/remove with the backend properly.

### 4. "My Favorites" View
Add ability to filter the list to show only favorited jobs (a button/toggle in the results header).

### 5. Job Detail Page Redesign
The detail page is very basic — raw HTML, no sidebar, no company info section. Enhance with:
- Company info card (logo, stage, size)
- Properly formatted description/requirements sections with card dividers
- Related/similar jobs section (using category-based suggestions or API)
- Salary highlight badge
- Skills/tags displayed as colored Ant Design tags

**Files:**
- `frontend/src/features/jobs/index.tsx`
- `frontend/src/features/jobs/Jobs.module.scss`
- `frontend/src/features/jobs/Detail.tsx`
- `frontend/src/features/jobs/JobDetail.module.scss`

---

## IV. Questions (题库练习)

### 1. Add Category Filter
Currently only difficulty + type filtering. Add a category select (using `questionApi` category data or a simple category list).

### 2. Practice Modal Enhancement
The modal for answering questions is functional but plain. Enhance with:
- Better option display (radio cards for choices)
- Progress indicator (current question # out of total)
- Timer display
- Keyboard shortcuts (Enter to submit)

### 3. Question Cards Visual Polish
Improve card layout with better visual hierarchy: difficulty badge, type tag, frequency, and an "开始练习" button that's always visible.

### 4. Tab Pagination
The "错题本" and "收藏题目" tabs don't paginate — only show first page. Add proper pagination.

**Files:**
- `frontend/src/features/questions/index.tsx`
- `frontend/src/features/questions/Questions.module.scss`

---

## V. Workbench (工作台)

### 1. Fix Resume/Stats Layout
Currently resume preview and stats are mutually exclusive (line 210: if resume exists → show preview, else → show stats). Show both: stats summary always visible, resume as a tab.

### 2. Delete Confirmation
Application delete button (line 143) has no confirmation. Add `Modal.confirm`.

### 3. Application Status Filter
Add status filter tabs (全部/待处理/筛选中/面试中/已拒绝/已录用) above the table.

**Files:**
- `frontend/src/features/workbench/index.tsx`
- `frontend/src/features/workbench/Workbench.module.scss`

---

## VI. AI Interview (AI面试)

### 1. Auto-scroll Chat
Messages list doesn't auto-scroll to bottom on new messages. Add `useEffect` with `scrollIntoView`.

### 2. Typing Indicator
Show a "AI正在输入..." indicator while waiting for response.

### 3. Chat UX Polish
- Message bubbles with better spacing and avatar icons
- Timestamp display
- Smooth scroll animation

**Files:**
- `frontend/src/features/aiInterview/index.tsx`
- `frontend/src/features/aiInterview/AIInterview.module.scss`

---

## VII. AI Advisor (AI求职顾问)

### 1. Image Upload Support
The API supports `image_url` but the UI has no image upload button. Add an image upload button in the message input area.

**Files:**
- `frontend/src/features/aiAdvisor/index.tsx`
- `frontend/src/features/aiAdvisor/components/MessageInput.tsx`
- `frontend/src/features/aiAdvisor/Advisor.module.scss`

---

## VIII. Profile (个人中心)

### 1. Fix Avatar Upload
The Upload component is wired to `handleAvatarChange` but there's no actual upload URL configured and the API doesn't support it. Either implement avatar upload via a new API endpoint or hide the upload button if not available.

### 2. Skills/ Tags Section
Add a section for the user to add skill tags (前端开发, React, TypeScript, etc.) for better job matching.

**Files:**
- `frontend/src/features/profile/index.tsx`
- `frontend/src/features/profile/Profile.module.scss`

---

## IX. Settings (设置)

### 1. Persist Settings
All settings switches are UI-only. Connect them to a user preferences API or localStorage persistence.

### 2. Fix Account Info
Account info is hardcoded (username: 'user123', email: 'user@example.com'). Connect to actual user data from user store.

### 3. Replace Native Select
Language selector uses HTML `<select>` instead of Ant Design `<Select>` for consistency.

**Files:**
- `frontend/src/features/settings/index.tsx`
- `frontend/src/features/settings/Settings.module.scss`

---

## X. Layout (MainLayout)

### 1. Sidebar Profile/Settings Links
The sidebar menu doesn't include profile/settings — they're only in the user dropdown. Add them at the bottom of the sidebar for quicker access.

**Files:**
- `frontend/src/components/layouts/MainLayout.tsx`
- `frontend/src/components/layouts/MainLayout.module.scss`

---

## Implementation Order (Recommended)

1. **Quick wins**: Document title, loading skeleton, fix settings/profile hardcoded data, fix empty search button, replace native select
2. **Layout & navigation**: Sidebar additions, collapsible filter bar
3. **Feature completion**: Persistent favorites, category filter for questions, workbench resume layout fix, image upload for advisor
4. **UX polish**: Entry animations, auto-scroll chat, typing indicator, practice modal enhancement, delete confirmations
5. **Visual polish**: Job detail redesign, question cards polish, settings persistence, skills section

## Verification
- Run `npm run dev` in `frontend/` and navigate each page to verify all improvements
- Check console for errors
- Confirm favorites persist after page refresh
- Verify chat auto-scroll works in AI Interview
