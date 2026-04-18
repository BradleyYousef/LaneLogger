from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
from database.db import get_db
from functools import wraps
from io import StringIO
import csv

main_bp = Blueprint("main", __name__)

# login required
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped

# home
@main_bp.route("/")
def index():
    return render_template("index.html")

# dashboard
@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

# athletes
@main_bp.route("/athletes", methods=["GET", "POST"])
@login_required
def athletes():
    db = get_db()
    if request.method == "POST":
        name = request.form["name"].strip()
        age = request.form.get("age")
        gender = request.form.get("gender")
        team = request.form.get("team")
        if name:
            db.execute("INSERT INTO athletes (name, age, gender, team) VALUES (?, ?, ?, ?)", (name, age, gender, team))
            db.commit()
        else:
            flash("Name required", "danger")
        return redirect(url_for("main.athletes"))
    athletes = db.execute("SELECT * FROM athletes ORDER BY name").fetchall()
    return render_template("athletes.html", athletes=athletes)

@main_bp.route("/athletes/delete/<int:athlete_id>")
@login_required
def delete_athlete(athlete_id):
    db = get_db()
    db.execute("DELETE FROM athletes WHERE id = ?", (athlete_id,))
    db.commit()
    return redirect(url_for("main.athletes"))

# events list
@main_bp.route("/events")
@login_required
def events():
    db = get_db()
    events = db.execute("SELECT * FROM events ORDER BY date").fetchall()
    return render_template("events.html", events=events)

# create event
@main_bp.route("/events/create", methods=["GET", "POST"])
@login_required
def create_event():
    if request.method == "POST":
        f = request.form
        db = get_db()
        db.execute(
            "INSERT INTO events (name, type, discipline, age_group, gender_group, date, location, lanes, heats) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (f["name"], f["type"], f["discipline"], f.get("age_group"), f.get("gender_group"), f.get("date"), f.get("location"), f.get("lanes"), f.get("heats"))
        )
        db.commit()
        return redirect(url_for("main.events"))
    return render_template("create_event.html")

# delete event
@main_bp.route("/events/delete/<int:event_id>")
@login_required
def delete_event(event_id):
    db = get_db()
    db.execute("DELETE FROM events WHERE id = ?", (event_id,))
    db.execute("DELETE FROM event_participants WHERE event_id = ?", (event_id,))
    db.execute("DELETE FROM results WHERE event_id = ?", (event_id,))
    db.commit()
    return redirect(url_for("main.events"))

# run event
@main_bp.route("/events/<int:event_id>/run", methods=["GET", "POST"])
@login_required
def run_event(event_id):
    db = get_db()
    event = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    if not event:
        return redirect(url_for("main.events"))
    heats = event["heats"] or 1
    lanes = event["lanes"] or 8
    all_athletes = db.execute("SELECT * FROM athletes ORDER BY name").fetchall()
    heat_number = int(request.args.get("heat", 1))
    if heat_number < 1 or heat_number > heats:
        heat_number = 1

    if request.method == "POST":
        action = request.form.get("action")

        # assign lanes
        if action == "assign":
            for lane in range(1, lanes + 1):
                athlete_id = request.form.get(f"lane_{lane}")
                if athlete_id:
                    existing = db.execute(
                        "SELECT id FROM event_participants WHERE event_id = ? AND heat_number = ? AND lane = ?",
                        (event_id, heat_number, lane)
                    ).fetchone()
                    if existing:
                        db.execute("UPDATE event_participants SET athlete_id = ? WHERE id = ?", (athlete_id, existing["id"]))
                    else:
                        db.execute(
                            "INSERT INTO event_participants (event_id, athlete_id, heat_number, lane) VALUES (?, ?, ?, ?)",
                            (event_id, athlete_id, heat_number, lane)
                        )
            db.commit()

        # save results
        elif action == "results":
            for lane in range(1, lanes + 1):
                result_val = request.form.get(f"result_{lane}")
                if not result_val:
                    continue
                participant = db.execute(
                    "SELECT * FROM event_participants WHERE event_id = ? AND heat_number = ? AND lane = ?",
                    (event_id, heat_number, lane)
                ).fetchone()
                if not participant:
                    continue
                athlete_id = participant["athlete_id"]
                db.execute(
                    "INSERT INTO results (event_id, athlete_id, heat_number, result_value, attempt_number) VALUES (?, ?, ?, ?, ?)",
                    (event_id, athlete_id, heat_number, float(result_val), 1)
                )
            db.commit()

        return redirect(url_for("main.run_event", event_id=event_id, heat=heat_number))

    # load participants
    participants = db.execute(
        "SELECT ep.*, a.name FROM event_participants ep JOIN athletes a ON ep.athlete_id = a.id WHERE ep.event_id = ? AND ep.heat_number = ? ORDER BY ep.lane",
        (event_id, heat_number)
    ).fetchall()

    # load results
    results = db.execute(
        "SELECT r.*, a.name, ep.lane FROM results r JOIN athletes a ON r.athlete_id = a.id LEFT JOIN event_participants ep ON ep.event_id = r.event_id AND ep.athlete_id = r.athlete_id AND ep.heat_number = r.heat_number WHERE r.event_id = ? AND r.heat_number = ? ORDER BY r.result_value ASC",
        (event_id, heat_number)
    ).fetchall()

    return render_template("run_event.html", event=event, heats=heats, lanes=lanes, heat_number=heat_number, all_athletes=all_athletes, participants=participants, results=results)

# export csv
@main_bp.route("/events/<int:event_id>/export")
@login_required
def export_results(event_id):
    db = get_db()
    rows = db.execute(
        "SELECT r.heat_number, a.name, r.result_value, r.position FROM results r JOIN athletes a ON r.athlete_id = a.id WHERE r.event_id = ? ORDER BY r.heat_number, r.result_value",
        (event_id,)
    ).fetchall()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Heat", "Athlete", "Result", "Position"])
    for r in rows:
        writer.writerow([r["heat_number"], r["name"], r["result_value"], r["position"]])
    output.seek(0)
    return send_file(output, mimetype="text/csv", as_attachment=True, download_name=f"event_{event_id}_results.csv")

@main_bp.route("/meets")
@login_required
def meets():
    db = get_db()
    meets = db.execute("SELECT * FROM meets ORDER BY date").fetchall()
    return render_template("meets.html", meets=meets)

@main_bp.route("/meets/create", methods=["GET", "POST"])
@login_required
def create_meet():
    if request.method == "POST":
        f = request.form
        db = get_db()
        db.execute(
            "INSERT INTO meets (name, date, location) VALUES (?, ?, ?)",
            (f["name"], f["date"], f["location"])
        )
        db.commit()
        return redirect(url_for("main.meets"))
    return render_template("create_meet.html")

@main_bp.route("/meets/<int:meet_id>")
@login_required
def view_meet(meet_id):
    db = get_db()
    meet = db.execute("SELECT * FROM meets WHERE id = ?", (meet_id,)).fetchone()
    events = db.execute("SELECT * FROM events WHERE meet_id = ?", (meet_id,)).fetchall()
    return render_template("view_meet.html", meet=meet, events=events)
