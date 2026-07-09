# When You Get Here — Art Direction & Image-Generation Bible
### Companion to the LOCKED script (`when-you-get-here-vA-brothers-welcome.md`)
Built for AI image generation (Nano Banana / Google Gemini image, OpenAI ImageGen / gpt-image). Every spread has a paste-ready prompt with characters, expressions, props, lighting, camera, palette, and text-safe area.

---

## 0. HOW TO USE THIS (consistency workflow — read first)

AI image models forget characters between images. To keep the same boy, cat, and rooms across 12 spreads:

1. **Generate reference sheets FIRST**, before any spread:
   - *Character sheet — the Boy:* front, 3/4, and side view, plus one happy + one sad expression.
   - *Character sheet — the two Cats (ginger-and-white, grey-and-white), Mama, Papa, the Baby.*
   - *Prop sheet:* the red toy car, the crayon star drawing, the swaddle blanket.
   - *Location plates:* the living-room window, the boy's bedroom, the nursery.
2. **Feed those references back in** on every spread (Nano Banana and gpt-image both accept reference images / image-to-image). Keep the written character tokens below **word-for-word identical** in every prompt — do not paraphrase them.
3. **Generate in story order** so lighting/time-of-day flows.
4. If your tool supports **seeds**, reuse the seed that produced the best character look.
5. **Aspect ratio:** these are double-page spreads → **landscape 3:2** (e.g., 2400×1600). For single-page portrait, switch to **4:5** and move the text-safe area to the lower third.
6. **Text is added later in layout** — every prompt ends by telling the model to render NO text and leave a calm area for it.

---

## 1. GLOBAL STYLE (prepend to every prompt)

> **STYLE TOKEN (copy verbatim):** *"Warm, tender contemporary children's picture-book illustration; hand-painted gouache-and-colored-pencil texture with soft visible grain; softly rounded, gently stylized characters with large expressive eyes, round cheeks, and warm friendly faces; cozy hopeful storybook mood; gentle diffused lighting with soft shadows; harmonious warm palette; painterly and soft-edged. NOT 3D-rendered, NOT photorealistic, NOT anime or manga, no hard vector outlines, no glossy CGI."*

> **GLOBAL NEGATIVES (append to every prompt):** *"Avoid: any text, letters, numbers, or watermark; photorealism; 3D render; anime; distorted or extra fingers; malformed faces; any cats beyond the two described (one ginger-and-white, one grey-and-white); harsh or frightening shadows. Keep the setting a purely warm, domestic home with no clinical or medical elements. Format: landscape 3:2, and keep the text-safe area clear."*
>
> *(Note: the medical negatives are phrased positively on purpose — naming equipment like "wires/monitors" in a negative can cause token models to summon it, and these are all cozy home scenes anyway.)*

**Overall palette (hold across the whole book):** warm creams and soft honey-gold as the base; dusty teal / sage green and soft sky-blue as secondaries; **the matte-red toy car is the single most saturated accent in the book** (use it sparingly so it always draws the eye); the two cats (ginger-and-white and grey-and-white) are warm secondary accents; dandelion-yellow and star-gold as highlights. Night spreads shift to deep indigo/navy with a warm amber interior glow. Skin tones stay warm throughout.

---

## 2. CHARACTER BIBLE (reuse these tokens verbatim)

> **CUSTOMIZE FREELY:** skin tone, hair color/texture, and features below are a warm default. To make the family your own, change these attributes in the tokens and they propagate to every spread (they live in one place on purpose). Everything else — poses, expressions, props, lighting — stays the same.

- **THE BOY (narrator, "big brother"):**
  *"a 3-year-old boy with warm medium-brown skin, short dark-brown softly curly hair, big dark-brown eyes, thick eyebrows, round full cheeks, a small gap-toothed smile, small toddler build; wearing a mustard-yellow short-sleeve t-shirt and navy-blue denim overalls, barefoot"*
  Night/bedtime variant: *"…wearing soft navy pajamas printed with tiny cream stars, barefoot."*
