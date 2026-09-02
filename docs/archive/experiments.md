# Experiment History

## 1. Purpose

This document records the experimental development of the BRouter
motorcycle routing model. It intentionally includes successful
approaches, rejected hypotheses, unexpected side effects and experiments
without practical routing impact.

The experimental rule is:

``` text
hypothesis -> controlled experiment -> quantitative comparison
           -> visual inspection of geometry changes -> design decision
```

A cost change alone is not considered evidence of a better route.

## 2. Initial Profile and Character Calibration

### Goal

Establish distinct motorcycle-routing characters on one common kinematic
base model:

``` text
Fast
Fast-Curvy
Curvy
Very Curvy
Curvy-Hilly
Curvy-Very-Hilly
```

### Calibration routes

The documented set included Biel/Bienne -\> Neuchatel, Bern -\> Luzern,
Thun -\> Andermatt and Zurich -\> Davos. These expose short mixed
routing, fast versus secondary-road choices, mountain sensitivity and
long alpine routing.

### Representative results

``` text
Biel/Bienne -> Neuchatel
Fast                 32.8 km   43.8 min    61 m ascent
Fast-Curvy           32.4 km   43.2 min   125 m
Curvy                36.1 km   48.1 min   273 m
Very Curvy           37.1 km   49.4 min   272 m
Curvy-Hilly          36.1 km   48.1 min   273 m
Curvy-Very-Hilly     40.3 km   53.8 min   810 m

Thun -> Andermatt
Fast                114.2 km  152.3 min  2674 m
Fast-Curvy          114.3 km  152.4 min  2676 m
Curvy               117.1 km  156.2 min  2663 m
Very Curvy          120.4 km  160.5 min  2993 m
Curvy-Hilly         117.1 km  156.2 min  2663 m
Curvy-Very-Hilly    119.9 km  159.9 min  2976 m
```

### Finding and decision

Curviness produced a clear routing character. Hilliness can influence
mountain routing, but its value as an independent user-facing character
was less convincing. The principal characters remain Fast, Curvy and
Very Curvy; hilliness remains a secondary dimension.

## 3. Pseudo-Tag Investigation

BRouter pseudo tags such as `estimated_traffic_class`,
`estimated_town_class` and `estimated_forest_class` were investigated as
possible additional evidence.

Key semantic finding:

``` text
direct OSM attribute != BRouter heuristic estimate
```

Pseudo tags are heuristic signals, not directly observed road facts. The
first detailed investigation concentrated on `estimated_traffic_class`.

## 4. Initial Traffic Sensitivity Experiments

### Hypothesis

Higher `estimated_traffic_class` values might identify less attractive
traffic conditions, so an additive penalty could improve Curvy routing.

Variants of increasing strength were tested, including medium, high and
stronger probe configurations.

### Observations

Fribourg -\> Altdorf changed around Huttwil and stronger probing could
cause larger corridor changes. Bern -\> Langnau changed around Worb; an
earlier stronger probe produced a larger deviation beginning near
Rufenacht. Other routes remained unchanged despite plausible
alternatives.

### Finding

The pseudo tag can influence routing, but a geometry change does not
establish that the interpretation is correct. Diagnostic access to the
underlying BRouter messages was required.

## 5. GeoJSON Message Diagnostics

`processUnusedTags=true` exposed BRouter's GeoJSON `messages` table,
allowing route sections to be inspected for highway class, maxspeed,
pseudo tags, surface and other way tags.

A Bern -\> Langnau changed section showed:

``` text
highway=tertiary
maxspeed=80
estimated_traffic_class=3
estimated_forest_class=4
surface=asphalt
```

Around Huttwil, the baseline used primary roads with known traffic
values while an alternative could use an unclassified road without a
traffic estimate.

Critical finding:

``` text
missing estimated_traffic_class != low traffic
```

Decision: missing pseudo-tag values must not be interpreted as
favourable evidence.

## 6. Local-Unknown Traffic Experiment

### Hypothesis

Treat missing traffic values differently on local roads.

Variants:

``` text
baseline
traffic-high-current
traffic-high-local-unknown
```

### Result

