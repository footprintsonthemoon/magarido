# BRouter Motorcycle Profiles – Testing and Calibration

## 1. Purpose

This document describes the testing and calibration methodology used by the
BRouter Motorcycle Profiles project.

Testing has three main objectives:

1. verify that generated profiles are technically valid,
2. verify that routing behaviour remains plausible,
3. determine whether different profiles provide meaningful and reproducible
   user value.

The objective is not to make every profile generate a different route for every
test case.

Identical routes are expected when geography, infrastructure or travel-time
differences provide no meaningful alternative.


## 2. Testing Principles

### 2.1 Test behaviour, not visual difference

A profile is not successful merely because its route looks different.

A difference should correspond to the intended routing behaviour.

For example:

- Fast should favour travel efficiency.
- Curvy should accept reasonable additional cost for attractive roads.
- Very Curvy should accept a stronger trade-off.
- Hilliness should only matter where meaningful topographical alternatives
  exist.


### 2.2 Identical routes are valid results

Two profiles may legitimately select the same route.

This can occur when:

- there is effectively only one practical road,
- an alternative is disproportionately slower,
- topography constrains the corridor,
- both profiles evaluate the available roads similarly.

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

A change is accepted only when it improves the general model without creating
unreasonable behaviour elsewhere.


### 2.4 Human evaluation matters

Numeric output alone cannot determine whether a motorcycle route is attractive.

Automated tests provide:

- route length
- estimated travel time
- ascent
- BRouter cost
- technical success or failure

Visual inspection and local knowledge provide additional information about:

- route character
- meaningful corridor differences
- unrealistic detours
- motorway use
- village and residential routing
- real-world motorcycle attractiveness

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

The remaining profiles are retained as experimental or diagnostic parameter
combinations.


## 5. Smoke Tests

Smoke tests answer the basic question:

> Can every generated profile successfully calculate a route?

They are intended to detect problems such as:

- invalid BRF syntax
- unsupported lookup values
- missing generated profiles
- broken expressions
- BRouter HTTP errors
- changes that make a profile unusable

Smoke tests are not intended to evaluate route quality.


## 6. Smoke-Test Baseline

The smoke test uses a known route between Biel/Bienne and Neuchatel.

A successful run should return one `[OK]` result for every development profile.

Example:

    python tools/run_smoke_tests.py

A failure must be investigated before calibration results are considered
meaningful.


## 7. Calibration Tests

Calibration tests compare the behaviour of profiles across routes with
different characteristics.

For each profile, the test tooling records values including:

- distance
- estimated travel time
- ascent
- BRouter routing cost

The generated GeoJSON routes can then be inspected visually.


## 8. Route-Choice Categories

A key lesson from calibration is that route length alone does not determine
whether a route is useful for comparing profiles.

The amount of real route choice is more important.

Three categories are used.


### 8.1 High-choice routes

Several plausible corridors or road types exist.

These routes are particularly useful for distinguishing profiles.

Possible alternatives may include:

- motorway
- major through-road
- secondary-road corridor
- rural road
- pre-alpine or hill corridor


### 8.2 Mixed-choice routes

Only part of the route provides meaningful alternatives.

Other sections may be constrained by geography or infrastructure.

These routes are useful for observing whether profile behaviour remains
sensible over longer journeys.

Profile differences should be evaluated primarily on the sections where real
choice exists.


### 8.3 Constrained routes

The road network or topography provides effectively one practical corridor.

Such routes are useful as regression tests but provide little information about
profile differentiation.

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

> Does each profile exhibit the routing character it claims to represent?

These are the primary tests for deciding whether a profile provides enough
user value to justify its existence.


### 9.3 Diagnostic tests

Question:

> Why does a particular routing behaviour occur?

A diagnostic test may split a long route into smaller sections.

Diagnostic tests are used to understand the cost model.

They must not be used as justification for route-specific tuning.


## 10. Biel/Bienne -> Neuchatel

### Role

Regression and topographical behaviour test.