- **THE BABY (sister, newborn):**
  *"a tiny newborn baby girl with warm brown skin with a soft newborn flush, a wisp of dark hair, delicate features, eyes gently closed or barely open; swaddled snugly in a cream chunky-knit blanket with one small embroidered red star"*
- **MAMA:**
  *"the mother, warm medium-brown skin, dark wavy hair in a loose low bun with a few soft loose strands, gentle almond eyes, mid-30s, wearing a soft sage-green cardigan over a cream top"* (the sage cardigan is her recognizable signature — keep it every appearance)
- **PAPA:**
  *"the father, warm medium-brown skin, short dark hair and a short neat beard, kind eyes, mid-30s, wearing a warm rust-and-cream plaid flannel shirt"*
- **THE CATS ("our cats," two males)** — in prompts, **"[CATS token]" = both cats together**:
  - *"CAT A — a plump friendly ginger-and-white tabby: orange mackerel stripes over a white chest, belly, and paws, a white muzzle, bright green eyes, a pink nose"*
  - *"CAT B — a plump friendly dark grey-and-white tabby: charcoal-grey mackerel stripes over a white chest, belly, and paws, a white muzzle, yellow-green eyes, a pink nose"*
  (the pair are a recurring background Easter-egg — try to place both somewhere in most spreads)

---

## 3. SETTING BIBLE (keep locations consistent)

