# Content Generation Concepts

Concepts to test in interviews (section D). **Not built in product yet** — use mock outputs and verbal descriptions.

## Concept cards

Show or describe each card; ask which they'd use and what they'd change.

---

### Card A — Caption draft

**What it is:** AI-written Instagram caption for a specific trend, editable before posting.

**Example:**

> Soft chrome is having a moment — milky base, brushed metal finish, clean almond shape. Perfect for clients who want shine without loud art. Book your chrome refresh this week.

**Includes:** 1 caption (80–150 words), tone matched to salon style (minimal, playful, luxury).

**Test question:** Would you edit and post this with your own photo, or write captions yourself?

---

### Card B — Hashtag set

**What it is:** 15–25 hashtags grouped by reach (broad + niche + local).

**Example:**

`#nailart #chromenails #almondnails #nailinspo #nailsoftiktok #hcmcnails #gelnails #cleangirl`

**Test question:** Do hashtags matter to you? Would a suggested set save time?

---

### Card C — Carousel outline

**What it is:** 3–5 slide storyboard for an Instagram carousel (text per slide, not designed graphics).

**Example slides:**

1. Hook: "The trend everyone's asking for this month"
2. Trend name + 1-sentence explanation
3. Color palette (3 colors)
4. "Book link in bio" CTA

**Test question:** Would you use this structure, or prefer a single image post?

---

### Card D — Image prompt / mood board

**What it is:** Reference image from trend research + optional AI prompt to generate a mood board (not replacing client's nail photo).

**Example prompt:**

> Almond nails, milky white base, soft gold chrome tips, natural lighting, salon setting, minimalist

**Test question:** Reference images only, or also AI-generated mood boards? Concerns about authenticity?

---

## AI vs UGC preference matrix

Ask interviewee to rank preference (1 = most preferred) for each row:

| Content type | A: AI draft, I edit | B: Templates only | C: I write myself | D: AI + my photo |
|--------------|---------------------|-------------------|-------------------|------------------|
| Caption text | | | | |
| Hashtags | | | | |
| Visual (image) | | | | |
| Reel script | | | | |

Record in [content-preference-ranking.md](../interviews/questionnaires/content-preference-ranking.md).

## Authenticity concerns to probe

- Will clients trust AI-written captions?
- Platform rules (Instagram/TikTok) on AI content
- Language quality (Vietnamese vs English)
- Salon brand voice — can AI match it?
- Competitors using obvious AI content — negative signal?

## MVP recommendation framework (post-validation)

| If interviews show… | Build first |
|---------------------|-------------|
| Captions are hardest; images are fine | Caption + hashtag generator from trend |
| Hashtags don't matter | Skip hashtags; focus trends + captions |
| Strong image authenticity requirement | Owner photo upload + AI caption only |
| Carousel demand in FI/INT | Carousel outline after caption MVP |
| VN needs Vietnamese | Localized caption generation priority |

## Related files

- Mock output: [samples/market-validation/mock-social-post.json](../../../samples/market-validation/mock-social-post.json)
- Interview section D: [interview-guide-en.md](../interviews/guides/interview-guide-en.md)
