import os
from dataclasses import dataclass, asdict
from typing import List, Optional

from flask import Flask, render_template, request
from dotenv import load_dotenv
from openai import OpenAI

# Loading environment variables from .env
load_dotenv()

# OpenAI client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

app = Flask(__name__)

# ====== Simple in-memory "database" of users ======
@dataclass
class StudentProfile:
    name: str
    major: str
    year: str
    study_style: str
    vibe: str
    subjects: str
    availability: str
    goals: str


registered_students: List[StudentProfile] = []


def compute_match_score(a: StudentProfile, b: StudentProfile) -> int:
    """Simple rule-based compatibility score."""
    score = 0

    if a.study_style.lower() == b.study_style.lower():
        score += 3

    if a.vibe.lower() == b.vibe.lower():
        score += 2

    for subject in a.subjects.lower().split(","):
        subject = subject.strip()
        if subject and subject in b.subjects.lower():
            score += 2

    for slot in a.availability.lower().split(","):
        slot = slot.strip()
        if slot and slot in b.availability.lower():
            score += 1

    if any(word in b.goals.lower() for word in a.goals.lower().split()):
        score += 1

    return score


def generate_ai_explanation_and_intro(
    seeker: StudentProfile, buddy: StudentProfile
) -> dict:
    """Use OpenAI to explain the match + draft an intro DM."""
    prompt = f"""
You are helping match students as study buddies.

Student A (the one looking for a buddy):
- Name: {seeker.name}
- Major: {seeker.major}
- Year: {seeker.year}
- Study style: {seeker.study_style}
- Vibe: {seeker.vibe}
- Subjects: {seeker.subjects}
- Availability: {seeker.availability}
- Goals: {seeker.goals}

Student B (the suggested match):
- Name: {buddy.name}
- Major: {buddy.major}
- Year: {buddy.year}
- Study style: {buddy.study_style}
- Vibe: {buddy.vibe}
- Subjects: {buddy.subjects}
- Availability: {buddy.availability}
- Goals: {buddy.goals}

1. In ONE short, casual sentence, explain why they would work well together as study buddies.
2. Write a short, friendly intro DM that Student A could send to Student B to start studying together.
The DM should sound like a real college student, be chill but not cringey, and mention at least one shared subject or study habit.

Format your answer exactly like this:

Reason: <one sentence>
Message: <one or two sentences>
"""

    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            instructions="You write concise, friendly text for college students.",
        )

        full_text = response.output_text

        reason = ""
        message = ""

        for line in full_text.splitlines():
            if line.lower().startswith("reason:"):
                reason = line.split(":", 1)[1].strip()
            elif line.lower().startswith("message:"):
                message = line.split(":", 1)[1].strip()

        if not reason:
            reason = full_text.strip()

        return {
            "reason": reason,
            "message": message or full_text.strip(),
        }

    except Exception:
        # Fallback if API fails
        return {
            "reason": "You share similar study styles and subjects, so you’d probably work well together.",
            "message": f"Hey {buddy.name}, I saw we match on StudySync and we’re studying some of the same stuff. Want to team up for a session?",
        }


@app.route("/", methods=["GET"])
def index():
    # Renders templates/index.html
    return render_template("index.html")


@app.route("/match", methods=["POST"])
def match():
    # Reading form fields
    name = request.form.get("name", "").strip()
    major = request.form.get("major", "").strip()
    year = request.form.get("year", "").strip()
    study_style = request.form.get("study_style", "").strip()
    vibe = request.form.get("vibe", "").strip()
    subjects = request.form.get("subjects", "").strip()
    availability = request.form.get("availability", "").strip()
    goals = request.form.get("goals", "").strip()

    seeker = StudentProfile(
        name=name,
        major=major,
        year=year,
        study_style=study_style,
        vibe=vibe,
        subjects=subjects,
        availability=availability,
        goals=goals,
    )

    # Find best match among existing students
    best_match: Optional[StudentProfile] = None
    best_score = -1

    for other in registered_students:
        if other.name == seeker.name:
            continue  # skip self

        score = compute_match_score(seeker, other)
        if score > best_score:
            best_score = score
            best_match = other

    ai_result = None
    if best_match:
        ai_result = generate_ai_explanation_and_intro(seeker, best_match)

    # Add current seeker to the pool for future matches
    registered_students.append(seeker)

    return render_template(
        "match.html",
        seeker=asdict(seeker),
        best_match=asdict(best_match) if best_match else None,
        ai_result=ai_result,
        num_others=len(registered_students) - 1,
    )


if __name__ == "__main__":
    app.run(debug=True)
