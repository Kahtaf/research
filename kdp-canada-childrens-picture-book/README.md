# Self-Publishing a Canadian Children's Picture Book: Format Requirements & POD Platform Comparison

Research for a Canada-based self-publisher preparing a 12-spread, ~285-word, full-color
AI-illustrated picture book (ages 2-5) for print (KDP/POD) and possibly ebook. Sections 1-6 cover
metadata/format requirements (front/back matter, Canadian ISBNs, Legal Deposit, AI disclosure,
EPUB); sections 7-11 compare print-on-demand platforms beyond KDP (IngramSpark, Blurb, print
quality, hardcover options, and Canada-specific practicalities).

## 1. Front matter

Only **two** front-matter pages are truly required in a self-published book: a **title page**
(recto) and a **copyright page** (verso, printed on the back of the title page). Everything else
is optional and genre-driven.

- **Half-title page**: a novel/adult-book convention, not standard in picture books — routinely
  skipped, which is sensible when every spread of a 24/32-page book is precious.
- **Copyright page** typically sits at page 2, though some indie picture-book publishers push it
  to the very last page so the story opens on a full-bleed spread instead — worth considering for
  a 12-spread book.
- **Dedication**: fully optional; if used, goes right after the title verso.
- **Copyright notice**: "Copyright © [Year] by [Author]. All rights reserved." The © symbol is
  *convention, not law* — Canada is a Berne Convention country, so copyright exists automatically
  on creation. Also conventional: publisher/imprint name, ISBN(s), an optional edition statement,
  and illustrator credit — since art here is AI-generated, credit the human author/creative
  director, optionally noting "illustrations created with the assistance of AI tools" alongside
  the KDP dashboard disclosure (§4). Skip "Printed in [country]" — POD print location varies by
  order.

## 2. ISBN — Canada specifics

**Library and Archives Canada (LAC)** issues ISBNs **free** to Canadian self-publishers via the
ISBN Canada program — the key edge over the US, where Bowker charges per ISBN. Eligibility just
needs a Canadian mailing address. Process: create an ISBN Canada account (name, address, accept
statement of use), await approval (reports range ~20 days to ~2 months — apply early), then pull
ISBNs instantly from "Manage Logbook → Assign New ISBN."

**Each format needs its own ISBN**: paperback and hardcover each get a separate one. **Kindle
ebooks need no ISBN** — Amazon assigns an ASIN instead; an ISBN only matters for the ebook if
distributing beyond Amazon (Kobo, Apple Books, IngramSpark). Both **KDP and IngramSpark accept
LAC-issued Canadian ISBNs** with no friction.

Caveat: KDP also offers its own free print ISBN, but that registers with Bowker under Amazon/KDP
as publisher of record and generally can't move to other print platforms later. Using your own
free LAC ISBN is the better default — you remain publisher of record and keep options open for
IngramSpark later. Get the ISBN before finalizing the cover so the barcode area can be planned.

## 3. Legal Deposit in Canada

Legal Deposit (SOR/2006-337), administered by LAC, is a statutory requirement, and self-published
authors are explicitly covered under the regulation's definition of "publisher." Copy count scales
with production volume: 4-99 copies → 1 copy required; 100+ → 2 copies. LAC's rules don't cleanly
address one-at-a-time POD "print runs," but the safe practical reading is: once the book is live
for public sale on KDP, treat it as deposit-triggering and submit at least one copy — LAC's own
framing centers on being "intended for sale or public distribution," which a live KDP listing
satisfies.

Physical submission: complete the Monograph publications form, mail a copy to LAC (550 de la Cité
Boulevard, Gatineau, QC J8T 0A7), and receive a deposit receipt by email; production/mailing cost
is deductible. Ebooks are deposited separately through LAC's online portal. A 285-word narrative
picture book comfortably clears LAC's "minimal text" exclusion (aimed at colouring books), so
deposit obligations apply normally.

## 4. AI-generated content disclosure (KDP, 2025-2026)

KDP's publishing dashboard (Content Details step) asks **"Is this content AI-generated?"** — if
checked, a follow-up asks whether the AI content is text, images, or translation. KDP
distinguishes **AI-generated** (produced by an AI tool — must be disclosed) from **AI-assisted**
(you created it; AI only edited/refined/brainstormed — no disclosure needed).

For this book, the illustrations (and likely cover art) are AI-generated, so disclosure is
required — select "images." Human-written text doesn't need flagging even if AI assisted with
editing. The disclosure is **not shown to shoppers**; it's for Amazon's internal compliance and
doesn't directly affect royalty, ranking, or category eligibility. But KDP enforcement (automated
+ human review) has increased through 2025-2026, and undisclosed AI content later flagged can
trigger removal or account action — disclosing costs nothing. This is a KDP platform policy, not
a Canadian legal requirement.

