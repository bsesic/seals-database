# Proposed ontology from the literature — seals & bullae (Southern Levant, Iron II–Persian)

A SKOS-style controlled-vocabulary proposal for **(A) the finds** and **(B) the
excavation / find-context**, aligned with the SSSL/CSSL corpus and Keel's
typology, derived from the source PDFs. It is meant to inform changes to the
Django `catalog` app (`backend/catalog/models.py`) and the planned RDF/LOD layer.

## Sources read (and short-codes used below)

| Code | Source |
|---|---|
| **[SSSL-FS]** | *SSSL factsheet 2.2* (CSSL project factsheet, Feb 2020) |
| **[SSSL-IR]** | *SSSL interim report* (SNSF Scientific Interim Report 2020–2021, ed. Uehlinger) |
| **[Ueh-1998]** | Uehlinger, *Westsemitisch beschriftete Stempelsiegel: ein Corpus und neue Fragen*, Biblica 79 (1998) 103–119 — review of Avigad & Sass, *WSS* |
| **[Keel-2005]** | Keel & Münger, "The Stamp Seal Amulets", in *Ashdod VI* (2005) |
| **[Keel-2011]** | Keel, "New Glyptic Evidence in Relation to Some Biblical Concepts", Eretz-Israel 30 (2011) |
| **[Keel-2012]** | Keel, "A Scarab from the Western Wall Plaza Excavations, Jerusalem", ʿAtiqot 72 (2012) |
| **[Ussishkin]** | Ussishkin, "A Synopsis of the Stratigraphical, Chronological and Historical Issues", *Lachish* Vol. I ch. 3 |
| **[Streit-2022]** | Streit & Höflmayer, "Tel Lakhish (Tel Lachish)", *Hadashot Arkheologiyot* 134 (2022) |

> **Note on missing files.** The three chapter PDFs
> `10.1515_9781575066530-007/008/009.pdf` are **not present** on disk — the only
> `10.1515` file in the literature folder is `10.1515_9783110487442.pdf` (a
> different De Gruyter volume, 143 MB), which was not part of this request.
> Those three chapters are therefore **not** reflected below; re-run with the
> correct paths if they are needed.

---

## 1. Find ontology

The find record in CSSL "still follows the schema of Keel's corpus entries" but
was deliberately enlarged **[SSSL-IR §2.2]**. The CSSL FileMaker entry
(Appendix 2 screenshot) is organised into these panels, which are effectively
the top-level groups of the find ontology:

> **Object · Manufacture · Base · Description · Dating · Context · Collection ·
> Bibliography**, plus media (Raw/Processed/Final images), **Comparanda**,
> **Reviews** and **Administration** (editorial workflow). **[SSSL-IR App. 2]**

Keel documents every seal in **three photographic views (Basis / Seite /
Rücken = base / side / back) and three interpretive line-drawings**
**[Ueh-1998 n.16; SSSL-IR App. 1]**. Two methodological rules from SSSL must be
baked into the ontology:

1. **Strict separation of *description* and *interpretation*** of the base
   engraving, especially iconography **[SSSL-IR §2.2]**.
2. **Strict adherence to the relative date of the find-context**, with enhanced
   granularity of the archaeological data (incl. associated finds)
   **[SSSL-IR §2.2]** — see §2.

Every category below is proposed as a **SKOS `ConceptScheme`** with explicit
`skos:broader`/`skos:narrower` parent→child hierarchies.

### 1.1 `scheme:object-type` — object / artefact type

The core object typology (Keel 1995a §-glossary = *OBO.SA* 10, the authoritative
reference cited throughout as `§NNN`) **[Keel-2005 n.1; Keel-2012]**.

```
Object type (skos:ConceptScheme)
├─ Stamp seal
│  ├─ Scarab                      [Keel-2005; Keel-2012]
│  ├─ Scaraboid                   [Keel-2005 no.6; Keel-2011]
│  ├─ Cowroid  (e.g. "Type III")  [Keel-2005 no.9, §403]
│  ├─ Conoid                      [Keel-2011]
│  ├─ Plaque (rectangular, domed-top §229; circular plaque) [Keel-2005 §229; Keel-2011]
│  ├─ Hammer-shaped / "duck" and other figural seals          [Keel-2011]
│  ├─ Signet ring / ring          [SSSL-IR, Tucci: "focus on signet-rings"]
│  └─ Amulet base / figural amulet (e.g. figurine base)        [Keel-2005 no.14, §394f]
├─ Cylinder seal                  [Keel-2011; Ussishkin (haematite cylinder, Cyprus)]
├─ Seal impression (sealing)
│  ├─ Bulla (clay sealing)        [Keel-2011]
│  └─ Jar-handle impression       → see §1.6
└─ Monumental inscription         [project scope: project-overview]
```

