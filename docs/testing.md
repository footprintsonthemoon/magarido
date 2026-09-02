# BRouter Motorcycle Profiles -- Testing and Calibration

## 1. Purpose

This document describes the testing and calibration methodology used by
the BRouter Motorcycle Profiles project.

Testing has three main objectives:

1.  verify that generated profiles are technically valid,
2.  verify that routing behaviour remains plausible,
3.  determine whether different profiles provide meaningful and
    reproducible user value.

The objective is not to make every profile generate a different route
for every test case.

Identical routes are expected when geography, infrastructure or
travel-time differences provide no meaningful alternative.

## 2. Testing Principles

### 2.1 Test behaviour, not visual difference

A profile is not successful merely because its route looks different.

A difference should correspond to the intended routing behaviour.

For example:

-   Fast should favour travel efficiency.
-   Curvy should accept reasonable additional cost for attractive roads.
-   Very Curvy should accept a stronger trade-off.
-   Hilliness should only matter where meaningful topographical
    alternatives exist.

### 2.2 Identical routes are valid results

Two profiles may legitimately select the same route.

This can occur when:

-   there is effectively only one practical road,
-   an alternative is disproportionately slower,
-   topography constrains the corridor,
-   both profiles evaluate the available roads similarly.

Artificially increasing parameter differences merely to force visually
different routes is explicitly avoided.

### 2.3 Avoid route-specific calibration

A concrete road or route may reveal a weakness in the model.

It must not directly result in a route-specific exception.

The required process is:

    observation
        ->
    general hypothesis
        ->
    model change
        ->
    independent validation

A change is accepted only when it improves the general model without
creating unreasonable behaviour elsewhere.

### 2.4 Human evaluation matters

Numeric output alone cannot determine whether a motorcycle route is
attractive.

Automated tests provide:

-   route length
-   estimated travel time
-   ascent
-   BRouter cost
-   technical success or failure

Visual inspection and local knowledge provide additional information
about:

-   route character
-   meaningful corridor differences
-   unrealistic detours
-   motorway use
-   village and residential routing
-   real-world motorcycle attractiveness

Both forms of evaluation are required.

## 3. Test Environment

The reference development environment is macOS.

BRouter runs locally using its standalone server.

The expected local endpoint is:

    http://localhost:17777/brouter

Profiles are generated from the canonical source model before testing.

Typical workflow:

    python tools/generate_profiles.py
    python tools/run_smoke_tests.py
    python tools/run_calibration_tests.py
    python tools/serve_results.py

The browser-based result viewer is used for visual route comparison.

## 4. Generated Profiles

The current development test set contains six profiles:

    moto-fast
    moto-fast-curvy
    moto-curvy
    moto-very-curvy
    moto-curvy-hilly
    moto-curvy-very-hilly

All six remain useful during calibration.

The current release candidates are:

    moto-fast
    moto-curvy
    moto-very-curvy

The remaining profiles are retained as experimental or diagnostic
parameter combinations.

## 5. Smoke Tests

Smoke tests answer the basic question:

> Can every generated profile successfully calculate a route?

They are intended to detect problems such as:

-   invalid BRF syntax
-   unsupported lookup values
-   missing generated profiles
-   broken expressions
-   BRouter HTTP errors
-   changes that make a profile unusable

Smoke tests are not intended to evaluate route quality.

## 6. Smoke-Test Baseline

The smoke test uses a known route between Biel/Bienne and Neuchatel.

A successful run should return one `[OK]` result for every development
profile.

Example:

    python tools/run_smoke_tests.py

A failure must be investigated before calibration results are considered
meaningful.

## 7. Calibration Tests

Calibration tests compare the behaviour of profiles across routes with
different characteristics.

For each profile, the test tooling records values including:

-   distance
-   estimated travel time
-   ascent
-   BRouter routing cost

The generated GeoJSON routes can then be inspected visually.

## 8. Route-Choice Categories

A key lesson from calibration is that route length alone does not
determine whether a route is useful for comparing profiles.

The amount of real route choice is more important.

Three categories are used.

### 8.1 High-choice routes

Several plausible corridors or road types exist.

These routes are particularly useful for distinguishing profiles.

Possible alternatives may include:

-   motorway
-   major through-road
-   secondary-road corridor
-   rural road
-   pre-alpine or hill corridor

### 8.2 Mixed-choice routes

Only part of the route provides meaningful alternatives.

Other sections may be constrained by geography or infrastructure.

These routes are useful for observing whether profile behaviour remains
sensible over longer journeys.

Profile differences should be evaluated primarily on the sections where
real choice exists.

### 8.3 Constrained routes

The road network or topography provides effectively one practical
corridor.

Such routes are useful as regression tests but provide little
information about profile differentiation.

Identical routes are expected and are not considered a failure.

## 9. Test Types

The calibration suite distinguishes three functional test types.

### 9.1 Regression tests

Question:

> Does the routing model continue to produce sensible routes?

Regression tests are intended to detect unintended side effects.

A route does not need to produce different results across profiles.

### 9.2 Behaviour tests

Question:

> Does each profile exhibit the routing character it claims to
> represent?

These are the primary tests for deciding whether a profile provides
enough user value to justify its existence.

### 9.3 Diagnostic tests

Question:

> Why does a particular routing behaviour occur?

A diagnostic test may split a long route into smaller sections.

Diagnostic tests are used to understand the cost model.

They must not be used as justification for route-specific tuning.

## 10. Biel/Bienne -\> Neuchatel

### Role

Regression and topographical behaviour test.

### Characteristics

The route follows a geographically constrained area around the lakes.

A hill chain north of the lakes creates a meaningful distinction between
a flatter lake corridor and a hillier alternative.

### Observations

Testing produced two broad route families.

Fast-oriented and moderately Curvy routing frequently use a similar lake
corridor.

Stronger Curvy and Hilly variants may move into the hill corridor.

### Interpretation

This is useful for observing topographical behaviour but is not an ideal
general-purpose calibration route.

The geography strongly determines the available alternatives.

A conceivable alternative south of the first lake and later crossing
toward the northern shore illustrates why local geographic knowledge
must not be converted directly into routing rules.

## 11. Bern -\> Luzern

### Role

High-choice behaviour test.

### Characteristics

The route provides meaningful choices between efficient major-road
routing and more motorcycle-oriented secondary-road corridors.

### Observations

Fast-oriented profiles form a clearly different route family from the
more Curvy profiles.

Curvy and Very Curvy can select substantially different routes with
relatively few shared sections.

### Interpretation

This is one of the strongest current tests for demonstrating that Very
Curvy has a distinct routing character.

It also demonstrates that the Curviness parameter can affect complete
corridor selection rather than merely producing small local deviations.

## 12. Thun -\> Andermatt

### Role

Mixed-choice alpine behaviour test.

### Characteristics

The western part of the route provides several meaningful alternatives.

A large part of the eastern section is constrained by alpine geography
and the available pass-road network.

Approximately 70 km of the roughly 115 km journey provide very limited
practical route choice.

### Observations

Fast and Curvy profile families differ meaningfully in the sections
where alternatives exist.

The complete routes may nevertheless appear relatively similar because a
large part of the journey converges onto the same road corridor.

### Interpretation

This route demonstrated an important testing principle:

> Profile differentiation must be evaluated relative to the portion of
> the journey where meaningful alternatives exist, not merely relative
> to total route length.

## 13. Thun -\> Interlaken

### Role

Diagnostic test.

### Observations

The profiles form two clear route families:

    moto-fast
    moto-fast-curvy

and:

    moto-curvy
    moto-very-curvy
    moto-curvy-hilly
    moto-curvy-very-hilly

### Interpretation

The test confirms that the Curvy model already influences route choice
before the more constrained alpine section of the longer Thun -\>
Andermatt journey.

## 14. Interlaken -\> Brienz

### Role

Diagnostic high-choice test.

### Characteristics

Two clearly different corridors exist around Lake Brienz.

A fast corridor is available via the A8.

An attractive through-road runs along the northern shore through the
Ringgenberg, Niederried and Oberried area.

### Observations

When this section is routed independently, the Curvy profile family
selects the northern alternative.

The Fast family selects the faster corridor.

### Interpretation

This test is particularly important because it demonstrates that the
routing model is capable of recognising the northern through-road as an
attractive motorcycle alternative.

