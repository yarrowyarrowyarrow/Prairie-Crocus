# Prairie Crocus — the backlog's archive

**What has left [`BACKLOG.md`](BACKLOG.md).** Every row that shipped, closed or was absorbed
into another, moved here **as it stood**, so the backlog itself lists only what is not yet
built. Split out in V3.77, on the owner's word that the backlog had become cumbersome: until
then shipped rows stayed in their tables, struck through, beside the open ones, and the file
carried the running totals of every release from V2.52 to V3.45 in one paragraph.

The reasoning behind each row is where it always was: [`ROADMAP_NEXT.md`](ROADMAP_NEXT.md)'s
ID ledger for F63 and up, [`PHILOSOPHY_ROADMAP.md`](PHILOSOPHY_ROADMAP.md) for F1–F62, and the
release plans under [`plans/`](plans/). **A row comes here when it ships**: add it under
*Shipped, by the group it was filed in*, with its version.

---

## Closed in the V3.77 rewrite

*Listed as open in the backlog, but finished, or one thing listed twice. Checked against the
ID ledger and the code on 27 November 2026.*

| Row | Why it closed |
|---|---|
| **F89** (group F) | What was left, the pollinator list typing cannot search, is the short picker of the region's pollinators in **F282** (V3.69): one row for one thing. |
| **F115** (group I) | Absorbed by **F268**: the shrubs are drawn from their own stems since V3.49, with a crown outline by species since V3.63 (`SHRUB_CROWN_SHAPES`). |
| **F116** (group I) | Absorbed by **F268**: fern fronds are drawn by their form since V3.67b (`03h-leafyforms.js`); the ostrich fern stays on F268's list. |
| **F180** (group O) | Absorbed by **F268** for the 250 Edmonton natives: grasses by their heads (V3.51), shrubs told apart (V3.63), a leaf colour for every native (V3.64), rosettes and tufts (V3.67b). The 174 plants outside the Edmonton list are unread, which F268's row says. |
| **F211** (group Q) | Taken into **F267** in V3.43 (the software path where Chromium blocks the driver). |
| **F234** (group S) | Complete: MD-1 to MD-3 and MD-5 in V3.21; MD-4 (*More detail* turns the Advanced tools on) with the Overview in V3.27 (`yard_overview_flow`). |
| **F237** (group S) | Complete: ED-1 to ED-5 and ED-11 in V3.24, ED-6 to ED-9 and ED-17 in V3.25, ED-10 in V3.26, ED-13 (`data/edition.json`, `data/fetched/` left out of the installer). ED-12 deferred and ED-14 cancelled in the plan. |
| **F238** (group S) | Complete as code: PR-1 to PR-4, PR-6, PR-9 in V3.26, PR-5 superseded. PR-7 and PR-8 are the data jobs F246 and F247, which stay open. The grades it added were taken off rows and pages in V3.58 (F273). |
| **F239** (group S) | Complete: OV-3 to OV-8 and OV-11 in V3.20; OV-1, OV-2, OV-9, OV-10, OV-12, OV-13 in V3.27. OV-14 was optional. |
| **F240** (group S) | Shipped in V3.29, as the row said. |
| **F241** (group S) | Complete on screen: WD-1 to WD-8 by V3.30. It left the word *pioneer* in 40 plants' free-text notes, which no screen shows (L8): a data job in group J. |
| **F254** (group T) | Complete: the tool in V3.38 (`scripts/make_example.py`), the owner's lot in V3.54 (F269). |
| **F264** (group U) | Shipped in V3.52. |
| **F265** (group U) | Shipped in V3.53. The owner's approval of the look from its sheet (D6) is in the backlog's owner table. |
| **F269** (group U) | Shipped in V3.54. Its question (is 399 plants and 680–1,400 first-year hours the right first impression) is in the backlog's owner table. |
| **F270** (group U) | Shipped in V3.55, and the animal photographs it waited on were fetched and folded in V3.76 (237 photographs). What is left, *who is eating here* by the animal's own season, stays open in group U. |
| **F280** (group V) | Complete across V3.71 to V3.76. |
| **Flower colour** (group J) | Done in V3.34: the owner answered all 343 flowering plants from photographs, recorded as `photo`. |
| **iNaturalist observation photos** (group J) | Built as F251's path in V3.35; every Edmonton native has photographs since V3.55. The 51 plants left without one are the photo job in group J. |
| **The last 46 uncited edges** (group J) | F128 shipped in V2.62; the 46 cannot be cited from GloBI. The life-stage thread it named is its own job in group J. |

### The rows as they stood

**F · Surface and sprawl**

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F89** | **The 3D preview's UX review.** Ten buttons over two rows, plus three sliders and two combos. V2.37 reordered row 2 and flipped the mouse buttons; the structural question is untouched. An honest retirement pass first. *(V3.05: the pass is in [`SURFACE_AUDIT.md`](SURFACE_AUDIT.md). Its sliders, 15 px wide at 1366 × 768, have their own row now: when, how you move, what you do. Left: Refresh from design is a manual sync; the creature list is the 721 rows typing cannot search, F196's other copy, waiting on the split `scene3d_window.py`'s ceiling asks for; the outputs' place; the light window.)* *(V3.08: the preview follows the design, its two outputs are on Share › Export as well, and the window is dark ([plan](plans/V3.08-design-and-share.md)). Left: the creature list.)* *(V3.43: the review counted the window again, sixteen controls in three rows; what is left of this row is F261's.)* *(V3.44: F261 shipped. A homeowner sees eight named controls in two rows; the other rows are the Advanced tools'. Left of this row: the pollinator list, 700 and more rows that typing cannot search, now an advanced tool that starts on an animal the design feeds.)* | S | Low | P5 |

**I · 3D fidelity leftovers**

| ID | Feature | Effort | Risk | Where it came from |
|----|---------|--------|------|---|
| **F115** | **Shrub aspect within a silhouette** — the within-class spread the herb and layer axes already got | M | Med — asset size | sprite audit |
| **F116** | **Fern density** | S | Low | sprite audit |

**J · Data work — startable today, no code required**

| Job | State, and the next step |
|---|---|
| **Flower colour** | *(Counts below are from V2.52. At V2.83, after V2.80 read 143 colours from a flora: **196 of 417** species are still `estimated`, 143 `flora`, 35 from the name or epithet, 43 blank.)* 359 species still carried a genus-level guess. 81 are grasses with no bloom colour and are excluded; of the 276 left, **110 sit in 25 genus groups sharing one hex** — the columbine bug's exact shape. `python scripts/colour_worklist.py --sheet colour-check.html` writes a contact sheet of the 199 that already have a photograph, worst group first, with the claimed colour as a swatch under each image. Two sittings. The 77 with no photograph need a flora, or a photo first |
| **iNaturalist observation photos** | The remaining lever for the 111 species with nothing: `/v1/observations?taxon_id=…&photo_license=…&quality_grade=research` for species whose taxon photo set is thin. Scoped in V2.36, not built. *(V3.34)* Measured: all 112 plants without a photo have three or more such observations, 109 have twelve or more; F251 builds it |
| **The last 46 uncited edges** | ✅ **F128 shipped in V2.62** — 2,406 of 2,452 GloBI edges now cite a named study, specimen collection or GBIF dataset, and the bibliography grew from 13 works to 46. The 46 that remain matched no observation record and no further fetch will change that; they still cite the aggregator, honestly. **Body part came back 0% across all 13,665 records**, so the sapsucker and mammal-browse edges V2.60 dropped are not recoverable from `/interaction` in any mode — a closed door rather than an open task. Life stage came back at 41%, which is a real shot at the 700 refused `larval_host` records and is not yet taken (**F128**) |

**O · Found by the 3D model audit (V2.87–V2.89)**

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F180** | **Telling species apart.** 80 grasses, sedges and rushes share three shapes; 51 rosette wildflowers look like one dark lettuce; the asters read as grass; 45 species on the smallest narrow-leaf variant read as bare stems. *(V2.96)* 40 of the 53 shrubs share one leaf green, the viewer's shrub default `#4f7a3a` (`scene_contract._FOLIAGE_BY_TYPE`): nothing records a shrub's leaf colour, and those shrubs are the darkest from a path. A colour per species needs a source per species, as F172's do. Ongoing: 10 to 20 species per sitting against reference photographs, on the tuning benches (`scripts/tune_morphology.py`). Shrub stretch is F115, fruit size F117, butterfly wing patterns F114 | L, ongoing | Low | P5, P13 |

