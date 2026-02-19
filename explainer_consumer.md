# REAA — Your Real Estate + Wealth Building Assistant

## What Is REAA?

REAA stands for Real Estate Agent Assistant. It watches public courthouse records — specifically "Lis Pendens" filings, which are early indicators that a property might be heading toward foreclosure — and pairs that data with blockchain-based financial tools so you can act on opportunities before most people even know they exist.

You don't need a real estate license. You don't need to understand crypto. REAA handles the technical plumbing. You just log in with a wallet, and the dashboard shows you what's happening in your local market plus the state of your financial position — all in one place.

---

## How It Works — Four Real People, Four Real Scenarios

### 1. Marcus — Rideshare Driver, Hartford CT

Marcus drives for Uber. Between rides, he opens REAA on his phone. The dashboard shows 14 new Lis Pendens filings in Hartford this week. He taps one — a 3-bedroom on Franklin Ave where the homeowner is behind on their mortgage. REAA's AI assistant explains what Lis Pendens means in plain English: "This property has a legal notice filed against it. The owner may be motivated to sell below market value within the next 3-6 months."

Marcus doesn't have $200K sitting around. But he screenshots the listing, sends it to a local investor he met at a meetup, and earns a $2,500 referral fee when the deal closes four months later.

**What REAA did:** Surfaced a public record that would have taken Marcus hours of courthouse research. Explained it without jargon. Put him in front of an opportunity that turned idle time into income.

### 2. Dana — Elementary School Teacher, Windsor CT

Dana has been contributing to a retirement account for 12 years. She's heard people make money in real estate but doesn't know where to start. She connects to REAA and sees 5 Connecticut towns being monitored with daily data. She also sees her DeFi position — a small amount she put into a lending protocol last year on the advice of a friend.

REAA's safety rating shows her health factor is strong. The AI chat tells her: "Your collateral is growing steadily. At current rates, your position has gained 7% this quarter." She also sees three new filings in her own town of Windsor — properties she drives past on her commute.

Dana starts tracking these properties. Six months later, she contacts one homeowner directly and negotiates a below-market purchase for her first rental property.

**What REAA did:** Connected the dots between Dana's existing financial position and local real estate data she never knew was publicly available. Made both worlds visible in one dashboard.

### 3. Ray — Small Business Owner, East Hartford CT

Ray owns a landscaping company. He knows his area well. When REAA shows him a cluster of Lis Pendens filings on the same street, he recognizes an opportunity — that block is two streets over from a new grocery store development. He uses REAA's AI to ask: "What's the average sale price for properties on Oak Street in the last year?" The assistant pulls context and gives him a grounded answer.

Ray buys one property at a tax sale, rehabs it using his own crew, and sells it 8 months later for a $45K profit.

**What REAA did:** Gave Ray data he already had the instinct to use, but packaged it so he could act quickly instead of spending weekends at the courthouse.

### 4. Keisha — College Senior, Rocky Hill CT

Keisha is 22 and has no savings for real estate. But she's curious. She connects her wallet (which holds $0) and browses the REAA dashboard. She sees how filings work, reads the AI explanations, and starts understanding how foreclosure cycles create buying opportunities. She sets up town tracking for Rocky Hill and Berlin.

Over the next year, she watches filing patterns and property values while she saves. When she's ready to invest, she already knows the market intimately.

**What REAA did:** Gave Keisha a free education in real estate market dynamics using real data from her own area — not a course, not a book, but a live feed of what's actually happening.

---

## "I Don't Do Crypto / I Don't Know Real Estate" — That's the Point

The most common reasons people don't use tools like REAA:

**"I don't understand blockchain."**
You don't need to. REAA uses blockchain behind the scenes for security (your login is a signed token from your wallet) and for tracking financial positions. You never have to write code, trade tokens, or understand smart contracts. If you can use Venmo, you can use REAA.

**"I'm not a real estate investor."**
Neither were Marcus or Keisha. REAA gives you access to the same public data that professional investors pay thousands to compile. What you do with it is up to you — refer deals, buy properties, or just learn.

**"This feels risky."**
REAA doesn't hold your money. It doesn't make trades for you. It shows you data and explains it. The DeFi monitoring is read-only for your connected wallet. You control every decision.

**"I don't have enough money."**
Start with zero. Browse filings. Learn your market. When you're ready to act, you'll know more than people who've been "meaning to get into real estate" for a decade.

---

## What the Numbers Look Like — Historical Context

**Bitcoin (for context on DeFi growth):**
- Jan 2020: ~$7,200
- Jan 2022: ~$38,000
- Jan 2024: ~$42,000
- Feb 2025: ~$96,000
- People who held even small positions saw significant growth. REAA's DeFi panel monitors this kind of position in real time.

**Hartford County Real Estate (where REAA operates):**
- Median home price (2019): ~$175,000
- Median home price (2024): ~$270,000
- That's 54% appreciation in 5 years.
- Lis Pendens filings in Hartford County average 30-50 per month — each one a potential below-market acquisition.

**Combined picture:** Someone who bought a distressed Hartford property in 2020 for $140K (below market due to Lis Pendens) and held a modest crypto position would have seen their real estate appreciate to ~$220K while their DeFi position may have grown 3-5x. REAA helps you see both sides of this picture simultaneously.

---

## Technical Overview (For Developers, Agents & Brokers)

- **Data Pipeline:** Automated daily scraping of Lis Pendens filings from 5 Connecticut towns (Hartford, East Hartford, Windsor, Berlin, Rocky Hill) via SearchIQS, stored in a PostgreSQL database across 8 normalized tables.
- **AI Assistant (REAA):** Perplexity `sonar` model with dynamic system prompts built from the user's own Postgres data — their tracked towns, recent filings, DeFi position, and income events. Supports multi-turn conversation with 5-message history context.
- **Auth:** Signed token authentication via `itsdangerous` TimestampSigner. Wallet address submitted at connect → server returns signed token → all subsequent API calls include `X-Auth-Token` header. Tokens expire after 7 days. Full data isolation between users.
- **DeFi Monitoring:** Read-only Aave V3 `getUserAccountData` calls for connected wallets on Arbitrum. Health factor, collateral, debt, and net worth displayed with color-coded safety ratings.
- **Rate Limiting:** Per-user chat rate limiting (20 calls/60 seconds) to prevent API abuse.
- **For Brokerages:** REAA can serve as a lead generation layer — filing data fed directly into your CRM pipeline. The AI assistant provides instant property analysis that would otherwise require a title search.
- **For Agents:** Monitor your farming areas automatically. Get daily alerts on new filings in your zip codes. Use REAA's data to approach distressed homeowners before competing agents.

---

**To try it, go to [reaa.io](https://reaa.io) and follow [@connectoreaa](https://twitter.com/connectoreaa) on socials.**
