# Notes: Amazon KDP Print-on-Demand for a Canadian Self-Publisher (Children's Picture Book)

## Task
Research KDP print-on-demand publishing from a Canada-based self-publisher's perspective, for a
12-spread (~285 word) full-color children's picture book (ages 2-5), AI-illustrated. Cover:
1. Account/tax prerequisites (Canada-specific)
2. Paperback specs
3. Hardcover via KDP
4. Pricing/royalty math
5. EPUB/Kindle ebook considerations

## Log

- Started 2026-07-09. Created folder `kdp-canada-childrens-picture-book/`.
- Plan: use WebSearch/WebFetch against kdp.amazon.com help pages and recent (2025-2026) community
  sources (since KDP changes specs/policy periodically). Will note source + date for key figures.

---

## Follow-up task (2026-07-09, same day): Front/back matter, ISBN Canada, legal deposit, AI disclosure, EPUB fixed-layout

New scope (continuation of the same overall investigation — Canada-based self-publisher, 12-spread
/ ~285-word / full-color AI-illustrated picture book, ages 2-5, going to print via KDP/POD):
1. Required/conventional front matter for a self-pub picture book
2. Canadian ISBN sourcing (LAC free vs Bowker/paid) + per-format ISBN rules
3. Legal Deposit at LAC for self-published/POD books
4. KDP AI-generated content disclosure requirement (2025-2026)
5. Back matter conventions + barcode/CIP
6. EPUB fixed-layout considerations for a short picture book

### Findings log

**Front matter (general convention, not Canada-specific):**
- Only two front-matter pages are truly required in any self-published book: title page (recto)
  and copyright page (verso, i.e., back of title page). Everything else — half-title, dedication,
  epigraph — is optional. Source: bookdesignmadesimple.com, Lulu blog, MSU LibGuide.
- Half-title pages are a novel/adult-book convention, uncommon in picture books; skipping it is
  normal and saves a spread in a page-count-constrained (e.g., 24/32-page) picture book.
- Common actual picture-book layout: page 1 = title page (sometimes combined with a small
  illustration), page 2 = copyright/CIP-style info + dedication, page 3 = story start. Some
  publishers push the copyright block to the very last page instead of page 2, to give the story
  a full-bleed opening spread — increasingly common indie-picture-book move to save an early
  spread for story/art rather than legal text. Worth mentioning as an option for a 12-spread book.
- Copyright notice: "Copyright © [year] by [Author]. All rights reserved." © symbol/format is
  *convention*, not legally required in Canada (Canada is a Berne Convention country — copyright
  exists automatically on creation; marking is just best practice / puts readers on notice).
  Source: firstchoicebooks.ca (Canadian self-pub shop), pagemaster.ca (Canadian).
- Copyright page conventionally also includes: publisher name/imprint, ISBN(s), printer info
  (POD printers like KDP/IngramSpark usually don't require "printed in [country]" statements the
  way old offset print runs did, but many indie books still add "Printed in [country of POD
  facility varies]" — for KDP this is misleading since POD location varies by order, so it's often
  omitted or replaced with a generic imprint line), edition statement ("First edition" — optional,
  useful mainly if you expect future revised editions), illustrator credit (important to name
  explicitly on copyright page + cover if the story text and art are by different named
  parties — for AI illustration, credit typically goes to the human creative director/author with
  a note on tools used only if desired, see AI disclosure section below), and CIP-style
  categorization if desired (see back matter section).

**ISBN — Canada specifics:**
- Library and Archives Canada (LAC) issues ISBNs to Canadian publishers/self-publishers **for
  free**, via the ISBN Canada program (canada.ca/en/library-archives/services/publishers/isbn.html
  → "Apply for an ISBN account"). This is the single biggest difference vs. the US, where ISBNs
  must be purchased from Bowker (~$125 single / cheaper in blocks of 10).
- Eligibility: must have a Canadian mailing address; self-publishers qualify as "publishers" for
  this purpose (no need to be an incorporated press).
- Process: create an online ISBN Canada account (legal name, contact info, Canadian address),
  accept statement of use, wait for account approval (reports vary: recent community anecdotes
  say up to ~20 days; some older guidance says up to 2 months — build in buffer time before your
  planned KDP publish date). Once approved, log in to "Manage Logbook" → "Assign New ISBN" to pull
  ISBNs instantly per format.
- **Each distinct format/edition needs its own ISBN**: paperback, hardcover, and ebook are each
  a separate ISBN if you want them separately tracked/listed as distinct editions. (Note: Kindle
  ebooks specifically do NOT require an ISBN at all — Amazon auto-assigns an ASIN for Kindle
  ebooks. ISBN is only mandatory for paperback/hardcover print editions on KDP, and optional-but-
  recommended for ebook editions distributed on other platforms like Kobo/Apple Books/IngramSpark,
  where an ISBN is how the ebook is identified in wide distribution.)
