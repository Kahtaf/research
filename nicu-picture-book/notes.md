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