- **THE HOME:** a cozy, sunlit craftsman-style house — warm honey-wood floors, cream and soft-sage walls, a woven rug, houseplants, framed family photos, lots of soft cushions. Lived-in and warm, never cluttered or messy.
- **THE BIG WINDOW (the book's visual anchor):** a large multi-pane (grid) window in the living room with a **wide wooden sill** the cats sit on, flanked by **cream linen curtains**, a small potted plant on one corner of the sill. Recurs in S1, S2, S3, S6, S7, S10, S12 — draw it the same each time.
- **THE BOY'S BEDROOM:** a low wooden bed with soft teal bedding and a star-patterned quilt, a small round rug, a shelf of toys. (S6.)
- **THE NURSERY:** a wooden crib with sage bedding, a hanging mobile of felt stars and clouds, a soft cream rug, a little armchair. A warm amber nightlight. (S9, S12.) *(S11, the first meeting, happens in the home entryway/living room, not the nursery.)*
- **THE YARD:** a small sunny backyard with green grass and a scatter of dandelions, a wooden fence, one leafy tree. (S4.)

**RECURRING PROPS (continuity — introduce, then pay off):**
- **The matte-red toy car:** a small, rounded, classic matte-red toy car (wood/tin look, no branding). Introduced on the windowsill in S1; featured S5; "kept ready" on a shelf S9; on the nursery shelf S12.
- **The bright star:** one especially large, warm-golden twinkling star in the night sky (S6, S12).
- **The crayon star drawing:** a child's yellow crayon drawing of a five-point star on paper, taped to the nursery wall; the boy makes and tapes it up in S9, and it stays on the wall in S12. (Not visible in S11, which is set in the entryway/living room.)
- **The swaddle blanket:** cream knit with the small red star (the baby, S11–S12).
- **The birds:** two or three little brown-and-blue songbirds outside the window (S3), can cameo elsewhere outside.

---

## 4. LIGHTING & TIME-OF-DAY ARC (so the book flows)

| Spread | Time | Light |
|---|---|---|
| 1 | Morning | warm golden sunrise through the window |
| 2 | Rainy day | cool silvery daylight, rain on glass, cozy warm interior |
| 3 | Bright day | clear cheerful daylight |
| 4 | Sunny midday | bright warm outdoor sun, blue sky |
| 5 | Afternoon | soft warm indoor daylight, low and golden |
| 6 | Night | deep indigo sky, warm amber bedroom lamp |
| 7 | Overcast dusk | muted, soft grey-blue, the one wistful low-light spread |
| 8 | Evening indoors | warm lamplight, tender and close |
| 9 | Bedtime | soft amber nightlight, calm |
| 10 | Late afternoon | warm, bright, hopeful golden light |
| 11 | Golden hour | the warmest light in the book, glowing |
| 12 | Night | indigo night + warm amber glow, the big star |

---

## 5. PER-SPREAD PROMPTS

*Each prompt = STYLE TOKEN + scene + GLOBAL NEGATIVES. The locked verse is shown for reference only — do NOT render it in the image.*

---

### SPREAD 1 — "A baby is coming"
**Locked text:** *My sister is coming. / Not today, and not tomorrow, but soon. / She's getting bigger and stronger every day, / somewhere warm and far away, / getting ready to come home to me. / And when you get here, little sister, / I'll show you everything.*
**Camera:** medium-wide, eye-level with the boy; window on the right, room opening to the left.
**Emotion:** hopeful, dreamy anticipation.

> [STYLE TOKEN] Wide landscape composition. Interior of a cozy, sunlit craftsman-home living room in warm golden morning light. In the foreground, [BOY token] stands on tiptoe at a large multi-pane window with a wide wooden sill and cream linen curtains, one small hand pressed to the glass, chin lifted, gazing out and slightly upward with a hopeful dreamy smile and bright wide eyes, eyebrows raised in wonder. On the windowsill beside him, the two cats ([CATS token]) are curled up together, content, next to a small matte-red toy car. Behind him the warm room shows honey-wood floors, a woven rug, a low shelf with picture books and framed family photos, and a leafy houseplant. Golden sunrise light streams through the window, warming his face and casting long soft shadows into the room. Palette: warm creams and honey-gold, dusty-teal accents, the red toy car a small vivid pop. Tender, hopeful mood. Leave calm empty space in the upper-left sky/wall area for text. [GLOBAL NEGATIVES]

---

### SPREAD 2 — "I'll show you the rain"
**Locked text:** *When you get here, / I'll show you the rain. / How it taps on the window, / how it makes the whole world shine. / I'll catch some in my hands for you.*
**Camera:** from just outside the house, looking in at the boy through the rain-streaked window.
**Emotion:** quiet delight and wonder.

> [STYLE TOKEN] Landscape composition. View from just outside the house, looking in through a large rain-streaked multi-pane window on a rainy day, cool silvery daylight. Inside, [BOY token] presses close to the glass with his hands cupped against the pane, as if trying to catch the raindrops sliding down the other side; his nose is almost to the glass and his face is bright with soft delight and round curious eyes, his breath lightly fogging a small patch. Raindrops streak and bead down the glass between the viewer and the boy; behind him the warm honey-and-cream interior glows cozily against the cool grey rain. the two cats ([CATS token]) sit on the windowsill inside, watching a single sliding raindrop, one with a paw raised. A small potted plant on the sill. Palette: cool silver-blues on the wet glass, warm cream-and-honey interior. Peaceful, snug, wistful mood. Leave calm space along the top for text. [GLOBAL NEGATIVES]

---

### SPREAD 3 — "I'll show you our cats"
**Locked text:** *When you get here, / I'll show you our cats. / They sit in the window all day / and chase the birds outside. / (They never, ever catch them.)*
**Camera:** medium, the windowsill as a little stage; boy and cat sharing the frame.
**Emotion:** giggly, warm comedy — the book's laugh beat.

> [STYLE TOKEN] Landscape composition, bright cheerful daylight. the two cats ([CATS token]) both perch on the wide wooden windowsill of the large multi-pane window, up on their haunches, front paws against the glass, tails puffed, eyes wide and comically fixated, mid-pounce energy but stuck behind the glass. Just outside, two or three little brown-and-blue songbirds flit on a branch, cheekily unbothered. Beside the cats, [BOY token] sits cross-legged on the sill or floor, laughing openly with his head tipped back, one hand resting on the ginger-and-white cat's back, delighted. Warm sunlit living room behind. Palette: cheerful warm daylight, the ginger-and-white and grey-and-white cats as warm focal accents against green foliage outside. Playful, funny, affectionate mood. Leave calm space in a lower or upper corner for text. [GLOBAL NEGATIVES]

---

### SPREAD 4 — "I'll show you how to blow a dandelion"
**Locked text:** *When you get here, / I'll show you how to blow a dandelion / until the whole sky fills up with white. / I'll save you the biggest one.*
**Camera:** low angle looking slightly up at the boy against the sky, seeds drifting up.
**Emotion:** pure joy, movement.

> [STYLE TOKEN] Landscape composition, bright warm midday sun, clear soft-blue sky. Outdoors in a small sunny backyard with green grass, scattered dandelions, a wooden fence and one leafy tree. [BOY token] crouches in the grass, cheeks puffed mid-blow, holding a big dandelion puff up to his lips, eyes crinkled with joy; a cloud of white dandelion seeds lifts and drifts up across the sky, catching the light. His other hand holds a second, extra-big dandelion carefully behind him (saving it). Sunlight backlights the floating seeds. the two cats ([CATS token]) bat at the drifting seeds nearby in the grass. Palette: fresh greens, warm sunlight, soft blue sky, dandelion-white and yellow highlights. Free, happy, breezy mood. Leave calm sky space in the upper third for text. [GLOBAL NEGATIVES]

---

### SPREAD 5 — "I'll show you my cars"
**Locked text:** *When you get here, / I'll show you my cars. / You can even hold the red one. / (I don't let anybody hold the red one.)*
**Camera:** top-down / high three-quarter over the rug, cars arranged in a line.
**Emotion:** proud, a little possessive, generous.