- KDP and IngramSpark both accept LAC-issued Canadian ISBNs without any problem — you just enter
  the 13-digit ISBN when setting up the print title. No requirement to use a US-based agency.
- Important nuance: KDP also offers its OWN free ISBN option for print books, but that ISBN gets
  registered with Bowker under KDP/Amazon's imprint info — meaning Amazon (via KDP) shows as
  publisher of record, and that ISBN typically can't be reused on other platforms (e.g.
  IngramSpark) later. For a Canadian self-publisher, using your own free LAC ISBN instead is
  better practice: you're listed as publisher of record, and the same ISBN could theoretically be
  reused across print platforms if you ever go wide (though in practice each *retailer's specific
  print edition* often still wants its own ISBN if trim/paper specs differ — safest to still get a
  fresh ISBN per platform+format combo, but at least the option remains yours to control since it's
  free from LAC anyway).
- Get the ISBN *before* finalizing cover design so the barcode area can be planned (though KDP/
  IngramSpark can auto-place the barcode — see back matter section).

**Legal Deposit — Canada:**
- Legal Deposit is a legal requirement (Legal Deposit of Publications Regulations, SOR/2006-337)
  administered by LAC: publishers who make a publication available in Canada must deposit copies
  with LAC, and "self-published authors" are explicitly included in the definition of publisher
  (a "publisher" = person who makes the publication available and controls/authorizes the content
  — this covers a self-publishing author directly).
- Copy count is tied to *print run size*, not sales: 4–99 copies produced → 1 copy required;
  100+ copies produced → 2 copies required. The physical-publications page doesn't explicitly
  address print runs under 4 copies (true POD "print run" is technically 1-at-a-time per order),
  which is the ambiguous case most solo picture-book authors on KDP actually fall into.
