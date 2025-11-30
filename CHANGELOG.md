# Changelog - LangSwap

All notable changes to the LangSwap project will be documented in this file.

---

## [1.0.0] - 2024-12-01

### 🎉 Initial Release - Production Ready

#### Core Features Implemented
- ✅ Bidirectional language learning (Thai ↔ English)
- ✅ 43+ interactive lessons across both languages
- ✅ Songs catalogue with dedicated tab
- ✅ Progress tracking and favorites system
- ✅ Text-to-Speech (TTS) for both Thai and English
- ✅ Swipe gestures for flashcard navigation
- ✅ Mute button with persistent preferences
- ✅ Dark/light theme toggle
- ✅ 14 language UI translations (i18n)

#### Translation & Voice
- ✅ Speech-to-Translate component with instant translation
- ✅ Push-to-talk microphone button (mobile)
- ✅ Voice recording with visual feedback
- ✅ Translation history (last 10)
- ✅ Language swap button
- 🔧 Speech-to-text API integration ready (mocked for now)

#### Authentication & Security
- ✅ JWT-based authentication with bcrypt password hashing
- ✅ Email/password login and registration
- ✅ Dual owner accounts created:
  - jakemadamson2k14@gmail.com (Jake Adamson - OWNER)
  - Northerner1993@gmail.com (Co-Owner - OWNER)
- ✅ Role-based access control (user, staff, admin, owner)
- ✅ Secure token storage with 7-day expiration

#### Staff Management System
- ✅ Admin dashboard for staff management
- ✅ Access code generator for staff registration
- ✅ Database storage for all access codes
- ✅ Comprehensive audit logging
- ✅ Permission assignment system:
  - global_sales_conduct
  - data_protection
  - staff_management
- ✅ Staff creation, listing, and deletion endpoints

#### Premium Subscription System
- ✅ Monthly plan: £5.99/month
- ✅ Lifetime plan: £2.99 (one-time payment)
- ✅ Coupon code system with validation
- ✅ Discount application
- ✅ Usage tracking
- ✅ Subscription status checking
- ✅ Ad removal for premium users

#### API Endpoints
**Authentication:**
- POST /api/register
- POST /api/login
- GET /api/me
- POST /api/init-admin

**Lessons:**
- GET /api/lessons
- GET /api/lessons/{id}
- POST /api/init-data

**Translation:**
- POST /api/translate

**Premium:**
- POST /api/subscribe
- GET /api/my-subscription
- POST /api/coupons
- GET /api/coupons/validate/{code}

**Staff Management:**
- POST /api/staff
- GET /api/staff
- DELETE /api/staff/{id}
- POST /api/access-codes/generate
- POST /api/staff/register-with-code
- GET /api/access-codes
- GET /api/access-codes/logs

#### Technical Improvements
- ✅ Logo integration (colored-logo.png)
- ✅ App.json updated with proper metadata
- ✅ Bundle identifier: com.langswap.app
- ✅ Microphone permissions configured
- ✅ Google Sign-In dependencies installed
- ✅ Professional README documentation
- ✅ Comprehensive .gitignore
- ✅ Database schema optimized

#### UI/UX Enhancements
- ✅ Dynamic header titles (Learn Thai / Learn English)
- ✅ Unified songs catalogue showing both languages
- ✅ Language badges on song cards (🇹🇭/🇬🇧)
- ✅ Play All functionality for songs
- ✅ Recording indicator with red pulsing dot
- ✅ Premium paywall with coupon input
- ✅ Professional login/register screens
- ✅ Responsive design for all screen sizes

#### Content Database
- ✅ 34 Thai lessons covering:
  - Alphabet, numbers, vocabulary
  - Colors, family, days, time
  - Phrases, conversations, dining
  - Travel, shopping, emergency
  - 100+ household items
  - Songs and music

- ✅ 12 English lessons covering:
  - Alphabet, numbers, greetings
  - Common phrases, animals
  - Colors, family, days
  - Household items
  - Songs

#### Known Limitations
- 🔧 Speech-to-text uses mock data (API integration pending)
- 🔧 Google Sign-In requires OAuth credentials
- 🔧 Google Pay integration pending for production payments
- 🔧 Push notifications not yet implemented

---

## [Planned for 1.1.0] - Q1 2025

### Upcoming Features
- [ ] Google Cloud Speech-to-Text API integration
- [ ] Google Sign-In completion
- [ ] Apple Sign-In implementation
- [ ] Google Pay live payment processing
- [ ] Offline lesson downloads
- [ ] Spaced repetition algorithm
- [ ] Achievement badges system
- [ ] Daily streak tracking
- [ ] Community leaderboards

### Technical Debt
- [ ] Migrate from expo-av to expo-audio (deprecated warning)
- [ ] Add comprehensive unit tests
- [ ] Implement E2E testing with Detox
- [ ] Performance optimization for large lesson sets
- [ ] Add crash reporting (Sentry)

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| 1.0.0 | 2024-12-01 | ✅ Production Ready |
| 1.1.0 | Q1 2025 | 🔄 Planned |
| 1.2.0 | Q2 2025 | 📋 Roadmap |

---

**Maintained by:** Jake Adamson  
**Contact:** jakemadamson2k14@gmail.com  
**Copyright:** © 2025 Jake Adamson. All Rights Reserved.