The fact that the visual effect may be less obvious on the complete Thun
-\> Andermatt route must therefore not be interpreted as evidence that
the northern road is incorrectly classified.

No Lake-Brienz-specific routing rule is required or desired.

## 15. Brienz -\> Andermatt

### Role

Diagnostic constrained-route test.

### Characteristics

The route is strongly determined by alpine geography and the available
pass roads.

There is little realistic corridor choice over a substantial portion of
the route.

### Interpretation

Profile convergence on this section is expected.

The test helps explain why the complete Thun -\> Andermatt route can
visually understate the differences observed in its western sections.

## 16. Zuerich -\> Davos

### Role

Long-distance alpine behaviour and regression test.

### Characteristics

The route combines long-distance travel with alpine terrain.

### Observations

Fast and Curvy profile families show different behaviour.

Several of the stronger Curvy and Hilly profiles can converge onto
similar corridors.

### Interpretation

The route is useful for verifying that the routing model remains
plausible over a longer alpine journey.

It also contributed to the observation that Curviness and Hilliness are
often correlated in real road networks.

## 17. Aigle -\> Martigny

### Role

Constrained regression test.

### Characteristics

The route is relatively short and follows a valley with limited
meaningful alternatives.

### Observations

Profile differences are small.

### Interpretation

This is expected.

The route is not particularly useful for profile differentiation, but
remains valuable for detecting unreasonable routing behaviour.

## 18. Biel/Bienne -\> Rotkreuz

### Role

High-choice behaviour test.

### Characteristics

The route crosses a substantial part of the Swiss Plateau and provides
multiple realistic combinations of motorway, major roads and
secondary-road corridors.

### Observations

Curvy and Very Curvy differ clearly over an initial portion of the
journey and later converge.

### Interpretation

The route provides useful evidence that Very Curvy can produce a
reproducible additional routing preference without requiring a
completely different route from start to destination.

## 19. Biel/Bienne -\> Cham

### Role

Former high-choice behaviour test.

### Observations

The test produced behaviour very similar to Biel/Bienne -\> Rotkreuz.

### Decision

The route was removed from the primary calibration set because the two
tests were considered too similar to provide sufficient independent
information.

This reflects a general test-suite principle:

> More test routes are not automatically better if they exercise
> essentially the same geographic and routing choices.

## 20. Lausanne -\> Thun

### Role

Long-distance high-choice behaviour test.

### Characteristics

The route combines motorway-oriented travel with rural and pre-alpine
alternatives.

### Observations

Fast and Fast Curvy showed some differences, particularly near the
beginning of the journey and around the Bern area.

On other test routes, however, Fast and Fast Curvy frequently remain
identical.

Curvy and Curvy Hilly did not show a meaningful difference.

### Interpretation

The test helped clarify the character of Fast Curvy.

When differences occur, they tend to appear before entering a dominant
motorway corridor or after leaving it.

This behaviour is plausible, but across the complete test set the
additional user value remains limited.

## 21. Fribourg -\> Altdorf

### Role

High-choice behaviour and topographical test.

### Characteristics

The route provides combinations of major-road, motorway, rural,
pre-alpine and more topographically varied alternatives.

### Observations

Curvy and Curvy Hilly differ only over a small portion of the route,
approximately five percent in visual inspection.

### Interpretation

This is significant because the route was deliberately selected as a
case where Hilliness had a reasonable opportunity to demonstrate
independent behaviour.

The limited difference adds evidence that a separate Hilly user profile
is not currently justified.

## 22. Fribourg -\> Ilanz

### Role

Long-distance alpine behaviour and regression test.

### Characteristics

This is a substantially longer route combining high-speed travel, rural
corridors and increasingly constrained alpine geography.

### Observations

The current routing behaviour was visually verified as plausible.

Fast, Curvy and Very Curvy remain meaningful routing concepts over the
longer journey.

### Interpretation

The test provides additional evidence that the current release
candidates do not depend solely on short or geographically narrow
calibration routes.

## 23. Fast vs. Fast Curvy

Fast Curvy was originally intended as an intermediate user profile:

    Fast
      ->
    Fast Curvy
      ->
    Curvy

Across the test set, Fast and Fast Curvy frequently produce identical
routes.

