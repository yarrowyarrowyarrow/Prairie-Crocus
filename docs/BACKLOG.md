# Prairie Crocus — the backlog

**Everything not yet built, in one place.** Rewritten in V3.77 to hold only that: each row says
what is left of it. Everything that shipped, closed or was folded into another row is in
[`BACKLOG_ARCHIVE.md`](BACKLOG_ARCHIVE.md), as it stood, with the history this file used to carry.
Checked against the ID ledger and the code on 27 November 2026.

**How this relates to the other documents.** This is the *index*: one line per thing, enough to
choose from. The **reasoning** for each entry stays where it was written:
[`ROADMAP_NEXT.md`](ROADMAP_NEXT.md)'s ID ledger for F63 and up,
[`PHILOSOPHY_ROADMAP.md`](PHILOSOPHY_ROADMAP.md) for F1–F62, and the plans under
[`plans/`](plans/). Follow the ID. New IDs come from the ledger's *Next free ID*, never from memory.

**The rule that keeps this file short.** When a row ships, move it to the archive with its version.
When part of it ships, cut the row to what is left. The groups keep their letters, because other
documents point at them ("group J", "group O", "group P"); a letter missing here had every row
ship, and is in the archive.

**Ratings.** Effort: **S** (hours to a day) · **M** (a few days) · **L** (a week or more) · **XL**
(a program of work). Risk: Low / Med / High, the chance of breakage, scope creep or a hard
dependency. **P** names the principle in [`DESIGN_PHILOSOPHY.md`](DESIGN_PHILOSOPHY.md).

**Open at V3.77: 69 features · 19 data jobs · 4 legacy items**, counted from the rows below.

---

## Waiting on the owner

