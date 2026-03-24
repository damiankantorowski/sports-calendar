CREATE TABLE IF NOT EXISTS sports (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    country_code CHAR(3)
);

CREATE TABLE IF NOT EXISTS venues (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100),
    UNIQUE (name, city, country)
);

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    event_date DATE NOT NULL,
    event_time TIME NOT NULL,
    _sport_id INTEGER NOT NULL,
    _venue_id INTEGER,
    _home_team_id INTEGER NOT NULL,
    _away_team_id INTEGER NOT NULL,
    description TEXT,
    CONSTRAINT events__sport_id_fk FOREIGN KEY (_sport_id) REFERENCES sports(id),
    CONSTRAINT events__venue_id_fk FOREIGN KEY (_venue_id) REFERENCES venues(id),
    CONSTRAINT events__home_team_id_fk FOREIGN KEY (_home_team_id) REFERENCES teams(id),
    CONSTRAINT events__away_team_id_fk FOREIGN KEY (_away_team_id) REFERENCES teams(id),
    CONSTRAINT events_home_away_check CHECK (_home_team_id <> _away_team_id)
);

INSERT INTO sports (name)
VALUES ('Football'), ('Ice Hockey')
ON CONFLICT (name) DO NOTHING;

INSERT INTO teams (name, country_code)
VALUES
    ('Salzburg', 'AUT'),
    ('Sturm', 'AUT'),
    ('KAC', 'AUT'),
    ('Capitals', 'AUT')
ON CONFLICT (name) DO NOTHING;

INSERT INTO venues (name, city, country)
VALUES
    ('Red Bull Arena', 'Salzburg', 'Austria'),
    ('Stadthalle', 'Vienna', 'Austria')
ON CONFLICT (name, city, country) DO NOTHING;

INSERT INTO events (event_date, event_time, _sport_id, _venue_id, _home_team_id, _away_team_id, description)
SELECT
    DATE '2019-07-18',
    TIME '18:30:00',
    s.id,
    v.id,
    ht.id,
    at.id,
    'League match'
FROM sports s
JOIN venues v ON v.name = 'Red Bull Arena' AND v.city = 'Salzburg' AND v.country = 'Austria'
JOIN teams ht ON ht.name = 'Salzburg'
JOIN teams at ON at.name = 'Sturm'
WHERE s.name = 'Football'
AND NOT EXISTS (
    SELECT 1 FROM events e
    WHERE e.event_date = DATE '2019-07-18'
      AND e.event_time = TIME '18:30:00'
      AND e._home_team_id = ht.id
      AND e._away_team_id = at.id
);

INSERT INTO events (event_date, event_time, _sport_id, _venue_id, _home_team_id, _away_team_id, description)
SELECT
    DATE '2019-10-23',
    TIME '09:45:00',
    s.id,
    v.id,
    ht.id,
    at.id,
    'Regular season game'
FROM sports s
JOIN venues v ON v.name = 'Stadthalle' AND v.city = 'Vienna' AND v.country = 'Austria'
JOIN teams ht ON ht.name = 'KAC'
JOIN teams at ON at.name = 'Capitals'
WHERE s.name = 'Ice Hockey'
AND NOT EXISTS (
    SELECT 1 FROM events e
    WHERE e.event_date = DATE '2019-10-23'
      AND e.event_time = TIME '09:45:00'
      AND e._home_team_id = ht.id
      AND e._away_team_id = at.id
);