Differences have been observed on some longer routes, including sections
of Lausanne -\> Thun and Biel/Bienne -\> Cham.

These differences tend to occur near the transition between local roads
and a dominant motorway corridor.

This behaviour is plausible:

> Fast Curvy remains strongly time-oriented but may choose a more
> attractive local alternative where the time difference is small.

However, the difference is not sufficiently frequent or substantial
across the current test set to justify another user-facing profile.

Current decision:

    retain as internal calibration level
    do not include in initial user-facing release

## 24. Curvy vs. Very Curvy

Curvy and Very Curvy produce reproducible differences.

On many routes these are relatively small local deviations.

On some routes the difference is much stronger.

Bern -\> Luzern is the clearest current example, with substantially
different route alternatives and relatively little overlap.

Biel/Bienne -\> Rotkreuz also demonstrates meaningful differences over
part of the route.

Current decision:

    retain Curvy
    retain Very Curvy
    include both as initial release candidates

## 25. Curvy vs. Curvy Hilly

Across most current test routes:

    Curvy == Curvy Hilly

or the difference is very small.

Fribourg -\> Altdorf produced a difference over only a small fraction of
the journey.

This supports the hypothesis that Curviness and Hilliness are strongly
correlated in the road networks currently tested.

Curvy already tends to prefer many of the secondary, tertiary and
topographically varied roads that a Hilly preference would favour.

Current decision:

    retain Hilliness in the internal model
    retain Hilly presets for experimentation
    do not include a separate Hilly profile in the initial release

## 26. Curvy Very Hilly

Curvy Very Hilly remains useful as an experimental extreme.

It helps determine whether stronger topographical weighting creates
meaningful behaviour.

Current testing does not demonstrate sufficient independent user value
to justify its inclusion in the initial release.

Current decision:

    retain as experimental profile
    do not include in initial user-facing release

## 27. Current Profile Decision

The current initial release candidates are:

    moto-fast
    moto-curvy
    moto-very-curvy

Experimental and calibration profiles remain:

    moto-fast-curvy
    moto-curvy-hilly
    moto-curvy-very-hilly

The experimental profiles should not be removed from the development
model merely because they are not released to users.

They remain useful for:

-   calibration
-   regression analysis
-   future model research
-   evaluating whether additional user profiles become useful later

## 28. Why Three User Profiles

The current three-profile set provides a simple and understandable
progression:

    Fast
      |
      v
    Curvy
      |
      v
    Very Curvy

Fast prioritises travel efficiency.

Curvy accepts moderate additional travel cost for motorcycle-oriented
road character.

Very Curvy accepts a stronger trade-off and can select substantially
different alternatives where the road network provides them.

The distinction can be explained to a rider without exposing BRouter
cost parameters.

## 29. Hilliness Decision

Hilliness remains a valid conceptual dimension.

Its absence from the initial user-facing profile set does not mean the
concept has been rejected.

Instead, current testing indicates that:

1.  Curviness already captures much of the same real-world road network.
2.  Separate Hilly profiles rarely produce meaningfully different
    routes.
3.  Adding such profiles would increase user choice without currently
    providing equivalent user value.

The parameter therefore remains available for future development.

## 30. Profile Reduction as a Positive Result

The project deliberately began with a broader parameter space.

Calibration was used to determine which combinations provide actual user
value.

Reducing six development presets to three user-facing profiles is
therefore a successful calibration result rather than a loss of
functionality.

The internal model remains richer than the public interface.

## 31. Future Validation

The current calibration set is heavily based on Switzerland.

Before declaring the routing model broadly stable, additional validation
should include geographically different road networks.

Useful future regions include:

-   Jura
-   Black Forest
-   Vosges
-   alpine regions outside Switzerland
-   flatter rural areas
-   regions with different OpenStreetMap tagging practices

The objective is to verify that current behaviour generalises beyond
Swiss geography and mapping conventions.

## 32. Future Automated Comparison

Current visual comparison is highly valuable but partly manual.

Future tooling may automatically compare generated routes using metrics
such as:

-   shared route percentage
-   unique route percentage
-   distance difference
-   travel-time difference
-   ascent difference
-   motorway share
-   road-class distribution
-   geographic corridor similarity

Such metrics should complement rather than replace visual evaluation.

