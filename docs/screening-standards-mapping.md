# Pre-screen standards mapping (parallel scores)

This demo keeps the **course rule triage** as the unlock gate for deep assessment.
Beside that gate it computes two **parallel** standard-inspired scores for trust and explanation.

## What still unlocks `#assess`

Unchanged project rules:

| Class | Rule |
| --- | --- |
| Insomnia | ≥2 yes among items 1, 6, 9 |
| Sleep Apnea | ≥2 yes in the apnea item set, **or** red-flag yes on 3, 4, or 12 |
| None | neither group flagged (optional deep path remains available) |

## STOP-Bang (parallel)

Classic STOP-Bang items mapped onto available demo inputs:

| Item | Meaning | Demo source |
| --- | --- | --- |
| S | Snoring | Screen q2 |
| T | Tired / daytime sleepiness | Screen q11 |
| O | Observed apnea | Screen q3 |
| P | Blood pressure | **Unavailable** (BP removed from demo features) |
| B | BMI > 35 | Deep-form BMI |
| A | Age > 50 | Deep-form age |
| N | Neck circumference | **Unavailable** |
| G | Male gender | Deep-form gender |

Bands used for display: 0–2 low, 3–4 intermediate, 5–8 high (counted only over answered items).

Reference: Chung F, Abdullah HR, Liao P. STOP-Bang questionnaire. *Chest*. 2016;149(3):631–638.

## ISI-inspired subset (parallel)

Not the full published ISI. Mapped subset only:

| Domain proxy | Demo source | Points if yes |
| --- | --- | --- |
| Sleep onset | Screen q1 | 2 |
| Sleep maintenance | Screen q6 | 2 |
| Early waking | Screen q9 | 2 |
| Daytime interference | Screen q11 | 2 |
| Daytime concentration | Screen q13 | 1 |
| Sleep satisfaction | Deep-form Quality of Sleep (inverted to 0–4) | 0–4 |

Display bands reuse common ISI total ranges on this subset score (max 13): ≤7, 8–14, 15–21, ≥22.

## Where it appears

- `#screen` triage result: partial STOP-Bang / ISI from questionnaire answers
- `#result`: refreshed with BMI / age / gender / sleep quality when present
- `#trust`: mapping summary for demos and reports
- Anonymous assessment logs store the computed `standards` object with the triage payload
