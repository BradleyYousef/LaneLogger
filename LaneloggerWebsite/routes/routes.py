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

@main_bp.route(
    "/athletes",
    methods=["GET", "POST"]
)
@login_required
def athletes():

    db = get_db()

    user_id = session["user_id"]

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        age = request.form.get(
            "age"
        )

        gender = request.form.get(
            "gender"
        )

        team = request.form.get(
            "team"
        )

        if not name:

            flash(
                "Athlete name is required.",
                "danger"
            )

            return redirect(
                url_for("main.athletes")
            )

        # Generate athlete number
        last_number = db.execute(
            """
            SELECT MAX(athlete_number)
            FROM athletes
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()[0]

        athlete_number = (
            last_number + 1
            if last_number is not None
            else 1
        )

        db.execute(
            """
            INSERT INTO athletes
            (
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
                age,
                gender,
                team
            )
        )

        db.commit()

        flash(
            "Athlete added successfully.",
            "success"
        )

        return redirect(
            url_for("main.athletes")
        )

    athletes = db.execute(
        """
        SELECT *
        FROM athletes
        WHERE user_id = ?
        ORDER BY name
        """,
        (user_id,)
    ).fetchall()

    return render_template(
        "athletes.html",
        athletes=athletes
    )


@main_bp.route(
    "/athletes/delete/<int:athlete_id>",
    methods=["POST"]
)
@login_required
def delete_athlete(
    athlete_id
):

    db = get_db()

    user_id = session["user_id"]

    db.execute(
        """
        DELETE FROM athletes
        WHERE id = ?
        AND user_id = ?
        """,
        (
            athlete_id,
            user_id
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

@main_bp.route(
    "/meets"
)
@login_required
def meets():

    db = get_db()

    user_id = session["user_id"]

    meets = db.execute(
        """
        SELECT *
        FROM meets
        WHERE user_id = ?
        ORDER BY date DESC
        """,
        (user_id,)
    ).fetchall()

    return render_template(
        "meets.html",
        meets=meets
    )


@main_bp.route(
    "/meets/create",
    methods=["GET", "POST"]
)
@login_required
def create_meet():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        date = request.form.get(
            "date"
        )

        location = request.form.get(
            "location"
        )

        if not name:

            flash(
                "Meet name is required.",
                "danger"
            )

            return render_template(
                "create_meet.html"
            )

        db = get_db()

        db.execute(
            """
            INSERT INTO meets
            (
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
                date,
                location
            )
        )

        db.commit()

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

@main_bp.route(
    "/events/create/<int:meet_id>",
    methods=["GET", "POST"]
)
@login_required
def create_event(
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

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        event_type = request.form.get(
            "event_type"
        )

        discipline = request.form.get(
            "discipline"
        )

        age_group = request.form.get(
            "age_group"
        )

        gender_group = request.form.get(
            "gender_group"
        )

        event_date = request.form.get(
            "event_date"
        )

        location = request.form.get(
            "location"
        )

        lanes = int(
            request.form.get(
                "lanes",
                8
            )
        )

        heats = int(
            request.form.get(
                "heats",
                1
            )
        )

        if not name:

            flash(
                "Event name is required.",
                "danger"
            )

            return render_template(
                "create_event.html",
                meet=meet
            )

        db.execute(
            """
            INSERT INTO events
            (
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
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

        return redirect(
            url_for(
                "main.view_meet",
                meet_id=meet_id
            )
        )

    return render_template(
        "create_event.html",
        meet=meet
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

            for lane in range(
                1,
                lanes + 1
            ):

                athlete_id = request.form.get(
                    f"lane_{lane}"
                )

                if not athlete_id:

                    continue

                # Verify athlete belongs to current user
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

                if not athlete:

                    continue

                existing = db.execute(
                    """
                    SELECT id
                    FROM event_participants
                    WHERE event_id = ?
                    AND heat_number = ?
                    AND lane = ?
                    """,
                    (
                        event_id,
                        heat_number,
                        lane
                    )
                ).fetchone()

                if existing:

                    db.execute(
                        """
                        UPDATE event_participants
                        SET athlete_id = ?
                        WHERE id = ?
                        """,
                        (
                            athlete_id,
                            existing["id"]
                        )
                    )

                else:

                    db.execute(
                        """
                        INSERT INTO event_participants
                        (
                            event_id,
                            athlete_id,
                            heat_number,
                            lane
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            event_id,
                            athlete_id,
                            heat_number,
                            lane
                        )
                    )

            db.commit()

        # ------------------------------------------
        # SAVE RESULTS
        # ------------------------------------------

        elif action == "results":

            for lane in range(
                1,
                lanes + 1
            ):

                result_value = request.form.get(
                    f"result_{lane}"
                )

                if not result_value:

                    continue

                participant = db.execute(
                    """
                    SELECT ep.*
                    FROM event_participants ep
                    JOIN athletes a
                        ON ep.athlete_id = a.id
                    WHERE ep.event_id = ?
                    AND ep.heat_number = ?
                    AND ep.lane = ?
                    AND a.user_id = ?
                    """,
                    (
                        event_id,
                        heat_number,
                        lane,
                        user_id
                    )
                ).fetchone()

                if not participant:

                    continue

                try:

                    result_value = float(
                        result_value
                    )

                except ValueError:

                    continue

                db.execute(
                    """
                    INSERT INTO results
                    (
                        event_id,
                        athlete_id,
                        heat_number,
                        lane,
                        result_value,
                        attempt_number
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        participant["athlete_id"],
                        heat_number,
                        lane,
                        result_value,
                        1
                    )
                )

            db.commit()

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