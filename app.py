import os
import psycopg
from psycopg.rows import dict_row
from flask import Flask, g, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "sports_calendar"),
        user=os.getenv("DB_USER", "sports_user"),
        password=os.getenv("DB_PASSWORD", "sports_pass"),
    )


def get_db():
    if "conn" not in g:
        # Reuse the same connection
        g.conn = get_connection()
    return g.conn


@app.teardown_request
def close_conn(exc):
    conn = g.pop("conn", None)
    if conn:
        conn.close()


def get_or_create_sport_id(cur, sport_name):
    cur.execute(
        """
        INSERT INTO sports (name) VALUES (%s)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        (sport_name,),
    )
    return cur.fetchone()[0]


def get_or_create_team_id(cur, team_name, country_code=None):
    # COALESCE ensures we don't overwrite an existing country_code with NULL
    cur.execute(
        """
        INSERT INTO teams (name, country_code)
        VALUES (%s, %s)
        ON CONFLICT (name) DO UPDATE
        SET country_code = COALESCE(EXCLUDED.country_code, teams.country_code)
        RETURNING id
        """,
        (team_name, country_code),
    )
    return cur.fetchone()[0]


def get_or_create_venue_id(cur, venue_name=None, city=None, country=None):
    if not venue_name:
        return None
    # A unique constraint on (name, city, country) to allow
    # multiple venues with the same name in different locations
    cur.execute(
        """
        INSERT INTO venues (name, city, country) VALUES (%s, %s, %s)
        ON CONFLICT (name, city, country) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        (venue_name, city, country),
    )
    return cur.fetchone()[0]


def fetch_events(sport=None, event_date=None):
    conditions, params = [], []
    if sport:
        conditions.append("s.name = %s")
        params.append(sport)
    if event_date:
        conditions.append("e.event_date = %s")
        params.append(event_date)
    query = """
        SELECT
            e.id,
            e.event_date,
            e.event_time,
            s.name AS sport,
            ht.name AS home_team,
            at.name AS away_team,
            v.name AS venue_name,
            v.city AS venue_city,
            v.country AS venue_country,
            e.description
        FROM events e
        JOIN sports s ON s.id = e._sport_id
        JOIN teams ht ON ht.id = e._home_team_id
        JOIN teams at ON at.id = e._away_team_id
        LEFT JOIN venues v ON v.id = e._venue_id
    """
    # Optionally filter by sport and/or date if provided
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY e.event_date, e.event_time"
    with get_db().cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        return cur.fetchall()


def fetch_event_by_id(event_id):
    with get_db().cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
                e.id,
                e.event_date,
                e.event_time,
                s.name AS sport,
                ht.name AS home_team,
                at.name AS away_team,
                v.name AS venue_name,
                v.city AS venue_city,
                v.country AS venue_country,
                e.description
            FROM events e
            JOIN sports s ON s.id = e._sport_id
            JOIN teams ht ON ht.id = e._home_team_id
            JOIN teams at ON at.id = e._away_team_id
            LEFT JOIN venues v ON v.id = e._venue_id
            WHERE e.id = %s
            """,
            (event_id,),
        )
        return cur.fetchone()


def get_sports():
    with get_db().cursor() as cur:
        cur.execute("SELECT name FROM sports ORDER BY name")
        return [row[0] for row in cur.fetchall()]


def create_event(payload):
    conn = get_db()
    with conn.cursor() as cur:
        sport_id = get_or_create_sport_id(
            cur, 
            payload["sport"]
        )
        home_team_id = get_or_create_team_id(
            cur,
            payload["home_team"],
            payload.get("home_team_country_code"),
        )
        away_team_id = get_or_create_team_id(
            cur,
            payload["away_team"],
            payload.get("away_team_country_code"),
        )
        venue_id = get_or_create_venue_id(
            cur,
            payload.get("venue_name"),
            payload.get("venue_city"),
            payload.get("venue_country"),
        )
        cur.execute(
            """
            INSERT INTO events (
                event_date, event_time,
                _sport_id, _venue_id,
                _home_team_id, _away_team_id,
                description
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                payload["event_date"],
                payload["event_time"],
                sport_id,
                venue_id,
                home_team_id,
                away_team_id,
                payload.get("description"),
            ),
        )
        event_id = cur.fetchone()[0]
    conn.commit()
    return event_id


@app.get("/")
def index():
    sport = request.args.get("sport") or None
    event_date = request.args.get("date") or None
    message = request.args.get("message", "")
    return render_template(
        "index.html",
        events=fetch_events(sport=sport, event_date=event_date),
        sports=get_sports(),
        active_sport=sport or "",
        active_date=event_date or "",
        message=message,
    )


@app.post("/events")
def create_event_from_form():
    form_payload = request.form.to_dict()
    required = ["event_date", "event_time", "sport", "home_team", "away_team"]
    if any(not form_payload.get(field) for field in required):
        return redirect(url_for("index", message="Missing required form fields"))
    create_event(form_payload)
    return redirect(url_for("index", message="Event added"))


@app.get("/api/events")
def api_get_events():
    sport = request.args.get("sport") or None
    event_date = request.args.get("date") or None
    return jsonify(fetch_events(sport=sport, event_date=event_date))


@app.get("/api/events/<int:event_id>")
def api_get_event(event_id):
    event = fetch_event_by_id(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    return jsonify(event)


@app.post("/api/events")
def api_create_event():
    payload = request.get_json(silent=True) or {}
    required = ["event_date", "event_time", "sport", "home_team", "away_team"]
    missing = [field for field in required if not payload.get(field)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    event_id = create_event(payload)
    return jsonify({"id": event_id}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