> **Change vs our model:** we currently have a coarse `Artefact.category`
> enum (`ObjectCategory`) **and** a flat `ObjectType` controlled term. Keep the
> coarse enum for faceting, but make `ObjectType` **hierarchical** (add
> `broader`) so the tree above can be expressed.

### 1.2 `scheme:seal-morphology` — scarab/scaraboid morphology (NEW)

For scarabs the chronologically diagnostic classification of **head / back /
side** follows **Tufnell 1984: 31–38** (codes such as `A1/I/?`, `B6/vIIv/?`,
`D4/vIv/?`, `B2/0/e9`, "Class D3 trapezoidal") **[Keel-2005 n.1; Keel-2012]**.
Beetle anatomy terms appear throughout: *clypeus, head, pronotum, elytra,
humeral callosities, lunate head* **[Keel-2012; Keel-2011]**.

```
Seal morphology (NEW scheme)
├─ Head type   (Tufnell 1984 code set)
├─ Back type   (Tufnell 1984 code set; e.g. pronotum/elytra rendering)
└─ Side type   (Tufnell 1984 code set)
```

This is **missing entirely** from our model and should be a dedicated
sub-typing (either three controlled-vocab fields on a scarab, or a structured
`SealMorphology` record). It is the single most "chronologically diagnostic"
feature when head/back/side views survive **[Keel-2005 intro]**.

### 1.3 `scheme:material` — material

```
Material
├─ Stone
│  ├─ Steatite / enstatite (often "baked steatite")   [Keel-2005; Keel-2012 §386–390]
│  ├─ Limestone                                        [Keel-2005 no.7; Keel-2011]
│  ├─ Serpentinite                                     [Keel-2011]
│  ├─ Carnelian                                         [Keel-2005 no.6]
│  ├─ Haematite                                         [Keel-2005 no.13; Ussishkin]
│  └─ (other hardstones)
├─ Faience                                              [Keel-2005 no.3, no.8, §394f]
├─ Glass                                                [Ussishkin, Level VII finds]
├─ Egyptian blue / composite
├─ Metal (bronze ring-mounts, gold)                     [Keel-2011; Keel-2012 "gold leaf"]
├─ Bone / ivory                                         [SSSL-IR "Iron Age II bone seals"; Keel-2005 §403]
└─ Clay (for bullae / sealings)                         [Keel-2011; Keel-2005 "mud sealing" §294]
```

Related sub-vocabularies needed alongside material (SSSL standardised these):

- **`scheme:surface-treatment` / glaze** — e.g. "baked steatite with red-brown
  glaze", "traces of glazing" **[Keel-2012; SSSL-IR App.1 "traces of glazing"]**.
- **`scheme:colour`** — SSSL explicitly standardised colours **[SSSL-IR §2.2]**.

> **Change vs our model:** `Material` is flat — add `broader` so steatite ⊂
> stone, etc. Add a `surface_treatment`/`glaze` vocab and a `colour` field.

### 1.4 `scheme:manufacture` — manufacture / technique / mounting (NEW)

SSSL added typologies "not only for the stamp seals proper but also for
**mounting devices, engraving techniques** etc." **[SSSL-IR §2.2]**.

```
Engraving technique
├─ Hollowed-out engraving                               [Keel-2005; Keel-2012 §328–334]
├─ Linear engraving                                     [Keel-2005 no.4, no.10]
├─ Hatched / with hatching                              [Keel-2005 no.1; Keel-2011]
├─ Cross-hatched                                        [Keel-2005 no.7]
└─ Drilled

Mounting device
├─ Perforated (longitudinal perforation)                [Keel-2005]
├─ Metal ring-mount (bronze/silver)                     [Keel-2011 "remains of a bronze ring"]
├─ Gold-leaf mount                                      [Keel-2012; Keel-2011 fig.6]
└─ Unmounted

Base layout / design-field
├─ Horizontally arranged                                [Keel-2005 passim]
├─ Vertically arranged                                  [Keel-2005]
└─ Register division (e.g. two registers)

Borderline / frame type  (Keel 1995a §190f)
├─ No borderline                                        [Keel-2005 no.1, no.6]
├─ Oval line border
└─ Barred / strand-rope border (§190f)                  [Keel-2005 no.9]
```