### Characteristics

The route follows a geographically constrained area around the lakes.

A hill chain north of the lakes creates a meaningful distinction between a
flatter lake corridor and a hillier alternative.

### Observations

Testing produced two broad route families.

Fast-oriented and moderately Curvy routing frequently use a similar lake
corridor.

Stronger Curvy and Hilly variants may move into the hill corridor.

### Interpretation

This is useful for observing topographical behaviour but is not an ideal
general-purpose calibration route.

The geography strongly determines the available alternatives.

A conceivable alternative south of the first lake and later crossing toward
the northern shore illustrates why local geographic knowledge must not be
converted directly into routing rules.


## 11. Bern -> Luzern

### Role

High-choice behaviour test.

### Characteristics

The route provides meaningful choices between efficient major-road routing and
more motorcycle-oriented secondary-road corridors.

### Observations

Fast-oriented profiles form a clearly different route family from the more
Curvy profiles.

Curvy and Very Curvy can select substantially different routes with relatively
few shared sections.

### Interpretation

This is one of the strongest current tests for demonstrating that Very Curvy
has a distinct routing character.

It also demonstrates that the Curviness parameter can affect complete corridor
selection rather than merely producing small local deviations.


## 12. Thun -> Andermatt

### Role

Mixed-choice alpine behaviour test.

### Characteristics

The western part of the route provides several meaningful alternatives.

A large part of the eastern section is constrained by alpine geography and the
available pass-road network.

Approximately 70 km of the roughly 115 km journey provide very limited
practical route choice.

### Observations

Fast and Curvy profile families differ meaningfully in the sections where
alternatives exist.

The complete routes may nevertheless appear relatively similar because a large
part of the journey converges onto the same road corridor.

### Interpretation

This route demonstrated an important testing principle:

> Profile differentiation must be evaluated relative to the portion of the
> journey where meaningful alternatives exist, not merely relative to total
> route length.


## 13. Thun -> Interlaken

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

The test confirms that the Curvy model already influences route choice before
the more constrained alpine section of the longer Thun -> Andermatt journey.


## 14. Interlaken -> Brienz

### Role

Diagnostic high-choice test.

### Characteristics

Two clearly different corridors exist around Lake Brienz.

A fast corridor is available via the A8.

An attractive through-road runs along the northern shore through the
Ringgenberg, Niederried and Oberried area.

### Observations

When this section is routed independently, the Curvy profile family selects the
northern alternative.

The Fast family selects the faster corridor.

### Interpretation

This test is particularly important because it demonstrates that the routing
model is capable of recognising the northern through-road as an attractive
motorcycle alternative.

The fact that the visual effect may be less obvious on the complete
Thun -> Andermatt route must therefore not be interpreted as evidence that the
northern road is incorrectly classified.

No Lake-Brienz-specific routing rule is required or desired.


## 15. Brienz -> Andermatt

### Role

Diagnostic constrained-route test.

### Characteristics

The route is strongly determined by alpine geography and the available pass
roads.

There is little realistic corridor choice over a substantial portion of the
route.

### Interpretation

Profile convergence on this section is expected.

The test helps explain why the complete Thun -> Andermatt route can visually
understate the differences observed in its western sections.


## 16. Zuerich -> Davos

### Role

Long-distance alpine behaviour and regression test.

### Characteristics

The route combines long-distance travel with alpine terrain.

### Observations

Fast and Curvy profile families show different behaviour.

Several of the stronger Curvy and Hilly profiles can converge onto similar
corridors.

### Interpretation

The route is useful for verifying that the routing model remains plausible over
a longer alpine journey.

It also contributed to the observation that Curviness and Hilliness are often
correlated in real road networks.


## 17. Aigle -> Martigny

### Role

Constrained regression test.

### Characteristics

The route is relatively short and follows a valley with limited meaningful
alternatives.

### Observations

Profile differences are small.

### Interpretation

This is expected.

The route is not particularly useful for profile differentiation, but remains
valuable for detecting unreasonable routing behaviour.