``` text
Bern -> Thun                 all geometrically identical
Biel -> Neuchatel            all geometrically identical
Fribourg -> Altdorf          current changed; local-unknown returned to baseline
Bern -> Langnau              current changed; local-unknown returned to baseline
```

### Finding and decision

The experiment corrected two known local effects but risked tuning
around Huttwil and Worb. It was not promoted as a general rule; the
route catalogue was expanded first.

## 7. Ten-Route Traffic Catalogue

The catalogue was expanded to:

``` text
Bern -> Thun
Biel -> Neuchatel
Fribourg -> Altdorf
Bern -> Langnau im Emmental
Bern -> Burgdorf
Biel -> Solothurn
Solothurn -> Langenthal
Bern -> Murten
Thun -> Interlaken
Neuchatel -> La Chaux-de-Fonds
```

Six of ten routes showed a geometry change in at least one traffic
variant.

### Visual findings

**Bern -\> Burgdorf:** Traffic Current and Traffic Local Unknown were
identical to each other but very different from baseline. Large parts
moved onto motorway.

**Solothurn -\> Langenthal:** The same structural behaviour appeared,
with a large motorway share.

**Bern -\> Murten:** Baseline and Traffic Current were identical.
Traffic Local Unknown merely selected a slightly different motorway
access in Bern.

**Neuchatel -\> La Chaux-de-Fonds:** Baseline and Traffic Local Unknown
were identical. Traffic Current diverged after leaving the A20 and used
another route for roughly the final 2-3 km.

### Finding

The broader catalogue exposed a structural problem hidden by the smaller
test set.

## 8. Traffic Coverage Analysis

Observed coverage across the tested route material:

``` text
Highway              Known %    Missing %
motorway                0.0       100.0
secondary             100.0         0.0
primary                99.9         0.1
trunk                   0.0       100.0
tertiary              100.0         0.0
unclassified            0.0       100.0
motorway_link           0.0       100.0
living_street           0.0       100.0
residential             0.0       100.0
trunk_link              0.0       100.0
service                 0.0       100.0
primary_link          100.0         0.0

known      199.97 km   49.3%
missing    205.34 km   50.7%
```

### Critical finding

Missingness was strongly correlated with road class. A global traffic
penalty therefore unintentionally expressed pseudo-tag coverage:

``` text
primary / secondary / tertiary -> usually known -> can receive penalty
motorway / trunk / local roads -> usually missing -> escape penalty
```

This explained the motorway shifts in Bern -\> Burgdorf and Solothurn
-\> Langenthal.

Decision: missing data is neither a penalty nor a bonus. Applicability
must be explicit.

## 9. Known Traffic-Class Distribution

For route sections where H2 traffic was known:

``` text
class 2     16.58 km     8.3%
class 3     76.44 km    38.2%
class 4     57.23 km    28.6%
class 5     34.14 km    17.1%
class 6     15.57 km     7.8%
```

The distribution differed by road hierarchy. A traffic class therefore
cannot be interpreted independently of H1 road context. This led to the
road-class-aware experiment.

## 10. Road-Class-Aware H2 Experiment

### Hypothesis

Apply `estimated_traffic_class` only within its observed scope and
interpret it in H1 road-class context.

Variants:

``` text
baseline
h2-context-low
h2-context-medium
h2-context-strong
```

### Result

Most routes remained stable. Changes occurred for Fribourg -\> Altdorf
at strong, Bern -\> Burgdorf at low/medium/strong, and Neuchatel -\> La
Chaux-de-Fonds at medium/strong. The previous motorway-corridor problem
disappeared.

### Visual findings

**Bern -\> Burgdorf:** baseline passed the hill in Burgdorf on the
southern side; H2 used the northern side. Local difference, without an
obvious traffic-routing benefit.

**Neuchatel -\> La Chaux-de-Fonds:** after leaving the A20, baseline
remained on the main road; H2 moved west through a neighbourhood to the
destination.

**Fribourg -\> Altdorf / Huttwil:** baseline remained on the main road;
H2 left it for a southern neighbourhood/local road.

### Finding and decision

Road-class-aware scope solved the major coverage bias but not the deeper
decision problem. A negative H2 penalty on a suitable main road can
still make an unrelated local alternative comparatively attractive.
Additive negative H2 evidence was therefore not accepted as the final
mechanism.

