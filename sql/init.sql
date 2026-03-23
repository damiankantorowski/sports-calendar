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