## 18. Biel/Bienne -> Rotkreuz

### Role

High-choice behaviour test.

### Characteristics

The route crosses a substantial part of the Swiss Plateau and provides
multiple realistic combinations of motorway, major roads and secondary-road
corridors.

### Observations

Curvy and Very Curvy differ clearly over an initial portion of the journey and
later converge.

### Interpretation

The route provides useful evidence that Very Curvy can produce a reproducible
additional routing preference without requiring a completely different route
from start to destination.


## 19. Biel/Bienne -> Cham

### Role

Former high-choice behaviour test.

### Observations

The test produced behaviour very similar to Biel/Bienne -> Rotkreuz.

### Decision

The route was removed from the primary calibration set because the two tests
were considered too similar to provide sufficient independent information.

This reflects a general test-suite principle:

> More test routes are not automatically better if they exercise essentially
> the same geographic and routing choices.


## 20. Lausanne -> Thun

### Role

Long-distance high-choice behaviour test.

### Characteristics

The route combines motorway-oriented travel with rural and pre-alpine
alternatives.

### Observations

Fast and Fast Curvy showed some differences, particularly near the beginning
of the journey and around the Bern area.

On other test routes, however, Fast and Fast Curvy frequently remain
identical.

Curvy and Curvy Hilly did not show a meaningful difference.

### Interpretation

The test helped clarify the character of Fast Curvy.

When differences occur, they tend to appear before entering a dominant
motorway corridor or after leaving it.

This behaviour is plausible, but across the complete test set the additional
user value remains limited.


## 21. Fribourg -> Altdorf

### Role

High-choice behaviour and topographical test.

### Characteristics

The route provides combinations of major-road, motorway, rural, pre-alpine and
more topographically varied alternatives.

### Observations

Curvy and Curvy Hilly differ only over a small portion of the route,
approximately five percent in visual inspection.

### Interpretation

This is significant because the route was deliberately selected as a case
where Hilliness had a reasonable opportunity to demonstrate independent
behaviour.

The limited difference adds evidence that a separate Hilly user profile is not
currently justified.


## 22. Fribourg -> Ilanz

### Role

Long-distance alpine behaviour and regression test.

### Characteristics

This is a substantially longer route combining high-speed travel, rural
corridors and increasingly constrained alpine geography.

### Observations

The current routing behaviour was visually verified as plausible.

Fast, Curvy and Very Curvy remain meaningful routing concepts over the longer
journey.

### Interpretation

The test provides additional evidence that the current release candidates do
not depend solely on short or geographically narrow calibration routes.


## 23. Fast vs. Fast Curvy

Fast Curvy was originally intended as an intermediate user profile:

    Fast
      ->
    Fast Curvy
      ->
    Curvy

Across the test set, Fast and Fast Curvy frequently produce identical routes.

Differences have been observed on some longer routes, including sections of
Lausanne -> Thun and Biel/Bienne -> Cham.

These differences tend to occur near the transition between local roads and a
dominant motorway corridor.

This behaviour is plausible:

> Fast Curvy remains strongly time-oriented but may choose a more attractive
> local alternative where the time difference is small.

However, the difference is not sufficiently frequent or substantial across the
current test set to justify another user-facing profile.

Current decision:

    retain as internal calibration level
    do not include in initial user-facing release


## 24. Curvy vs. Very Curvy

Curvy and Very Curvy produce reproducible differences.

On many routes these are relatively small local deviations.

On some routes the difference is much stronger.

Bern -> Luzern is the clearest current example, with substantially different
route alternatives and relatively little overlap.

Biel/Bienne -> Rotkreuz also demonstrates meaningful differences over part of
the route.

Current decision:

    retain Curvy
    retain Very Curvy
    include both as initial release candidates


## 25. Curvy vs. Curvy Hilly

Across most current test routes:

    Curvy == Curvy Hilly

or the difference is very small.

Fribourg -> Altdorf produced a difference over only a small fraction of the
journey.

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