## 11. Evidence-Fusion Architecture

The experiments led to this conceptual model:

``` text
                 Reality
                    |
          +---------+---------+
          |                   |
         OSM             Measurement stations
          |                   |
     +----+----+              H3
     |         |         measured data
    H1        H2
 direct    heuristic
     |         |              |
     +---------+--------------+
               |
         Evidence Fusion
               |
          Confidence
```

H1 is direct OSM evidence and the independent routing basis. H2 is
heuristic evidence such as BRouter pseudo tags. H3 represents
independent measured evidence, for example future ASTRA or cantonal
traffic measurements.

Core principles:

``` text
more evidence != automatic truth
missing evidence != negative evidence
missing evidence != positive evidence
```

The streams provide different observations of reality and contribute to
confidence rather than acting as competing truths.

## 12. ASTRA and Cantonal Traffic Data Hypothesis

Swiss traffic measurements may eventually provide an H3 source
independent of BRouter's heuristic.

Complementary properties:

``` text
BRouter H2
    broad heuristic coverage in applicable road classes
    estimated rather than measured

ASTRA / cantonal H3
    physically measured traffic
    spatially incomplete
```

Open questions include historical DTV/DWV availability, geographic
coverage, station-to-OSM mapping, temporal representativeness, vehicle
classes, licensing and redistribution.

H3 is part of the architecture but not yet part of production routing.
Real-time traffic is secondary because the primary model is intended to
work offline.

## 13. Gated H2 Evidence Experiment

### Hypothesis

Instead of penalising unfavourable H2 traffic, H2 should only strengthen
an H1-suitable road when favourable evidence exists:

``` text
H2 AVAILABLE
and H1 suitable through-road class
and favourable C2/C3
    -> small positive preference

C4/C5/C6, MISSING, NOT_APPLICABLE
    -> no H2 modification
```

Compared variants:

``` text
baseline
h2-low       previous additive reference
h2-gated     positive gated evidence
```

### Result

The additive H2 Low reference still changed Bern -\> Burgdorf. The gated
variant was geometrically identical to baseline on all ten routes.

``` text
Bern -> Burgdorf
baseline      23.2 km   32.4 min   244 m   cost 43943
h2-low        22.8 km   32.7 min   256 m   cost 44667   changed
h2-gated      23.2 km   32.4 min   244 m   cost 43943   unchanged
```

H2 still changed costs slightly on some routes:

``` text
Biel -> Neuchatel       52215 -> 52209
Fribourg -> Altdorf    247621 -> 247609
Bern -> Langnau         55625 -> 55619
```

### Finding

The safety hypothesis was confirmed: no motorway coverage bias, no
Huttwil neighbourhood detour, no La Chaux-de-Fonds neighbourhood detour
and no new geometry regression. Practical routing value remained
unproven because no gated route changed geometry.

## 14. Gated H2 Sensitivity Experiment

### Goal

Determine whether gated evidence was merely calibrated too
conservatively while keeping semantics fixed.

Variants:

``` text
baseline
gated-low
gated-medium
gated-strong
```

### Result

``` text
gated-low       0 / 10 changed routes
gated-medium    0 / 10 changed routes
gated-strong    0 / 10 changed routes
```

Costs changed slightly where favourable H2 evidence existed:

``` text
Biel -> Neuchatel
baseline        52215
gated-low       52209
gated-medium    52201
gated-strong    52195

Fribourg -> Altdorf
baseline       247621
gated-low      247609
gated-medium   247596
gated-strong   247580
```

### Finding and decision

The gated approach remained robust under stronger positive evidence, but
practical routing value was still not demonstrated. Strength should not
simply be increased until geometry changes; that would optimise for a
route change rather than evidence quality.

Current H2 traffic status:

``` text
negative additive H2
    rejected as unsafe

road-class-aware negative H2
    improved scope
    still produced undesirable local effects

positive gated H2
    semantically preferred
    robust
    practical routing benefit not yet demonstrated
```

H2 traffic remains experimental rather than a production routing
feature.

## 15. Design Principles Derived from the Experiments

### Direct evidence is the base

H1 remains independently capable of producing a route. Optional evidence
must not be required for basic routing.

### Missing is a state, not a value