These are **missing** from our model and are precisely the fields SSSL calls
out as enlargements of Keel's schema.

### 1.5 `scheme:iconographic-motif` — iconography

SSSL introduced **"iconographic keywords" and a consistent iconographic
terminology / taxonomy** **[SSSL-IR §2.2]**. Motifs are cited by Keel 1995a §
and should map to those. A hierarchy (which we already support on
`IconographicMotif.broader`) grouping constituents under scenes/figures:

```
Iconographic motif
├─ Deities / divine figures
│  ├─ Amun / Amun-Re (ram-headed; with ʿAtef crown)     [Keel-2005 no.3,5,11, §585; Keel-2012 §642]
│  ├─ Baal-Seth / storm-god (winged, flanked by uraei)  [Keel-2011; §126]
│  ├─ Ptah, Maʿat, Hathor (Hathor-sistrum)              [Keel-2005 no.9]
│  └─ Anthropomorphic worshipper / seated figure        [Keel-2011]
├─ Hybrid / composite beings
│  ├─ Sphinx (human-faced; ram-headed)                  [Keel-2005 no.5,7, §544–552]
│  ├─ Cherub (lion body + human head + vulture wings)   [Keel-2011]
│  ├─ Griffin
│  └─ Uraeus / winged uraeus (= Seraph)                 [Keel-2005 no.9,12; Keel-2011]
├─ Animals
│  ├─ Lion / recumbent lioness                          [Keel-2005 no.1; Keel-2012]
│  ├─ Bull / bovine (bull-worship)                      [Keel-2011]
│  ├─ Crocodile                                          [Keel-2005 no.1]
│  ├─ Falcon, waterfowl, caprid, etc.
│  └─ Scarab beetle (as motif)
├─ Symbols / emblems
│  ├─ Winged sun-disc                                   [Keel-2011]
│  ├─ Sun-disc, moon crescent
│  ├─ Empty throne / cherubim-throne                    [Keel-2011]
│  ├─ Sacred tree / branch                              [Keel-2011]
│  └─ ʿAnkh, nfr, nb, and other hieroglyphic emblems
├─ Egyptian formulae / "pseudo-script"
│  ├─ ʿnrʾ-type (anra) formula (§469f)                  [Keel-2005 no.10, §469f]
│  ├─ ḥtp-R(ʿ) / offering formula                       [Keel-2005 no.10]
│  ├─ Throne-names / royal cartouches (e.g. Ramesses IV)[Keel-2005 no.4]
│  └─ ḫpr + nb + nfr groups                             [Keel-2005 no.12, §516]
└─ Geometric / floral
   ├─ Concentric circles                                [Keel-2012 jar-handle]
   ├─ Scroll / spiral, cross, rosette
   └─ Floral (lotus, palmette)
```

Two ontology implications:

- **Hieroglyphic signs** should be recordable by **Gardiner sign-list code**
  (e.g. `O49`, `R4`, `D21`, `N35`, `S3`, `D17`, `U21`) **[Keel-2005 n.1;
  Keel-2012]** — either a dedicated `scheme:gardiner-sign` vocab or a tag space.
- The **description vs interpretation** separation **[SSSL-IR §2.2]** means a
  motif link should carry whether it is an observed constituent or an
  interpreted identification.

### 1.6 `scheme:jar-stamp-type` — jar-handle / administrative stamp impressions (NEW)