> [STYLE TOKEN] Landscape composition, soft warm afternoon indoor light. High three-quarter view looking down at [BOY token] kneeling on a woven rug on the honey-wood floor, a neat line of small toy cars spread in front of him. He holds up the **matte-red toy car** in both hands toward the viewer with a proud, slightly bashful grin and shining eyes, offering it. The other toy cars (blues, greens, yellow) trail in a row beside him, the red one clearly the treasured favorite. the two cats ([CATS token]) doze together on a cushion in the background; a shelf with books and a framed photo behind. Palette: warm creams and wood tones, muted toy colors, the red car the brightest saturated pop in the frame. Warm, tender, funny mood. Leave calm space along one side for text. [GLOBAL NEGATIVES]

---

### SPREAD 6 — "I'll show you the nighttime"
**Locked text:** *When you get here, / I'll show you the nighttime. / The moon. The stars. / I already picked one out for you. / That one. That's yours.*
**Camera:** from inside the dark bedroom, boy silhouetted-ish at the window pointing up at one bright star.
**Emotion:** hushed awe.

> [STYLE TOKEN] Landscape composition, night. [BOY token in navy star-print pajamas] kneels on his low bed by a window, leaning on the sill, pointing up with one finger at a single especially large, warm-golden twinkling star among many smaller stars and a soft crescent moon in a deep indigo sky. His upturned face is lit warmly by a bedside amber lamp, eyes wide with quiet wonder, mouth softly open. The cozy bedroom has teal bedding and a star-patterned quilt; the two cats ([CATS token]) curled asleep together at the foot of the bed. The chosen star glows noticeably brighter than the rest. Palette: deep indigo night outside, warm amber lamplight inside, gold star highlights. Hushed, magical, tender mood. Leave calm dark-sky space in the upper area for text. [GLOBAL NEGATIVES]

---

### SPREAD 7 — "But you're taking a long time"
**Locked text:** *But you're taking a long time. / Every morning I ask, "Today?" / And every morning, "Not yet. / Soon. She's getting stronger." / Waiting is the hardest thing I know.*
**Camera:** medium, boy small in the frame at the big window, seen from behind/side; lots of quiet space.
**Emotion:** the ache — wistful, longing, patient sadness. The emotional low point.