``` text
MISSING != 0 != low traffic != high traffic
```

Where useful, distinguish `AVAILABLE`, `MISSING` and `NOT_APPLICABLE`.

### Applicability is explicit

Evidence is interpreted only where its semantics apply. Coverage must
not silently become a road preference.

### Evidence does not equal truth

H1, H2 and H3 are observations or hypotheses with different strengths
and limitations. They contribute to confidence.

### Optional evidence should be gated

Optional evidence should support a decision meaningful in the base model
rather than accidentally create an unrelated alternative.

### Geometry must be inspected

Cost differences alone are insufficient. Changed geometry must be
inspected to understand actual routing behaviour.

### Test broadly before special-casing

A fix for Huttwil or Worb is not accepted until it survives a broader
catalogue.

## 16. Experiment Status Summary

  --------------------------------------------------------------------------
  Experiment         Purpose           Result              Status
  ------------------ ----------------- ------------------- -----------------
  Character          Establish         Clear useful        Retained
  calibration        Fast/Curvy/Very   differentiation     
                     Curvy behaviour                       

  Hilliness          Add elevation     Useful as secondary Secondary
                     preference        dimension           

  Initial H2 traffic Avoid higher      Geometry reacts,    Superseded
  penalties          estimated traffic semantics uncertain 

  Message            Inspect           Exposed             Retained tooling
  diagnostics        pseudo-tag        missing-value       
                     evidence          problem             

  Local-unknown      Correct known     Fixed examples but  Rejected as
  treatment          local detours     risked special-case general solution
                                       tuning              

  Ten-route          Test beyond known Exposed motorway    Retained test set
  catalogue          examples          coverage bias       

  Coverage analysis  Understand H2     Missingness         Key finding
                     availability      strongly road-class 
                                       dependent           

  Traffic-class      Interpret H2 in   Road class matters  Key finding
  distribution       context                               

  Road-class-aware   Scope H2          Removed motorway    Partially
  H2                 correctly         bias; local detours successful
                                       remained            

  Evidence-fusion    Treat sources as  Coherent H1/H2/H3   Retained
  model              evidence          architecture        

  Gated H2           Positive evidence 0/10 regressions,   Preferred
                     on H1-suitable    0/10 geometry       hypothesis,
                     roads             benefits            experimental

  Gated sensitivity  Test stronger     Low/Medium/Strong   Stable, benefit
                     positive evidence all 0/10 changes    unproven
  --------------------------------------------------------------------------

## 17. Open Experiments

### Other H2 pseudo tags

Candidates include `estimated_town_class` and `estimated_forest_class`.
Each must undergo:

``` text
semantics -> coverage -> applicability -> missing-state analysis
          -> sensitivity -> catalogue -> visual inspection
```

### Avoid Cities

`avoid_cities` requires an explicit user-intent model. It must not
simply become a blanket `residential` penalty or a direct mapping of
`estimated_town_class`.

### H3 feasibility

ASTRA and cantonal traffic data require a separate feasibility study
before integration.

### Geographic generalisation

Future validation should include Jura, Alps, Black Forest, Vosges, flat
rural areas and regions with different OSM tagging practices.

### Automated route similarity

Useful future metrics include shared route %, unique route %, road-class
distribution, motorway share, local-road share and corridor change.

### Production regression suite

Once semantics stabilise, selected routes and behaviours should become
explicit release regression tests.

## 18. Urban-Context and Core-Burden Investigation

### Goal

Investigate whether settlement context can improve motorcycle-road
character without turning individual urban tags into a blanket penalty.

The specific problem is to distinguish between:

``` text
acceptable through-road or bypass
```

and:

``` text
unattractive route through a settlement core
```

The investigation is diagnostic only. No production routing penalty is
introduced by this experiment.

### Evidence sources

The experiment considered direct OSM evidence and BRouter-derived
evidence, including signals such as:

-   speed environment,
-   OSM crossings,
-   traffic signals and other intersection-control evidence,
-   BRouter `estimated_crossing_class`,
-   BRouter `estimated_traffic_class`,
-   BRouter `estimated_town_class`,
-   local road context.

The existing evidence rules continue to apply:

``` text
missing evidence != negative evidence
missing evidence != positive evidence
```