It helps determine whether stronger topographical weighting creates meaningful
behaviour.

Current testing does not demonstrate sufficient independent user value to
justify its inclusion in the initial release.

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

The experimental profiles should not be removed from the development model
merely because they are not released to users.

They remain useful for:

- calibration
- regression analysis
- future model research
- evaluating whether additional user profiles become useful later


## 28. Why Three User Profiles

The current three-profile set provides a simple and understandable progression:

    Fast
      |
      v
    Curvy
      |
      v
    Very Curvy

Fast prioritises travel efficiency.

Curvy accepts moderate additional travel cost for motorcycle-oriented road
character.

Very Curvy accepts a stronger trade-off and can select substantially different
alternatives where the road network provides them.

The distinction can be explained to a rider without exposing BRouter cost
parameters.


## 29. Hilliness Decision

Hilliness remains a valid conceptual dimension.

Its absence from the initial user-facing profile set does not mean the concept
has been rejected.

Instead, current testing indicates that:

1. Curviness already captures much of the same real-world road network.
2. Separate Hilly profiles rarely produce meaningfully different routes.
3. Adding such profiles would increase user choice without currently providing
   equivalent user value.

The parameter therefore remains available for future development.


## 30. Profile Reduction as a Positive Result

The project deliberately began with a broader parameter space.

Calibration was used to determine which combinations provide actual user
value.

Reducing six development presets to three user-facing profiles is therefore a
successful calibration result rather than a loss of functionality.

The internal model remains richer than the public interface.


## 31. Future Validation

The current calibration set is heavily based on Switzerland.

Before declaring the routing model broadly stable, additional validation should
include geographically different road networks.

Useful future regions include:

- Jura
- Black Forest
- Vosges
- alpine regions outside Switzerland
- flatter rural areas
- regions with different OpenStreetMap tagging practices

The objective is to verify that current behaviour generalises beyond Swiss
geography and mapping conventions.


## 32. Future Automated Comparison

Current visual comparison is highly valuable but partly manual.

Future tooling may automatically compare generated routes using metrics such
as:

- shared route percentage
- unique route percentage
- distance difference
- travel-time difference
- ascent difference
- motorway share
- road-class distribution
- geographic corridor similarity

Such metrics should complement rather than replace visual evaluation.


## 33. Route Similarity

A particularly useful future metric would quantify how much two profiles
actually share the same road geometry.

For example:

    Fast vs Curvy
        35% shared

    Curvy vs Very Curvy
        82% shared

This would provide a more objective basis for deciding whether two profiles
are meaningfully different.

Care must be taken with GPS geometry and parallel carriageways, which can make
simple coordinate comparison misleading.


## 34. Future Regression Baselines

Once the first release is stable, selected route results should become formal
regression baselines.

A future model change could then report:

- unchanged route
- small deviation
- major corridor change
- distance delta
- time delta
- ascent delta

Major changes should be reviewed before modifying a released routing model.


## 35. Release Validation

Before an initial release, the following should be true:

- all generated profiles pass smoke tests
- Fast produces plausible efficient routes
- Curvy produces meaningful alternatives where available
- Very Curvy demonstrates a stronger but still plausible preference
- motorways remain available unless explicitly disabled
- residential and service-road routing remains conservative
- constrained routes do not produce artificial detours
- experimental profiles remain available for calibration
- documentation reflects the actual model behaviour
- generated release profiles work with BRouter and OsmAnd on Android


## 36. Current Testing Status

The current model has reached a point where the primary routing concepts are
considered plausible.

Testing has provided evidence for:

- a meaningful Fast profile
- a meaningful Curvy profile
- a distinct Very Curvy profile
- insufficient user-facing differentiation for Fast Curvy
- insufficient user-facing differentiation for Hilliness
- correct handling of situations where geography limits route choice
- the importance of distinguishing local route behaviour from complete
  end-to-end route behaviour

The next phase should focus on release consolidation and tooling rather than
continued parameter tuning without new evidence.