> [STYLE TOKEN] Landscape composition, soft overcast dusk, muted grey-blue light — the quietest, most subdued spread. [BOY token] sits alone on the wide wooden windowsill of the big multi-pane window, knees pulled up, chin resting on his folded arms, gazing out at an empty grey street with a small wistful, longing expression and slightly downturned mouth. The room behind him is dim and still. the two cats ([CATS token]) sit quietly beside him, also facing out, gentle companions. Lots of calm negative space; the boy is small in a large soft frame to feel the waiting. Palette: muted soft greys and dusty blues, one small warm light in the room to keep hope alive. Tender, aching, patient mood — sad but safe, never frightening. Leave generous calm space around the boy for text. [GLOBAL NEGATIVES]

---

### SPREAD 8 — "What if you miss it?"
**Locked text:** *But what if you get here / and the rain has stopped? / What if you miss it? / "There's always more rain," says Mama. / "And the rain was never the best thing. / The best thing is you. And me. And us."*
**Camera:** close, intimate two-shot — Mama and boy together.
**Emotion:** worry soothed into warmth; the emotional turn.

> [STYLE TOKEN] Landscape composition, warm indoor evening lamplight, tender and close. [MAMA token] sits on a soft cushioned sofa cradling [BOY token] in her lap; he looks up at her with a worried little frown and searching eyes, and she looks down at him with a gentle reassuring smile, one hand cupping his cheek, foreheads almost touching. Cozy living room around them, a warm lamp glowing, the big window dark and rainy behind. the two cats ([CATS token]) curled beside them on the sofa. The mood turns from worry to comfort. Palette: warm honey lamplight, sage-green (Mama's cardigan) and cream, soft and enveloping. Loving, safe, intimate mood. Leave calm space to one side for text. [GLOBAL NEGATIVES]

---

### SPREAD 9 — "I keep everything ready"
**Locked text:** *So I wait. / I keep the red car ready. / I keep your star ready. / I keep everything ready / for when you get here.*
**Camera:** medium, boy in the nursery/his room setting things in place.
**Emotion:** tender purpose, quiet love, patience.

> [STYLE TOKEN] Landscape composition, soft warm amber nightlight, calm and cozy. [BOY token in navy star-print pajamas] stands on tiptoe in the nursery, carefully taping a **child's yellow crayon drawing of a star** onto the wall beside the wooden crib, tongue poking out in concentration, a caring focused expression. On a low shelf he has arranged, "ready," the **matte-red toy car** and a small folded blanket. A hanging mobile of felt stars and clouds drifts above the crib; sage-green nursery walls; a warm amber nightlight glows. the two cats ([CATS token]) watch from the doorway. Palette: warm amber and soft sage, cream, the red car and yellow star drawing as gentle accents. Tender, purposeful, patient mood. Leave calm wall space for text. [GLOBAL NEGATIVES]

---

### SPREAD 10 — "She's coming home"
**Locked text:** *And then, one day, / "She's coming home." / I run to the window. / I've been ready for so long.*
**Camera:** dynamic — boy mid-run toward the window, motion and light bursting in.
**Emotion:** explosive joy, anticipation breaking open.

> [STYLE TOKEN] Landscape composition, warm bright late-afternoon golden light flooding in. [BOY token] runs full-tilt across the living room toward the big multi-pane window, arms flung back, mouth open in a huge joyful shout, eyes bright and wide, hair bouncing — full of motion and excitement. Through the window, warm golden light pours in and a car is just pulling into the driveway outside. A cushion tumbles, the woven rug ruffles under his feet to show speed. the two cats ([CATS token]) startle awake, ears up. Palette: bright warm golds and creams, hopeful and luminous. Exuberant, joyful, breathless mood. Leave calm space in a corner for text. [GLOBAL NEGATIVES]

---

### SPREAD 11 — "And here you are" (THE FIRST MEETING)
**Locked text:** *And here you are. / Small, and new, and finally, finally here. / "Hi," I whisper. "I've been waiting for you." / And you wrap your whole hand / around one of my fingers.*
**Camera:** intimate close-up on the baby's tiny hand around the boy's finger, faces near.
**Emotion:** the emotional peak — awe, tenderness, holy quiet.

> [STYLE TOKEN] Landscape composition, the warmest glowing golden-hour light in the book. An intimate close-up centered on the meeting of hands: the **baby's tiny hand, with exactly five little fingers, gently curling around the boy's one outstretched finger**, both hands rendered clearly and tenderly with correct, natural anatomy, held at the center of the frame. Just above and behind, in soft focus, [BOY token] leans in with an expression of pure hushed awe (wide shining eyes, softly parted lips, raised eyebrows), whispering. Beyond him, blurred into a warm golden halo, is the gentle suggestion of [MAMA token] cradling [BABY token] swaddled in the cream knit blanket with the small red star, and [PAPA token]'s tearful proud smile just behind. The whole family and cozy home entryway melt into soft focus so the two joined hands stay the sharp focal point. Palette: glowing warm golds, cream, soft skin tones, the small red star on the blanket a tiny accent. Overwhelming tenderness, love, and wonder. Leave calm warm space above for text. [GLOBAL NEGATIVES]

---

### SPREAD 12 — "You're finally here" (FINAL)
**Locked text:** *Come on. Let me show you. / The rain. The cats. The dandelions. The moon. / And that star up there? / That one's still yours. / But you're the best thing I ever waited for. / You're here. / You're finally here.*
**Camera:** wide, warm — boy at the nursery window at night holding/showing the baby the big star.
**Emotion:** contentment, completion, quiet joy. The resolution.

> [STYLE TOKEN] Landscape composition, night — deep indigo sky through the window with the one large warm-golden star, and a cozy warm amber glow inside the nursery. [BOY token in navy star-print pajamas] stands (steadied by [MAMA token]'s hands, or kneeling safely beside the crib) gently showing [BABY token], swaddled in the red-star blanket, the view out the multi-pane window, one small finger pointing up at the big bright star. The boy's face is soft with contented pride and love; the baby's eyes are barely open toward the light. On the nursery shelf: the **matte-red toy car**; on the wall: the **yellow crayon star drawing** from Spread 9; the felt-star mobile above the crib. the two cats ([CATS token]) curled asleep together on the rug. The whole room glows warm against the indigo night. Palette: indigo night + warm amber interior, gold star highlight, the red star blanket accent — the book's warm palette resolving. Peaceful, complete, loving mood. Leave calm space (dark window or wall) for text. [GLOBAL NEGATIVES]

---

## 6. COVER (bonus)
> [STYLE TOKEN] Portrait book-cover composition. [BOY token] on tiptoe at the big multi-pane window in warm golden light, one hand on the glass, looking up and out with hopeful anticipation; the two cats ([CATS token]) on the sill; the matte-red toy car on the sill; a single warm-gold star faintly visible in the daytime sky outside. Cozy, inviting, warm. Leave the top third open and uncluttered for the title *When You Get Here*. [GLOBAL NEGATIVES]

---

## 7. QUICK CONSISTENCY CHECKLIST (verify each generated image)
- [ ] Boy: same face, hair, mustard tee + navy overalls (or star pajamas at night), barefoot.
- [ ] Cats: both present — ginger-and-white (green eyes) and grey-and-white (yellow-green eyes); no extra cats added.
- [ ] Same big multi-pane window with wide wooden sill + cream curtains in all window spreads.
- [ ] Red toy car present where required (S1, S5, S9, S12) and matte red.
- [ ] The bright star matches (S6, S12); the crayon star drawing appears S9→S12 (nursery; not in S11).
- [ ] Baby's blanket = cream knit with one small red star (S11, S12).
- [ ] Mama in sage-green cardigan; Papa in rust plaid.
- [ ] Lighting matches the time-of-day arc (Section 4).
- [ ] No text, no medical equipment, no hand deformities.