In particular, missing `estimated_town_class` values must not be
interpreted as evidence that a road is outside a settlement.

### Rolling-window diagnostic

A 500 m rolling-window diagnostic was used to compare known
urban-positive and rural-negative cases.

Across the available diagnostic windows, the positive and negative
groups showed useful aggregate separation. Representative group averages
were:

``` text
                              positive       negative
<= 50 km/h share               84.52 %        63.98 %
OSM crossings/km                 5.98           1.68
signals/km                       1.90           0.23
H2 crossings/km                 11.17           5.48
H2 traffic coverage             74.98 %        64.17 %
H2 traffic mean                  4.85           2.82
H2 town coverage                28.49 %         0.00 %
```

This demonstrates that settlement context can be visible in combined
evidence, but it does not establish a reliable routing score.

Important observations:

1.  `estimated_town_class` is too incomplete to serve as the sole urban
    detector.
2.  Individual features overlap between urban and rural environments.
3.  Route-local persistence is more informative than a route-wide
    average.
4.  A useful model should identify sustained settlement-core burden
    rather than penalise every occurrence of an urban-looking tag.

### Controlled bypass-vs-core cases

Aarberg and Buren were then used as controlled diagnostic cases because
each provides a useful comparison between an acceptable
bypass/through-route and an undesirable settlement-core route.

The diagnostic introduced a deliberately strict core predicate and
measured the length of contiguous route sections satisfying that
predicate.

Representative observations were:

``` text
Aarberg
    acceptable bypass:
        longest strict-core run =   0 m

    undesirable core route:
        longest strict-core run = 243 m

Buren
    acceptable bypass:
        strict-core runs = 2 x 166 m

    undesirable core route:
        longest strict-core run = 427 m
```

The important result is not the absolute values themselves. The
experiment suggests that the *continuity and accumulated length* of
core-like routing may contain more useful information than the mere
presence of a `living_street`, low speed limit or another isolated urban
feature.

### Core-burden hypothesis

The resulting general hypothesis is:

``` text
undesirable settlement routing
    may be characterised by
sustained contiguous core-like exposure
    rather than
the presence of individual urban tags
```

A future diagnostic may therefore derive a `core_burden` representation
from local evidence and route continuity.

This is intentionally not yet a production definition.

In particular, the observed Aarberg and Buren values must **not** be
converted directly into a rule such as:

``` text
strict_core >= 200 m -> penalise
```

Such a threshold would be calibration to two known cases rather than
evidence of a general routing property.

### Current decision

No urban penalty, core penalty or threshold is accepted into the
production routing model at this stage.

Retained findings:

-   settlement context is potentially useful implicit evidence,
-   `estimated_town_class` alone is insufficient,
-   missing town evidence remains unknown rather than rural,
-   local rolling windows are more useful than global route averages,
-   contiguous core exposure is a promising diagnostic feature,
-   isolated low-speed or urban tags must not automatically make a road
    unattractive,
-   acceptable bypasses may themselves contain short core-like sections.

### Next experiment

The next step is broad independent validation of the `core_burden`
hypothesis.

The catalogue should contain three classes:

``` text
A. desirable or acceptable through-routes / bypasses
B. known undesirable settlement-core routes
C. rural controls
```

The validation should answer:

1.  Does contiguous core burden separate A from B across multiple towns?
2.  Do rural roads remain unaffected?
3.  Are short unavoidable settlement passages tolerated?
4.  Does the signal generalise beyond Aarberg and Buren?
5.  Which underlying features contribute useful evidence without
    becoming route-class proxies?
6.  Can useful behaviour be obtained without a route-specific threshold?

Only after this validation should a routing experiment apply any
core-burden modifier and compare resulting geometry.

### Independent validation of `strict_core`

The initial `strict_core` diagnostic separated the Aarberg and Buren
calibration pairs well. To test whether this was a general property
rather than local calibration, the predicate was frozen unchanged and
evaluated on independent, visually validated route pairs.

The frozen predicate was:

``` text
(highway = living_street AND maxspeed <= 20)
OR
(highway = service AND service = parking_aisle)
```

Independent candidate pairs were prepared for Murten, Solothurn,
Langenthal and Willisau. Sursee and Fribourg were excluded before
measurement because visual inspection showed that the proposed "bypass"
was not actually the better through-route. This preserves ground truth
independently of the detector result.

