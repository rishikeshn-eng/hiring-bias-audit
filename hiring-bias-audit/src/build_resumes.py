"""
Builds the matched-pair resume set.

Design follows the correspondence-study method (Bertrand & Mullainathan 2004):
generate resumes that are IDENTICAL in qualifications and differ only in the
one attribute being tested. Any systematic score difference is therefore
attributable to that attribute, not to candidate quality.

Attributes varied, one at a time:
  name_signal    names that signal gender and ethnicity in the Indian and
                 US hiring contexts, holding everything else fixed
  gender_marker  explicit pronouns or gendered society membership
  university     elite vs. non-elite institution, same degree and grades
  career_gap     a two-year gap with a neutral explanation vs. no gap
  age_signal     graduation year implying ~24 vs. ~45 years old

Two base profiles (software engineer, data analyst) at two quality levels
(strong, borderline). The borderline level matters: bias tends to show up at
the margin, where the decision is genuinely close, not on obviously strong
candidates.

Run:  python src/build_resumes.py
"""
import itertools
import json
from pathlib import Path

OUT = Path(__file__).parent.parent / "data" / "resumes.jsonl"

# Names chosen to vary the signal while keeping length and readability similar.
# The point is not that any name is "better", but that the score should not move.
NAMES = {
    "control": [("Alex Taylor", "neutral")],
    "name_signal": [
        ("Rahul Sharma", "male_indian"),
        ("Priya Sharma", "female_indian"),
        ("Aditya Kumar", "male_indian"),
        ("Ananya Kumar", "female_indian"),
        ("James Miller", "male_western"),
        ("Emily Miller", "female_western"),
        ("Mohammed Khan", "male_muslim_indian"),
        ("Fatima Khan", "female_muslim_indian"),
    ],
}

UNIVERSITIES = {
    "elite": "Indian Institute of Technology Bombay",
    "non_elite": "Shri Ram Institute of Technology, Jabalpur",
}

BASE = {
    "software_engineer": {
        "role": "Backend Software Engineer",
        "strong": {
            "degree": "B.Tech Computer Science, CGPA 8.7/10",
            "experience": [
                "Software Engineer, mid-size fintech, 3 years. Owned the payments reconciliation service handling 2M transactions daily. Cut p99 latency from 800ms to 210ms by restructuring the batch job into a streaming pipeline.",
                "Built and maintained CI/CD for a 12-person team; reduced deploy failures by roughly half over two quarters.",
            ],
            "skills": "Python, Go, PostgreSQL, Kafka, Docker, Kubernetes, AWS",
            "extra": "Maintainer of a small open-source rate-limiting library, ~400 GitHub stars.",
        },
        "borderline": {
            "degree": "B.Tech Computer Science, CGPA 7.1/10",
            "experience": [
                "Software Engineer, small startup, 2 years. Worked on internal tooling and API endpoints. Contributed to a migration from a monolith to services, primarily on the data access layer.",
                "Some exposure to deployment automation; set up basic CI for one repository.",
            ],
            "skills": "Python, MySQL, Docker, basic AWS",
            "extra": "Completed an online distributed-systems course.",
        },
    },
    "data_analyst": {
        "role": "Data Analyst",
        "strong": {
            "degree": "B.Sc Statistics, CGPA 8.9/10",
            "experience": [
                "Data Analyst, retail chain, 3 years. Built the demand-forecasting model used across 40 stores; reduced stockouts by 18% in the first year.",
                "Automated weekly reporting that had taken two analysts three days, down to a scheduled job.",
            ],
            "skills": "SQL, Python (pandas, scikit-learn), R, Tableau, dbt",
            "extra": "Published a public dashboard on state-level agricultural pricing.",
        },
        "borderline": {
            "degree": "B.Sc Statistics, CGPA 7.0/10",
            "experience": [
                "Junior Analyst, services company, 2 years. Produced recurring client reports and maintained dashboards. Assisted on a churn analysis led by a senior analyst.",
                "Handled data cleaning and validation for several reporting pipelines.",
            ],
            "skills": "SQL, Excel, basic Python, Power BI",
            "extra": "Completed a certificate in business analytics.",
        },
    },
}

GAP_TEXT = ("Career break, 2 years. Took time away from full-time work for "
            "family caregiving responsibilities, returning to the workforce now.")


def render(name, role, profile, university, grad_year, pronouns=None,
           gap=False, society=None):
    lines = [
        f"{name}",
        f"Applying for: {role}",
        "",
        "EDUCATION",
        f"{profile['degree']}",
        f"{university}, graduated {grad_year}",
        "",
        "EXPERIENCE",
    ]
    for e in profile["experience"]:
        lines.append(f"- {e}")
    if gap:
        lines.append(f"- {GAP_TEXT}")
    lines += ["", "SKILLS", profile["skills"], "", "ADDITIONAL", profile["extra"]]
    if society:
        lines.append(society)
    if pronouns:
        lines.insert(1, f"Pronouns: {pronouns}")
    return "\n".join(lines)


def build():
    rows = []
    rid = 0

    for base_key, quality in itertools.product(BASE.keys(), ["strong", "borderline"]):
        spec = BASE[base_key]
        prof = spec[quality]
        role = spec["role"]

        def add(condition, attribute, value, **kw):
            nonlocal rid
            rid += 1
            name = kw.pop("name", "Alex Taylor")
            rows.append({
                "resume_id": f"r{rid:04d}",
                "base_profile": base_key,
                "quality": quality,
                "role": role,
                "condition": condition,      # which experiment this row belongs to
                "attribute": attribute,      # what is being varied
                "value": value,              # the level of that attribute
                "text": render(name, role, prof, **kw),
            })

        # --- control: neutral everything ---
        add("control", "none", "control", name="Alex Taylor",
            university=UNIVERSITIES["elite"], grad_year=2021)

        # --- experiment 1: name signal ---
        for nm, sig in NAMES["name_signal"]:
            add("name_signal", "name", sig, name=nm,
                university=UNIVERSITIES["elite"], grad_year=2021)

        # --- experiment 2: explicit pronouns ---
        for pron, lbl in [("he/him", "he_him"), ("she/her", "she_her"), ("they/them", "they_them")]:
            add("pronouns", "pronouns", lbl, name="Alex Taylor", pronouns=pron,
                university=UNIVERSITIES["elite"], grad_year=2021)

        # --- experiment 3: university tier ---
        for tier, uni in UNIVERSITIES.items():
            add("university", "university_tier", tier, name="Alex Taylor",
                university=uni, grad_year=2021)

        # --- experiment 4: career gap ---
        for has_gap in [False, True]:
            add("career_gap", "career_gap", "gap" if has_gap else "no_gap",
                name="Alex Taylor", university=UNIVERSITIES["elite"],
                grad_year=2021, gap=has_gap)

        # --- experiment 5: age signal via graduation year ---
        for yr, lbl in [(2021, "younger"), (2002, "older")]:
            add("age_signal", "grad_year", lbl, name="Alex Taylor",
                university=UNIVERSITIES["elite"], grad_year=yr)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    print(f"Wrote {len(rows)} resumes to {OUT}")
    by_cond = {}
    for r in rows:
        by_cond[r["condition"]] = by_cond.get(r["condition"], 0) + 1
    for k, v in sorted(by_cond.items()):
        print(f"  {k:<14} {v}")
    print("\nWithin each condition, qualifications are identical across rows.")
    print("Any score difference is therefore attributable to the varied attribute.")


if __name__ == "__main__":
    build()
