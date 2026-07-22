import csv
from functools import wraps
from io import StringIO

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file,
    abort
)

from database.db import get_db


main_bp = Blueprint(
    "main",
    __name__
)


# --------------------------------------------------
# AUTHENTICATION DECORATOR
# --------------------------------------------------

def login_required(view):

    @wraps(view)
    def wrapped(*args, **kwargs):

        if "user_id" not in session:
            flash(
                "Please log in first.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        return view(
            *args,
            **kwargs
        )

    return wrapped


# --------------------------------------------------
# HOME
# --------------------------------------------------

@main_bp.route("/")
def index():

    return render_template(
        "index.html"
    )


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@main_bp.route("/dashboard")
@login_required
def dashboard():

    db = get_db()

    user_id = session["user_id"]

    athlete_count = db.execute(
        """
        SELECT COUNT(*)
        FROM athletes
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()[0]

    meet_count = db.execute(
        """
        SELECT COUNT(*)
        FROM meets
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()[0]

    event_count = db.execute(
        """
        SELECT COUNT(*)
        FROM events e
        JOIN meets m
            ON e.meet_id = m.id
        WHERE m.user_id = ?
        """,
        (user_id,)
    ).fetchone()[0]

    return render_template(
        "dashboard.html",
        athlete_count=athlete_count,
        meet_count=meet_count,
        event_count=event_count
    )


# --------------------------------------------------
# ATHLETES
# --------------------------------------------------

@main_bp.route("/athletes", methods=["GET", "POST"])
@login_required
def athletes():

    db = get_db()

    user_id = session["user_id"]

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        age = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        team = request.form.get("team", "").strip()

        if not name:
            flash("Athlete name is required.", "danger")

            return redirect(
                url_for("main.athletes")
            )

        # Find the next athlete number
        last_number = db.execute(
            """
            SELECT MAX(athlete_number)
            FROM athletes
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

        if last_number[0] is None:
            athlete_number = 1
        else:
            athlete_number = last_number[0] + 1

        # Add athlete
        db.execute(
            """
            INSERT INTO athletes (
                user_id,
                athlete_number,
                name,
                age,
                gender,
                team
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                athlete_number,
                name,
                age if age else None,
                gender if gender else None,
                team if team else None
            )
        )

        db.commit()

        flash(
            f"Athlete #{athlete_number} added successfully.",
            "success"
        )

        return redirect(
            url_for("main.athletes")
        )

    # Only show athletes belonging to this user
    athletes = db.execute(
        """
        SELECT *
        FROM athletes
        WHERE user_id = ?
        ORDER BY athlete_number ASC
        """,
        (user_id,)
    ).fetchall()

    return render_template(
        "athletes.html",
        athletes=athletes
    )


@main_bp.route("/athletes/delete/<int:athlete_id>")
@login_required
def delete_athlete(athlete_id):

    db = get_db()

    db.execute(
        """
        DELETE FROM athletes
        WHERE id = ?
        AND user_id = ?
        """,
        (
            athlete_id,
            session["user_id"]
        )
    )

    db.commit()

    flash(
        "Athlete deleted.",
        "success"
    )

    return redirect(
        url_for("main.athletes")
    )


# --------------------------------------------------
# MEETS
# --------------------------------------------------

@main_bp.route("/meets")
@login_required
def meets():

    db = get_db()

    meets = db.execute(
        """
        SELECT *
        FROM meets
        WHERE user_id = ?
        ORDER BY date
        """,
        (
            session["user_id"],
        )
    ).fetchall()

    return render_template(
        "meets.html",
        meets=meets
    )


@main_bp.route("/meets/create", methods=["GET", "POST"])
@login_required
def create_meet():

    db = get_db()

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        meet_date = request.form.get("date", "").strip()
        location = request.form.get("location", "").strip()

        if not name:
            flash("Meet name is required.", "danger")

            return render_template(
                "create_meet.html"
            )

        db.execute(
            """
            INSERT INTO meets (
                user_id,
                name,
                date,
                location
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                session["user_id"],
                name,
                meet_date,
                location
            )
        )

        db.commit()

        flash("Meet created successfully.", "success")

        return redirect(
            url_for("main.meets")
        )

    return render_template(
        "create_meet.html"
    )

@main_bp.route(
    "/meets/<int:meet_id>"
)
@login_required
def view_meet(
    meet_id
):

    db = get_db()

    meet = db.execute(
        """
        SELECT *
        FROM meets
        WHERE id = ?
        AND user_id = ?
        """,
        (
            meet_id,
            session["user_id"]
        )
    ).fetchone()

    if not meet:

        abort(404)

    events = db.execute(
        """
        SELECT *
        FROM events
        WHERE meet_id = ?
        ORDER BY event_date
        """,
        (meet_id,)
    ).fetchall()

    return render_template(
        "view_meet.html",
        meet=meet,
        events=events
    )


# --------------------------------------------------
# CREATE EVENT
# --------------------------------------------------

@main_bp.route("/meets/<int:meet_id>/events/create", methods=["GET", "POST"])
@login_required
def create_event(meet_id):

    db = get_db()

    # Get the meet belonging to the logged-in user
    meet = db.execute(
        """
        SELECT *
        FROM meets
        WHERE id = ?
        AND user_id = ?
        """,
        (
            meet_id,
            session["user_id"]
        )
    ).fetchone()

    # The meet does not exist or belongs to another user
    if meet is None:
        flash("Meet not found.", "danger")
        return redirect(url_for("main.meets"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        event_type = request.form.get("type", "").strip()
        discipline = request.form.get("discipline", "").strip()
        age_group = request.form.get("age_group", "").strip()
        gender_group = request.form.get("gender_group", "").strip()
        event_date = request.form.get("event_date", "").strip()
        location = request.form.get("location", "").strip()

        try:
            lanes = int(request.form.get("lanes", 8))
        except (TypeError, ValueError):
            lanes = 8

        try:
            heats = int(request.form.get("heats", 1))
        except (TypeError, ValueError):
            heats = 1

        # Validate required fields
        if not name:
            flash("Event name is required.", "danger")

            return render_template(
                "create_event.html",
                meet=meet,
                meet_id=meet_id
            )

        if not event_type:
            flash("Event type is required.", "danger")

            return render_template(
                "create_event.html",
                meet=meet,
                meet_id=meet_id
            )

        if not discipline:
            flash("Discipline is required.", "danger")

            return render_template(
                "create_event.html",
                meet=meet,
                meet_id=meet_id
            )

        # Create the event
        db.execute(
            """
            INSERT INTO events (
                user_id,
                meet_id,
                name,
                type,
                discipline,
                age_group,
                gender_group,
                event_date,
                location,
                lanes,
                heats
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                meet_id,
                name,
                event_type,
                discipline,
                age_group,
                gender_group,
                event_date,
                location,
                lanes,
                heats
            )
        )

        db.commit()

        flash("Event created successfully.", "success")

        return redirect(
            url_for(
                "main.view_meet",
                meet_id=meet_id
            )
        )

    return render_template(
        "create_event.html",
        meet=meet,
        meet_id=meet_id
    )

# --------------------------------------------------
# EVENTS
# --------------------------------------------------

@main_bp.route(
    "/events"
)
@login_required
def events():

    db = get_db()

    events = db.execute(
        """
        SELECT
            e.*,
            m.name AS meet_name
        FROM events e
        JOIN meets m
            ON e.meet_id = m.id
        WHERE m.user_id = ?
        ORDER BY e.event_date
        """,
        (
            session["user_id"],
        )
    ).fetchall()

    return render_template(
        "events.html",
        events=events
    )

@main_bp.route("/events/delete/<int:event_id>", methods=["POST"])
@login_required
def delete_event(event_id):

    db = get_db()

    user_id = session["user_id"]

    # Check that the event exists and belongs to the logged-in user
    event = db.execute(
        """
        SELECT id
        FROM events
        WHERE id = ?
        AND user_id = ?
        """,
        (
            event_id,
            user_id
        )
    ).fetchone()

    if event is None:
        flash(
            "Event not found or you do not have permission to delete it.",
            "danger"
        )

        return redirect(
            url_for("main.events")
        )

    # Delete results belonging to this event
    db.execute(
        """
        DELETE FROM results
        WHERE event_id = ?
        """,
        (event_id,)
    )

    # Delete event participants
    db.execute(
        """
        DELETE FROM event_participants
        WHERE event_id = ?
        """,
        (event_id,)
    )

    # Delete the event
    db.execute(
        """
        DELETE FROM events
        WHERE id = ?
        AND user_id = ?
        """,
        (
            event_id,
            user_id
        )
    )

    db.commit()

    flash(
        "Event deleted successfully.",
        "success"
    )

    return redirect(
        url_for("main.events")
    )


# --------------------------------------------------
# RUN EVENT
# --------------------------------------------------

@main_bp.route(
    "/events/<int:event_id>/run",
    methods=["GET", "POST"]
)
@login_required
def run_event(
    event_id
):

    db = get_db()

    user_id = session["user_id"]

    # Verify event ownership
    event = db.execute(
        """
        SELECT
            e.*,
            m.user_id
        FROM events e
        JOIN meets m
            ON e.meet_id = m.id
        WHERE e.id = ?
        AND m.user_id = ?
        """,
        (
            event_id,
            user_id
        )
    ).fetchone()

    if not event:

        abort(404)

    lanes = event["lanes"]
    heats = event["heats"]

    heat_number = int(
        request.args.get(
            "heat",
            1
        )
    )

    if heat_number < 1:

        heat_number = 1

    if heat_number > heats:

        heat_number = heats

    # Only show this user's athletes
    all_athletes = db.execute(
        """
        SELECT *
        FROM athletes
        WHERE user_id = ?
        ORDER BY name
        """,
        (user_id,)
    ).fetchall()

    if request.method == "POST":

        action = request.form.get(
            "action"
        )

        # ------------------------------------------
        # ASSIGN LANES
        # ------------------------------------------

        if action == "assign":

            user_id = session["user_id"]

            # Make sure the event belongs to the logged-in user
            event_owner = db.execute(
                """
                SELECT id
                FROM events
                WHERE id = ?
                AND user_id = ?
                """,
                (
                    event_id,
                    user_id
                )
            ).fetchone()

            if event_owner is None:

                flash(
                    "Event not found or you do not have permission to manage it.",
                    "danger"
                )

                return redirect(
                    url_for("main.events")
                )


            for lane in range(1, lanes + 1):

                athlete_id = request.form.get(
                    f"lane_{lane}"
                )


                # If the lane is empty, remove any
                # existing athlete from that lane
                if not athlete_id:

                    db.execute(
                        """
                        DELETE FROM event_participants

                        WHERE event_id = ?
                        AND heat_number = ?
                        AND lane = ?
                        AND user_id = ?
                        """,
                        (
                            event_id,
                            heat_number,
                            lane,
                            user_id
                        )
                    )

                    continue


                # Make sure the selected athlete
                # belongs to the logged-in user
                athlete = db.execute(
                    """
                    SELECT id
                    FROM athletes

                    WHERE id = ?
                    AND user_id = ?
                    """,
                    (
                        athlete_id,
                        user_id
                    )
                ).fetchone()


                if athlete is None:

                    flash(
                        "Invalid athlete selection.",
                        "danger"
                    )

                    continue


                # Check whether this lane already
                # has an athlete assigned
                existing = db.execute(
                    """
                    SELECT id

                    FROM event_participants

                    WHERE event_id = ?
                    AND heat_number = ?
                    AND lane = ?
                    AND user_id = ?
                    """,
                    (
                        event_id,
                        heat_number,
                        lane,
                        user_id
                    )
                ).fetchone()


                if existing:

                    # Update existing assignment
                    db.execute(
                        """
                        UPDATE event_participants

                        SET athlete_id = ?

                        WHERE id = ?
                        AND user_id = ?
                        """,
                        (
                            athlete_id,
                            existing["id"],
                            user_id
                        )
                    )


                else:

                    # Create new assignment
                    db.execute(
                        """
                        INSERT INTO event_participants (
                            user_id,
                            event_id,
                            athlete_id,
                            heat_number,
                            lane
                        )

                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            user_id,
                            event_id,
                            athlete_id,
                            heat_number,
                            lane
                        )
                    )


            db.commit()

            flash(
                "Lane assignments saved successfully.",
                "success"
            )
        # ------------------------------------------
        # SAVE RESULTS
        # ------------------------------------------

        elif action == "results":

            user_id = session["user_id"]

            # Verify that the event belongs to the logged-in user
            event_owner = db.execute(
                """
                SELECT id
                FROM events
                WHERE id = ?
                AND user_id = ?
                """,
                (
                    event_id,
                    user_id
                )
            ).fetchone()

            if event_owner is None:
                flash(
                    "Event not found or you do not have permission to manage it.",
                    "danger"
                )

                return redirect(
                    url_for("main.events")
                )

            for lane in range(1, lanes + 1):

                result_val = request.form.get(
                    f"result_{lane}"
                )

                # No result entered for this lane
                if not result_val:
                    continue

                # Find the athlete assigned to this lane
                participant = db.execute(
                    """
                    SELECT *
                    FROM event_participants
                    WHERE event_id = ?
                    AND user_id = ?
                    AND heat_number = ?
                    AND lane = ?
                    """,
                    (
                        event_id,
                        user_id,
                        heat_number,
                        lane
                    )
                ).fetchone()

                # No athlete assigned to this lane
                if participant is None:
                    continue

                athlete_id = participant["athlete_id"]

                # Make sure the athlete belongs to this user
                athlete = db.execute(
                    """
                    SELECT id
                    FROM athletes
                    WHERE id = ?
                    AND user_id = ?
                    """,
                    (
                        athlete_id,
                        user_id
                    )
                ).fetchone()

                if athlete is None:
                    continue

                # Convert the result to a number
                try:
                    result_value = float(result_val)

                except (TypeError, ValueError):

                    flash(
                        f"Invalid result entered for Lane {lane}.",
                        "danger"
                    )

                    continue

                # Save the result
                db.execute(
                    """
                    INSERT INTO results (
                        user_id,
                        event_id,
                        athlete_id,
                        heat_number,
                        lane,
                        result_value,
                        attempt_number
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        event_id,
                        athlete_id,
                        heat_number,
                        participant["lane"],
                        result_value,
                        1
                    )
                )

            db.commit()

            flash(
                "Results saved successfully.",
                "success"
            )

        return redirect(
            url_for(
                "main.run_event",
                event_id=event_id,
                heat=heat_number
            )
        )

    participants = db.execute(
        """
        SELECT
            ep.*,
            a.name
        FROM event_participants ep
        JOIN athletes a
            ON ep.athlete_id = a.id
        WHERE ep.event_id = ?
        AND ep.heat_number = ?
        AND a.user_id = ?
        ORDER BY ep.lane
        """,
        (
            event_id,
            heat_number,
            user_id
        )
    ).fetchall()

    results = db.execute(
        """
        SELECT
            r.*,
            a.name
        FROM results r
        JOIN athletes a
            ON r.athlete_id = a.id
        WHERE r.event_id = ?
        AND r.heat_number = ?
        AND a.user_id = ?
        ORDER BY r.result_value ASC
        """,
        (
            event_id,
            heat_number,
            user_id
        )
    ).fetchall()

    return render_template(
        "run_event.html",
        event=event,
        lanes=lanes,
        heats=heats,
        heat_number=heat_number,
        all_athletes=all_athletes,
        participants=participants,
        results=results
    )


# --------------------------------------------------
# EXPORT RESULTS
# --------------------------------------------------

@main_bp.route(
    "/events/<int:event_id>/export"
)
@login_required
def export_results(
    event_id
):

    db = get_db()

    event = db.execute(
        """
        SELECT
            e.*
        FROM events e
        JOIN meets m
            ON e.meet_id = m.id
        WHERE e.id = ?
        AND m.user_id = ?
        """,
        (
            event_id,
            session["user_id"]
        )
    ).fetchone()

    if not event:

        abort(404)

    rows = db.execute(
        """
        SELECT
            r.heat_number,
            r.lane,
            a.name,
            r.result_value,
            r.position
        FROM results r
        JOIN athletes a
            ON r.athlete_id = a.id
        WHERE r.event_id = ?
        AND a.user_id = ?
        ORDER BY
            r.heat_number,
            r.result_value
        """,
        (
            event_id,
            session["user_id"]
        )
    ).fetchall()

    output = StringIO()

    writer = csv.writer(
        output
    )

    writer.writerow(
        [
            "Event",
            "Heat",
            "Lane",
            "Athlete",
            "Result",
            "Position"
        ]
    )

    for row in rows:

        writer.writerow(
            [
                event["name"],
                row["heat_number"],
                row["lane"],
                row["name"],
                row["result_value"],
                row["position"]
            ]
        )

    output.seek(0)

    return send_file(
        StringIO(
            output.getvalue()
        ),
        mimetype="text/csv",
        as_attachment=True,
        download_name=(
            f"event_{event_id}_results.csv"
        )
    )