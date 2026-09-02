# Pseudo-Tag Sensitivity Test

This version fixes two issues in the first sensitivity-test generator.

1. The generated baseline contained `assign semantic_factor =1.00`. BRouter's
   expression parser expects the assignment token to be separated correctly.

2. More importantly, the first generator multiplied `road_character_cost` by a
   semantic factor. That couples traffic/town semantics to the existing
   road-character penalty and gives no independent effect where
   `road_character_cost` is zero.

The corrected experiment uses an additive BRF costfactor contribution:

```text
final BRF costfactor
    =
road_character_cost
    +
semantic_penalty
```

The three strengths are calibration ranges:

```text
low
medium
probe
```

`probe` is deliberately strong and is not a production candidate.

Run:

```bash
python tools/run_semantic_sensitivity_tests.py
```