A Judahite/Yehud administrative-stamp typology (SSSL module C2/D1, Koch &
Lipschits "Stamped-Jars from Judah") **[SSSL-IR §3.1, publ. list #13]**; Keel
§313 notes *Jehud* impressions appear only late (end 5th c.) **[Ueh-1998 n.5]**:

```
Jar-stamp impression type
├─ lmlk ("belonging to the king") — Iron IIB, late 8th c.
│  ├─ Two-winged emblem (sun-disc)
│  ├─ Four-winged emblem (scarab)
│  └─ Place-name legend: Hebron / Socoh / Ziph / mmšt
├─ "Private" stamp impressions (l + personal name) — associated with lmlk
├─ Incised concentric-circle handles — post-lmlk                [Keel-2012]
├─ Rosette impressions — Iron IIC, late 7th c.
├─ Lion impressions — Neo-Babylonian / early Persian, 6th c.
└─ Yehud (yhd / yhwd) impressions — Persian–early Hellenistic
   └─ Lipschits–Vanderhooft types (early / middle / late groups)  [Ueh-1998 n.5 = Keel §313]
```

This whole class is **missing** from our model (only a coarse
`jar_handle_impression` category exists) and needs its own hierarchical vocab.

### 1.7 `scheme:script` and `scheme:language` — for inscribed seals

The standard reference is **Avigad & Sass, *Corpus of West Semitic Stamp Seals*
(WSS, 1997)**, 1217 entries, the "unentbehrliche Standardreferenz" for inscribed
NW-Semitic seals of Iron Age II–III **[Ueh-1998]**. WSS classifies by "national"
script groups; Keel/Uehlinger stress that these are **script traditions, not
languages**, and that the labels are debated **[Ueh-1998 pp.108–110]**:

```
Script (WSS "national" groups + the debate)
├─ Northwest Semitic (alphabetic)
│  ├─ Hebrew (Israelite / Judahite)          WSS 1–711   (58.4%)   [Ueh-1998 n.20]
│  ├─ Phoenician                             WSS 712–749 (3.1%)
│  ├─ Aramaic                                WSS 750–856 (8.8%)
│  ├─ Ammonite                               WSS 857–1005 (12.2%)
│  ├─ Moabite                                WSS 1006–1047 (3.5%)
│  ├─ Edomite                                WSS 1048–1057 (1%)
│  ├─ Philistine (possibly)                  WSS 1065–1069 (0.4%)  [Ueh-1998 n.21, Herr 1978]
│  └─ "South Palestinian script" (Herr's umbrella term)           [Ueh-1998 p.109]
├─ Mixed / ambiguous groups (Mischgruppen)   [Ueh-1998 p.109]
│  ├─ Hebrew–Phoenician, Hebrew–Aramaic, Hebrew–Ammonite
│  ├─ Moabite-or-Edomite, Phoenician-or-Aramaic(-or-Ammonite), Aramaic-or-Ammonite
│  └─ Undefined / unassigned                 WSS 1120–1189
├─ Egyptian hieroglyphic / pseudo-hieroglyphic                     [Keel-2005; Keel-2012]
└─ Anepigraphic (no script)                  [Ueh-1998: Buchanan & Moorey, Ashmolean III]
```

```
Language (kept distinct from script)       [Ueh-1998: "Schrift ≠ Sprache"]
├─ Hebrew · Phoenician · Aramaic · Ammonite · Moabite · Edomite
├─ Egyptian
└─ Unknown / none
```

> **Change vs our model:** `ScriptType` and `Language` are flat — add `broader`,
> add the mixed/undefined concepts, and keep script and language as **separate**
> axes (our model already splits them, which matches the literature). Add an
> **authenticity** axis (below) — WSS devotes a whole rubric to "questionable
> and forged seals" (WSS 1195–1215) because most inscribed seals come from the
> antiquities market, not excavations **[Ueh-1998 pp.104, 108]**.

### 1.8 `scheme:production-group` — workshops / groups / series (NEW)

SSSL added "enhanced information about manufacture, attribution to established
**groups or series**" **[SSSL-IR §2.2]** and whole modules compare "local and
regional profiles and traditions" **[SSSL-IR §3.1]**. Named groups in the
literature:

```
Production group
├─ Early Iron Age Mass-Produced Stamp Seals (EIAMPS)   [SSSL-IR §3.1]
├─ "Iron Age II bone seals"                            [SSSL-IR §3.1]
├─ Post-Ramesside mass-produced scarabs                [Keel-2011]
├─ Local workshops (e.g. Beth-Shean valley group)      [SSSL-IR §3.1]
└─ (regional / site traditions)
```

Plus an **`scheme:authenticity`** vocab (genuine / questionable / forged /
modern) and a **`scheme:find-circumstance`** vocab (scientific excavation /
surface find / antiquities-market / unprovenanced), both demanded by
**[Ueh-1998]** and by Keel's distinction between legal excavations and market
finds.

---

## 2. Find-context ontology

### 2.1 Spatial hierarchy

The literature requires a deeper spatial model than our single flat
`StratigraphicContext` row. Tel Lachish is excavated by **multiple successive
expeditions, each with its own stratigraphy and numbering**, which must be
*correlated* **[Streit-2022; Ussishkin]**:

```
Site (tell / findspot)                      e.g. Tel Lachish = Tell ed-Duweir
└─ Excavation / expedition                  British Wellcome-Marston 1932–38 (Starkey/Tufnell);
   │                                         Hebrew Univ. (Aharoni) 1966–68;
   │                                         Tel Aviv Univ. (Ussishkin) 1973–93;
   │                                         Garfinkel/Hasel 2013–17; Austrian-Israeli 2017–19
   ├─ Area                                   Area S, Area P, Area D, Area GE …
   │  └─ Square / grid unit                  C9, D12, B12 …   (grid retained across expeditions)
   │     └─ Locus / feature                  Locus (L1223), Wall (W1027), pit, tomb, floor
   │        └─ Basket / registration no.     L1200/B11314  (find registration)
   └─ Stratum / level                        Level III, Level S-3 …
      └─ Phase / sub-phase                    S-3c, S-3b, S-3a (use-phases)
```

Key modelling requirements drawn from the sources:

- **One site → many excavations** (our `Excavation.findspot` FK already allows
  this; good) — each with permit numbers (e.g. `G-45/2017`), map reference,
  director/institution, and a **grid naming-convention prefix** (Lachish loci
  carry the `TAU-` prefix for Tel Aviv University loci) **[Streit-2022]**.
- **Cross-expedition equivalences**: the same wall is `W1027 = TAU-W1075 /
  W1077`; strata/levels across expeditions must be correlatable
  **[Streit-2022]**. This needs an explicit *equivalence / concordance*
  relation between context records of different excavations.
- **Stratum ≠ Locus ≠ Phase**: stratum has sub-**phases** (S-3c/b/a); loci
  belong to strata; "associated finds" are recorded per locus
  **[Streit-2022; SSSL-IR §2.2 "associated finds"]**.
- **Find circumstance / certainty of context**: Streit flags contexts as
  *secured*, *fill*, *not sealed from above*, *ambiguous* — the date of an
  object is only as good as its context **[Streit-2022]**.

> **Change vs our model:** `StratigraphicContext` currently stores
> `area`/`locus`/`stratum` as free-text chars on a single row with one `period`
> FK. Recommend promoting **Stratum** (with phase) and **Locus** (with
> basket/registration + feature type) to first-class entities, adding **Square**
> and a **context-equivalence** relation, and recording **associated finds** and
> **context reliability**.

### 2.2 Chronology / periods — note that schemes differ

Periods should live in **multiple `PeriodScheme`s** (our model already supports
this), because excavations and Egyptologists use different, non-aligned systems.

**(a) Southern-Levant archaeological scheme (SSSL/Keel usage)** — approximate:

| Period | Approx. date BCE | Source note |
|---|---|---|
| Iron Age I (IB) | ~1150–950 | Keel: Iron IB ~1150–950 **[Keel-2011]** |
| Iron Age IIA | ~950–825/850 | Keel: Iron IIA ~950–825 **[Keel-2011]** |
| Iron Age IIB | ~830/800–701 | ends with Sennacherib **[Ussishkin; Streit-2022]** |
| Iron Age IIC | ~700–586 | end of Judah **[Keel-2011; project scope]** |
| Neo-Babylonian | 586–539 | |
| Persian | 539–332 | Yehud stamps; Keel §313: *Jehud* impressions from end 5th c. **[Ueh-1998 n.5]** |

**(b) Tel Lachish, radiocarbon-refined (Streit & Höflmayer 2022, Areas S & P)**
— shows how a single site's levels map to periods and absolute dates
**[Streit-2022 Table 1]**:

| Period | Date (cal BCE) | Area S | Area P |
|---|---|---|---|
| Iron IIB | 800–701 | III | – |
| Iron IIB | 850–800 | IV | IV |
| Iron IIA | 950–850 | V | – |
| Iron I | *hiatus* | – | – |
| LB IIIB | 1200–1130 | VI | – |
| LB IIIA | 1300/1250–1200 | VII | P-1 |
| LB II | 1350–1300/1250 | S-1 | P-2 |
| LB II | 1425–1350 | S-2 | P-2 |
| LB II–IB | 1500/1450–1425 | S-3 | – |
| LB IA | 1550–1500/1450 | interim | – |
| MB IIB | 1750–1550 | – | P-3/4/5 |
| MB IIA | 2000–1750 | – | P-6 |

**(c) Tel Lachish historical anchors (Ussishkin)** — the site-specific Level
scheme, with historical destruction dates **[Ussishkin]**:

- Level VII = LB IIIA (Fosse Temple III; Ramesses III; 13th c.)
- Level VI = destroyed by fire, 12th c. (end of Canaanite city)
- Level V = Iron IIA
- Level IV = Iron IIB (Judean Palace-Fort fortress city)
- Level III = destroyed by **Sennacherib, 701 BCE**
- Level II = destroyed by the **Babylonians, 586 BCE**
- Level I = Persian (–Hellenistic)

**(d) Egyptian dynasties** — Keel dates scarabs *by dynasty*, so this is a
parallel period scheme **[Keel-2005; Keel-2012]**: XVIIIth (1539–1292), XIXth
(1292–1190), XXth (1190–1075), XXIst, XXIInd (945–713), XXVth, etc. Examples:
Ramesses IV throne-name = XXth Dyn. 1156–1150 **[Keel-2005 no.4]**; Western-Wall
scarab = Dyn. XXII 945–713 **[Keel-2012]**.

**Modelling implication — dating is multi-source and may conflict:**
- *Archaeological* (stratum/level) date vs *epigraphic/stylistic* date can
  disagree — Keel routinely gives a "Date" that weighs iconography, technique,
  material and find-context against each other **[Keel-2005 passim]**.
- Record an object's date as a **range (earliest/latest year)** with a **basis**
  (stratigraphic / stylistic / epigraphic / contextual) and a **certainty**,
  rather than a single `Period` FK. The High-vs-Low chronology debate for Iron
  IIA means absolute years are themselves contested **[Streit-2022]**.

> **Change vs our model:** keep `PeriodScheme`→`Period` (multi-scheme is right),
> but seed **three+ schemes** (Levantine archaeological, Egyptian dynasties,
> per-site levels) and add numeric `date_min`/`date_max` + `dating_basis` +
> `dating_certainty` on `Artefact` (we currently have one `period` FK plus a
> free-text `dating_text`).

---

## 3. Mapping to our model (`backend/catalog/models.py`)

What exists today and what is missing / should change, per the literature.

### 3.1 Add hierarchy (`broader`/`parent`) to all vocab

Only `IconographicMotif.broader` and `Region.parent` are hierarchical today. The
literature treats **every** typology as a tree. **Add `broader` to**
`ObjectType`, `Material`, `ScriptType`, `Language`. (Rationale: §1.1, §1.3, §1.7.)

### 3.2 New controlled-vocabulary schemes to add

| New vocab | Why / source | §above |
|---|---|---|
| `SealMorphology` (head/back/side, Tufnell 1984 codes) | most diagnostic feature for scarabs **[Keel-2005; Keel-2012]** | 1.2 |
| `EngravingTechnique` | SSSL enlargement **[SSSL-IR §2.2]** | 1.4 |
| `MountingDevice` | SSSL enlargement **[SSSL-IR §2.2]** | 1.4 |
| `BorderType` (Keel §190f) | **[Keel-2005]** | 1.4 |
| `BaseLayout` (horizontal/vertical/registers) | **[Keel-2005]** | 1.4 |
| `SurfaceTreatment` / glaze, `Colour` | SSSL standardised **[Keel-2012; SSSL-IR]** | 1.3 |
| `JarStampType` (lmlk / rosette / lion / Yehud …) | Koch & Lipschits **[SSSL-IR §3.1]** | 1.6 |
| `ProductionGroup` (EIAMPS, bone seals, workshops) | SSSL modules **[SSSL-IR §2.2, §3.1]** | 1.8 |
| `GardinerSign` (or tag space) | **[Keel-2005; Keel-2012]** | 1.5 |

### 3.3 New / changed fields on `Artefact`

- **`authenticity`** (genuine / questionable / forged / modern) — WSS rubric
  **[Ueh-1998]**. Missing.
- **`find_circumstance`** (excavated / surface / market / unprovenanced) —
  **[Ueh-1998; Keel]**. Missing.
- **`production_group`** FK → `ProductionGroup`; **`workshop`/origin** already
  partly covered by `origin_region`/`origin_note` (keep).
- **Dating**: add `date_min`/`date_max` (ints, BCE negative), `dating_basis`,
  `dating_certainty`; keep `period` FK + `dating_text` **[Keel; Streit]**. §2.2.
- **Scarab morphology** fields/record (head/back/side) **[Keel-2005]**. §1.2.
- **Manufacture** fields: `engraving_technique`, `mounting_device`,
  `base_layout`, `border_type`, `surface_treatment`, `colour` **[SSSL-IR]**. §1.4.

### 3.4 Relations that are missing

- **Comparanda / related-artefact** self-relation (CSSL has a dedicated
  "Comparanda" module) **[SSSL-IR App.2]** — typed links: *parallel*, *same
  workshop/group*, *seal↔its impression* (link a bulla to the seal that made
  it), *join/duplicate*. We have **no** artefact-to-artefact relation today.
- **Jar-stamp**: attach `JarStampType` to impression artefacts. Missing.

### 3.5 Find-context (`Excavation` / `StratigraphicContext`) changes

- `Excavation`: add `institution/expedition`, `permit_number`, `grid_prefix`
  (e.g. `TAU-`), `map_reference` **[Streit-2022]**. (Already has director/years;
  `findspot` FK already allows many excavations per site — good.)
- `Findspot`: consider `parent` for **sub-site modelling** (tell → named sub-site
  such as "City of David" / "Area G") — note this partly overlaps the `area`
  concept; decide whether sub-site lives on `Findspot` or on context `Area`.
- `StratigraphicContext`: promote **`Stratum`** (with `phase`/sub-phase) and
  **`Locus`** (with `basket`/registration number, `feature_type`) to entities;
  add **`Square`**; add a **context-equivalence/concordance** relation across
  expeditions (`W1027 = TAU-W1075`) **[Streit-2022]**; add **associated finds**
  and **context reliability** (secured / fill / unsealed / ambiguous)
  **[Streit-2022]**.

### 3.6 Epigraphy — mostly adequate, small additions

`Inscription` (script/language/technique/position/line_count) and `Reading`
(normalized/diplomatic/transliteration/translation/certainty/is_preferred/
generated_by_model) already match Keel/WSS practice well. Additions:

- **Seal-legend formula** vocab and structured **onomastics** (personal name,
  patronymic `bn` + PN, title/profession, `lmlk`/royal formula) — WSS devotes
  Part II *Onomastikon* to exactly this (names, titles "Berufsbezeichnungen",
  place-names, formulae, filiation) **[Ueh-1998 pp.105–106]**.
- `Inscription.script`/`language` should point at the hierarchical script/
  language vocab of §1.7 (incl. mixed/undefined concepts).

### 3.7 Media — adequate, align vocabulary

`MediaItem.view` (obverse/reverse/side/impression/modern_impression/detail) maps
to Keel's **base / back / side** convention; consider aliasing `obverse`→**base**
and `reverse`→**back**, and ensure both a **photograph** *and* an **interpretive
drawing** can coexist per view (the `kind` field already allows this) — Keel
always publishes 3 photo views + 3 drawings **[Ueh-1998 n.16; SSSL-IR App.1]**.
CSSL further distinguishes **raw / processed / final** images and an editorial
review status per image **[SSSL-IR App.2]** — optional `MediaItem.processing_stage`
and `review_status`.

### 3.8 Editorial workflow (optional)

CSSL has explicit **Reviews / Administration** (status *pending / accepted / to
be revised*, assigned graphic staff, copyright holder) **[SSSL-IR App.2]**. We
have only `Artefact.is_published`. A light `editorial_status` enum would mirror
the corpus workflow.

---

## 4. CSSL / SSSL alignment for Linked Open Data

**Project identity.** The corpus we align to is **CSSL — *Corpus of Stamp Seals
from the Southern Levant*** (https://cssl.levantineseals.org/), the open-access
successor to Othmar Keel's **CSSPI** (*Corpus der Stempelsiegel-Amulette aus
Palästina/Israel*) and **CSAJ** (*Corpus der Siegel-Amulette aus Jordanien* =
Eggler & Keel) **[SSSL-FS; SSSL-IR §1.1]**. "Southern Levant" explicitly covers
Israel, Jordan and Palestine, designed to extend beyond modern borders to the
Central/Northern Levant, Egyptian delta and Arabia **[SSSL-FS]**.

**Technical conventions to mirror.** CSSL+ is being built on **Numishare**
(Ethan Gruber / American Numismatic Society) together with **CollectiveAccess**
**[SSSL-IR §2.2]**. Numishare is the engine behind **Nomisma.org**, whose
pattern we should imitate for LOD:

- **Stable, dereferenceable HTTP IRIs** per concept and per object, with content
  negotiation to RDF/XML + SPARQL (we already expose RDF via `djangordf` /
  Fuseki — keep IRIs stable and align them to CSSL's when published).
- **SKOS `ConceptScheme`s** for every typology (exactly the §1–§2 schemes),
  with `skos:exactMatch` / `skos:closeMatch` to CSSL and Nomisma-style URIs —
  our `ControlledTerm.skos_uri` and `Period.skos_uri` fields are the hooks.
- Each CSSL entry page is planned around **~20 fields** with links, images, maps
  and multi-parameter search **[SSSL-IR §2.3]** — matches our faceted model.

**Identifier schemes to carry** (populate `catalog.Identifier.scheme`) so an
object can be cited across corpora **[Ueh-1998; Keel-2005 n.1; Keel-2012]**:

| Scheme | Form | Source |
|---|---|---|
| `CSSL` | CSSL object id / URI | **[SSSL-FS/IR]** |
| `CSSPI` | *OBO.SA* vol. + site + no. (e.g. "Keel 1997: Aschdod Nr. 42"; "Keel 2010b: Tell el-Farʿa-Süd No. 209") | **[Keel-2005; Keel-2011; Keel-2012]** |
| `CSAJ` | Eggler & Keel (Jordan) corpus no. | **[Keel-2011 refs]** |
| `WSS` (= `CWSS`) | Avigad & Sass number (1–1217) — standard citation for inscribed NW-Semitic seals | **[Ueh-1998]** |
| `Keel-§` | Keel 1995a (*OBO.SA* 10) paragraph no. for forms/motifs/materials | **[Keel-2005 n.1; Keel-2012]** |
| `Tufnell-1984` | head/back/side classification code | **[Keel-2005 n.1]** |
| `Gardiner` | hieroglyphic sign-list code | **[Keel-2005; Keel-2012]** |
| `IAA` | Israel Antiquities Authority registration / permit no. | **[Keel-2011; Keel-2012; Streit-2022]** |
| museum inv. no. | per holding `Repository` | **[Keel-2005]** |

**Place / period authorities.** Keep `Findspot.gazetteer_uri` (align to Pleiades
/ ANE place gazetteers; SSSL standardises place-names **[SSSL-IR §2.2]**) and
`Period.skos_uri` (align to **PeriodO / ChronOntology** for the Iron IIA–Persian
ranges and Egyptian dynasties of §2.2).

**Sibling LOD datasets to cross-link** (named at the SSSL Digital Humanities
workshop) **[SSSL-IR §4.1]**: **ACAWAI-CS** (Annotated Digital Corpus of Ancient
West Asian Imagery: Cylinder Seals), **CDLI**, **CMS** (Corpus der minoischen und
mykenischen Siegel), **Levantine Ceramics Project (LCP)**, **Yale Babylonian
Collection**, and **Nomisma.org**. Provide `skos:exactMatch` / `owl:sameAs`
links to these where concepts or objects overlap.

**Documentation convention.** Mirror Keel/WSS object documentation: **3
photographic views (base, side, back) + 3 interpretive line-drawings** per
object **[Ueh-1998 n.16; SSSL-IR App.1]**, and keep the SSSL rule of separating
*description* from *interpretation* in the data model **[SSSL-IR §2.2]**.