## 33. Route Similarity

A particularly useful future metric would quantify how much two profiles
actually share the same road geometry.

For example:

    Fast vs Curvy
        35% shared

    Curvy vs Very Curvy
        82% shared

This would provide a more objective basis for deciding whether two
profiles are meaningfully different.

Care must be taken with GPS geometry and parallel carriageways, which
can make simple coordinate comparison misleading.

## 34. Future Regression Baselines

Once the first release is stable, selected route results should become
formal regression baselines.

A future model change could then report:

-   unchanged route
-   small deviation
-   major corridor change
-   distance delta
-   time delta
-   ascent delta

Major changes should be reviewed before modifying a released routing
model.

## 35. Release Validation

Before an initial release, the following should be true:

-   all generated profiles pass smoke tests
-   Fast produces plausible efficient routes
-   Curvy produces meaningful alternatives where available
-   Very Curvy demonstrates a stronger but still plausible preference
-   motorways remain available unless explicitly disabled
-   residential and service-road routing remains conservative
-   constrained routes do not produce artificial detours
-   experimental profiles remain available for calibration
-   documentation reflects the actual model behaviour
-   generated release profiles work with BRouter and OsmAnd on Android

## 36. Optional-Evidence Coverage and Scope Tests

Optional evidence must be tested for applicability and coverage as well
as for apparent routing quality.

### 36.1 Coverage-by-Road-Class Result

The ten-route baseline traffic catalogue produced:

``` text
Highway              Distance      Known    Missing   Known %  Missing %
motorway              169.64 km      0.00     169.64      0.0      100.0
secondary              96.96 km     96.93       0.03    100.0        0.0
primary                93.96 km     93.90       0.06     99.9        0.1
trunk                  13.57 km      0.00      13.57      0.0      100.0
tertiary                8.98 km      8.98       0.00    100.0        0.0
unclassified            8.35 km      0.00       8.35      0.0      100.0
motorway_link           7.88 km      0.00       7.88      0.0      100.0
living_street           3.15 km      0.00       3.15      0.0      100.0
residential             1.80 km      0.00       1.80      0.0      100.0
trunk_link              0.61 km      0.00       0.61      0.0      100.0
service                 0.23 km      0.00       0.23      0.0      100.0
primary_link            0.16 km      0.16       0.00    100.0        0.0
```

Overall:

``` text
known     199.97 km   49.3 %
missing   205.34 km   50.7 %
```

The overall percentage is not a useful description by itself.
Missingness is strongly structured by road class.

For H2 traffic semantics, uncovered road classes should therefore be
treated as outside the observed applicability scope rather than as
low-traffic roads.

### 36.2 Traffic-Class Matrix

Within covered road classes, the baseline catalogue observed:

``` text
primary
    C2   1.84 km
    C3  27.69 km
    C4  33.88 km
    C5  18.65 km
    C6  11.84 km

secondary
    C2  14.74 km
    C3  47.78 km
    C4  19.43 km
    C5  11.36 km
    C6   3.62 km

tertiary
    C3   0.97 km
    C4   3.92 km
    C5   4.09 km
```

Overall known traffic distribution:

``` text
C2   16.58 km    8.3 %
C3   76.44 km   38.2 %
C4   57.23 km   28.6 %
C5   34.14 km   17.1 %
C6   15.57 km    7.8 %
```

The spread within primary and secondary demonstrates that H2 is not
merely a one-to-one restatement of H1 road class. It provides additional
heuristic differentiation inside covered road classes.

### 36.3 Regression Principle

Future H2 traffic experiments shall satisfy:

``` text
missing / not applicable evidence
    -> no fabricated value
    -> no automatic routing advantage
    -> no silent substitution
```

Bern -\> Burgdorf and Solothurn -\> Langenthal remain regression cases
for the failure mode where additive traffic penalties push routing
toward motorway corridors outside H2 traffic scope.

Huttwil and Worb remain useful local inspection cases for unintended
shifts toward local or unclassified roads.

### 36.4 Next Traffic Test

The next experiment shall be a road-class-aware H2 traffic test.

It shall:

-   apply H2 only where the traffic heuristic is applicable,
-   interpret traffic class in H1 road-class context,
-   use conservative weights,
-   keep the base motorcycle-road model independent,
-   compare the complete route catalogue,
-   inspect all changed geometries visually,
-   avoid tuning around a single location.

No H3 measured traffic data is required for this test.

### 36.5 Road-Class-Aware H2 Result

The road-class-aware additive H2 experiment used conservative low,
medium and strong traffic modifiers only on primary, secondary and
tertiary roads.

The experiment successfully removed the earlier structural bias toward
motorway corridors caused by globally penalising roads with known
`estimated_traffic_class` values.

However, visual inspection showed that additive negative evidence could
still cause undesirable local rerouting:

``` text
Fribourg -> Altdorf / Huttwil
    baseline remains on the main road
    strong H2 leaves it for a neighbourhood road

Neuchatel -> La Chaux-de-Fonds
    baseline remains on the main road after leaving the A20
    medium H2 takes a local neighbourhood route to the destination

Bern -> Burgdorf
    low H2 changes only a local hill-side routing decision
```

The conclusion is that road-class-aware scope solves the coverage-bias
problem but does not by itself make additive negative H2 evidence safe.

### 36.6 Gated H2 Experiment

A gated evidence experiment was therefore introduced.

Instead of penalising roads with high H2 traffic classes, H2 was allowed
only to provide a small positive preference when:

``` text
H2 is AVAILABLE
and
H1 identifies a suitable through-road class
and
H2 traffic evidence is favourable
```

The first gated variant used favourable evidence only for traffic
classes C2 and C3 on primary, secondary and tertiary roads.

All other states were neutral:

``` text
C4 / C5 / C6
    -> no H2 modification

MISSING
    -> no H2 modification

NOT_APPLICABLE
    -> no H2 modification
```

This directly implements the principles:

``` text
missing evidence is not evidence

absence must not become an advantage

H2 may support H1 but must not replace it
```

### 36.7 Gated H2 Result

The complete ten-route catalogue was tested with:

``` text
baseline
h2-low
h2-gated
```

The additive `h2-low` reference still changed Bern -\> Burgdorf.

The gated variant produced no geometry change on any of the ten routes.

Representative results:

``` text
Bern -> Burgdorf
    baseline   23.2 km   32.4 min   244 m   cost 43943
    h2-low     22.8 km   32.7 min   256 m   cost 44667   changed
    h2-gated   23.2 km   32.4 min   244 m   cost 43943   baseline geometry

Fribourg -> Altdorf
    baseline   cost 247621
    h2-gated   cost 247609
    geometry unchanged

Biel -> Neuchatel
    baseline   cost 52215
    h2-gated   cost 52209
    geometry unchanged

Bern -> Langnau
    baseline   cost 55625
    h2-gated   cost 55619
    geometry unchanged
```

The result confirms the safety hypothesis of the gated model:

-   the known coverage bias does not return,
-   the Huttwil neighbourhood detour does not return,
-   the La Chaux-de-Fonds neighbourhood detour does not return,
-   no new geometry regression appears in the catalogue.

The initial gated weights are nevertheless too weak to produce a
route-choice change. The next experiment is therefore a gated
sensitivity test that changes only the strength of positive H2 evidence
while keeping the gating semantics unchanged.

## 37. Urban-Context and Core-Burden Validation

Settlement-context research is treated as an optional-evidence
validation problem before it becomes a routing-cost experiment.

The initial diagnostic uses local rolling windows rather than route-wide
averages. This is intended to detect sustained local settlement context
while avoiding the assumption that one isolated tag defines an
unattractive urban section.

The first controlled cases are Aarberg and Buren. They compare
acceptable bypass/through-road geometry with deliberately undesirable
routes through the settlement core.

Current diagnostic observations include:

``` text
Aarberg
    acceptable bypass:       longest strict-core run =   0 m
    undesirable core route:  longest strict-core run = 243 m

Buren
    acceptable bypass:       strict-core runs = 2 x 166 m
    undesirable core route:  longest strict-core run = 427 m
```

These values are diagnostic observations, not acceptance thresholds.

### Validation requirements

Before any production routing modifier is considered, the core-burden
hypothesis shall be tested on a broader catalogue containing:

-   acceptable bypasses and through-routes,
-   undesirable settlement-core routes,
-   rural negative controls,
-   routes with short unavoidable village passages,
-   routes with different road hierarchies,
-   geographically independent cases.

A successful validation should demonstrate that:

1.  sustained core-like exposure is more characteristic of undesirable
    settlement routing than of acceptable through-routes,
2.  short isolated core-like sections do not automatically make a route
    bad,
3.  rural controls do not acquire false urban burden,
4.  missing H2 evidence is not interpreted as rural evidence,
5.  the result does not depend on Aarberg- or Buren-specific thresholds.

### Test methodology

The preferred sequence is:

``` text
ground-truth cases
    ->
feature extraction in local windows
    ->
contiguous core-burden diagnostics
    ->
cross-case comparison
    ->
visual geometry inspection
    ->
only then: routing-cost experiment
```

No score, weighting or routing penalty should be introduced during the
diagnostic phase.

If a later routing-cost experiment is justified, it must be evaluated
against the normal regression catalogue to ensure that settlement
avoidance does not create neighbourhood detours, motorway shifts or
other unrelated corridor changes.


### Independent `strict_core` validation result

The frozen `strict_core` predicate was tested after visual ground-truth
validation on Murten, Solothurn, Langenthal and Willisau. Aarberg and Buren
remained excluded calibration cases.

All eight independent routes returned zero `strict_core` distance:

```text
Murten       bypass 0 m   core 0 m
Solothurn    bypass 0 m   core 0 m
Langenthal   bypass 0 m   core 0 m
Willisau     bypass 0 m   core 0 m
```

This fails the required independent positive-control test. The predicate must
not be promoted to a general core detector or converted into a routing
threshold. It may only remain available as optional high-confidence evidence
where the underlying tags are present.

### Local-excursion diagnostic result

A structural through-road -> local-road -> through-road diagnostic was then
tested without changing routing cost.

Results showed longer detected excursions on every acceptable bypass than on
its paired core route:

```text
Murten       bypass 1204 m   core 994 m
Solothurn    bypass  458 m   core 358 m
Langenthal   bypass  502 m   core 268 m
Willisau     bypass  118 m   core   0 m
```

The Emmental rural control also produced a 2134 m local excursion.

This diagnostic therefore fails semantic validation and must not be turned
into a threshold or penalty. In Willisau the difference is mainly a southern
branch through apparently sparsely settled terrain, showing directly why
local-road hierarchy is not equivalent to undesirable urban routing.

### Test decision

Both branches are closed as general routing mechanisms:

```text
strict_core detector       -> rejected as general detector
local-excursion detector   -> rejected as burden proxy
```

Future settlement-routing tests should return to continuous evidence
diagnostics rather than binary core detection.

The next diagnostic phase should compare a small set of robust evidence
components across:

- accepted city through-routes,
- valid bypasses,
- deliberately undesirable alternatives,
- normal village passages,
- rural controls.

No production routing-cost experiment should start until such a continuous
burden representation demonstrates useful ordering on independent cases.


## 38. Current Testing Status

The current model has reached a point where the primary routing concepts
are considered plausible.

Testing has provided evidence for:

-   a meaningful Fast profile
-   a meaningful Curvy profile
-   a distinct Very Curvy profile
-   insufficient user-facing differentiation for Fast Curvy
-   insufficient user-facing differentiation for Hilliness
-   correct handling of situations where geography limits route choice
-   the importance of distinguishing local route behaviour from complete
    end-to-end route behaviour

The next phase should focus on release consolidation and tooling rather
than continued parameter tuning without new evidence.

## 39. Final Urban-Burden Routing Validation

After the diagnostic branches had been closed, one bounded production-cost
experiment was allowed. It used only already investigated evidence:
`estimated_traffic_class`, `estimated_town_class` and `strict_core` as optional
high-confidence evidence.

The stopping rule was fixed in advance: v0.1 -> at most one v0.2 -> final
urban decision. Both strengths produced the same outcome on 12 cases: 11
routes were unchanged; only Zurich changed, selecting another plausible bridge
and shortening from 7.44 km to 7.01 km (-5.8 %). The bridge choice was judged
neutral without reliable traffic-volume knowledge. Aarberg and Buren remained
unchanged.