- In practice, for KDP/POD books, "print run" is not a fixed batch the way it is for offset
  printing — you're not printing 100 copies upfront. Common guidance from Canadian self-pub
  communities (e.g., Lorraine Reguly's "Legal Deposit: It's the Law" post) is: once your POD book
  is made available for public sale (i.e., live and orderable on Amazon/KDP), LAC still expects a
  deposit — treat it as if you produced enough copies to trigger deposit, i.e., submit at least 1
  copy of the paperback and register the ebook. Don't rely on the "under 4 copies" ambiguity as an
  exemption — LAC's own framing is about the book being "intended for sale or public distribution,"
  which a live KDP listing satisfies regardless of literal units printed at any one moment.
- Physical submission: fill out the Monograph publications form (PDF, on canada.ca), mail 1 (or 2)
  physical copies to LAC, 550 de la Cité Boulevard, Gatineau, QC J8T 0A7. You get a legal deposit
  receipt by email. Cost of producing/mailing the deposit copy is a deductible business expense
  (labour + materials only, not "market value").
- Digital/ebook version: submitted separately through LAC's online deposit portal after creating
  an account (contact: epe@bac-lac.gc.ca for digital; legal.deposit@bac-lac.gc.ca for physical
  questions).
- Note: items with "minimal text" like colouring books are called out as NOT usually accepted —
  a 285-word narrative picture book is well above that bar and squarely subject to deposit.

**KDP AI-generated content disclosure (2025-2026):**
- KDP's publishing dashboard (Content Details step, 2nd step of the title setup flow) asks: "Is
  this content AI-generated?" with a checkbox: "Yes, some of this content is AI-generated." If
  checked, a follow-up asks which content type — text, images, or translation.
- Official checkbox language (per secondary/summary sources referencing KDP's Content Guidelines,
  kdp.amazon.com/en_US/help/topic/G200672390): "This title contains AI-generated content. This
  includes text (e.g., chapters, sections), images (e.g., illustrations, diagrams, cover art), or
  translations that were produced using AI tools."
- KDP distinguishes **AI-generated** (content actually created by an AI tool — this is what must
  be disclosed) from **AI-assisted** (you created the content yourself; AI merely helped edit,
  refine, error-check, translate-assist, or brainstorm — this does NOT require disclosure).
- For THIS project specifically: full-color AI-illustrated picture book = the interior
  illustrations (and likely the cover) are AI-generated images → disclosure is REQUIRED, tick
  "yes," select "images" as the AI-generated content type. If the text/story was human-written
  (even if AI helped edit/brainstorm), the text itself does not need to be flagged as AI-generated
  — only the images.
- The AI-generated disclosure is NOT shown to shoppers on the public product/detail page — it's
  for Amazon's internal compliance/records only. It does not affect royalty rate, search ranking,
  or category eligibility by itself.
- Non-disclosure risk: failure to disclose AI content, if later detected (Amazon uses automated
  pattern/metadata detection plus human review, and enforcement reportedly increased through
  2025-2026), can lead to content removal or account-level enforcement action. Given this book is
  explicitly AI-illustrated, disclose proactively — low cost, meaningful downside if skipped.
- No general Canadian *legal* AI-disclosure requirement was found specific to book publishing (as
  of this research) — this is purely a KDP platform policy, not Canadian statute. (Copyright Board/
  CIPO AI-authorship questions are a separate, unsettled area — not required reading for shelving
  metadata on a picture book, out of scope here.)

**Back matter conventions:**
- Author bio: common but optional for picture books; typically 2-4 sentences on inside back cover
  or a back-matter page, sometimes paired with an illustrator bio/credit (relevant here since the
  "illustrator" is an AI tool directed by the author/creative lead — bios usually still credit the
  human author/creator, not the AI system, though some indie AI-illustrated books add a small
  note like "illustrations created with the assistance of AI tools, directed and curated by
  [author]").
- "About this book" / discussion-prompt / activity page: increasingly common in modern indie
  picture books (parent-child discussion questions, a simple activity, or a note on the book's
  theme) — optional but a nice value-add, not a convention required for validity.
- Barcode/ISBN on back cover: KDP and IngramSpark both **auto-generate and place the barcode**
  for you if you leave the barcode area blank on your cover file — this is the recommended
  default workflow (leave ~0.25 in / 0.635 cm clearance in the bottom-right area, white/light
  background). You CAN supply your own pre-rendered barcode, but platforms may still overwrite it,
  so it's simplest to just leave the zone clear and let KDP/IngramSpark place it.
- Cataloging-in-Publication (CIP) data: true Library of Congress CIP is NOT available to
  self-published/POD authors — the LOC program is restricted to books expected to be widely
  acquired by libraries in advance of publication (via traditional publishers). Canadian
  self-publishers were never eligible for LOC CIP anyway (that's a US program; Canada's own
  historical "Canadian CIP" program run by LAC was discontinued years ago). Self-published indie
  authors who want CIP-style metadata on the copyright page (useful for school/library
  acquisitions) typically buy "Publisher's CIP" from a third-party service, or simply skip it —
  most solo picture-book self-publishers skip CIP entirely since libraries generate their own
  catalog records anyway once they acquire a book via ISBN. Not required, low-value for a small
  first print run.

**EPUB / fixed-layout for picture books:**
- Standard *reflowable* EPUB (the default ebook format, text-flows-and-reformats-per-device) is
  unsuitable for picture books because reflowable EPUB treats images as inline content that can
  shrink, reflow, or separate from their paired text depending on device/font-size settings —
  breaks the tight text-in-relation-to-illustration layout picture books depend on.
- **Fixed-layout EPUB (FXL)** locks each page's exact dimensions/layout (like a fixed "photograph"
  of each spread) so text and image stay precisely positioned regardless of device — the correct
  format for image-heavy children's books, comics, and cookbooks.
- Tooling: Amazon's dedicated "Kindle Kids' Book Creator" tool is effectively **deprecated/
  retired** — Amazon stopped accepting the .mobi output it produced (mobi support ended
  ~2022). Amazon now directs authors to **Kindle Create**, which supports a "Kids' book" /
  fixed-layout / "print replica" style workflow: import a print-ready PDF or a folder of
  per-page JPGs, and it builds a fixed-layout KPF file for KDP. Downside: KPF is an
  Amazon-proprietary format that locks you to KDP/Kindle only — not portable to Kobo/Apple
  Books/IngramSpark ebook distribution.
- For true cross-platform fixed-layout EPUB (needed if going wide beyond just Kindle — e.g.
  IngramSpark ebook, Apple Books, Kobo, Kotobee, library aggregators), options are heavier-duty:
  Adobe InDesign's built-in "Export for EPUB (Fixed Layout)"; dedicated tools like Kotobee
  Author; or paid tools like Vellum (Vellum is Mac-only and, notably, does NOT support true
  fixed-layout picture-book EPUBs — Vellum is built for reflowable text books; it's the wrong
  tool for an image-heavy 12-spread picture book).
- Typical image specs for fixed-layout EPUB pages: target ~2048px on the longest side (sharp on
  iPad Retina without bloating file size); some guidance suggests up to ~2560x1600 as a good
  average target across device resolutions (device range spans roughly 1024x768 up to
  2732x2048). RGB color (not CMYK — screens are RGB, differs from your print-ready CMYK files).
  JPEG for painterly/gradient-heavy art, PNG for flat-color or line art or where transparency is
  needed.
- Cost/benefit for THIS project (12 spreads, ~285 words, ages 2-5): true multi-platform
  fixed-layout EPUB is a meaningful extra production step (separate RGB export pass, per-page
  positioning, possibly a different tool from your print layout tool). Given the book is short
  and the primary channel is KDP print (POD), a pragmatic path is: (a) ship print first via KDP/
  IngramSpark, and (b) if an ebook edition is wanted, use Kindle Create's Kids'-book/fixed-layout
  workflow (import your print PDF/page images) to get a Kindle-only fixed-layout edition cheaply,
  deferring true cross-platform FXL EPUB (InDesign/Kotobee) unless/until you plan to distribute
  ebooks beyond Amazon. This matches common advice from picture-book-specific self-pub sources
  (e.g., Darcy Pattison, IndieKidsBooks) that for a single short title, the ebook is often not
  worth the disproportionate formatting effort unless there's a specific market reason for it.

### Sources consulted (key ones)
- canada.ca/en/library-archives/services/publishers/isbn.html (LAC ISBN program)
- canada.ca/en/library-archives/services/publishers/legal-deposit/about.html (LAC legal deposit)
- canada.ca/en/library-archives/services/publishers/legal-deposit/physical-publications.html (copy counts)
- kdp.amazon.com/en_US/help/topic/G200672390 (KDP Content Guidelines, incl. AI disclosure)
- kdp.amazon.com/en_US/help/topic/GTJ8LBXL6Z4WV5QX and G201834170 (KDP ISBN/imprint help)
- kdp.amazon.com/en_US/help/topic/G5HDYGP4BXLX4RUW (KDP barcodes)
- loc.gov/programs/cataloging-in-publication (CIP eligibility — confirms self-pub/POD excluded)
- ingramspark.com/free-isbns, ingramspark.com/blog/isbn-facts-for-self-publishers
- bookdesignmadesimple.com (front/back matter conventions, CIP)
- darcypattison.com (picture-book-specific ebook/EPUB formatting guidance)
- firstchoicebooks.ca, pagemaster.ca, foglioprint.com, authorimprints.com (Canadian self-pub shops)
- Community secondary sources cross-checked for the 2025-2026 KDP AI-disclosure checkbox wording
  (exact wording not independently confirmed on a live KDP dashboard screenshot in this pass —
  flagged as best-available secondary-source paraphrase of KDP's own language, consistent across
  multiple independent write-ups).

### Wrap-up
README.md updated with a new set of sections (1-6) covering front matter, Canadian ISBN sourcing,
Legal Deposit, KDP AI disclosure, back matter, and EPUB fixed-layout. Trimmed from an initial
~1500-word draft to ~1175 words to stay close to the requested 700-1000 word target while keeping
all six numbered sections and load-bearing facts/links.

---

## Original task (business/production mechanics): Account/tax, paperback specs, hardcover, royalty math, ebook

This picks up the original 5-part scope noted at the top of this file (account/tax prerequisites,
paperback specs, hardcover, pricing/royalty math, EPUB/ebook), which is complementary to the
front-matter/ISBN/legal-deposit/AI-disclosure/back-matter work above. Findings below; final
combined report is in README.md, reorganized so both investigations read as one continuous guide.

### Tax/account (Canada) — confirmed via official KDP help pages
- Tax interview: choose Canada as country of residence, provide SIN (individual) or Business
  Number (incorporated), complete W-8BEN (individual) or W-8BEN-E (business) to claim the
  Canada-US tax treaty rate (Article XII, royalties) -> 0% US withholding instead of the 30%
  default for authors who skip the interview. W-8BEN is valid ~3 years then must be renewed.
- Payment: official "When will I get paid?" page (kdp.amazon.com/en_US/help/topic/GK2MKZUL6U3SFBPZ)
  confirms direct deposit (EFT) goes straight to a Canadian bank account (1-5 business days), no
  minimum balance required. Wire transfer needs $100 CAD minimum; checks aren't offered in
  Canada. No Payoneer or US bank account needed today (that was a historical workaround, no
  longer necessary). Paid monthly, ~60 days after the sales month closes.
- Business Number / GST-HST: not required to start — operate as an unregistered sole proprietor
  using your SIN. CRA requires GST/HST registration (which auto-issues a Business Number) only
  once total revenue from taxable supplies exceeds $30,000 CAD across 4 consecutive calendar
  quarters — very unlikely for a single first picture book. Voluntary registration below that
  threshold locks you in for at least 1 year.
- ISBN "catch" (ties into the ISBN section above): KDP's free ISBN lists Amazon/"Independently
  Published" as publisher of record. Official Expanded Distribution help page
  (kdp.amazon.com/en_US/help/topic/GQTT4W3T5AYK7L45) confirms a free KDP ISBN CAN technically be
  used for Expanded Distribution (Amazon + IngramSpark partner channel), provided that exact ISBN
  hasn't already been submitted to another distribution service. The practical catch (consistent
  across many indie-publishing sources): that ISBN can't later be reused on a different POD
  platform (IngramSpark direct, Draft2Digital, etc.), and many bookstores/libraries are reluctant
  to hand-order titles listing Amazon as publisher. This reinforces the earlier finding that a
  free LAC (Canadian) ISBN is the better default for a Canadian self-publisher.

