import os
import uuid
from dataclasses import dataclass, asdict
from typing import List, Optional

from flask import Flask, render_template, request
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# OpenAI client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

app = Flask(__name__)

# ---------- File upload config ----------
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------- In-memory "database" ----------
@dataclass
class StudentProfile:
    student_id: str   # USF Student ID
    name: str
    major: str
    year: str
    study_style: str
    vibe: str
    subjects: str
    availability: str
    goals: str
    photo_filename: str = ""   # stored image filename


registered_students: List[StudentProfile] = []
# who this user liked / passed
likes_by_user: dict[str, set[str]] = {}
passes_by_user: dict[str, set[str]] = {}

# simple in-memory chat: chat_id -> list of {"sender_id", "sender_name", "text"}
chats: dict[str, list[dict]] = {}


def find_student(student_id: str) -> Optional[StudentProfile]:
    for s in registered_students:
        if s.student_id == student_id:
            return s
    return None


def make_chat_id(a_id: str, b_id: str) -> str:
    # stable chat id for a pair of students
    return "-".join(sorted([a_id, b_id]))



def compute_match_score(a: StudentProfile, b: StudentProfile) -> int:
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
    prompt = f"""
You are helping match students as study buddies.

Student A (the one looking for a buddy):
- Name: {seeker.name}
- USF ID: {seeker.student_id}
- Major: {seeker.major}
- Year: {seeker.year}
- Study style: {seeker.study_style}
- Vibe: {seeker.vibe}
- Subjects: {seeker.subjects}
- Availability: {seeker.availability}
- Goals: {seeker.goals}

Student B (the suggested match):
- Name: {buddy.name}
- USF ID: {buddy.student_id}
- Major: {buddy.major}
- Year: {buddy.year}
- Study style: {buddy.study_style}
- Vibe: {buddy.vibe}
- Subjects: {buddy.subjects}
- Availability: {buddy.availability}
- Goals: {buddy.goals}

1. In ONE short, casual sentence, explain why they would work well together as study buddies.
2. Write a short, friendly intro DM that Student A could send to Student B to start studying together.

Format your answer exactly like:

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
        return {
            "reason": "You share similar study styles and subjects, so you’d probably work well together.",
            "message": f"Hey {buddy.name}, I saw we match on StudySync and we’re studying some of the same stuff. Want to team up for a session?",
        }


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/match", methods=["POST"])
def match():
    # ---- Form fields ----
    student_id = request.form.get("student_id", "").strip()
    name = request.form.get("name", "").strip()
    major = request.form.get("major", "").strip()
    year = request.form.get("year", "").strip()
    study_style = request.form.get("study_style", "").strip()
    vibe = request.form.get("vibe", "").strip()
    subjects = request.form.get("subjects", "").strip()
    availability = request.form.get("availability", "").strip()
    goals = request.form.get("goals", "").strip()

    # ---- File upload handling ----
    photo_file = request.files.get("photo")
    photo_filename = ""

    if photo_file and allowed_file(photo_file.filename):
        original_name = secure_filename(photo_file.filename)
        _, ext = os.path.splitext(original_name)

        # Unique filename: USF ID + random tag + extension
        unique_tag = uuid.uuid4().hex[:8]
        safe_name = f"{student_id}_{unique_tag}{ext.lower()}"

        photo_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
        photo_file.save(photo_path)
        photo_filename = safe_name
        print("Saved photo as:", photo_filename)

    # ---- Build this student's profile ----
    seeker = StudentProfile(
        student_id=student_id,
        name=name,
        major=major,
        year=year,
        study_style=study_style,
        vibe=vibe,
        subjects=subjects,
        availability=availability,
        goals=goals,
        photo_filename=photo_filename,
    )

    # ---- Find best match ----
    best_match: Optional[StudentProfile] = None
    best_score = -1

    for other in registered_students:
        if other.student_id == seeker.student_id:
            continue

        score = compute_match_score(seeker, other)
        if score > best_score:
            best_score = score
            best_match = other

    ai_result = None
    if best_match:
        ai_result = generate_ai_explanation_and_intro(seeker, best_match)

    # ---- Save this student ----
    registered_students.append(seeker)

    # DEBUG: see what filenames we have
    print(">>> seeker:", seeker.student_id, seeker.name, "photo:", seeker.photo_filename)
    if best_match:
        print(">>> best_match:", best_match.student_id, best_match.name, "photo:", best_match.photo_filename)

    # ---- Render result page ----
    return render_template(
        "match.html",
    seeker=seeker,
    best_match=best_match,
    ai_result=ai_result,
    num_others=len(registered_students) - 1,
    )
@app.route("/swipe/<student_id>", methods=["GET", "POST"])
def swipe(student_id: str):
    current = find_student(student_id)
    if not current:
        return "Student not found. Make sure you signed up first.", 404

    # ensure sets exist
    likes = likes_by_user.setdefault(student_id, set())
    passes = passes_by_user.setdefault(student_id, set())

    message = None
    matched_with: Optional[StudentProfile] = None
    match_chat_id: Optional[str] = None

    if request.method == "POST":
        action = request.form.get("action")
        target_id = request.form.get("target_id")

        if target_id:
            # find the student we just swiped on (for messages)
            target_student = find_student(target_id)

            if action == "like":
                likes.add(target_id)

                # did they already like you?
                other_likes = likes_by_user.setdefault(target_id, set())
                if student_id in other_likes:
                    # MUTUAL MATCH 🎉
                    matched_with = target_student
                    message = f"It's a match with {matched_with.name}! 🎉 You can start chatting."
                    match_chat_id = make_chat_id(student_id, target_id)
                else:
                    # one-sided like: request sent
                    if target_student:
                        message = f"You liked {target_student.name}. Match request sent — if they like you back, you'll be able to chat."
                    else:
                        message = "Match request sent."
            elif action == "pass":
                passes.add(target_id)
                if target_student:
                    message = f"You skipped {target_student.name}."

    # pick the next candidate to show
    candidate: Optional[StudentProfile] = None
    for other in registered_students:
        if other.student_id == student_id:
            continue
        if other.student_id in likes or other.student_id in passes:
            continue
        candidate = other
        break

    return render_template(
        "swipe.html",
        current=current,
        candidate=candidate,
        message=message,
        matched_with=matched_with,
        match_chat_id=match_chat_id,
    )

@app.route("/chat/<chat_id>", methods=["GET", "POST"])
def chat(chat_id: str):
    current_id = request.args.get("me") or request.form.get("me")
    other_id = request.args.get("other") or request.form.get("other")

    if not current_id or not other_id:
        return "Chat requires ?me=<your_id>&other=<their_id> in URL.", 400

    current = find_student(current_id)
    other = find_student(other_id)
    if not current or not other:
        return "Student(s) not found.", 404

    messages = chats.setdefault(chat_id, [])

    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if text:
            messages.append(
                {
                    "sender_id": current.student_id,
                    "sender_name": current.name,
                    "text": text,
                }
            )
        # avoid form resubmit on refresh
        return render_template(
            "chat.html",
            chat_id=chat_id,
            current=current,
            other=other,
            messages=messages,
        )

    return render_template(
        "chat.html",
        chat_id=chat_id,
        current=current,
        other=other,
        messages=messages,
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", error=None)

    # POST
    student_id = request.form.get("student_id", "").strip()
    student = find_student(student_id)

    if not student:
        # no account yet
        return render_template(
            "login.html",
            error="No account found for that USF ID. Please create an account first.",
        )

    # redirect to dashboard for that student
        return redirect(url_for("dashboard", student_id=student_id))

@app.route("/dashboard/<student_id>", methods=["GET"])
def dashboard(student_id: str):
    current = find_student(student_id)
    if not current:
        return "Student not found.", 404

    my_id = current.student_id

    # likes I sent
    my_likes = likes_by_user.get(my_id, set())

    # incoming requests = people who liked me, but I never liked them back
    incoming_requests_ids = []
    for other_id, their_likes in likes_by_user.items():
        if other_id == my_id:
            continue
        if my_id in their_likes and other_id not in my_likes:
            incoming_requests_ids.append(other_id)

    incoming_requests = [find_student(sid) for sid in incoming_requests_ids if find_student(sid)]

    # mutual matches = we both liked each other
    mutual_ids = []
    for other_id in my_likes:
        other_likes = likes_by_user.get(other_id, set())
        if my_id in other_likes:
            mutual_ids.append(other_id)

    mutual_matches = [find_student(sid) for sid in mutual_ids if find_student(sid)]

    return render_template(
        "dashboard.html",
        current=current,
        incoming_requests=incoming_requests,
        mutual_matches=mutual_matches,
    )
@app.route("/accept_match", methods=["POST"])
def accept_match():
    me_id = request.form.get("me_id")
    other_id = request.form.get("other_id")

    if not me_id or not other_id:
        return "Missing IDs", 400

    me = find_student(me_id)
    other = find_student(other_id)
    if not me or not other:
        return "Student not found.", 404

    # Like them back
    my_likes = likes_by_user.setdefault(me_id, set())
    my_likes.add(other_id)

    # Now it's a mutual match, create chat ID
    chat_id = make_chat_id(me_id, other_id)

    # redirect straight to chat
    return redirect(url_for("chat", chat_id=chat_id, me=me_id, other=other_id))



if __name__ == "__main__":
    app.run(debug=True)
