DROP TABLE IF EXISTS round_scores;
DROP TABLE IF EXISTS fight_scores;
DROP TABLE IF EXISTS judges;

CREATE TABLE judges (
  judge_id SERIAL PRIMARY KEY,
  name TEXT UNIQUE
);

CREATE TABLE fight_scores (
  fight_id TEXT REFERENCES fights(fight_id),
  judge_id INT REFERENCES judges(judge_id),
  event_id TEXT REFERENCES events(event_id),
  total_fighter1 INT,
  total_fighter2 INT,
  PRIMARY KEY (fight_id, event_id, judge_id)
);

CREATE TABLE round_scores (
  fight_id TEXT REFERENCES fights(fight_id),
  event_id TEXT REFERENCES events(event_id),
  judge_id INT REFERENCES judges(judge_id),
  round_number INT,
  fighter1_score INT,
  fighter2_score INT,
  PRIMARY KEY (fight_id, event_id, judge_id, round_number)
);