### Paperback specs — confirmed via official KDP pages
- Popular trims for picture books: 8.5x8.5in (square, most popular), 8x10in (portrait), 10x8in
  (landscape). Custom range allowed: width 4-8.5in, height 6-11.69in.
- Paper/ink tiers (official Color Ink Options page,
  kdp.amazon.com/en_US/help/topic/GX56BFPW4BKNPGFW): Standard color = 50-61lb/74-90gsm inkjet,
  MINIMUM 72 PAGES (too high for a 24-32pg book). Premium color = 60-71lb/88-105gsm toner,
  MINIMUM 24 PAGES — the correct tier for a 12-spread (24pg) book.
- Paperback overall minimum page count: 24, must be a multiple of 4.
- Bleed: 0.125in (3.2mm) on all sides (official Paperback Submission Guidelines,
  kdp.amazon.com/en_US/help/topic/G201857950).
- Interior PDF: images >=300 DPI (recommend capping ~600 DPI to manage file size), fonts
  embedded, min 7pt text, margins scale with page count (0.375in minimum for 24-150pg books).
- Cover spine width formula (same official page): page count x 0.002252in (white paper), x
  0.0025in (cream), x 0.002347in (color paper). For a 24-page premium-color book that's only
  ~0.056in of spine — effectively no room for readable spine text/title.