## 5. Back matter conventions

- **Author bio**: common but optional (2-4 sentences, often inside back cover); bios conventionally
  credit the human author/creative director rather than the AI tool.
- **"About this book" / discussion or activity page**: an increasingly common indie add-on, not a
  formal requirement.
- **Barcode/ISBN on back cover**: KDP and IngramSpark **auto-generate and place the barcode** if
  you leave the barcode zone blank on your cover file (recommended default — ~0.25 in / 0.635 cm
  clearance, bottom-right, light background); supplying your own risks being overwritten.
- **Cataloging-in-Publication (CIP) data**: true Library of Congress CIP is unavailable to
  self-published/POD titles (restricted to books pre-acquired by libraries via traditional
  publishers); Canada's own historical CIP program was discontinued. Third-party "Publisher's CIP"
  exists but most solo picture-book self-publishers skip it — libraries generate their own catalog
  records from the ISBN anyway. Low priority here.

## 6. EPUB / fixed-layout for picture books

Standard *reflowable* EPUB doesn't work for picture books — it lets text and images resize/reflow
independently per device, breaking the tight text-to-illustration relationship. **Fixed-layout
EPUB (FXL)** locks each spread's exact dimensions and positioning instead — the correct format for
image-heavy children's books.

Tooling: Amazon's dedicated "Kindle Kids' Book Creator" is effectively retired (Amazon stopped
accepting its .mobi output). Amazon now points authors to **Kindle Create**, which supports a
fixed-layout/kids'-book workflow — import a print-ready PDF or a folder of per-page JPGs to output
a KPF file for KDP. Downside: KPF is Amazon-proprietary, locking you to Kindle only. For true
cross-platform FXL EPUB (Apple Books, Kobo, IngramSpark, library aggregators), heavier tools are
needed: Adobe InDesign's "Export for EPUB (Fixed Layout)" or Kotobee Author. **Vellum does not
support fixed-layout picture-book EPUBs** — it's built for reflowable text and is the wrong tool.

Typical image specs: ~2048px on the longest side (sharp on retina tablets without bloating file
size; device range spans ~1024x768 to ~2732x2048). RGB, not the CMYK used for print files; JPEG
for painterly/gradient art, PNG for flat-color/line art or transparency.

**Worth it for this book?** With only 12 spreads and a print-first strategy, ship print first, and
if an ebook is wanted, use Kindle Create's kids'-book workflow (reusing print files) for a cheap
Kindle-only edition. Reserve true cross-platform FXL EPUB for later, only if distributing beyond
Amazon — for a single short title, a full multi-platform EPUB build is often disproportionate
effort relative to payoff.

## 7. IngramSpark: the main KDP alternative

**Setup cost**: Per IngramSpark's own official price sheet (effective Feb 1, 2026), **title
set-up is now free** for print, ebook, or combined, and **revisions are also free** — several
older blog posts still cite a $25 revision fee; that's outdated. The only recurring cost is a
**Market Access Fee of 1.875% of list price per sale** (covers their 45,000+-retailer network),
plus incidental fees (US check-payment $25, file-copy retrieval $25) that don't apply if paid by
direct deposit/PayPal.

**Canada friendliness**: IngramSpark pays Canadian accounts by **direct deposit in CAD** (even for
amounts under $50 CAD) or PayPal — comparable friction to KDP. One quirk: the compensation
calculator doesn't show a live CAD number (it's pegged to USD/exchange rate), but this is cosmetic.
Payment runs on a standard ~90-day lag, same as everywhere.

