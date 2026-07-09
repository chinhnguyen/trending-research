# Demo Script — Interview Product Walkthrough

Use during section C of the interview. Duration: ~10 minutes. Requires local web app or pre-saved reports as fallback.

## Before the call

1. Start backend: `willbe-api` (http://127.0.0.1:8000)
2. Start frontend: `cd web && npm run dev` (http://127.0.0.1:5173)
3. Pre-run reports for interviewee's region (save as fallback):
   - Neutral: category `nails`, region = `vietnam` / `finland` / `global`
   - Personalized: match their stated style from warm-up questions
4. Open `samples/market-validation/mock-social-post.json` in a tab or printout
5. Share screen; close unrelated tabs

## Script

### Intro (30 sec)

> "I'd like to show you something we're building — a tool that researches current nail trends and, in the future, helps turn those into social posts. This is an early version. I want your honest reaction — what feels useful and what doesn't."

### Part 1 — Neutral trends (3 min)

1. Navigate to **New research** → mode **Neutral**
2. Set region to interviewee's market (or `global`)
3. Run research (or open pre-saved report if live run is slow)
4. Walk through the report:
   - Summary paragraph
   - 2–3 trend cards: name, description, popularity, colors, techniques
   - Citation links under web research
   - Reference image on a trend card

**Ask:**

- "Do these trends feel current to you?"
- "Would you share any of these with your team or clients?"
- "Does anything feel too generic or wrong for your market?"

### Part 2 — Personalized trends (3 min)

1. New research → mode **Personalized**
2. Enter preferences based on what they said in warm-up (colors, shapes, style keywords)
3. Show how picks differ from neutral report

**Ask:**

- "Do these feel more relevant to your salon style?"
- "Would you trust these for your next week's content plan?"

### Part 3 — Content concept (3 min)

> "Imagine each trend came with a ready-to-edit Instagram caption and hashtags. Here's a mock of what that could look like."

Show `mock-social-post.json`:

- Trend name + description
- Suggested caption (editable tone)
- Hashtag set
- Posting tip (e.g. "Pair with a photo of your latest chrome set")

**Ask:**

- "Would you publish something like this with your own photo?"
- "What would you change before posting?"

### Close demo (30 sec)

> "Thank you — that helps a lot. We'll talk more about pricing and preferences next."

## Fallback if demo fails

- Open a pre-saved report from a prior run (same region)
- Or show screenshots exported from a successful run
- Note in post-interview form: `demo_mode: live | fallback | screenshots`

## Capture tags (for post-interview form)

| Tag | Meaning |
|-----|---------|
| `trends_feel_current` | Positive reaction to trend quality |
| `trends_too_generic` | Negative — not specific enough |
| `citations_helpful` | Liked source links |
| `images_helpful` | Liked reference images |
| `personalized_better` | Personalized > neutral for them |
| `would_use_weekly` | Expressed intent to use regularly |
| `caption_mock_positive` | Liked mock social post concept |
| `caption_mock_negative` | Rejected or heavily skeptical |

## Technical notes

- Web UI: [web/src/pages/NewResearchPage.tsx](../../../web/src/pages/NewResearchPage.tsx)
- Trend cards: [web/src/components/TrendCard.tsx](../../../web/src/components/TrendCard.tsx)
- Typical run time: 30–90 seconds with web search enabled
- Use `--no-web-search` only as last resort (worse quality)