- Print quality reputation: mixed for full color. KDP shows an on-screen warning before ordering
  proofs that photo-dense/color-heavy art can print "grainy." Community complaints (KDP
  Community, Medium, kboards) cite muddy/dark color reproduction (often actually a CMYK
  conversion issue on the author's file) and occasional wavy pages. Premium color plus a properly
  converted CMYK PDF avoids most of this; some authors prefer IngramSpark for color fidelity, but
  that's outside strict KDP scope.

### Hardcover via KDP — confirmed via official KDP pages
- Launched ~2021, no longer flagged as "beta" in current help docs.
- Trim sizes: 5.5x8.5, 6x9, 6.14x9.21, 7x10, 8.25x11in — **no square 8.5x8.5 option**, unlike
  paperback.
- Paper: black ink on cream/white; premium color on white only (no "standard color" hardcover
  tier at all).
- **Critical limitation**: hardcover minimum page count is 75 pages (official Hardcover Printing
  Cost page, kdp.amazon.com/en_US/help/topic/GHT976ZKSKUXBB6H), for both black ink and premium
  color. A 24-32 page picture book falls well short — would need padding (bonus back matter,
  activity pages, etc.) to reach 75 pages just to qualify for hardcover at all.
- Cost formula (US, official page): $5.65 fixed + $0.012/page (black, 110-550pg range) or $5.65
  fixed + $0.065/page (premium color, 75-550pg range). At the 75-page floor with premium color:
  ~$10.53 print cost before any royalty is even calculated.

### Royalty/pricing math — confirmed via official KDP pages + June 2025 policy change
- Formula: royalty = (list price x rate) - print cost.
- **Recent change (June 10, 2025)**: royalty rate is 60% only for list prices >= $9.99 USD /
  $13.99 CAD (and equivalents in other currencies); below those thresholds the rate drops to 50%.
  Applies to both paperback and hardcover print royalties (does not affect ebook royalty tiers).
  Source: official kdpcommunity.com announcement thread, corroborated by multiple 2025 write-ups.
- Paperback cost formulas (official Paperback Printing Cost page,
  kdp.amazon.com/en_US/help/topic/G201834340):
  - US (Amazon.com) premium color: $1.00 fixed + $0.065/page (quoted flat for 42-828pg, though
    the Color Ink Options page indicates per-page cost can range $0.065-0.080 depending on
    regular vs. large trim; 8.5x8.5 and 8x10 both count as "large trim" since they exceed 6.12in
    width or 9in height — a large-trim square/portrait picture book is likely nearer the upper
    end of that range in practice).
  - Canada (Amazon.ca) premium color: $1.26 CAD fixed + $0.085 CAD/page (same large-trim caveat
    likely applies).
- Worked examples (all pre-tax, USD unless noted; approximate since exact large-trim per-page
  cost requires KDP's live calculator for a specific title):
  - 24-page premium color paperback, large trim, print cost ~$2.56-$2.92 (say ~$2.75 midpoint):
    - $12.99 -> royalty ~$5.05 (60% tier, above $9.99 threshold)
    - $16.99 -> royalty ~$7.45
    - $19.99 -> royalty ~$9.25
  - 32-page version (common trade convention padding with front/end matter), print cost
    ~$3.08-$3.56 (say ~$3.30):
    - $12.99 -> royalty ~$4.49
    - $16.99 -> royalty ~$6.89
    - $19.99 -> royalty ~$8.69
  - Amazon.ca (CAD) 24-page premium color, print cost ~$3.30-$3.78 CAD (say ~$3.50): note the 60%
    threshold in Canada is $13.99 CAD, not $9.99 CAD equivalent — a $12.99 CAD list price falls
    into the 50% tier.
    - $12.99 CAD (50% tier) -> royalty ~$3.00 CAD
    - $16.99 CAD (60% tier) -> royalty ~$6.69 CAD
    - $19.99 CAD (60% tier) -> royalty ~$8.50 CAD
  - Hardcover, padded to the 75-page minimum, premium color, large trim, print cost
    ~$10.53-$11.65 (say ~$11.00): minimum viable list price to avoid a negative royalty is
    roughly $11.00/0.6 = ~$18.33. At $19.99 -> royalty only ~$1.00; at $24.99 -> royalty ~$3.99.
    $12.99/$16.99 are not viable list prices for this hardcover cost structure.
  - **Bottom line**: paperback at $12.99-$19.99 nets a healthy ~$4.50-$9.25 royalty/copy for this
    short book; hardcover, once padded to the 75-page floor, needs $19.99+ pricing just to clear
    a thin margin — paperback is the more natural/profitable format for a genuinely 24-32 page
    picture book.

### Ebook economics addendum (complements the EPUB/fixed-layout tooling notes above)
- Ebook royalty tiers unaffected by the June 2025 print-royalty change: still 35% vs. 70%. The
  70% tier requires a $2.99-$9.99 list price, an eligible territory (Canada included), and either
  KDP Select enrollment or price-matching against other retailers.
- Delivery fee at the 70% tier = $0.15/MB of Amazon's *compressed* file size. Image-heavy
  fixed-layout picture books commonly land 8-15MB post-compression, which can claw back
  $1.20-$2.25 per sale in delivery fees alone — a meaningful bite out of the royalty for a
  low-priced picture book.
- Net read: ebook is worth doing as a low-effort secondary channel once the print files exist
  (and it unlocks Kindle Unlimited page-read income if enrolled in KDP Select), but picture-book
  ebook sales volumes are typically much smaller than print — most picture-book buyers want a
  physical read-aloud/gift object, not a screen experience for a 2-5 year old.

### Sources consulted (this pass, official KDP pages)
- kdp.amazon.com/en_US/help/topic/GK2MKZUL6U3SFBPZ (When will I get paid)
- kdp.amazon.com/en_US/help/topic/G201834180 (Print Options)
- kdp.amazon.com/en_US/help/topic/GX56BFPW4BKNPGFW (Color Ink Options)
- kdp.amazon.com/en_US/help/topic/G201857950 (Paperback Submission Guidelines)
- kdp.amazon.com/en_US/help/topic/GHT976ZKSKUXBB6H (Hardcover Printing Cost)
- kdp.amazon.com/en_US/help/topic/G201834340 (Paperback Printing Cost)
- kdp.amazon.com/en_US/help/topic/GQTT4W3T5AYK7L45 (Expanded Distribution)
- kdpcommunity.com official thread on the June 10, 2025 royalty rate change
- Secondary sources used for cross-checking/context only (kdpeasy.com, kindlepreneur.com,
  theauthorcentral.com, foglioprint.com, savvynewcanadians.com, wise.com) — all figures used in
  the report were verified against an official KDP help page where possible.

### Wrap-up (this pass)
Merged this pass's findings into README.md alongside the existing front-matter/ISBN/legal-deposit/
AI-disclosure/back-matter/EPUB sections, reorganizing into one continuous lifecycle guide: account
& tax setup -> ISBN -> paperback specs -> hardcover -> pricing/royalty math -> front matter ->
legal deposit -> AI disclosure -> back matter -> ebook/EPUB (tooling + economics combined).

---

## Follow-up task (2026-07-09, same day): POD options BEYOND KDP (IngramSpark, Blurb, hardcover comparison, Canada practicalities)

Scope: compare IngramSpark, Blurb, and dedicated kids-book POD shops (48hrbooks, Mixam) against
KDP, focused on print quality reputation, hardcover jacket-vs-case-laminate availability by trim
size, the "print both KDP + IngramSpark" strategy, and Canada-specific shipping/payment mechanics.
Findings appended to README.md as new sections 7-11 (the file already had sections 1-6 from a
concurrent/earlier pass covering front matter, ISBN, legal deposit, AI disclosure, back matter, and
EPUB — this pass extends rather than replaces that structure).

### Key findings / numbers (with sources)

- **IngramSpark official price sheet** (fetched directly as PDF from
  `myaccount.ingramspark.com/documents/IngramSparkPriceSheet.pdf`, "EFFECTIVE: February 1st, 2026"
  — the single most authoritative/current source found this pass, superior to several outdated
  SEO blogs that surfaced in search results):
  - Title set-up fees: **$0/Free** for print-only, ebook-only, combined, AND revisions. This
    contradicts multiple 2024-2025 blogs still citing a $25 revision fee — trust the official PDF.
  - Market Access Fee (their distribution-network fee): **1.875% of local list price per sale**
    (some blogs say "1%" — outdated).
  - Other fees: File Copies Administration $25 (rare admin request), Publisher Compensation Check
    Payment $25 (US payments only, irrelevant if paid by direct deposit/PayPal), Order Handling Fee
    for publisher-direct/author-copy orders (variable, calculated at order time).
  - Trim-size cost tiers split into **"Small" (<6.15in width) vs "Large" (>=6.15in width)**.
    **True jacketed hardcover is offered ONLY at "Small" trims** across every paper/ink combo in
    the sheet. Common picture-book trims (8.5x8.5, 8x10) are "Large" -> **case laminate only, no
    jacket**, on IngramSpark. Corroborated independently by web search snippets before the PDF
    fetch ("In 8.5 x 8.5, IngramSpark offers only the case laminate hard cover, not the dust
    cover option").
  - Worked cost example, 32-page full-color book, "Large" trim (rates from the PDF):
    - Paperback, Premium Color 70lb: $1.41 + $0.0946x32 ~= **$4.44/unit**
    - Paperback, Ultra-Premium Color 70lb: $2.66 + $0.1061x32 ~= **$6.06/unit**
    - Hardcover (case laminate), Premium Color 70lb: $6.69 + $0.1003x32 ~= **$9.90/unit**
    - Hardcover (case laminate), Ultra-Premium Color 70lb: $7.70 + $0.1061x32 ~= **$11.10/unit**
    - (At "Small" trim, jacketed hardcover Premium Color would be $8.43+$0.0752x32~=$10.84;
      Ultra-Premium jacketed ~=$12.27 — not applicable to standard picture-book trims.)
  - Qty discount tiers (publisher-direct orders): 100-299=2%, 300-399=5%, 400-499=7.5%,
    500-999=10%, 1,000-1,499=15%, up to 10,000+=35%.
  - Print service time (production only, excludes shipping): paperback ~5 business days economy,
    hardcover ~10 business days economy (rush = +30% surcharge, 1-2 days).

- **Canada payment on IngramSpark**: CAD direct deposit (even for payouts <$50 CAD) or PayPal;
  ~90-day payment lag (platform standard, not Canada-specific). The CAD compensation calculator
  doesn't show a live number because it's pegged to USD/exchange rate — cosmetic quirk, not a
  blocker. [indiepublishinggroup.com]

- **KDP print-cost formula cross-check**: consistent with the more detailed official figures
  already in the "Royalty/pricing math" section above ($1.00 fixed + $0.065/page US premium
  color) — a 32-page color paperback lands in the same **~$3-4.50/unit** ballpark as IngramSpark's
  paperback color pricing, i.e. paperback unit costs are roughly comparable between the two
  platforms; the real cost/margin gap shows up on hardcover and on IngramSpark's lower net
  royalty % (wholesale-discount model vs KDP's flat 60%).

- **KDP hardcover trim sizes** (cross-check, consistent with existing notes above): only 5 fixed
  sizes (5.5x8.5, 6x9, 6.14x9.21, 7x10, 8.25x11) — **no 8.5x8.5 square option**, and KDP hardcover
  is **case laminate only, no jacket, ever**. Multiple sources note authors use KDP for paperback +
  IngramSpark for hardcover specifically to get a square trim (accepting case laminate either way).

- **Print quality reputation** (self-pub blogs/community, 2024-2025; direct Reddit r/selfpublish
  search came back empty via WebSearch — the tool doesn't index Reddit threads well here, so
  findings below are from blogs/community write-ups instead):
  - homespunstoriespress.com (Jul 2025 hands-on comparison): KDP colors read "natural, true-to-
    life" (RGB workflow); IngramSpark Ultra-Premium read "oversaturated/reddish" (CMYK workflow) on
    the same illustrated file. IngramSpark hardcover (<76pg) had glue-line/binding issues in their
    test. Verdict: KDP better/cheaper for small creators; IngramSpark's value is distribution
    reach, not print quality, for this reviewer.
  - kadavy.net: generally satisfied with IngramSpark hardcover (Digital Cloth + jacket, later
    jacketed case laminate); main complaint was Amazon showing false "1-2 month" shipping estimates
    on Ingram-distributed-to-Amazon listings, hurting sales velocity until volume picked up.
  - 48hrbooks: praised for color image reproduction and service; one reviewer's hardcover was
    glue-bound, not stitch-bound, and wished that had been flagged upfront.
  - Mixam: good value, vivid color reported by multiple reviewers; complaints centered on packaging
    (loosely shrink-wrapped books, beat-up boxes) rather than print quality itself; ~2-week
    turnaround typical.
  - Consistent caveat across all sources: print-quality opinions are anecdotal/run-to-run variable
    — always order a physical proof before a real print run.

- **Blurb**: only 3 rectangular trims (5x8, 6x9, 8x10) — **no square trim** (the classic 8x8/
  8.5x8.5 picture-book format isn't offered). Two hardcover types: ImageWrap (no jacket, image
  printed on case) and Linen with printed dust jacket — both only on those 3 trims. Distribution is
  weaker than IngramSpark by default (own Blurb bookstore + "Sell on Amazon" program); opt-in
  Ingram-distribution add-on exists but at lower royalty than direct IngramSpark. Reviews mixed:
  sturdy cover/thick pages praised by some, cracked hardcover cases/ink transfer/pinkish cast
  reported by others.

- **KDP + IngramSpark "print both" strategy**: widely recommended (selfpublishingadvice.org cites
  this as endorsed by IngramSpark's own leadership) — publish on both, KEEP KDP Expanded
  Distribution UNCHECKED. Reason: if checked, the KDP edition also lists into Ingram's wholesale
  network as non-returnable/low-discount stock, undercutting the better terms your dedicated
  IngramSpark edition offers the same bookstores/libraries — an ISBN/edition conflict. Practical
  flow: publish KDP paperback first (easiest to proof), then add the IngramSpark edition (often a
  different ISBN) for hardcover + wide distribution. KDP keeps the better Amazon royalty (flat 60%)
  vs Ingram's default 55% wholesale discount (~45% net).

- **Canada shipping/printing facilities**: no confirmed dedicated IngramSpark or KDP print plant in
  Canada. Ingram's owned POD plants: US (Tennessee x2, Pennsylvania), UK (Milton Keynes), Australia
  (Melbourne) — Canadian orders are cross-border. IngramSpark's shipping page states 3-7 business
  day delivery to Canadian provinces once printed, duties/taxes/brokerage bundled into the quoted
  shipping rate. KDP community threads report author-copy shipping to Canada as comparatively
  expensive/sometimes slow (multi-week), no up-front cost calculator. A claim that Amazon has a
  Canadian KDP print facility could NOT be verified against an authoritative source — flagged as
  unconfirmed in the README rather than stated as fact.

### Sources used (this pass)
- https://myaccount.ingramspark.com/documents/IngramSparkPriceSheet.pdf (official, effective Feb 1 2026 — primary source for all $ figures)
- https://www.ingramspark.com/pricing
- https://www.ingramspark.com/plan-your-book/print/trim-sizes
- https://www.ingramspark.com/print-discounts
- https://janefriedman.com/ingramspark-no-longer-charges-setup-fees-but-adds-market-access-fee/ (updated Apr 2025)
- https://homespunstoriespress.com/ingram-spark-vs-kdp-print-quality/ (Jul 2025 hands-on comparison)
- https://kadavy.net/blog/posts/ingramspark-hardcover/
- https://www.indiepublishinggroup.com/complete-guide-to-ingramspark-publishing-for-canadian-authors/
- https://selfpublishingadvice.org/how-authors-use-ingramspark-and-kdp-together/
- https://oldmatemedia.com/new-trim-size/ and oldmatemedia.com/guides/publish-kdp-and-ingramspark/
- https://www.blurb.com/hardcover-and-paperback-books, https://www.blurb.com/pricing, https://www.blurb.com/ingram
- https://www.48hrbooks.com/testimonials, muddycolors.com Mixam review (2024)
- kdpcommunity.com threads on author-copy shipping cost/time to Canada
- neolemon.com / kdpcommunity.com on KDP hardcover trim-size limits (no 8.5x8.5, no jacket)

### Wrap-up (this pass)
README.md extended with new sections 7-11 (IngramSpark, Blurb, print quality reputation + hardcover
jacket-vs-case-laminate comparison table, print-both strategy, Canada practicalities) plus expanded
Key Sources. Title/intro line updated to describe the now-combined scope (format requirements +
platform comparison) without altering the existing sections 1-6. New content runs ~1,150 words —
slightly over the 700-1000 target due to the added comparison table and five distinct sub-topics
requested (IngramSpark, Blurb, print quality, hardcover jacket-vs-case-laminate, print-both
strategy, Canada practicalities all in one pass); kept concise per sub-topic rather than cutting a
requested sub-topic to hit the word count exactly.
