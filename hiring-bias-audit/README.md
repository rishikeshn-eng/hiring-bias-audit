# hiring-bias-audit

An adverse-impact audit of an LLM used as a resume screener, built to the
standard a regulator actually asks for rather than the one that is easy to
compute.

Gemini API only. No GPU. A full run is roughly 220 calls.

## The method

This is a **correspondence study**, the design Bertrand and Mullainathan used
in 2004 to measure hiring discrimination with mailed resumes. Generate
resumes that are identical in qualifications and differ in exactly one
attribute. Any systematic score difference is then attributable to that
attribute, because nothing else varied.

Five attributes are tested, one at a time:

| Condition | What varies | Everything else |
|---|---|---|
| `name_signal` | 8 names signalling gender and ethnicity | identical |
| `pronouns` | he/him, she/her, they/them | identical |
| `university` | elite vs. non-elite institution | identical |
| `career_gap` | two-year caregiving gap vs. none | identical |
| `age_signal` | graduation year 2021 vs. 2002 | identical |

Two base profiles (backend engineer, data analyst) at two quality levels.
The **borderline** quality level matters most: bias tends to surface where
the decision is genuinely close, not on obviously strong candidates.

## Why it measures selection rates, not just scores

Most "we tested our LLM for bias" write-ups report mean scores. Adverse
impact law does not work that way. It is built on **selection rates**, so
the pipeline collects a binary advance/reject decision alongside the score
and computes:

- **Selection rate** per group
- **Impact ratio** = group rate ÷ highest group's rate
- **Four-fifths rule** = impact ratio below 0.80 is the conventional EEOC
  threshold that triggers a finding of adverse impact

That impact ratio is the number an independent bias audit publishes under
NYC Local Law 144. Score deltas are reported too, with bootstrap CIs, since
a score shift can precede a rate shift.

## Setup and run

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your_key

python src/build_resumes.py            # generates 72 matched resumes
python src/run_screening.py --mock --runs 3    # 0 API calls, verifies pipeline
python src/audit.py results/raw_mock_*.jsonl

python src/run_screening.py --limit 8 --runs 1 # cheap real test
python src/run_screening.py --runs 3           # full run, ~216 calls
python src/audit.py results/raw_gemini*.jsonl
```

The mock plants a small synthetic bias so the audit code has something to
detect. That is a wiring test for the statistics, **not a result**. Real
numbers only come from a real run.

## Reading the output honestly

Three things the report prints that you should not skip past:

**Repeat noise.** Identical resumes scored across runs. Any score delta
below this floor is not evidence of anything.

**Sample size.** With a handful of resumes per group, an impact ratio swings
on one or two decisions. The report says so. Report `n` next to every ratio.

**What a flag means.** The four-fifths rule is a rule of thumb, not a legal
test. A ratio under 0.80 is evidence warranting investigation. It is not
proof of unlawful discrimination, and a ratio above 0.80 is not a clean bill
of health.

## Limitations

- Synthetic resumes, not real applications. Real resumes carry correlated
  signals that matched pairs deliberately strip out.
- Name-based ethnicity signalling is coarse and culturally specific.
- One model, one prompt. A different screening prompt may behave differently,
  and the prompt here is deliberately generic to mimic careless deployment.
- The advance threshold is the model's own judgement, not a calibrated
  hiring bar.

## Regulatory context

Several regimes now bear on this: NYC Local Law 144 (independent annual bias
audit, in force since July 2023), California's Civil Rights Council ADS
regulations under FEHA (October 2025), Illinois HB 3773 (January 2026), and
the EU AI Act's high-risk classification for employment systems (obligations
moved to December 2027). See the companion `aedt-compliance-map` project.

**Nothing here is legal advice, and this is not an independent bias audit in
the statutory sense.** Those must be performed by an independent auditor on
the deployed tool with real applicant data.