The independent validation produced:

``` text
Place          Bypass longest strict_core   Core longest strict_core
Murten                    0 m                         0 m
Solothurn                 0 m                         0 m
Langenthal                0 m                         0 m
Willisau                  0 m                         0 m
```

Solothurn was the strongest independent positive-control case: the core
route visibly entered the northern old-town area while the bypass was a
valid alternative. The detector still returned zero for both.

Decision:

``` text
strict_core
    is rejected as a general settlement-core detector
```

It may still be retained as optional high-confidence evidence when
present, because the calibration cases show that such tags can identify
genuinely burdensome local sections. Absence of `strict_core`, however,
carries no meaning and must not be treated as evidence that a route
avoids an urban core.

This result is important because it prevents Aarberg/Buren-specific OSM
tagging from becoming a production rule.

### Road-continuity / local-excursion hypothesis

After the `strict_core` result, a more structural hypothesis was tested:

``` text
functional through road
        ->
contiguous local-road run
        ->
functional through road
```

Local roads were defined diagnostically as:

``` text
residential
living_street
service
unclassified
```

and through roads as the motorway/trunk/primary/secondary/tertiary
families.

The goal was not to classify an old town, but to detect an unnecessary
temporary excursion from a through corridor into a local network.

The diagnostic was run on:

-   Murten, Solothurn, Langenthal and Willisau core/bypass pairs,
-   acceptable controls in Thun, Biel, Bern, Zurich, Ins and Twann,
-   rural controls in the Emmental and Seeland.

Representative results were:

``` text
Place          Bypass longest   Core longest
Murten             1204 m          994 m
Solothurn           458 m          358 m
Langenthal          502 m          268 m
Willisau            118 m            0 m

Emmental rural     2134 m
```

The pair deltas consistently pointed in the wrong direction: the
acceptable bypass had the longer local excursion in every pair.

Visual interpretation also explains why this is not merely a threshold
problem. In Willisau, for example, the two routes differ mainly in one
branch; the bypass runs south through an apparently sparsely settled
area. The detector nevertheless reports a local excursion only on that
acceptable bypass. In Murten, almost half of the valid bypass was
structurally classified as local excursion. The rural Emmental control
produced a 2.1 km excursion.

Decision:

``` text
road-hierarchy local excursion
    is rejected as a proxy for undesirable settlement routing
```

The experiment demonstrates that a useful motorcycle bypass need not
remain on a higher OSM road hierarchy. Conversely, an unattractive urban
passage can remain on a primary, secondary or tertiary road. Road
hierarchy therefore does not encode the intended semantics.

### Resulting direction

The two rejected detectors narrow the design space:

``` text
strict_core
    precise in some places
    but too specific to local tagging

local excursion
    broader structurally
    but semantically wrong
```

The next investigation should therefore not introduce another binary
"old-town" detector.

The more promising direction is a continuous, evidence-based notion of
local routing burden. Earlier urban diagnostics already showed aggregate
separation between known urban and rural contexts using combinations of
speed environment, crossings, signals and related evidence.

A future `urban_burden` diagnostic should therefore:

1.  remain continuous rather than `urban=true/false`,
2.  use multiple independent observations rather than one tag,
3.  distinguish evidence from confidence and availability,
4.  tolerate normal town and city through-routes,
5.  not penalise a road solely because it is residential, local or
    urban,
6.  be validated on acceptable city passages, rural controls and
    deliberately undesirable alternatives before affecting routing cost.

The routing objective remains unchanged:

> Prefer a sensible motorcycle through-route or bypass when one exists,
> without generically avoiding towns, villages or urban roads.

No production urban/core penalty has yet been accepted.

### Continuous `urban_burden` routing experiment

Following rejection of the binary `strict_core` detector and the
road-hierarchy `local excursion` proxy, the final urban investigation
tested the continuous evidence-based direction proposed above directly
in routing.

The experiment deliberately used only evidence already investigated:

``` text
estimated_traffic_class
estimated_town_class
strict_core as optional high-confidence evidence
```