**Trim sizes & hardcover**: IngramSpark's pricing splits trims into **"Small" (<6.15" width)** and
**"Large" (≥6.15" width)**. This matters a lot for picture books: classic square/portrait
picture-book trims like **8.5×8.5" or 8×10" fall into "Large," which only gets case-laminate
hardcover — true jacketed hardcover is offered only at "Small" trims** (5×8" up to 6.14×9.21").
So a standard-size picture book on IngramSpark gets a sturdy case-laminate hardcover, not a jacket.

**Paper/color options for interiors**: Standard Color, Premium Color (70lb white, recommended for
heavy ink coverage/illustration), and Ultra-Premium Color (satin/sheen finish).

**Worked cost example** (32-page full-color book, "Large" trim, per official Feb 2026 rates):
paperback Premium Color ≈ **$4.44/unit**, Ultra-Premium ≈ **$6.06**; case-laminate hardcover
Premium Color ≈ **$9.90**, Ultra-Premium ≈ **$11.10**. Quantity discounts start at 100 copies (2%)
up to 35% at 10,000+.

**Distribution vs KDP**: this is IngramSpark's real advantage — its catalog reaches 40,000+
bookstores, libraries, and retailers (including Barnes & Noble, Apple Books, and, for Canada, a
direct line into the **Indigo/Chapters** wholesale system), with **returnable** stock terms
bookstores actually want. KDP's reach is essentially Amazon-only unless you tick "Expanded
Distribution," which resells through Ingram anyway but as non-returnable, lower-discount stock.

**Royalty math vs KDP**: KDP pays a flat 60% of list price minus print cost. IngramSpark instead
takes a **wholesale discount (default ~55%)**, so you net roughly **~45%** of list price minus
print cost — a materially thinner margin per Amazon sale, offset by access to sales channels KDP
can't reach at all.

## 8. Blurb

Blurb is photo-book-centric and it shows: only **three rectangular trims** (5×8", 6×9", 8×10") —
**no square trim**, so the classic 8×8/8.5×8.5 picture-book format isn't available. Two hardcover
styles: **ImageWrap** (no jacket, image printed directly on the case) and **Linen with a printed
dust jacket** — both limited to those same three trims. Pricing runs from roughly $21-23 for a
base hardcover, similar ballpark to IngramSpark. Distribution is weaker by default (Blurb's own
storefront + a "Sell on Amazon" option); an opt-in Ingram-distribution add-on exists but nets a
lower royalty than publishing on IngramSpark directly. Reviews are mixed for picture-book-style use:
some praise sturdy covers and thick pages, others report cracked hardcover cases, ink transfer, or
a pinkish color cast — worth ordering a proof before committing to a print run.

## 9. Print quality reputation (2024-2026 community consensus)

No platform has a spotless reputation among self-publishers illustrating full-color books:

- **KDP**: uses an RGB workflow; widely described as producing more natural, "true-to-life" color
  on illustrated covers/interiors, and is the cheapest option — but its lower-tier paper is thin
  enough that some show-through is reported, and hardcover is case-laminate only (see §7 and the
  original KDP-hardcover notes in this folder).
- **IngramSpark**: uses CMYK, and its Ultra-Premium tier is sometimes described as
  **oversaturated/reddish** compared side-by-side with KDP on the same file; hardcover binding
  (especially under ~76 pages) has drawn complaints about glue lines and page-transparency
  inconsistency in at least one detailed 2025 comparison. Its wider distribution, not print
  quality, is the reason people use it.
- **48hrbooks**: consistently praised for color image reproduction and customer service for
  children's books; note their hardcover option is glue-bound (not stitch-bound) — ask before
  ordering if binding durability matters.
- **Mixam**: good value and vivid color reported by multiple users; complaints center on packaging
  (books arriving loosely wrapped in beat-up boxes) rather than the print itself; ~2-week turnaround
  typical.

**Bottom line**: reputations are anecdotal and run-to-run variable — every source, without
exception, recommends ordering a physical proof copy before a real print run, regardless of vendor.

### 9b. Hardcover: jacket vs. case-laminate, by vendor

| Vendor | True jacketed hardcover? | At picture-book trims (8×8/8.5×8.5/8×10)? | Rough unit cost, 32pg full color |
|---|---|---|---|
| **KDP** | No — case laminate only, no jacket option exists on KDP at all | Case laminate only; no 8.5×8.5 hardcover trim exists on KDP | ~$3-4.50 paperback; hardcover somewhat higher (KDP hardcover uses a separate, smaller fixed set of trims) |
| **IngramSpark** | Yes, but **only at "Small" trims** (<6.15" wide) | No — falls to "Large," case laminate only | ~$9.90 (Premium Color) to ~$11.10 (Ultra-Premium) case-laminate hardcover |
| **Blurb** | Yes (Linen + dust jacket), on its 3 rectangular trims only | No square trim at all; ImageWrap (no jacket) is the closest fit | ~$21-23 base hardcover (varies by trim/paper) |

Net: **no mainstream POD service offers a true dust-jacketed hardcover at a standard square
picture-book trim size** — a jacket forces either a smaller/non-square trim (IngramSpark "Small")
or accepting Blurb's fixed rectangular sizes. For an 8.5×8.5 or similar square trim, case laminate
is the realistic hardcover option everywhere.

## 10. Using KDP + IngramSpark together ("print both")

This is a **commonly recommended strategy**, reportedly endorsed by IngramSpark's own leadership:
publish paperback (and hardcover) on both, since KDP wins on Amazon margin (flat 60% royalty) and
IngramSpark wins on everywhere-else reach (bookstores, libraries, Chapters/Indigo in Canada).

**The critical gotcha**: **do not enable KDP's "Expanded Distribution."** If checked, KDP's own
edition also gets pushed into Ingram's wholesale network — but as non-returnable, low-discount
stock, which undercuts the better returnable terms your dedicated IngramSpark edition offers the
same bookstores, and can create duplicate/competing listings for the same ISBN. The standard
workflow: publish the KDP paperback first (easiest platform to proof), leave Expanded Distribution
unchecked, then separately publish the IngramSpark edition (often with its own ISBN) for hardcover
and wide distribution.

## 11. Canada-specific practicalities

- **Printing location**: neither KDP nor IngramSpark has a confirmed dedicated print plant in
  Canada. Ingram's owned POD plants are in the US (Tennessee ×2, Pennsylvania), UK, and Australia;
  Canadian orders are cross-border. (A claim that Amazon has a Canadian KDP plant could not be
  verified against any authoritative source and should be treated as unconfirmed.)
- **Author-copy shipping**: IngramSpark quotes **3-7 business days** to Canadian provinces once
  printed, with duties/taxes/brokerage bundled into the shipping quote at checkout. KDP community
  threads describe author-copy shipping to Canada as comparatively **expensive and sometimes
  slow (multi-week)**, with no cost calculator — the total only appears near the end of the order
  flow, which has drawn repeated complaints.
- **Payment/currency**: IngramSpark pays CAD via direct deposit or PayPal on its standard ~90-day
  cycle; KDP pays in USD (or local currency per marketplace) on its own schedule — factor in
  exchange conversion either way.
- **Distribution edge for Canada**: IngramSpark's wholesale relationship gives direct access to
  **Chapters/Indigo**, Canada's dominant bookstore chain — a channel KDP cannot reach on its own.

## Key sources

- Library and Archives Canada — [ISBN program](https://www.canada.ca/en/library-archives/services/publishers/isbn.html), [Legal Deposit overview](https://www.canada.ca/en/library-archives/services/publishers/legal-deposit/about.html), [Physical publications deposit](https://www.canada.ca/en/library-archives/services/publishers/legal-deposit/physical-publications.html)
- Amazon KDP — [Content Guidelines / AI disclosure](https://kdp.amazon.com/en_US/help/topic/G200672390), [Get an ISBN](https://kdp.amazon.com/en_US/help/topic/GTJ8LBXL6Z4WV5QX), [Barcodes](https://kdp.amazon.com/en_US/help/topic/G5HDYGP4BXLX4RUW), [Print cost formula](https://kdp.amazon.com/en_US/help/topic/G201834340)
- Library of Congress — [Cataloging-in-Publication Program](https://www.loc.gov/programs/cataloging-in-publication/about-this-program/) (confirms self-pub/POD ineligibility)
- IngramSpark — [Free ISBNs](https://www.ingramspark.com/free-isbns), [ISBN facts for self-publishers](https://www.ingramspark.com/blog/isbn-facts-for-self-publishers), [Official price sheet (PDF, eff. Feb 2026)](https://myaccount.ingramspark.com/documents/IngramSparkPriceSheet.pdf), [Pricing](https://www.ingramspark.com/pricing), [Trim sizes](https://www.ingramspark.com/plan-your-book/print/trim-sizes), [Print discounts](https://www.ingramspark.com/print-discounts)
- [Jane Friedman — IngramSpark fee-policy update](https://janefriedman.com/ingramspark-no-longer-charges-setup-fees-but-adds-market-access-fee/) (updated Apr 2025)
- [Homespun Stories Press — IngramSpark vs. KDP print quality](https://homespunstoriespress.com/ingram-spark-vs-kdp-print-quality/) (Jul 2025 hands-on comparison)
- [Kadavy.net — IngramSpark hardcover review](https://kadavy.net/blog/posts/ingramspark-hardcover/)
- [Indie Publishing Group — IngramSpark guide for Canadian authors](https://www.indiepublishinggroup.com/complete-guide-to-ingramspark-publishing-for-canadian-authors/)
- [Alliance of Independent Authors / selfpublishingadvice.org — using IngramSpark and KDP together](https://selfpublishingadvice.org/how-authors-use-ingramspark-and-kdp-together/)
- [Old Mate Media — publish on both KDP and IngramSpark](https://oldmatemedia.com/guides/publish-kdp-and-ingramspark/), [IngramSpark's new trim size for children's books](https://oldmatemedia.com/new-trim-size/)
- Blurb — [Hardcover & paperback books](https://www.blurb.com/hardcover-and-paperback-books), [Pricing](https://www.blurb.com/pricing), [Ingram distribution add-on](https://www.blurb.com/ingram)
- [48 Hour Books — testimonials](https://www.48hrbooks.com/testimonials); Muddy Colors — Mixam self-publishing review (2024)
- Darcy Pattison — picture-book-specific ebook/EPUB formatting guidance
- Book Design Made Simple, First Choice Books (Canada), Pagemaster.ca (Canada), AuthorImprints — front/back matter and Canadian self-publishing practice

Full research log with additional detail and secondary-source cross-checks: see `notes.md` in this
folder.