The urban-burden modifier is therefore **not accepted into the v1 production
routing model**. There were no clear regressions, but also no demonstrated
benefit in the calibration cases. Increasing the strength further merely to
force route changes would violate the generalisation requirement and risk
local overfitting.

The production `moto-curvy` profile remains unchanged by the urban
investigation. Reconsideration requires materially better independent evidence
or a new general hypothesis, not another weighting iteration.

## 40. v1 Routing-Core Acceptance and Freeze

The v1 routing core was subjected to a final acceptance pass after the urban
investigation had been closed. This pass was deliberately a validation step,
not another calibration loop.

### 40.1 Routing characters

The release characters `fast`, `curvy` and `very-curvy` were compared on a
mixed catalogue of short, long, alpine and high-choice routes.

Visual review produced the following acceptance observations:

- Neuchatel -> Biel: Fast and Curvy converge; Very Curvy provides a good,
  distinctly curvier alternative.
- Bern -> Luzern: all three characters produce clearly different and plausible
  routes. This is the strongest positive differentiation case.
- Thun -> Andermatt: Curvy and Very Curvy are similar, with only a small
  difference around Interlaken. The long-route result also illustrates that a
  locally attractive sub-route need not be selected by the global optimum.
- Interlaken -> Brienz: Curvy and Very Curvy converge on the expected scenic
  north-side route, while Fast selects the expected faster corridor. This
  supports segment-based planning.
- Brienz -> Andermatt: all three converge, as expected from the geographically
  constrained pass corridor.
- Zurich -> Davos: Fast behaves as expected; Curvy and Very Curvy show
  meaningful, plausible differentiation.
- Aigle -> Martigny: Fast and Curvy remain close, while Very Curvy selects a
  distinctly more winding route.
- Fribourg -> Altdorf: Fast selects its own motorway-oriented corridor; Curvy
  and Very Curvy differ substantially in the final third, with Very Curvy
  providing the stronger winding-road character.

Acceptance decision: `fast`, `curvy` and `very-curvy` are accepted as the v1
routing characters. Convergence is explicitly acceptable where geography or
constraints leave no meaningful alternative.

### 40.2 Hilliness

The planner-level hilliness preference passed all three defined regression
cases:

| Route | Hills | Selection | Distance | Time | Ascent | Cost |
|---|---|---|---:|---:|---:|---:|
| Biel/Bienne -> Neuchatel | strong | BRouter alt 2 | 40.3 km | 48.2 min | 810 m | 70011 |
| Fribourg -> Altdorf | moderate | BRouter alt 2 | 172.9 km | 185.6 min | 2090 m | 308341 |
| Thun -> Andermatt | strong | baseline | 113.3 km | 132.1 min | 2674 m | 196336 |

This confirms the intended semantics: hilliness may select a meaningfully
hillier acceptable alternative, but it does not simply maximise ascent.
Already mountainous routes may correctly retain the baseline.

### 40.3 Constraints

`avoid_motorways` and `avoid_toll` were validated as independent constraints.

Bern -> Luzern with `avoid_motorways` produced the same constrained corridor
for Fast and Curvy:

| Character | Distance | Time | Ascent |
|---|---:|---:|---:|
| Fast | 84.0 km | 101.3 min | 875 m |
| Curvy | 84.0 km | 101.3 min | 875 m |

This convergence is acceptable because the hard constraint substantially
reduces the available corridor choice.

Martigny -> Aosta confirmed the semantic separation:

| Intention | Distance | Time | Ascent | Cost |
|---|---:|---:|---:|---:|
| Fast + avoid motorways | 73.2 km | 83.9 min | 1473 m | 115474 |
| Fast + avoid toll | 77.9 km | 102.1 min | 2023 m | 140871 |

The two controls must therefore remain separate planner constraints.

### 40.4 Freeze decision

The v1 routing core is accepted and frozen.

The accepted v1 routing model consists of:

```text
routing characters:
    fast
    curvy
    very-curvy

constraints:
    avoid_motorways
    avoid_toll

secondary preference:
    hills:
        off
        moderate
        strong
```

No further routing-weight calibration is planned for v1. Changes to routing
weights or semantics require either a reproducible regression defect or
materially new independent evidence. Cosmetic differentiation between profiles
is not sufficient reason to change the model.
