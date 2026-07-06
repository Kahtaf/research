# NICU Picture Book — Working Notes

## Task
- Draft exists: "The Smallest Light" (Book 1), a NICU story for a 3yo big brother (Zaki) whose baby sister (Aliza) is in the NICU. Target audience 2–3 yo.
- Goal: download transcripts of 20+ popular children's books, analyze their language, and do multiple refinement passes on the draft to perfect language & impact.

## Plan
1. Gather 20+ transcripts of popular children's picture/board books (esp. bedtime, comfort, sibling, repetition themes).
2. Analyze craft patterns: sentence length, refrain structure, vocabulary level, rhythm, page-turn mechanics, comfort devices.
3. Multiple refinement passes on the draft against those patterns.
4. Write README report.

## Progress log
- Set up folder + transcripts subfolder.
- Dispatched 3 parallel agents to fetch transcripts of modern popular books.
- **Copyright issue:** agents' attempts to reproduce FULL text of in-copyright books (Goodnight Moon, Llama Llama, etc.) were blocked by Anthropic's output content filter (copyright/verbatim-reproduction filter). Not a safety filter.
- **User direction:** pivot corpus to PUBLIC-DOMAIN children's books only — no copyright infringement.
- Deleted the 7 full-text copyrighted reproductions that had been saved.
- KEPT 8 fair-use craft-analysis files (short refrain quotes + structural notes only): owl-babies, the-kissing-hand, time-for-bed, llama-llama, the-going-to-bed-book, were-going-on-a-bear-hunt, little-blue-truck, goodnight-gorilla. These are commentary, not reproduction. Owl Babies is the single closest structural model for our book.
- Now building the primary corpus from PUBLIC-DOMAIN sources (Project Gutenberg): the lyrical nursery/lullaby tradition, which is actually a better register match for "The Smallest Light" than modern commercial board books.

## Public-domain corpus targets (freely reproducible)
Verse (highest relevance — lyrical, bedtime, baby, moon/star themes):
- Christina Rossetti — Sing-Song: A Nursery Rhyme Book (1872): tiny tender baby/mother/sleep poems
- Robert Louis Stevenson — A Child's Garden of Verses (1885): "The Moon", "Escape at Bedtime" (stars), "The Land of Nod", "Bed in Summer", "My Bed is a Boat", "Young Night Thought"
- William Blake — Songs of Innocence (1789): "Infant Joy", "A Cradle Song", "The Lamb", "Nurse's Song"
- Eugene Field — "Wynken, Blynken, and Nod", "The Sugar-Plum Tree"
- Alfred Tennyson — "Sweet and Low" (a lullaby about a father coming home over the sea — directly echoes Papa driving home)
- Jane Taylor — "The Star" (full "Twinkle, Twinkle, Little Star")
- Traditional lullabies: Golden Slumbers (Dekker), Hush Little Baby, Rock-a-bye Baby, Sleep Baby Sleep, Now the Day Is Over
- Mother Goose moon/star rhymes: "I See the Moon", "Star Light Star Bright", "Hey Diddle Diddle"
- Edward Lear — "The Owl and the Pussy-Cat"
Prose picture-book classics (structure/repetition):
- Beatrix Potter — The Tale of Peter Rabbit; The Tale of Benjamin Bunny; The Tale of Jemima Puddle-Duck
- Wanda Gág — Millions of Cats (famous cumulative refrain)

## Corpus assembled (20 works, transcripts/ folder — gitignored, not committed)
Full PD text: Peter Rabbit, Benjamin Bunny, Jemima Puddle-Duck, Wynken/Blynken/Nod + Sugar-Plum Tree (Field), Sweet and Low (Tennyson), The Star (Jane Taylor), The Owl and the Pussy-Cat (Lear), traditional lullabies & moon/star rhymes.
PD craft-analysis w/ short quotes: A Child's Garden of Verses (Stevenson), Songs of Innocence (Blake), Sing-Song (Rossetti).
Fair-use craft-analysis of modern classics (short quotes only): Owl Babies, The Kissing Hand, Time for Bed, Llama Llama Red Pajama, The Going-to-Bed Book, We're Going on a Bear Hunt, Little Blue Truck, Goodnight Gorilla.

## KEY CONVERGENCES — the tradition is already writing our book
- **Tennyson, "Sweet and Low":** mother lulls baby while "Father will come to thee soon ... Silver sails all out of the west / Under the silver moon." = Papa driving home + our Spread 12 silver moon. Also line-doubling: "Sweet and low, sweet and low"; "while my little one, while my pretty one, sleeps."
- **Jane Taylor, "The Star":** "the traveller in the dark / Thanks you for your tiny spark ... He could not see which way to go / If you did not twinkle so"; "For you never shut your eye." = Papa's dark drive, Zaki's guiding star, and Spread 1's light that "never looks away."
- **Blake, "Infant Joy":** whole poem = a blessing repeated over a 2-day-old. Template for "A small light for a small girl." Tiny 2-4 word lines for the tiny subject.
- **Stevenson, "The Moon":** one moon shining on many scattered creatures at once = our thesis (four lights → one shared moon). Catalogue rhythm.
- **Rossetti, "Love me — I love you":** ring form (open+close on same line); "arms under you, eyes above you" = kangaroo care geometry.
- **Owl Babies:** littlest sibling has ONE unchanging line ("I want my Mummy!"); name fear plainly; understated reunion + big physical joy; parent reframes at end ("You knew I'd come back").

## CRAFT PATTERNS TO APPLY (distilled)
1. Ring composition — last line echoes first. (Have it; tighten.)
2. Refrain that BLESSES, in fixed bottom-right position, varying one word.
3. Doubling of small words to slow/soothe: "days and days," "sweet and low," "little one... pretty one."
4. Form mirrors content: tiny subject -> tiny lines (2-5 words).
5. Soft consonants (l, m, n, s, sh, w) on the calm spreads; save hard stops for the one hard spread.
6. Catalogue/list rhythm with parallel grammar for the "four lights" montage.
7. Name the hard feeling plainly, then hold it — don't over-explain or rescue too fast.
8. Meter as emotion: shorten/tighten lines for worry (Spread 7), lengthen/slow for comfort.
9. Give the child (Zaki) ONE repeated line of his own, like Bill's in Owl Babies.
10. Concrete over abstract: hands, headlights, a switch — never "love"/"hope" said outright.
11. Reciprocity as climax: the child gives the comfort back (Kissing Hand; Zaki gives his light).
12. End on the barest, smallest words ("You're home.").

## Book 2
- Researched NICU/sibling book landscape + metaphor-comfort genre (see book2-research.md).
- Key gap: the sibling's inner life AT HOME while baby is elsewhere — under-served; ideal for a metaphor.
- Avoid clichés: tiny-fighter/miracle framing, equipment tour, guaranteed-homecoming.
- Freshest sibling-active vehicles: kite, nest/egg, tended seed, knitted blanket. (Lighthouse/stars overlap Book 1's light motif.)
- Brainstormed 4 concepts; AskUserQuestion selector glitched; per user "continue," developed the recommended one: THE KITE.
- Draft: the-string-book2-draft.md. First-person (Zaki), daytime/sky palette (counterpart to Book 1's night). Refrain "I've got the string" -> "I've got you." Wind = the machines/hard days reframed as what holds her up. Continuity: her star, the red car, shared nightlight, Grandma's cardigan.