**Q · From the owner's answers to the V3.05 surface audit**

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F211** | **3D on a machine whose graphics driver Chromium blocks.** QtWebEngine refuses WebGL on blocklisted drivers and the preview shows only its error message (V3.05 made that message plain). A software path, `--ignore-gpu-blocklist` or SwiftShader, would draw slowly rather than not at all; the owner said yes. The risk is a slow 3D view on a machine that should have used the hardware *(V3.43: part of F267.)* | M | Med | P5 |

**S · The homeowner's path (the V3.17 plan)**

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F234** | **Simple by default, advanced on request** (MD-1 to MD-5): one remembered switch that hides tools, never work. | M | Med (every guard runs in both modes) | P13 |
| **F237** | **The region pack** (ED-1 to ED-11, ED-13, ED-17): Edmonton as data, Calgary as a second folder; the score counts the Edmonton list (E5). | L | Med (touches twelve modules' nativity) | P9, P12 |
| **F238** | **Plants that lead** (PR-1 to PR-6, PR-9): ranked by impact and feasibility, best picks first. *PR-1 to PR-4, PR-6, PR-9 shipped V3.26; PR-7 and PR-8 are F246 and F247.* | L | Med (a ranking people will question) | P6, P13 |
| **F239** | **How your yard is doing** (OV-1 to OV-14): one overview, and the advanced pages made to agree. *OV-3 to OV-8 and OV-11 shipped V3.20; OV-1, OV-2, OV-9, OV-10, OV-12, OV-13 V3.27; OV-14 optional.* | L | Med | P5, P6, P9 |
| **F240** | **Plan My Yard** (PY-1 to PY-12): plants where the person drew, to a cover target, replace and try again. *PY-3, PY-5 shipped V3.18; PY-12 V3.27; PY-1, PY-2, PY-4, PY-9 to PY-11 V3.28; PY-6 to PY-8 V3.29: shipped.* | L | Med (the generator's tests) | P1, P13 |
| **F241** | **The words** (WD-1 to WD-8): one name for each thing, held by a test. *WD-4 V3.18, WD-6 V3.19, WD-1 V3.21, WD-3 and WD-8 V3.26, WD-7 V3.27, WD-2 and WD-5 V3.30.* | M | Low | P5 |

**T · The owner's test run of V3.37 (the V3.38 plan)**

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F254** | **The example yard, authored from a real design.** It opened on a downtown street, 19 plants covering 35% of an 88 m² rectangle. A tool turns a saved design into the pack's example; the lot is the owner's (D1). Planned V3.38 | M | Low | P2, P13 |

**U · The 3D preview, reviewed from real use (the V3.43 plan)**

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F264** | ✅ **V3.52**. **Plan My Yard reads the shade on the map** (3D-5): the planner trades a plant the house or a tree already there would shade out for a kind that takes the shade, where it stands, by the preview's own shade model. Review lot by the fifth summer: 14 lost, now 0. [Plan](plans/V3.52-a-plan-that-survives-its-preview.md) | M | Med | P9 |
| **F265** | ✅ **V3.53**, pending the owner's approval from its sheet (D6). **Light** (3D-6), takes F187. [Plan](plans/V3.53-light.md) | M | Med, every scene's look | P13 |
| **F269** | ✅ **V3.54**. **The example is the owner's lot.** [Plan](plans/V3.54-the-example-lot.md). Open: whether 399 plants and 680-1,400 first-year hours is the right first impression | S | Med | P13 |
| **F270** | **What is left of the Design tab's review (V3.55).** [Plan](plans/V3.55-the-year-and-who-it-feeds.md). The animal photo fetch on the owner's PC and its fold; *who is eating here* by the animal's own season (only bees record one; a month is the plant's) | S | Med | P10 |

**V · A new tester (the V3.69 plan)**

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| **F280** | **One way to put things on the map** ([plan](plans/V3.71-one-palette.md)): one table of kinds every reader asks; one palette of three verbs; old designs converted to what the map showed; a shed a building, a hedge real shrubs; path surfaces, decks, doors, downspouts, mulch rings. Five increments, V3.71 to V3.75; the first (one table) ✅ V3.71, the second (the Yard palette, conversion on open) ✅ V3.72, the third (the drawn kinds in 3D) ✅ V3.73, the fourth (hedges you can plant, solid fences' shade) ✅ V3.74, then the Yard tab tidied and the hedge made an existing one ✅ V3.75, and doors, downspouts, spigots and mulch rings ✅ V3.76: **complete**. | L | Med (file format) | P2, P9, P10 |

---

## Closed by the owner's answers (V3.77)

*Rows whose only open part was a decision, closed when the owner answered the
[decisions page](https://claude.ai/artifact/2bm9oj98vH8qGc3M4cR2cz) on 27 November 2026. The
answers to the rest are carried on their rows in the backlog.*

| Row | Answer |
|---|---|
| **F189 "Native Prairie Aromatics" and P12** (group J) | **Keep it as authored.** The owner's call under P12, made with the four plants' standing as Indigenous medicines and the grouping's shape in front of them. Nothing changes in the data |

| Job | What is left |
|---|---|
| **F189 "Native Prairie Aromatics" and P12** | Four of its seven are widely known on the prairies as Indigenous medicines; whether the grouping sits inside P12's hard rule is the owner's call. Left exactly as authored |

---

## Shipped, by the group it was filed in

### A · Confidence and provenance

> **✅ Shipped in V2.53** — F8, F12, F13, F14 and F28 together, over one shared
> vocabulary (`src/confidence.py`). Plan:
> [`V2.53-the-confidence-block`](plans/V2.53-the-confidence-block.md). One row
> survives, because the increment found a contradiction it deliberately did not
> resolve.

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| ~~**F124**~~ | ✅ **Shipped in V2.60.** The layer map knew six of the catalogue's eleven `plant_type` values, so 311 of 437 species — `wildflower` alone is 210 — occupied no vegetation layer and a prairie meadow scored 0 of 15. Now complete and **height-aware**, because filing all 292 herbaceous-group species under one layer would have reached 3 of 15 and called it fixed; the 0.30 m groundcover boundary is read off the catalogue's own `groundcover` type. The meadow reaches 6 of 15. **The residual is bigger than the fix and is now F129** | S | Done | P6, P2 |
| ~~**F129**~~ | ✅ **Shipped in V2.65.** The layer component's denominator is now the **reference community's own layers**, not the five-layer forest-garden stack. `reference_ecosystem`'s specs were already honest (Mixedgrass Prairie and Wet Meadow declare no canopy genera) and `reference_fidelity` already dropped zero-count layers, so the fix reuses that judgement rather than copying it — a test reads the source to prove it. A prairie planting on prairie: 6.0 → **10.0 / 15**. The same planting in Aspen Parkland **drops to 3.8**, which is the point: a measurement that could only raise the number would be a compliment. The 12 callers that pass no ecoregion are unmoved, and the panel row names its basis | M | Done | P6, P2, P9 |
| ~~**F120**~~ | ✅ **Shipped in V2.65.** 117 contradictions by the time it was taken. The first pass proposed 101 species and was wrong: reading the relationship alone let a bumblebee, a grasshopper, a gall midge, a horntail and a **deer mouse** vote. 107 of 346 `larval_host` edges are not lepidoptera, and `host_plant` is what drives design_critic's butterfly/moth line — so `_TAG_BACKED_BY_EDGE` now names the taxon that has to be at the far end, and the gate and the fixer read the one table. **80 real corrections**: `host_plant` 30 → 95, `bird_food` 78 → 104, worked example **+7 points**. Additive only — absence of an edge is absence of evidence (P9) | S | Done | P9, P3 |

### B · WANT and SHOW — the argument the app doesn't make

*The app argues superbly that a native yard is ecologically valuable. Nobody
converts a lawn on ecological grounds alone, and nobody's spouse, neighbour or
HOA does. Principle 13 exists to name this.*

**✅ F76 and F75 shipped in V2.56** — before / after / in five years as one page,
and the cues-to-care checker. Plan:
[`V2.56-the-argument-never-made`](plans/V2.56-the-argument-never-made.md).
F77 (the neighbour's-eye view) shipped in V2.33 as the `sidewalk` camera preset.
One row survived, a bug the increment found rather than a feature it declined
to build, and it shipped in V3.05.

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| ~~**F123**~~ | ✅ **Shipped in V3.05.** The 3D window keeps the last still it renders on the main window (`scene3d_window.keep_still`, as `before_after_flow` keeps F76's) and Export PDF passes it, so F69's page reaches the PDF; its status line says so. A new or opened design drops the last one's still and before/after, so one design's render cannot reach another's PDF | — | Done | — |

### F · Surface and sprawl

*Six side tabs, roughly twenty sub-tabs, three inner tabs under Plants, ten
buttons on the 3D toolbar. (V3.05 counted them from the real window: 6 tabs, 26
pages, 169 controls, 18 in the 3D window; [`SURFACE_AUDIT.md`](SURFACE_AUDIT.md).)
Every one was justified when it landed. Together they
are why a novice cannot find the thing they need and a designer cannot get to a
deliverable quickly. There is precedent for fixing this well: the Forage tab was
retired in V2.25 once Planning → Wildlife covered the same question, and nothing
was lost.*

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| ~~**F94**~~ | ✅ **Shipped in V3.07–V3.08.** The retirement pass came first, as this row asked ([`SURFACE_AUDIT.md`](SURFACE_AUDIT.md), V3.05), then the owner's decision on every page, then the restructure: five side tabs by the question a person brings (Site, Placement, Design, Share, Learn), Planning merged away, one Share place for what leaves the app, and every jump to a page made by the page, not its index (`src/side_panel_layout.py`; [plan](plans/V3.07-placement-and-the-site-tab.md), [plan](plans/V3.08-design-and-share.md)) | L | High | P5 |

### G · Notes, and going outside

*P11 (the body and the site know things the screen does not) is the principle
this app has always been thinnest on in practice.*

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| ~~**F32**~~ | ✅ **Shipped in V3.05.** Site › Field Notes › *Print this sheet…* prints the ten site-walk prompts in walking order on one page, each with a box to tick, what is already noted, and ruled lines to write on, then three lines for anything else; the ruling spaces itself to fill the page (`field_notes.walk_sheet`, `pdf_export.export_field_sheet`). The design PDF carries the same page as its first job, before Site prep. It was the last unbuilt item in the ACT/OUTPUT stage | — | Done | — |

### H · Depth and relationships

*Connoisseur depth. Ranked here by cost, cheapest first, because several got much
cheaper when F7 landed and nobody has re-read them since.*

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| ~~**F19**~~ | ✅ **Shipped in V3.05.** The cell the generator chose is read back in words (`placement_score.explain_cell_for_plant`: "Full sun, as it likes", "…not its best: the closest fit left", slope, edge, a tree's drip line), and every other placing rule names itself (`src/why_here.py`: a vine at its host's foot, a mixed stand, a community, the design review's additions, the pond), carried on the plant's feature as `why_here` and shown first on its page: 108 of 108 plants in a probe design, from 71 of 102 when only scored cells said. **A click on a placed plant now opens that page**: the map had always sent the click, and nothing in Python listened. With no terrain or shade for the site the page says the plants were only spread out. Hand-placed plants carry none. Left: the 3D preview's card is per species and a reason is per plant, so it does not show there | — | Done | — |

### J · Data work — startable today, no code required

*The bottleneck on several features above is data, not engineering. These are the
jobs that move it, with the tooling that already exists.*

| Job | State, and the next step |
|---|---|
| ~~**Name the 1,194 held animals**~~ | ✅ **Shipped across V2.63 (F127) and V2.64 (F130).** The naming question was answered by the author — *scientific name only for those without a common name* — and it unblocked everything: **998 animals admitted, 820 written in V2.64 alone**, fauna 167 → **1,147**, edges 2,813 → **7,714**, coverage 275 → **302 of 437**. 101 of the last 820 have an accepted English name and **719 keep their binomial**, which for a solitary bee is the name rather than a shortfall. What is still held is 120 species I could not place and 42 trinomials the catalogue cannot key on — neither is waiting on a decision. **The unfinished thread is elsewhere**: 18 admitted animals get no row because every one of their records is an adult nectaring observation GloBI files as `eatenBy`, and F128's 41% life-stage data is the untaken route to the ~700 refused `larval_host` edges behind them |
| ~~**Re-derive the ranges without the buffer**~~ | ✅ **Shipped V2.76.** Re-fetched from GBIF 2026-08-21 and derived by containment. Records 489,546 → **361,447**; region rows 4,215 → **3,643**; species with rows 422 → **420**. `--buffer-artefacts` put the error at **493 of 4,218 claims (11.7%)** and, more usefully, showed it was **concentrated in one region**: `western_continental_ranges` is the BC interior ranges clipped to a hairline inside Alberta (0.02% of the mapped area, 36× smaller than Northern Continental Divide), so its five-kilometre apron swept in nearly every montane record near the border — **135 species → 15**. Interior regions barely moved (Cypress Upland 231 → 228, Selwyn Lake Upland 10 → 8), which is what a boundary fix should look like. Two species lost every row (*Panicum virgatum* at 3 records, *Symphyotrichum campestre* at 6) and now band `unknown` rather than `unlikely`, because under-collected and absent are indistinguishable below the floor. The point cache means the next such question costs no network |
| ~~**Ask VASCAN about nativity and names**~~ | ✅ **Shipped in V2.80** (F137/F144/F149). The API could not be asked usefully, so the checklist was read from VASCAN's Darwin Core Archive instead; every one of 417 rows now carries `native_provinces_source = 'flora'`. Plans: [`V2.80-the-inference-gets-a-source`](plans/V2.80-the-inference-gets-a-source.md), [`V2.80-the-names-were-the-problem`](plans/V2.80-the-names-were-the-problem.md) |
| ~~**Merge the synonym duplicates**~~ | ✅ **Shipped across V2.80 and V2.82.** The Stiff Goldenrod pair was resolved by the archive (`KNOWN_NATIVITY_CONFLICTS` is empty), *Achillea millefolium* merged into *A. borealis*, and V2.82 merged five more pairs VASCAN showed to be one taxon (422 → 417). `validate_accepted_names` now fails the gate on a new one |
| ~~**Publish the occurrence points**~~ | ✅ **Shipped in V2.80 as F147**: 171,896 marks over 426 species, herbarium specimens and field observations as separate layers with a no-JavaScript toggle, CC-BY-NC admitted for a coordinate but not for a photograph on the author's V2.79 reasoning. Plan: [`V2.80-only-facts-backed-by-data`](plans/V2.80-only-facts-backed-by-data.md) |
| ~~**Promote the seven staged trees (F161)**~~ | ✅ **Done in V2.87** by the author's VASCAN and GBIF runs; all seven promoted, two widened to AB, SK. Plan: [`V2.87-the-trees-arrive`](plans/V2.87-the-trees-arrive.md) |
| ~~**Black Hawthorn's thorns (F167)**~~ | ✅ **Done in V2.87, closed in V3.05.** The row arrived with `has_thorns` set when F161 promoted it; the kid-safe filter leaves it out (checked: 375 kid-safe plants, no Black Hawthorn). The row stayed open here two releases after it was true |
| ~~**The five '1?' nativity flags (F199)**~~ | ✅ **Shipped in V3.05** (schema 92): the five are 1, and `data_quality.NATIVE_TO_ALBERTA` no longer allows '1?', so a native-only generated design includes them. *The row as it stood:* `native_to_alberta` still carries the seed's '1?' on False Box, Flat-topped White Aster, Round-leaved Alumroot, Stiff Sunflower and Tall Anemone, all five recorded in Alberta by VASCAN. The pickers read `native_province` since V3.00 and show them; the generator, its critic, the design goals and the API still filter on the flag (`native_only`), so a native-only design leaves them out. Set the five to 1 in `plants_master.json`, bump the schema, and `data_quality.NATIVE_TO_ALBERTA` can stop allowing '1?'. Found by V3.00 |
| ~~**The Edmonton review (F220)**~~ | ✅ **Done in V3.13.** The owner answered all 108 species on the [review page](https://claude.ai/artifact/VPeWXtdA1FFRD1n67MyNSg), yes or no with no reasons: 59 yes, 49 no, none left out. `derive_local_flora.py --merge` folded them in, and the list went from 193 to 250 species. The page stays the record: change an answer there and fold in again. Plan: [`V3.13-the-edmonton-answers`](plans/V3.13-the-edmonton-answers.md) |
| ~~**Peace River Parkland**~~ | ✅ **Arrived with the survey in V2.67**, as an Alberta natural subregion of Peace Lowland rather than as a hand-added polygon — which is why it was right to hold it in V2.51: drawing one more shape would have put a *guess* where a published boundary was available, in a layer that decides what real properties get recommended. Selectable in the filter since V2.68, along with the other 20 subregions |
| ~~**Real CEC ecoregion polygons**~~ | ✅ **Shipped in V2.66–V2.68.** `tools/ecoregions/` is a six-stage pipeline (fetch → inspect → harmonize → validate → render → export) and the layer is the **National Ecological Framework v2.2** rather than CEC: 24 ecoregions in 6 ecozones clipped to Alberta and Saskatchewan, with Alberta's 21 natural subregions joined **spatially, never by name**. Two of the three sources refuse a proxied session, so the author ran those stages. Adoption cost almost no code because V2.38 made the polygon file the vocabulary — but it did expose that `lookup_ecoregions` had never handled MultiPolygon, answering *you are in no ecoregion* rather than raising. The heuristic `ab_ecoregion` tags were re-derived by measured overlap in V2.68, and three of the six old regions turned out misplaced rather than coarse |

### M · Found by the V2.83 review

*A review of the code and the published site in V2.83. The catalogue work of
V2.66–V2.82 held up; these are the places where it is not reaching the people it
is for, or is wrong in a way a reader can see. Reasoning per row in the
`ROADMAP_NEXT.md` ledger; evidence in
[`plans/V2.83-the-work-was-not-reaching-anyone`](plans/V2.83-the-work-was-not-reaching-anyone.md).*

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| ~~**F158**~~ | ✅ **Released 24 Sep as V2.83** (`release-V2.83`), so an install from 25 Aug is offered it by Help → Check for Updates. Plan: [`V2.83-the-work-was-not-reaching-anyone`](plans/V2.83-the-work-was-not-reaching-anyone.md) | — | Done | — |
| ~~**F153**~~ | ✅ **Shipped in V2.84.** 43 rows to `other_insect`, the mapping fixed, `validate_bee_taxon` in the gate. Plan: [`V2.84-a-wasp-is-not-a-bee`](plans/V2.84-a-wasp-is-not-a-bee.md) | — | Done | — |
| ~~**F156**~~ | ✅ **Shipped in V2.84**, and reaches readers when the site is republished (F157). Plan: [`V2.84-a-wasp-is-not-a-bee`](plans/V2.84-a-wasp-is-not-a-bee.md) | — | Done | — |
| ~~**F154**~~ | ✅ **Shipped in V2.85.** Province-aware nativity, locality ranking from the 0.25° grid (`src/site_fit.py`), communities and repairs under the same rules. Plan: [`V2.85-recommend-for-the-yard`](plans/V2.85-recommend-for-the-yard.md) | — | Done | — |
| ~~**F155**~~ | ✅ **Shipped in V2.85.** 4–21 → 64–121 plants on a 216 m² yard, more species, no single species above a quarter. Plan: [`V2.85-recommend-for-the-yard`](plans/V2.85-recommend-for-the-yard.md) | — | Done | — |

### N · Found by answering the Bur Oak question (V2.86)

*Which native trees can do what Bur Oak does, for Alberta and for small yards. The answer was a group of genera; asking it found four things wrong. Reasoning in [`plans/V2.86-trees-for-where-the-oak-is-not`](plans/V2.86-trees-for-where-the-oak-is-not.md). The data rows it opened (F161, F165, F167) are in J.*

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| ~~**F162**~~ | ✅ **Shipped in V2.86.** Birch and oak join the keystone genera; `KEYSTONE_GENERA` gated both ways; schema v87 | — | Done | — |
| ~~**F163**~~ | ✅ **Shipped in V2.86.** A tree taller than the lot is wide is too big for it. Calgary's yard 64 → 119 plants once its Lodgepole Pine went | — | Done | — |
| ~~**F164**~~ | ✅ **Shipped in V2.86.** "Burr Oak" finds Bur Oak, desktop and website | — | Done | — |

### O · Found by the 3D model audit (V2.87–V2.89)

*Every plant and animal the 3D preview draws, rendered through the real viewer and
checked against the species: 424 plants and 1,144 animals
([report](https://claude.ai/artifact/4DxfwtbLxQsLHWMdUkELXD), summarised in the
sixth pass of [`SPRITE_AUDIT.md`](SPRITE_AUDIT.md)). Batch A, the code fixes,
shipped in V2.88 ([plan](plans/V2.88-reading-what-was-recorded.md)). These are the
batches that need a new model, a data decision or a flora. The audit's advice on
size: **one family per increment**, smallest first (horsetails, then the pond, then
succulents), because 5 to 20 species is what one contact sheet can show clearly.
F172's corrections can ride along with whichever increment touches those species.
V2.89 shipped the climbers and the horsetails ([plan](plans/V2.89-climbers-and-horsetails.md)) and found F181 and F182 on the way.
V2.90 shipped the pond and F181 ([plan](plans/V2.90-vines-find-hosts-and-the-pond.md)) and found F183.
V2.91 shipped F182 and F183 ([plan](plans/V2.91-additions-find-open-ground.md)) and found F184; F185 is the pond rule V2.90 left open, numbered.
V2.92 shipped F178, the trees ([plan](plans/V2.92-trees-with-their-own-shape.md)), and found F186.
V2.93 shipped F177, the succulents and cacti ([plan](plans/V2.93-succulents-and-cacti.md)).
V2.94 shipped F186, the dark crowns ([plan](plans/V2.94-leaves-let-light-through.md)), and found F187 and F188.
V2.95 shipped F185, water plants in the pond ([plan](plans/V2.95-water-plants-go-in-the-pond.md)).
V2.96 shipped F188, the shrubs' shade ([plan](plans/V2.96-shrubs-show-their-shade.md)).
V2.97 shipped F174, the birds' bodies and where they stand ([plan](plans/V2.97-birds-with-their-own-bodies.md)).*

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| ~~**F174**~~ | ✅ **Shipped in V2.97.** Nine bird builds, each authored with its wings at its birds' real span and a folded pair shown at rest, picked by genus (`src/bird_body_plan.py`). **Every bird had been drawn about 2.4 times its length**, not only the twelve: the viewer sets a model's width to the wingspan and the old wings were paddles (robin 52 → 22 cm, crane three metres long → standing 1.07 m). Hawks and owls sit on a tall tree's top, a hawk soars over a young design, an owl with no tree is not drawn; grouse and cranes walk on the ground; the goose and duck float on a pond. Left: one span-to-length ratio per build draws long- and short-tailed birds 14-25% off (F119); the ptarmigans' range (F190); bird colours (F172); no dove build (no plant edge, never drawn) | — | Done | — |
| ~~**F175**~~ | ✅ **Shipped in V2.90.** Each wetland plant drawn by its own body from its recorded habit (`src/pond_habit.py`): floating leaves on a pond's water, submerged plants showing only what reaches the surface, broad leaves on stalks, mare's-tail's whorled stems. Four submerged plants and Water Parsnip recorded correctly | — | Done | — |
| ~~**F176**~~ | ✅ **Shipped in V2.89.** Horsetails drawn as jointed stems from a new `jointed` growth form: whorled, whorled above, or plain banded rods with a pointed tip. The two grass plumes they wore are gone | — | Done | — |
| ~~**F177**~~ | ✅ **Shipped in V2.93.** Each succulent drawn by its own body (`src/succulent_habit.py`, `24-succulents.js`): the prickly pears as chains of spiny pads with their flowers on the rims, the ball cactus as a cluster of spiny globes, soapweed yucca as blue-grey rosettes of sword leaves sending up flower stalks in their season, roseroot as leafy stems, and the stonecrop, which the audit had passed, as flowering stems over a mat. New growth forms `pads` and `globose` (schema v91) | — | Done | — |
| ~~**F178**~~ | ✅ **Shipped in V2.92.** Ten trees with models of their own at their species' proportions: the elm's vase, box elder's several trunks and three-leaflet leaves, both cottonwoods, Peach-leaved Willow, the juniper as a cone foliated to the ground, water birch and Bebb's willow as clumps of stems, and pines with whorls, a crooked trunk and dead stubs instead of bottle brushes. Black Spruce stays White Spruce's model (P9: nothing recorded tells them apart) | — | Done | — |
| ~~**F179**~~ | ✅ **Shipped in V2.89.** The owner's rule: a vine climbs the tree or shrub whose footprint touches its own, and with none it lies on the ground, 30 cm at most. Decided once in Python (`src/vine_habit.py`) and fitted to the host's drawn crown | — | Done | — |
| ~~**F181**~~ | ✅ **Shipped in V2.90.** The generator seats each vine at the base of a tree or shrub it planted, on the sunny side, and with none says so in the design notes (the owner's option c) | — | Done | — |
| ~~**F182**~~ | ✅ **Shipped in V2.91.** A grass, sedge or rush is never pollinator forage, bloom period or not (the owner's rule), in both forage calendars: the docent's and Planning → Wildlife. The docent's season beat, which had never played because its callers pass no bloom data, now does | — | Done | — |
| ~~**F183**~~ | ✅ **Shipped in V2.91.** What the design review adds goes in open ground, read from the plants actually placed (`src/open_ground.py`): free ground by the main pass's spacing, the ground that suits the plant, beside the planting; a vine at a shrub's foot. Never a plant that needs standing water; an animal fed only by such plants gets a note instead | — | Done | — |
| ~~**F185**~~ | ✅ **Shipped in V2.95.** A plant that needs standing water goes in a pond or is not placed (`src/pond_planting.py`): floating and submerged plants in the open water, emergents in the shallows of the north two-thirds of the shore, floating leaves on at most half the water; with no pond they are left out and named. A pond the design left bare is planted, the pond communities are seated in the pond, and the wildlife and goal top-ups use it. **In the app the generated pond had never reached the map at all**: the controller copied only plants, so generated structures now come too | — | Done | — |
| ~~**F186**~~ | ✅ **Shipped in V2.94.** Leaves let light through: a leaf seen from its shaded side takes the sun and sky falling on its far side, times the share a leaf passes (0.55 for broad leaves, 0.45 for herbs, 0.3 for needles), and the baked shade now falls on the sky, with only 30% of it on the sun. The crown bake stands on the ground, not on the crown's lowest leaf. Over the 20 trees from 1.6 m, near-black 57% → 38%; Trembling Aspen 39% → 2%. The evergreen conifers improve least: dark recorded colours, opaque needles and the shade between tiers, with the weak ground bounce (F187) adding a little | — | Done | — |
| ~~**F187**~~ | ✅ **Shipped in V3.53 with F265.** **The ground bounce is a seventh of what it should be.** A surface facing down is lit only by the hemisphere light's ground colour, `0x5d6e51` at 0.9 (0.13 in luminance). The viewer's own noon sun and sky, falling on the ground it draws, would reflect about 0.9. It keeps a spruce's tier undersides, trunks, walls and animals' bellies dark on their shaded side. It is not the main reason the evergreen conifers are still 45-74% near-black from a path after V2.94: two brighter ground colours were tried and the conifers gained only 0.02-0.03 in luma, where their dark recorded colours, opaque needles and the real shade between tiers weigh more. **A look for the whole viewer, so the owner's call**: every scene changes *(V3.43: the owner asked for the look to improve; this is part of F265, approved from a before/after sheet.)* | S | Med — every scene's look | P13 |
| ~~**F188**~~ | ✅ **Shipped in V2.96.** The shrub layer asked for its leaf material without saying its geometry carries colours, which reads as no, so no shrub had drawn its baked shade or Stylised's gradient. Turned on, the old bake put 35% of a shrub's pixels near-black from a path; the eight shrub models are rebaked with the trees' `CROWN_AO`. Over the 53 shrubs from 1.6 m, near-black 19% → 25%, still brighter than the trees; from above the shade between leaf clusters rises 19%. Every `surfaceMaterial` call must now state the argument | — | Done | — |
| ~~**F190**~~ | ✅ **Shipped in V3.37** ([plan](plans/V3.37-animals-recorded-near-the-yard.md)). Each animal is *here*, *stray*, *elsewhere* or *unrecorded* for a region pack (`src/fauna_fit.py`), from its GBIF records within the pack's circle against what its province records predict for its group; absence counts only past ten expected, or in a group recorded 1,000+ times an animal near the place (birds), so 464 of 1,144 read *unknown* and stay drawn (P9). The 3D preview draws no stray or elsewhere animal: 365 of 400 simulated Edmonton designs drew one, ptarmigans in 23; none do. The Overview names only an animal recorded near the yard. Left: "recorded as food for N kinds" still counts every animal (the owner's call), six sets of fauna rows that are one species | — | Done | — |

### P · Found by the V2.98 review of picking and placing

*The app run on a virtual display (1440 × 900 and 1366 × 768, Arial-metric fonts,
the example design) and its accessibility tree read through AT-SPI, to answer the
owner's "it seems somewhat crowded and somewhat inaccessible". The review proposed
six steps in order, numbered here **F191–F196** so "step 3" and "F193" are one
thing; the owner chose step 3 first. Its report lives outside the repo, so the
findings each step answers are summarised in its row. V2.98 shipped F193
([plan](plans/V2.98-placing-moves-to-the-map.md)), V2.99 F191
([plan](plans/V2.99-looking-is-not-placing.md)), V3.00 F192 ([plan](plans/V3.00-one-picker-one-species-page.md)),
V3.01 F194 ([plan](plans/V3.01-filters-people-can-read.md)), V3.02 F195's keyboard and screen-reader half ([plan](plans/V3.02-keyboard-and-screen-reader.md)), V3.03 its visual half ([plan](plans/V3.03-what-can-be-seen.md)), V3.04 F197 ([plan](plans/V3.04-start-screen-filters-and-the-slope.md)), V3.05 F196, F198 and F200 ([plan](plans/V3.05-every-surface-counted.md)).*

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| ~~**F191**~~ | ✅ **Shipped in V2.99.** Selecting only looks: it names the plant on a Place button under the list, or shows the community, and leaves the map alone. Measured on V2.98, a click, ▶, an arrow key and keyboard focus arriving in either list each armed the map. A Place action arms it (the button, Enter, a double-click, the context menu, which communities gained), and **once placing, choosing another plant switches to it**, so the V2.37 tester's "the last thing" still cannot be placed; a drag into the mix and ▶ do not switch. The map shows a footprint under the cursor: the plant, a Qty cluster as it will land, a pattern's first plant, a community's members at their offsets. Found on the way: a built mix rode along on any plant's Row/Grid/Circle and was planted instead; the pattern preview's rings had a 0.5 m floor, twice a forb's placed marker. Left: warnings after placing on other plants or over the boundary (F198); a keyboard way to put a plant down (F195) | — | Done | — |
| ~~**F192**~~ | ✅ **Shipped in V3.00.** Browse, the Plant Directory and the community builder are one picker (`plant_picker.py`) over one vocabulary (`plant_filters.py`): nine facets and nine qualities, the Directory's five role toggles folded into Role because they ran the same query. **The painted card is gone**: a plant's page, the Directory's widget page moved out of its window, opens beside the Browse list over the map's right edge on a click or an arrow, with Place and Add to mix; placing closes it. Each row badge has its own tooltip and a row reads its facts to a screen reader. The order is **Recorded near this site** when there is a pin (renamed from the review's "suits this site", which nothing here can know), then zone, pond plants last. The Directory's page can place when a design is open. Found on the way: the Native filter dropped five species VASCAN records in Alberta (F199), "Animals supported" had always sorted A–Z, and the page counted relationships as species (Boreal Yarrow 334, 296 animals). Left: Native follows Alberta wherever the pin is (F200) | — | Done | — |
| ~~**F193**~~ | ✅ **Shipped in V2.98.** A bar over the map while placing holds the pattern settings of both tabs and says what the next click does; it goes when placing stops, Esc in the map included, which Python could not see before: after Esc, one click on empty map planted a whole community outside the yard. The panels scroll instead of squeezing. Found and fixed on the way: community spacing did nothing for Row/Grid/Circle (16 communities in a 4.65 m row), a re-arm could fire after Esc, the spacing armed was the previous community's. Left: the habitat score live in Stats but behind Calculate in Analysis, the third bullet of the finding this step answered, which is not placing | — | Done | — |
| ~~**F194**~~ | ✅ **Shipped in V3.01.** A chosen filter reads its dimension and joins its values by its own rule ("Type: Tree or Shrub", "Role: Bird Food and Larval Host"), and each list opens on a line saying how ticked values combine, because Role keeps plants with *every* role and the rest keep plants with *any*. What is on is a row of chips, each removing its own filter, with Clear all; an empty result names the restriction that emptied it and offers to remove it, with the count that would bring back. The stale "● Shrub" had a cause: the wheel over a closed box, ↓, or Return in its list made Shrub the combo's current item, whose icon Qt draws and whose name Qt writes back when its tick changes; the combo now keeps no current item, the wheel scrolls the panel, and ↑, ↓ and Space open the list. The site's soil pH (hides 105 of 424 at pH 8.0) is a chip and a toggle, removable for the session, and leaves with the site, which it never had. Whether it should filter at all is the owner's call, raised; its ranges' provenance is F201 | M | Low | P9 |
| ~~**F195**~~ | ✅ **Shipped in V3.02 and V3.03.** *Keyboard and screen reader* (V3.02, [plan](plans/V3.02-keyboard-and-screen-reader.md)): focus visible everywhere, the map usable by keyboard, F6 between the map and the panel, the single letters scoped to the map, every control named, and Redo's Ctrl+Shift+Z, which never worked, fixed. *What can be seen* (V3.03, [plan](plans/V3.03-what-can-be-seen.md)): no text under 12 px (190 font sizes in the source, Plant Communities and Field Notes 90% under it), one muted grey at 5.5:1 for the four that failed, every control at least 24 px by one raise-only rule (`target_size.py`), and **plants coloured by type everywhere**: community members had been by layer until a reopen and the builder had five greens of its own. Each marker is outlined in its colour darkened 60% (grass 1.0:1 on the yard → 4.9:1; members on a canopy 1.0–1.8:1 → 4.5–6.7:1 on screen), and the legend is built from the markers' table: all eleven types, where it had six and no wildflower, and no "Community outline", which nothing drew (F202). Found on the way: Leaflet drew a sub-metre plant up to 44% out of round, and missed clicks on its top and bottom; every circle is round now. Also found: **an unticked checkbox's box was invisible** (1.11:1 under Fusion, 20 boxes on the window under 3:1), now drawn by one style (`indicator_style.py`, 6.3:1); and in DejaVu Sans, CI's font, Field Notes and Plant Communities scrolled sideways, now wrapping. Left: the edges of fields and buttons (F203), the satellite basemap, display scaling and high-contrast modes | — | Done | — |
| ~~**F196**~~ | ✅ **Shipped in V3.05.** Each community's row says its size, sun and moisture beside its name ("8 plants · Full Sun · Mesic"), a value left out when it is Unknown or Mixed; "For a creature…" has a find box that narrows its 721 rows and picks the first match (the Monarch was entry 446); the builder's Cancel asks before discarding a community laid out by hand, and closes at once when nothing was. Left: the sorts behind "No grouping" and "Sort: A–Z", and the builder's raw offsets and fixed-size dots | — | Done | — |
| ~~**F197**~~ | ✅ **Shipped in V3.04.** The start screen's Continue, Open a design, See a finished design and Recover waited for `map_ready`, which fires once per page load and had usually fired before anyone chose (traced in V2.98: ready at 1.92 s, Continue at 25.87 s, never loaded). The map now says whether it has loaded (`MapWidget.is_ready`) and a choice made after that is carried out at once, framed again when the map is first shown (`fitWhenShown`), since a map hidden behind the start screen is 0 × 0 | — | — | — |
| ~~**F198**~~ | ✅ **Shipped in V3.05.** The bar over the map says where each placement landed, with Undo beside it: "2 of 4 landed outside the boundary.", "It sits inside Blue Grama Grass's circle." (`src/landing_check.py`; inside means one plant's centre in the other's circle, half its spacing). It never refuses, since overlap is sometimes the design; it says nothing when the ground was clear, and nothing about a boundary when none is drawn. An undo clears it. Left: a tint on the markers that overlap | — | Done | — |
| ~~**F200**~~ | ✅ **Shipped in V3.05.** Native, the row badge and the Native toggle's tooltip follow the pin's province (`site_fit.province_at`): a Saskatoon yard's list keeps Saskatchewan's natives, as the generator beside it has since V2.85. No pin, or a pin outside the two provinces, keeps Alberta, as before | — | Done | — |

### Q · From the owner's answers to the V3.05 surface audit

*The owner answered every page and question in [`SURFACE_AUDIT.md`](SURFACE_AUDIT.md)
on 2 October 2026. Most answers are moves inside F94 (the side panel), F89 (the 3D
preview) and F86 (notes); the asks that are features of their own are numbered here.
V3.07 enacted the first half of F94 ([plan](plans/V3.07-placement-and-the-site-tab.md));
V3.08 its merges, F89's answers, F209 and F210 ([plan](plans/V3.08-design-and-share.md)),
and opened F212; V3.09 is planned for F206, F207, F208 and F211.*

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| ~~F208~~ | ~~**Field Study beyond a five-question quiz.**~~ ✅ **Shipped V3.40** ([plan](plans/V3.40-field-study-by-topic.md)): topics in three groups, a choice of plants and of length, best scores per topic. | M | Med | P5, P7 |
| ~~**F209**~~ | ✅ **Shipped in V3.08.** Every primary button is the app's green: three were not (Sun & Shade's orange, Wind's teal and blue; the audit's purple had gone by then), and Refresh wind data is grey now the pin brings the rose. The 3D preview and Growth Snapshots wear the app's stylesheet (`ui_style.WINDOW_STYLE`), and a test fails on any button filled in a colour of its own | S | Low | P13 |
| ~~**F210**~~ | ✅ **Shipped in V3.08.** Nineteen opening paragraphs cut to what the page cannot say by itself, 3,487 characters to 2,103: lists the page shows anyway, restated headings, advice and slogans went; anything a person needs to act stayed | M | Low | P2 |

### T · The owner's test run of V3.37 (the V3.38 plan)

*The owner used V3.37 as a first-time user would and sent what got in the way:
the example yard, the guide link and the Learn side. The evidence, the order and
the owner's decisions are in the [V3.38 plan](plans/V3.38-the-learn-side-and-the-example.md).*

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| ~~**F253**~~ | ✅ **Shipped in V3.38.** Help › How to Plan Your Yard opens `data/guide.md` in a window, offline; the README's five steps are held equal to it by a test | S | Low | P13 |

### U · The 3D preview, reviewed from real use (the V3.43 plan)

*The owner asked for a review of the 3D preview by actually testing a design, and a plan to make it a
useful, realistic and inspiring picture. A planned 15 x 37 m lot through the real viewer, 50 pictures:
the plants had years of care and the yard round them (house, ground, street, light, camera, timeline)
almost none. Fifteen findings, eight increments, nine decisions, all in the
[V3.43 plan](plans/V3.43-the-3d-preview-reviewed.md), which is the handover: start there. It lifts the G4 freeze.*

| ID | Feature | Effort | Risk | P |
|----|---------|--------|------|---|
| ~~**F260**~~ | ✅ **Shipped in V3.43** (3D-1). Buildings solid, the camera on the yard, a street view at the real frontage, Walk past the house, year 0 as *fully grown*, short-lived plants as fewer plants, animals only on plants that stand, fruit at 3 to 16 cm, a frame-rate readout (Ctrl+Shift+F), and a gate that renders a whole yard | — | Done | — |
| ~~**F261**~~ | ✅ **Shipped in V3.44** (3D-2, [plan](plans/V3.44-getting-to-3d.md)). *See it in 3D* on the plan strip and the Overview's street item without the Advanced tools switch (M2, D1); two short rows with named moments and viewpoints, the rest behind the switch; opens on the fifth summer in July from the street (D5); a view from the house; sliders that keep up; card text at 12 px | — | Done | — |
| ~~**F262**~~ | ✅ **Shipped in V3.45** (3D-3, [plan](plans/V3.45-your-yard-not-a-green-field.md)). Every drawn area, hedge and fence reaches the 3D scene; lawn inside the outline and pale ground outside it (D3); the street where its side is known; houses with a roof inside their recorded height | — | Done | — |
| ~~**F263**~~ | ✅ **Shipped in V3.46** (3D-4, [plan](plans/V3.46-a-timeline-you-can-believe.md)). The season is decided once from the region's frost dates and drawn by one viewer chunk: herbs a hand high in April and dry stems from October through the snow, every deciduous woody plant bare alike (shrubs never were), a dormant meadow tawny instead of olive. The losses are said where and which (`scene.timeline_notes`, a button in the picture with a list and rings on the ground), and what shades them is the shade model's own answer. **Asking it found the model wrong twice**: a building was a circle out to its farthest corner with every plant inside it "under" it, and a wildflower shaded like a spruce all year. Both put right: the review lot's losses by the fifth summer went from 136 to 14 | M–L | Med | P4, P5, P9 |

---

## Retired from the open lists

*Carried here once, so the next reader does not go looking for them. Each was
listed as open somewhere and is not.*

| ID | Why it is closed |
|----|---|
| **F77** · the neighbour's-eye view | **Shipped V2.33.** `src/presentation_still.py` declares `CAMERA_PRESETS = ("overview", "orbit", "walk", "sidewalk")` and names it as F77 in a comment; the camera is in `html/scene3d/08-modes.js` |
| **F62** · aspect axis on layer archetypes | **Shipped V2.33 as F65** (renumbered on the way in) |
| **F60** · blade-class axis on tree archetypes | **Absorbed by F64**, shipped V2.33 |
| **F20** · maintenance-over-time curve | Delivered in substance by **F42** — `maintenance_calendar` ships 36–76 → 18–38 → 9–19 → 6–11 hours a year, with a test that fails if the curve ever flattens. Only a chart is missing, and it belongs inside F42 rather than as its own card |
| **F33** · seasonal observation journal | **Subsumed by F73 + F86.** A dated photograph tied to a placed plant is a better journal entry than a timestamped string, and F86 owns the unification |
| **F15** · pollinator-pathway overlay · **F30** · invisible-relationship legend | **Merged into F5**, which shipped in V2.31 with a legend and a filter row. A month scrubber on that overlay is the remaining cheap follow-on |
| **F31** · glossary page | **Folded into F45.** In-context definitions beat a separate page — but note the *Site Info tooltips* half in Group E is genuinely unbuilt |
| **F34** · shearing-layers data audit | **Retired as a feature.** It is a data-quality check and belongs as an assertion in `src/data_quality.py` |
| **F39** · sensor integration hooks | **Dropped until a user asks.** Speculative IoT, external dependency, no evidence of demand, unchanged on the list for a very long time |
| **F212** · the address search reaches Saskatchewan | **Set aside by the owner in V3.16**: "I want the app to be edmonton focused." The row had the cause wrong as well. The search has covered Saskatchewan since V2.14 (`property_data.geocode_address`); only its words say Alberta. What bounds it is the view bias: a box about 50 km either side of the map's centre, with `bounded=1`, so a search reaches about 50 km from where the map is looking, which from Edmonton is the metropolitan region. Not checked live (the session's network refused Nominatim), [plan](plans/V3.16-the-version-in-the-title.md) |

---

## The state of the argument (as written in V2.52, last touched in V3.05)

The roadmap's own list of *what this app is not good at yet* has five entries.
Since it was written, **two and a half have been paid down**:

| Weakness | State |
|---|---|
| "It looks like a diagram" | **Largely fixed** — V2.33/34/36 (surfaces, aspect axes, florets, seed heads, fauna morphology) |
| "Its photographs don't show the plant" | **Barely moved.** 111 of 434 plants have none and 62 of 69 bees have none — but `plant_photos.json` shipped as a literal `[]` until V2.62, and **the first habit shot in the catalogue is now in it**. Group C |
| "It never argues that a native yard is beautiful" | **Paid down** — V2.56 (F76 before/after/five years, F75 cues to care) |
| "It has no professional workflow" | **Half built** — V2.57 (F92 the order file, F91 substitution). F113 and F93 remain |
| "It sprawls" | **Unbuilt.** Group F |

That observation had a companion, and it is worth recording that it stopped
being true: through V2.51 the note here read *"the design side proper has not
had an increment since V2.42."* V2.56 and V2.57 were both design-side, which is
why two of the five moved at once.

What is left is lopsided rather than long. **Photographs** are gated on a
licensing decision only the owner can make (Group C), **sprawl** is an L-effort
restructure (Group F), and the two remaining professional-workflow walls are
both bigger than the two that fell. The cheap work now is not in these five at
all — it is the bugs the increments keep finding while building other things,
each of which is small and each of which is waiting on a decision rather than
on engineering. F124 shipped in V2.60 and produced F129; F129 and F120 both
shipped in V2.65 and F120 produced its own correction (the taxon requirement)
before it landed. **F123 is what is left of that seam.** The measured bugs are
a renewable resource, because measuring one exposes the next. *(F123 shipped in
V3.05.)*

---

## The totals, as they were kept from V2.52 to V3.45

**Totals (at V3.29, with the homeowner-path plan): 57 code features · 20 data jobs · 4 legacy-ledger items.**
*(V2.52: 41. Shipped since: F8/F12/F13/F14/F28 in V2.53, F121 in V2.54, F122 and
F104 in V2.55, F76 and F75 in V2.56, F92 and F91 in V2.57, F125 in V2.59, F124
and F127a in V2.60, F128 in V2.62, F127/F130 in V2.63–V2.64, **F120/F129/F131 in
V2.65**. Opened since: F120, F123, F124 — all three found by the increments
themselves — plus F126 from author feedback, F127/F128, which are the two
halves of F125 that its own gates refused to guess at, F129, which F124
exposed the moment it was fixed, and F131, which F128's own re-fetch made
possible two increments after it landed. **V2.83**: the VASCAN, synonym-merge and
occurrence-point data jobs had shipped in V2.80–V2.82 without leaving this file,
and six rows opened from the V2.83 review, F153–F158, as group M. The totals were
recounted from the rows rather than adjusted. **V2.84**: F153, F156 and F158 shipped,
F159 opened. **V2.85**: F154 and F155 shipped, F160 opened. **V2.86**: F162–F164 shipped; F161 staged and waiting on the author's VASCAN run; F165–F167 opened. **V2.87**: F161 shipped; F168–F171 opened. **V2.88**: nine opened by the 3D model audit, F172–F180 in group O, all counted as code features; F117 gained the fruit-size finding and F119 narrowed to birds and mammals. **V2.89**: F176 and F179 shipped; F181 and F182 opened, both found by that work; F172 gained the Wild Clematis flower. **V2.90**: F175 and F181 shipped; F183 opened, found by that work; F172 gained buckbean's leaf size. **V2.91**: F182 and F183 shipped; F184 opened, found by that work, and F185 numbered, the pond rule V2.90 left open. **V2.92**: F178 shipped; F186 opened, found by that work. **V2.93**: F177 shipped; F172 gained Roseroot's flower colour. **V2.94**: F186 shipped; F187 and F188 opened, both found by that work. **V2.95**: F185 shipped; F189 opened as a data job; F172 gained Spiked Water-milfoil's name. **V2.96**: F188 shipped; F180 gained the shrubs' shared leaf green. **V2.97**: F174 shipped; F190 opened, found by that work; F119 gained the birds' body length. **V2.98**: the review of picking and placing numbered its six steps F191–F196 and the start-screen race F197, as group P; F193 shipped, so six opened. **V2.99**: F191 shipped, on the owner's call, since it reversed V2.37; F198 opened, the half of the review's finding 10 no step answered. **V3.00**: F192 shipped, which took F194's "suits this site" order and its one filter set with it; F199 opened as a data job and F200 as a feature, both found by that work. **V3.01**: F194 shipped; F201 opened as a data job, found by that work. **V3.02**: F195's keyboard and screen-reader half shipped and its row narrowed to what can be seen, so the total is unchanged. **V3.03**: F195 shipped, its visual half, with a fix found on the way (Leaflet drew small plants as ellipses); F202 and F203 opened, both found by that work. **V3.04**: F197 shipped, with two fixes the owner reported (a filter list needing a second click to close, and the 3D preview on a slope); F204 opened, found by the second. **V3.05**: F19, F32, F123, F196, F198, F199 and F200 shipped, bundled with the retirement pass F94 and F89 asked for first ([`SURFACE_AUDIT.md`](SURFACE_AUDIT.md)), which leaves both open for the owner's decisions; F167 was found already done (its row arrived with `has_thorns` set when F161 promoted it in V2.87) and closed. Nothing opened: what the audit left is in its own page. **V3.06**: F205, the north arrow and scale bar, opened and shipped together on the owner's request, so the totals do not move. **V3.07**: the owner answered the audit; the first half of F94 shipped and it stays open, and the answers that are features of their own opened as F206–F211, group Q. **V3.08**: F94 shipped, its second half (Design's merges, Notes on one page, a Share place, Planning merged away), with F209 and F210; F89 narrowed to the 3D preview's creature list and F86 to its one store; F212 opened, found by that work. **V3.09–V3.11**: the simple versions of F206 (V3.09, tidied in V3.11) and F207 (V3.10) shipped; both rows stay open for their heavier steps, so the totals do not move. **V3.11**: F213, the boundary that could not be pressed once a plant was on the map, opened and shipped together; F214, the relationship web under the same canvas, opened, found by that work. Then F215–F217 on the owner's asks, opened and shipped together, so the totals do not move: a measurement in the design (undo, the selection box, saving), the boundary's Corner Handles switch, and a legend that names only what is drawn, boundaries Simple or Named and plants by Type or numbered Species. Then F218 on the owner's report, opened and shipped together: the species numbers seen at every zoom. F219 opened, a colour per species, which the owner set aside as possibly a third legend mode. **V3.12**: F220–F222 opened and shipped together on the owner's ask, so the code-feature total does not move; two data jobs opened, both F220's: the owner's review of the 108 species the Edmonton rule cannot settle, and the specimen labels that would settle much of it by data. **V3.13**: the Edmonton review done, all 108 answered and folded in (one data job closed) **V3.14**: F223–F226 opened and shipped together on the owner's asks, so the code-feature total does not move (a filter's second click, communities filed by where their plants are recorded, the filters in two tiers, availability re-ranked and favoured); one data job opened, F227, the owner's review of the availability tiers. **V3.15**: F228, one click updates an installed Windows copy, opened and shipped together on the owner's ask; F229 and F230 opened, the two steps it left as decisions (one click on macOS, an update with no Windows prompt), as group R. **V3.16**: F231, the version in the title bar, opened and shipped together on the owner's ask for a release to test V3.15's updater with, so it moves nothing; F212 retired on the owner's call ("I want the app to be edmonton focused"), so 50 → 49. **V3.17**: F232, the app's own icon in place of PyInstaller's, opened and shipped together on the owner's ask, so the totals do not move. Then, docs only, the homeowner-path plan ([`homeowner/`](homeowner/README.md)) opened F233–F249 as group S: twelve code features (F233–F242, F244, F245) and five data jobs (F243, F246–F249), so 49 → 61 and 15 → 20. **V3.18**: the plan's increment 1 shipped, parts of F233, F235, F236, F240, F241 and F242 (FN-1 pulled forward from increment 14), and F171's row half; none closes, so the totals do not move. **V3.19**: the plan's increment 2 shipped, the other fifteen quick fixes, so F233 closes (61 → 60), and WD-6 of F241. **V3.20**: increment 3 shipped, OV-3 to OV-8 and OV-11 of F239; it stays open for the overview itself, so the totals do not move. **V3.21**: increment 4 shipped, F234 but for MD-4 (which needs the overview) and WD-1 of F241; neither closes. **V3.22**: increment 5 shipped, the deletions, so F235 closes (60 → 59). **V3.23**: increment 6 shipped, the front door, so F236 closes (59 → 58). **V3.24**: increment 7 shipped, ED-1 to ED-5 and ED-11 of F237; it stays open for increment 8. **V3.25**: increment 8 shipped, ED-6 to ED-9 and ED-17 of F237, which stays open for ED-10; F227's mechanism shipped (levels from the nurseries' stock and a review page to fill them) and it stays open for its data, so the totals do not move. **V3.26–V3.28**: increments 9 to 11 shipped parts of F238, F239 and F240, none closing. **V3.29**: increment 12 shipped PY-6 to PY-8, so F240 closes (58 → 57). **V3.30**: increment 13 shipped WD-2 and WD-5 of F241; WD-6's seed-data half stays, so it stays open. **V3.31**: increment 14 shipped most of F242 (FN-2 to FN-6, FN-8, FN-11, FN-12); it stays open for the runbook and the release of increment 15. **V3.32**: increment 15's buildable half shipped (the runbook, the pinned libraries, the session notes and a pre-flight test that added Swap to the plant page); F242 and F243 stay open for the owner's steps: five sessions, a second maintainer, the promotion. **V3.33**: the owner chose five next (colours, animals, photos, the year by month, updates without the admin prompt); F250 opened for the year by month, and the colour review shipped as tooling, F172 staying open until the answers are in. **V3.34–V3.37**: F251 opened (V3.34) and its path built (V3.35); the animals' count (V3.36) and rule (V3.37) shipped F190; F252, existing features in Sun & Shade, opened and shipped together on the owner's ask (V3.37), so it moves nothing. **V3.38**: the owner's test run of V3.37 opened F253–F256 and F258 as group T (five code features) and F257 (a data job), and answered F208's open question; F253 shipped in the same increment, so four open. **V3.43**: the owner's review of the 3D preview opened F260–F267 as group U, eight code features, and F260 shipped in the same increment; F187 and F211 are taken into F265 and F267, and what is left of F89 into F261. **V3.44**: F261 shipped, the second of the eight (the door, the two short rows, the opening view); nothing opened. **V3.45**: F262 shipped, the third (the ground, the lines, the street, the roofs); nothing opened. The totals above are V3.29's and have not been recounted since.)*

---

## Recommendations, as they were written (V2.65, V2.83, V3.17)

**The V3.17 homeowner-path plan's order**, if the owner wants to finish rather than add: its [increments](homeowner/11-work-plan.md#3-the-increments), trust fixes first (F233, shipped V3.19), then the simple app (F234–F236), the region (F237), the three new things the homeowner sees (F238–F240), the words (F241) and finishing (F242–F243). It supersedes the V2.83 order below for that goal.

**The V2.83 review's order**, which puts delivery ahead of features: **F158** (release, so
installs get what has shipped) → **F157** (a site build that keeps its analytics and feedback
form) → **F153** (wasps out of bees) → **F156** (the site on a phone) → **F154** then **F155**
(recommendations fitted to the yard, and designs that fill it). Group M says why for each.

The list below is the V2.65-era recommendation, kept as it was written.

The pick is the owner's. Asked for one, in order:

1. **F123 — the presentation still never reaches the PDF.** The last of the
   measured-bug seam: F120 and F129 both shipped in V2.65, so the score now
   tells the truth about hosts, bird food and structure. F123 is a wire that
   was never connected — `still_pixmap` is computed and never passed — which
   makes it the cheapest remaining thing that a user can see.
2. **Group D — F113 (design variants) or F93 (reusable palettes).** Two walls of
   the professional workflow are down; these are the two left, and both are
   bigger than what shipped.
3. **Group F — the sprawl.** Named as a weakness, and the 3D toolbar's size
   ceiling has now shaped three increments running, which is the guard telling
   you something the backlog already says.

*(Group A's confidence block shipped in V2.53, Group B in V2.56, and half of
Group D and Group E besides. The pattern this file was written to expose —
"next" meaning "not this time, again" — is broken.)*