The modifier was additive to the existing `calculated_cost`. It did not
replace the established road-character model and did not introduce a
generic residential, local-road or town-avoidance rule. Speed was not
penalised a second time because the kinematic model already represents
travel speed.

Two bounded strengths were tested:

``` text
urban burden v0.1
    conservative additive weighting

urban burden v0.2
    moderately stronger weighting of the same evidence
    no new detector and no new evidence source
```

The stopping rule was defined before the second run:

``` text
v0.1
    ->
at most one v0.2
    ->
final urban decision
```

The catalogue contained the Aarberg and Buren calibration cases,
acceptable controls in Thun, Biel, Bern, Zurich, Ins and Twann, and
independent town cases in Murten, Solothurn, Langenthal and Willisau.

#### v0.1 result

``` text
Case            Geometry
Aarberg         unchanged
Buren           unchanged
Thun            unchanged
Biel            unchanged
Bern            unchanged
Zurich          changed
Ins             unchanged
Twann           unchanged
Murten          unchanged
Solothurn       unchanged
Langenthal      unchanged
Willisau        unchanged
```

Only Zurich changed. The route shortened from 7.44 km to 7.01 km, a
difference of -5.8 %. Visual inspection showed that the material
difference was the choice of another bridge. Both alternatives were
considered plausible without reliable knowledge of actual traffic
volumes. The change was therefore judged neutral rather than a
demonstrated improvement or regression.

Most importantly, the known Aarberg and Buren calibration cases remained
unchanged.

#### v0.2 result

v0.2 moderately strengthened the same traffic, town and `strict_core`
contributions. No new heuristic was introduced.

The routing result was identical in structure to v0.1:

``` text
Case            Geometry
Aarberg         unchanged
Buren           unchanged
Thun            unchanged
Biel            unchanged
Bern            unchanged
Zurich          changed
Ins             unchanged
Twann           unchanged
Murten          unchanged
Solothurn       unchanged
Langenthal      unchanged
Willisau        unchanged
```

Zurich again selected the same plausible alternative bridge and
shortened from 7.44 km to 7.01 km. All other cases remained unchanged.

#### Final urban decision

The continuous urban-burden hypothesis is **not accepted into the
production routing model for v1**.

The reason is not a demonstrated regression. Both tested strengths were
stable across the catalogue. The problem is insufficient demonstrated
benefit:

``` text
12 test cases
11 unchanged
1 neutral plausible alternative
0 clear regressions
0 clear improvements in the Aarberg/Buren calibration cases
```

Increasing the modifier further merely to force route changes would
violate the project validation method. It would optimise for a desired
geometry rather than for independently supported semantics and would
increase the risk of local overfitting.

The production `moto-curvy` profile therefore remains unchanged by this
investigation. The experimental urban profiles are not release profiles.

Retained conclusions:

-   settlement and traffic context can contain useful evidence,
-   `estimated_town_class` and `estimated_traffic_class` must still be
    interpreted with their coverage and applicability limitations,
-   `strict_core` may identify genuine burden where present but does not
    generalise as a detector,
-   road hierarchy does not reliably distinguish a useful bypass from an
    undesirable urban passage,
-   a continuous multi-evidence modifier is safer than a binary urban
    detector but did not demonstrate enough routing benefit to justify
    production complexity,
-   no stronger urban penalty should be calibrated solely to make
    Aarberg or Buren change route,
-   future reconsideration requires materially better independent
    evidence, broader measured data, or a new general hypothesis rather
    than another strength iteration.

The routing objective remains:

> Prefer a sensible motorcycle through-route or bypass when one exists,
> without generically avoiding towns, villages or urban roads.

The urban/core-burden investigation is therefore closed for v1.

## 19. Current Position

The project has not established that `estimated_traffic_class` should
influence production motorcycle routing.

It has established a more fundamental rule:

``` text
pseudo tags can provide useful evidence
but their coverage and semantics must be understood first
and missing evidence must never be invented
```

Preferred architecture:

``` text
H1 direct OSM evidence
        |
        +------------------+
                           |
H2 heuristic evidence ----+----> Evidence Fusion -> Confidence
                           |
H3 measured evidence -----+
```

The routing model remains usable from H1 alone. H2 and future H3 may
increase confidence where available and applicable, but no optional
evidence stream is treated as truth by itself.