*Most rows wait on engineering. These wait on a decision or a step only the owner can take; the
column says what each holds up. The questions are on the
[decisions page](https://claude.ai/artifact/2bm9oj98vH8qGc3M4cR2cz) with their context and a
recommendation each; a session reads the answers there (`ArtifactData list` on `answers`) and
moves each answered row out of this table.*

| What | Holds up |
|---|---|
| V3.77's seven decisions: the *Slope grid* box (D1), which contours get a height (D2), lawn conversion (D3), existing features under the Yard tab (D4), yard patterns in the simple app (D5), the design's own plants in the map's shade (D6), the emoji (D7) ([plan](plans/V3.77-slope-and-the-yard-from-use.md#decisions-for-the-owner)) | F278, F289–F293 |
| The design file or a screenshot of the fire pit drawn as a shed | F288 |
| Retire Share › Present, or keep it (V3.38's D4; retiring it is recommended) | F258 |
| Review each walk's lead species (V3.38's D7) | F255 |
| Approve the light from its before/after sheet (V3.53's D6; shipped, pending approval) | the 3D look |
| Whether 399 plants and 680–1,400 first-year hours is the right first impression for the example (V3.54) | the example lot |
| Two headline changes to the habitat score: grass bloom out of bloom continuity, and structure points by habitat value (V3.38's D3) | F184, F256 |
| Whether "recorded as food for N kinds" should count only animals recorded near the yard (left by F190, V3.37) | the food counts |
| One nomenclature for the 18 recent recombinations | group J |
| Whether the "Native Prairie Aromatics" community sits inside P12's hard rule | F189 |
| Yes to widening the 37 rows VASCAN records in Saskatchewan | F170 |
| The German yellowjacket's nativity (a correction is a decision) | F159 |
| Whether an estimated soil pH range should hide a plant or only rank it | F201 |
| A rule for junipers beside saskatoons and hawthorns | F169 |
| Edges on fields and buttons (every panel's look changes) | F203 |
| The relationship web above the plants, or its clicks routed through the map | F214 |
| A per-user Windows install, with its move out of Program Files | F230 |
| The bee photograph licence: CC BY-SA for bees as for other animals, or the stricter CC0/CC BY bar (F37 A1), leaning on F67's models to carry identification | photographs, group J |
| The site's Umami website ID and feedback URL | F157 |
| A feedback mailbox, a second maintainer, promoting a release | F242 |
| Three to five usability sessions with homeowners | F243 |
| Correct the 28 familiar animals drafted in V3.37 | F249 |
| More nursery lists on the stock review page | F227 |
| Own photograph picks on the photo review page (optional: every native has photographs) | F247, F251 |

---

## C · Photographs and observations

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F73** | **"In my yard, on this date."** Tag a person's photo to a *placed plant* and a *date*, so it becomes an observation: F51's phenology prompt ("we predict X in bloom around now: early, late, on time?") lands there, the old F33 journal is delivered with the best possible entries, and after two or three seasons the person owns their own site's bloom dates. The `taken_on` column exists (`src/db/photos.py`, schema v55): UI work, no schema bump | M | Low | P11, P4 |
| **F74** | **The seedling sheet.** In May a first-year conversion is forty green rosettes and the beginner weeds their own milkweed. The `seedling` photo slot, keyed to the planting map's numbers (F41), printed with the plan; honest where there is no photo (P9). **Blocked on content**: almost no species has a seedling photograph | S–M | Low | P11, P8 |

## D · The designer's workflow

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F113** | **Design variants, side by side.** *(F90 until V2.52; F90 is the plant directory.)* "Duplicate as a variant", then a comparison: habitat score, cost range, first-year and steady-state hours, food-web status, species and wildlife counts, native ratio, with the differences named. Every number exists; holding two projects at once and comparing them is the missing part. Options with their trade-offs rather than one confident answer is P9 at the scale of a design | L | Med | P9, P1 |
| **F93** | **Reusable palettes.** Save the current selection as a named palette and apply it to a new site **with site fit checked again**, which a person cannot do quickly and the app can. Extends `polycultures`, which already keeps user rows through a reseed | M | Low | P1 |

## E · The Learn side

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F105** | **Challenges and achievements.** Briefs with win conditions over the sandbox ("support 5 bee species on 20 m²", "something in bloom every week April to October"), scored by `habitat_score`, `forage_calendar` and `habitat_nudges`. **Achievements for going outside**, or the game argues against P11. F32 and F73 are the hooks | M | Med | P11, P13 |
| **F85** | **The companion.** *(Absorbed F106, the same feature filed twice.)* A fauna guide (a caterpillar, a bee, a chickadee) that explains the app as you go, starting with Site Info. Reuses `onboarding.py`'s progress model, `docent.py`'s beat shape and `learn_state`. New: a widget-anchoring idea, tour progress kept, **and the art**. It should push people outside, not keep them at the screen (P11) | L | Med | P5, P13 |
| **F107** | **Hand-painted butterfly and moth wings.** `scripts/tune_fauna.py` already edits wing shape, colours and pattern with drawn vocabularies. Missing: the painting. The animal models ship with **no UVs and no textures by contract**, so the wing material needs its own path in `09-models.js`, plus a template, an import path (`photo_import`, which strips a yard's coordinates) and a slot that survives a reseed. A conversation about the template first | L | Med | P13, P5 |
| **F83** | **Know the plant by its characters.** Show a photograph, ask for the leaf shape or flower arrangement, score it, with the 64 drawn vocabularies in `html/botany/`. Field Study's topics (V3.40) name plants from photographs; asking for the *character* is what is left | M | Low | P5, P7 |
| **F88** | **The Learn tab as a curriculum.** Three lessons were drafted in V3.41 for the owner's rewrite ([plan](plans/V3.41-three-lessons.md)). Left: the app and the fauna tracks, and progress kept between sessions (`learn_state` can hold it). **P12 applies**: a flora track must not become a route to plant-use knowledge, and every new learning surface joins the scan in `tests/test_plant_directory.py` | L | Low | P5, P7 |

## G · Notes and going outside

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F86** | **Notes that add up.** *"Make a note from any menu or on the design itself and have all these notes feed a master note doc that can use this info in a functional way."* Site › Notes shows the site walk, the design journal and the map's pinned notes on one page since V3.08; the stores are still separate. The hard half is "functional": decide what a note can *do* (become a task, pin to a plant, date an observation) before joining the storage | M | Med | P11, P4 |

## H · Depth and relationships

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F49** | **Ornamental to native swap card.** The garden-centre moment. A curated `native_swaps_master.json` (ornamental, the role it plays, the native keyed to a real plant, the gain), a table and a lookup; a 25-row list of what Alberta garden centres sell proves it | S–M | Med | P6, P8 |
| **F38** | **Notes for degraded ground.** Cited restoration techniques for contaminated and compacted ground. Content, directional | S | Low | P8 |
| **F18** | **A repair sequence from the soil.** From measured soil and disturbance, recommend pioneer cover, soil builders, then the target community: `property_data.fetch_soil`'s pH and texture against the plants' pH ranges and `succession.successional_role` | M | Med | P8, P4 |
| **F23** | **Placement rules you can read.** Density per m², native first, anti-monoculture and layer balance are constants inside `placement_score` and `llm_design`; lifted into one named, documented rule object, P1 is shown rather than claimed | M | Low | P1 |
| **F25** | **Mycorrhizal and symbiosis edges.** Frankia, ericoid, AMF from plant notes as data: a table, a `UNION ALL` arm in the `relationship_edges` view and an `EdgeKind`, and the web and the API carry it. The data is the bottleneck (mostly genus-level) | M | Med (schema) | P3 |
| **F26** | **Successional-sequence edges.** "Pioneer A prepares the ground for climax B", directed, driving planting order and the timeline | M | Med (schema) | P3, P4 |
| **F29** | **Ranges on the timeline.** A slow, expected and fast growth band from `years_to_maturity`, not one line | M | Low | P9, P4 |
| **F21** | **Ecosystem services as ranges.** Carbon, stormwater, cooling, pollination beside the habitat score, **only if the ranges stay wide and said** | M | Med | P6, P9 |
| **F36** | **Community spacing from competition.** Offsets from canopy and competition rules rather than fixed ones, refining F22/F35's naturalistic spacing; partly met since V3.59, when the seeded communities are laid out by rule (`community_layout`) | L | Med (schema) | P1, P4 |
| **F27** | **Habitat corridors.** The design against natural features nearby; needs outside data | L | Med | P3 |

## I · 3D fidelity

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F114** | **Wing patterns as geometry**: eyespots and bands, deferred from F84. Written and removed once (the marks would not render, a coplanar ordering problem); the data, vocabulary and bench are in place | M | Med | P13 |
| **F117** | **Fruit drawn at its size.** A shrub's fruit is a card held into winter since V3.63 (`15d-woodyfruit.js`); every other fruit is still a point sized by its form (3–16 cm since V3.43), estimates until a fruit's own size is recorded | S–M | Low (schema for the size) | P13 |
| **F118** | **Better creature models.** As filed, the bee is spheres and two flat discs; the birds were rebuilt in V2.97 (F174). Blender work in `scripts/blender/assetlib/fauna.py`, driven by the morphology all flying groups now have | M | Med | P13 |
| **F119** | **Birds and mammals from data, not name tables.** Birds take their body from their genus since V2.97, their colours still from a name table; one span-to-length ratio per build draws long- and short-tailed birds 14–25% off, and `bird_morphology` records no body length | M | Med (schema) | P13 |

## J · Data jobs

*Jobs that move data rather than code, most with tooling that exists. The owner's decisions they
wait on are in the table at the top.*

| Job | What is left |
|---|---|
| **Photographs** (F257, the bee licence) | **51 of 424 plants** have none, none of them on the Edmonton list. **849 of 1,144 animals** have none: 280 of 338 bees, 351 of 408 other insects, 215 of 343 butterflies and moths, 3 of 49 birds. The V3.76 fetch (`scripts/fetch_animal_photos.py`, on the owner's PC) asked for 258 animals, the region's named ones first, and found photographs for 237; the rest have not been asked. Bees stay held to CC0/CC BY until the licence decision |
| **F247 lead photographs for the top 60** | Every one has photographs since V3.55; left is the owner choosing the one that leads, for beauty, on the photo review page (F251) |
| **F248 toxicity for the top 60** | 48 of the top 60 have no record; the poison wording rests on it |
| **F246 the spread review** | Confirm or correct 26 candidate spreaders, and say "not yet checked" for the blanks |
| **F249 the animals an Edmonton homeowner knows** | 28 drafted in the V3.37 plan for the owner to correct into the pack's `overview.familiar_animals` |
| **F243 usability sessions** | Three to five Edmonton homeowners, seven tasks; the notes page and a pre-flight test exist (V3.32) |
| **F227 where each plant can be bought** | The mechanism and the first five lists shipped (V3.25–V3.26: 70 of 250 natives Available). Left: more nurseries' lists, pasted on the [stock review page](https://claude.ai/artifact/M34LyMq1RPqXcNRTLuDmwW) and folded in (`tools/stock_review/README.md`) |
| **Larval-host records from life stage** | GloBI's life stage came back for 41% of records (F128, V2.62): the route to about 700 refused `larval_host` edges, and to the 18 admitted animals with no row because every record of them is an adult nectaring |
| **The recombinations, and four names that need a flora** | 18 recombinations VASCAN accepts and the regional floras have not adopted, allowlisted in `data_quality.KNOWN_NOMENCLATURE` (one decision, the owner's); and four look-ups in a printed flora: *Carex rostrata* / *utriculata*, *Viburnum opulus*, and "Indigenous Ricegrass" and "Rat Root" / "Bear Root" as P12 questions ([plan](plans/V2.82-the-harebells-were-not-swapped.md)) |
| **Manitoba** | `tools/ecoregions/common.py` names Alberta and Saskatchewan only. A rebuild with Manitoba as a subject province, a wider GBIF window and a full re-derivation; `interlake_plain` is the only region with no species rows |
| **F168 candidate species** | 50 natives the catalogue does not carry, in [`CANDIDATE_SPECIES.md`](CANDIDATE_SPECIES.md); in through the pending file and a VASCAN run |
| **F170 widen the under-claimed provinces** | 37 rows VASCAN records in Saskatchewan that the catalogue calls Alberta-only; a `widen` bucket, reported before applied |
| **F171 the real Green Milkweed** | The row is Oval-leaf Milkweed since V3.18; add *Asclepias viridiflora* through the pending file, which needs VASCAN |
| **F165 Bur Oak's Saskatchewan animals** | 2 caterpillar-host edges against Chokecherry's 17; a sourcing pass on a machine with egress |
| **F189 "Native Prairie Aromatics" and P12** | Four of its seven are widely known on the prairies as Indigenous medicines; whether the grouping sits inside P12's hard rule is the owner's call. Left exactly as authored |
| **F201 the soil pH ranges' source** | All 424 rows carry a range and none says where it came from (102 at exactly 5.5–7.5). Record a source per row, mark defaults as estimated, and ask whether an estimate should hide a plant or only rank it |
| **The labels behind the Edmonton specimens (F220)** | The point cache keeps a sheet's place and year, not its label, where "cultivated" is written. The text of the ~2,000 sheets within 50 km would settle questions like Manitoba Maple's 14 collections. Needs egress (GBIF answers 403 in a session) |
| **Bird morphology** | All 24 rows `verified = 0`, entered from the literature with no network; wing area null for every row. AVONET (CC BY 4.0) and Dunning's handbook, in a session with egress |
| **"Pioneer" in 40 plants' notes** | What WD-6 (V3.19) left: the word is in the free-text `notes` of 40 rows, which no screen shows (L8). Tidy when those rows are next touched |

## K · Legacy ledger

*Still "Planned" in [`ROADMAP.md`](ROADMAP.md), which is otherwise history. Not ranked.*

| ID | Feature | Note |
|----|---------|---|
| **X1** | Google Earth KML/KMZ import and export | The scan and OSM imports cover most of what it was for |
| **X4** | Sharing designs through an online library | `.perma.geojson` is portable; the missing part is a place to put it |
| **V1** | Vegetation layer indicators | Partly covered by the relationship web's layer filter and the 3D layers |
| **P4 / P5** | Crop rotation tracker · "energy leak" mapping | **Retirement candidates**, from before the move to native habitat |

## M · Found by the V2.83 review

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F157** | **A site build anybody can repeat.** The published site has no analytics and no feedback form because the flags are typed by hand. A checked-in config and a build that refuses to publish without it; needs the owner's Umami ID and feedback URL | S | Low | P9 |
| **F160** | **Communities a province's natives cannot fill.** A seeded community is offered only when every member is native to the yard's province; since V3.59 the seeded communities are Edmonton's, so for Saskatchewan the answer is communities written for it | S–M | Low (seed data) | P1, P9 |
| **F159** | **The German yellowjacket is filed as native.** *Vespula germanica* has `ab_native = 1`; it is introduced in North America. A nativity correction, the owner's | S | Low (reseed) | P9 |

## N · Found by the Bur Oak question (V2.86)

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F169** | **Junipers beside saskatoons.** Juniper is the alternate host of the rusts that spot saskatoon and hawthorn fruit, and the spores travel far, so a spacing push does nothing. A rule: no juniper with saskatoons, or the design says why both | S | Low (generator rule) | P3, P13 |
| **F166** | **Larval-host records by genus.** The butterfly and moth file names host genera (*Salix*, *Populus*) that `src/db/derived_edges.py` never expands, as it does for nectar. A new tree would get edges on arrival; it moves the edge layer and every score that reads it | M | Med | P3, P9 |

## O · Found by the 3D model audit (V2.87)

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F172** | **Catalogue corrections the audit found.** The flower colours are done (V3.34). Left, as listed in V3.34 and not checked again since the V3.48–V3.67 model work: three habit records (Northern Bedstraw "sprawling", Western Wood Lily "grassy", Water Arum's spathe counted as 40 flowers), 21 bird colour rows, 21 bee genera missing from the look table (64 bees wear the default), Spiked Water-milfoil's English name (the usual name of the Eurasian invasive), Buckbean's leaf size, Wild Clematis's flower | S | Low (reseed) | P9, P13 |
| **F173** | **Insect body plans.** A wasp, a true bug, an ant, a grasshopper, a moth at rest; V2.88 put these on the nearest model and flagged them `interim`. Reaches 92 wasps and sawflies, 33 bugs, 6 ants, 7 grasshoppers and 189 moths | M | Med (Blender) | P5, P10 |
| **F184** | **The habitat score counts grass bloom.** Bloom continuity reads every `bloom_period`, grasses included; a grass-heavy prairie mix scores 52 where it would score 46, with June and July a gap the score calls covered. A headline change, the owner's | S | Low (moves the headline) | P6, P9 |

## P · Found by the V2.98 review of picking and placing

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F202** | **A community drawn as one thing.** Nothing outlines a placed community: its members share an id the move tool reads, and nothing else. An outline (the members' hull or the community's radius), on placement and load, following a move, with the name on hover | M | Low | P10 |
| **F203** | **Edges on fields and buttons.** 64 stylesheets outline fields and secondary buttons at 1.52:1; `#5a8a5a` (3.75:1) would carry WCAG 1.4.11's 3:1. Every panel's look changes, so the owner's call | S | Low | — |
| **F204** | **3D terrain past the boundary.** The 3D fetches elevation for the boundary's box only, so on a hillside the ground past the fence is a level terrace. Fetch the scene's extent, padded, for the 3D window only | S–M | Low | P9 |
| **F214** | **The relationship web cannot be hovered or clicked.** It sits under the plants' canvas, which covers the map from the first plant on. Above the plants its lines would lie over them; routing its clicks through the map, as V3.11 did for the boundary, is the other road. The owner's call | S | Low | P5, P10 |
| **F219** | **A colour per species, as a third legend mode.** Set aside by the owner once the numbers could be seen (V3.11). Needs its own marker style (measured: about a dozen colours stay apart; today's marker is three quarters outline) | M | Low | P5 |

## Q · From the owner's answers to the V3.05 surface audit

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F206** | **A community's page, the rest.** The page beside the list shipped in V3.09–V3.11. Left (T9): two pages side by side, and editing a community from its page ([plan](plans/V3.09-community-page-and-features-scan.md)) | M | Med | P10, P13 |
| **F207** | **Buildings and trees from the map and the satellite together, the heavier steps.** *Scan this area* shipped in V3.10. Left (T6–T8): open building footprints, the satellite lined up automatically, buildings from the owner's own imagery; a licensing question about Esri pixels stands in front of T7 | L | High | P5, P11 |

## R · Updating an installed copy

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F229** | **One click on macOS.** Today the disk image opens and the person drags, replaces, quits and reopens. A helper that waits for the app to quit, swaps the bundle with a rollback and reopens it; today's steps when Applications is not writable. Try it on a real Mac before it ships | M | Med | — |
| **F230** | **An update with no Windows prompt.** One Yes per update remains because the program lives in Program Files. A per-user install removes it and the *Unknown publisher* prompt, but needs a move out of the old folder that pinned icons still point at. The owner's decision | M | Med | — |

## S · The homeowner's path (the V3.17 plan)

*The plan's code is finished; what is left is below, the owner's steps in the table at the top,
and its data jobs (F243, F246–F249) in group J.*

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F242** | **Finishing, the owner's steps.** Everything buildable shipped V3.18–V3.32 (licence, services, prereleases with a promote step, the guide, the runbook, pinned libraries). Left: the feedback mailbox, a second maintainer, and promoting a release | S | High (outside parties) | — |
| **F244** | **The Calgary edition** (ED-15): a second region pack, about a developer-week plus a local reviewer of about 230 species | L | Med (needs a reviewer) | P9 |
| **F245** | **The Regina edition** (ED-16): waits for the University of Regina herbarium on GBIF | L | High (data that does not exist yet) | P9 |
| **F250** | **Your yard month by month, as a picture**: what the design *looks like* each month ("your June is all yellow"), from the checked colours and the bloom periods. Design › Through the year (V3.55) says what flowers each month in words; the picture is not built | M | Low | P13, P4 |

## T · The owner's test run of V3.37 (the V3.38 plan)

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F255** | **The walk teaches one plant at a time, the last step.** Built V3.38–V3.39. Left: the owner's review of each walk's lead species (D7) | S | Low | P3, P5, P10 |
| **F256** | **The score and features in the walk.** Animals fed and the Habitat Value Score above the walk with their change; a bee hotel, brush pile, snag, leaf litter or bare ground added and pulled; structure points by what each does (D3), a headline change | M | Med | P6, P9 |
| **F258** | **Share › Present, kept or retired.** The narrated tour left the Learn window in V3.38; whether Share › Present stays is D4 (retiring it recommended; the script stays for the stills and the API) | S | Low | P5 |

## U · The 3D preview (the V3.43 plan)

*Six of the eight increments shipped (V3.43–V3.53). [The V3.43 plan](plans/V3.43-the-3d-preview-reviewed.md) is the handover.*

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F266** | **Big trees, full beds** (3D-7). Triangle budgets by crown size, herb bodies with leaf mass, detail levels that differ (D7). Blender | L | Med | P5, P13 |
| **F267** | **Runs on the laptop it is for** (3D-8). The software path where Chromium blocks the graphics driver (F211, the owner's yes), and detail chosen from the measured frame rate | M | Med | P5 |
| **F268** | **The plant models against photographs**, ongoing. All 250 Edmonton natives read and drawn from their own numbers (V3.48–V3.67: wildflowers, shrubs, trees, vines, grasses; mean score 5.86 after V3.67c). Left: the water plants' own bodies (the arrowheads, pond-lily, floating marsh-marigold), the horsetails, prickly-pear, cones and the clematis's seed heads, the jack pine at 4, and the 174 plants outside the Edmonton list, unread. The V3.62 and V3.67 plans' tables rank what is still wrong. Absorbed F115, F116 and F180 in V3.77 | L, ongoing | Low | P5, P13 |
| **F270** | **Who is eating here, by the animal's own season.** *Through the year* shipped in V3.55 and its animal photographs in V3.76; a month is still the plant's month, because only bees record a flight season | S | Med | P10 |

## V · A new tester (the V3.69 plan)

*Verbatim in [`USER_FEEDBACK.md`](USER_FEEDBACK.md); traced and ordered in
[the V3.69 plan](plans/V3.69-a-new-tester.md). Each section is planned before it is built.*

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F276** | **Existing trees you can trust**: installed builds have no rasterio, so the scan never reads the canopy-height map; correctable conifer or broadleaf, height and species; a read crown in 3D | M–L | Med (packaging) | P9 |
| **F277** | **The scan in seconds**: the region's buildings, treetops and slope shipped with its pack | L | Med (installer size, licences) | P8 |
| **F278** | **Sun and shade as one path**: existing features first, the steps in order, the time scrubber on the map, the arc tied to the shade. Extended in V3.77: existing buildings and trees under the Yard tab (*Already here*, D4), Site › Features retired, Sun & Shade's first line linking to it ([plan](plans/V3.77-slope-and-the-yard-from-use.md)) | M | Low | P5, P11 |
| **F279** | **Select everything, move everything**: a drag moves every selected kind, one undo step. Extended in V3.77: fences, walls, hedges and swales are in no selection path at all (click, box, Select All, drag, corners), and the map's notes are not selectable | S–M | Low | — |
| **F281** | **Water in the design**: water routed from the downspouts (placed since V3.76), runoff by the slope, a rain garden planted, not kept out | M | Med (local rules) | P1, P8 |
| **F282** | **The bee game, refined**: a short picker of the region's known pollinators with photos and cards, the viewer focused on start, the orbs explained. Also the 3D's pollinator list that typing cannot search (F89's last part). The animal photographs it waited on arrived in V3.76 | M | Low | P5 |
| **F283** | **The walk as a game in the simple app**: net, plant, smell | M | Low | P5, P13 |
| **F284** | **The years passing, in every view**: a play button on When and Season | S–M | Low | P4 |
| **F285** | **Words a beginner can act on**: a visible Advanced switch; Edible narrowed; Food for a fussy eater explained | S | Low (P12 on the records) | P12 |
| **F286** | **The first launch says it is working**: no (Not Responding) at start | S–M | Low (needs a Windows measurement) | — |
| **F287** | **The PDF report in colour, and adding up**: status words coloured, the planting map by type or species with a key, a total cost | S–M | Low | P13 |
| **F288** | **Structures you can believe**, part 2: the objects that stay objects rebuilt ([review](plans/V3.69-structures-and-shapes-reviewed.md); part 1 shipped V3.70). Added in V3.77: the owner's fire pit drawn as a shed, not reproduced (the real viewer draws it right); likeliest the placeholder box an unloaded model gets, in the Building's brown | M | Low | P9, P13 |

## W · The owner on the slope and the Yard tab (the V3.77 plan)

*Verbatim in [`USER_FEEDBACK.md`](USER_FEEDBACK.md); traced, with seven decisions, in
[the V3.77 plan](plans/V3.77-slope-and-the-yard-from-use.md).*

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F289** | **Slope you can read**: labels on every 5th line from round heights, inside the boundary or the ramp; the grid chosen by the elevation source and said, the *Slope grid* box gone (D1, D2) | S | Low | P9 |
| **F290** | **Several yard things at once**: Row, Grid, Circle and Fill area for objects and for areas placed as a rectangle or circle, at their size plus a gap, one undo step (D5) | M | Low | — |
| **F291** | **A path drawn as a line** at a width, stored as its strip | S–M | Low | — |
| **F292** | **The Yard tab finished**: an emoji for every kind (D7); lawn conversion retired into a bed's "lawn now" and *Wild ground to keep* (D3) | S–M | Med (P8) | P8 |
| **F293** | **The map's shade follows the design**: redrawn after every edit; objects cast at one height shared with the 3D; woody plants from 1 m; the design's own plants a switch (D6) | M | Med (the planner's shade cells) | P5, P9 |

---

## Where to start: the recommended order (V3.77)

The pick is the owner's. This is the recommendation, made in V3.77 from the state above. It
reads one fact first: installed copies are on **V3.68**, the last promoted release (25 November
2026, six downloads), so nothing since has reached anyone, and the user base is small enough that
watching a few people use the app is worth more than any feature.

**0. Decide.** The table at the top, answered on the
[decisions page](https://claude.ai/artifact/2bm9oj98vH8qGc3M4cR2cz), where each question carries
its context and a recommendation and the answers are saved for the next session to read.

**1. V3.78, the easy wins: the map tells the truth.** Each is small, its cause found, and most
were hit by the owner or a tester:

| Win | Row |
|---|---|
| The shade on screen redraws after placing a plant, object or line | F293's first part |
| Contour labels on screen and inside the boundary, on every 5th line; the *Slope grid* box gone | F289 |
| Fences, walls, hedges and swales caught by the selection box, Select All and Delete | F279's lines |
| An emoji for every Yard kind | F292's first half |
| The PDF's status words in colour and a total cost on *What to buy* | F287's part |
| An object's stand-in box no longer looks like a building | F288 (the fire pit) |
| The bee game takes the keyboard at once and says what the orbs are | F282's two small fixes |

**2. Promote a release**, after trying its installer on a real Windows machine: V3.76's first
build stopped at launch, and the tests in a session cannot open the real window.

**3. Watch three to five people use it** (F243): both outside testers found what nobody inside
could, mostly tools that exist and could not be found.

**4. V3.79, a site you can trust** (F276, F278, F293). Shade decides what goes where, and Plan My
Yard already swaps plants by it: the scan in installed copies (no rasterio, so no canopy-height
map), existing features first on the Yard tab, the map's shade showing the design. Measure Plan
My Yard's shade cells before and after. Packaging is the risk.

**5. V3.80, placing yard things** (F290, F291; F292's lawn half once D3 is answered).

**6. V3.81, water in the design** (F281): downspouts exist since V3.76; a rain garden planted,
water routed by the slope.

**7. 3D on the laptop it is for** (F267, before F266): on a machine whose graphics driver
Chromium blocks, the 3D shows only an error.

**Held back, on purpose:** more model polish (F268, F266) until F267; the designer's workflow
(F113, F93), written for professionals before the V3.17 turn to the Edmonton homeowner; the
Calgary edition (F244) until the sessions say Edmonton works.

The plans whose orders this draws on: [V3.77](plans/V3.77-slope-and-the-yard-from-use.md#a-suggested-order),
[V3.69](plans/V3.69-a-new-tester.md#recommended-order),
[V3.43](plans/V3.43-the-3d-preview-reviewed.md). The V3.17 homeowner-path plan is finished as
code; what it left is the owner's (the table at the top) and group J's data jobs.
