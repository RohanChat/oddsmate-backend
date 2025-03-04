DROP TABLE IF EXISTS fights;
DROP TABLE IF EXISTS fight_stats;
DROP TABLE IF EXISTS round_stats;

CREATE TABLE fights (
  fight_id TEXT PRIMARY KEY,
  event_id TEXT REFERENCES events(event_id),
  fight_url TEXT,
  status TEXT,              -- e.g., 'live', 'finished'
  current_round TEXT,
  current_time TEXT,
  last_updated TIMESTAMPTZ,
  referee TEXT,
  fighter1_id TEXT REFERENCES fighters(fighter_id),
  fighter2_id TEXT REFERENCES fighters(fighter_id),
  final_method TEXT         -- updated when fight concludes
);

-- Index on fight_id column
CREATE INDEX idx_fights_fight_id ON fights(fight_id);

-- Index on status column
CREATE INDEX idx_fights_status ON fights(status);

CREATE TABLE fight_stats (
    fight_id                     TEXT REFERENCES fights(fight_id),
    fighter_id                   TEXT REFERENCES fighters(fighter_id),
    kd                           INT,  -- knockdowns

    -- Significant Strikes (aggregated)
    sig_strikes_landed           INT,
    sig_strikes_attempted        INT,
    sig_strikes_accuracy       NUMERIC,  -- e.g. 53.0

    -- Breakdown: Head
    head_strikes_landed          INT,
    head_strikes_attempted       INT,

    -- Breakdown: Body
    body_strikes_landed          INT,
    body_strikes_attempted       INT,

    -- Breakdown: Leg
    leg_strikes_landed           INT,
    leg_strikes_attempted        INT,

    -- Breakdown: Distance
    distance_strikes_landed      INT,
    distance_strikes_attempted   INT,

    -- Breakdown: Clinch
    clinch_strikes_landed        INT,
    clinch_strikes_attempted     INT,

    -- Breakdown: Ground
    ground_strikes_landed        INT,
    ground_strikes_attempted     INT,

    -- Total Strikes (should equal sum of breakdowns if computed)
    total_strikes_landed         INT,
    total_strikes_attempted      INT,
    total_strikes_accuracy      NUMERIC,


    -- Takedowns
    td_landed                    INT,
    td_attempted                 INT,
    td_accuracy                  NUMERIC(5,2),  -- e.g. 0.0

    -- Submission Attempts and Reversals
    sub_att                      INT,
    reversals                    INT,

    -- Control Time (stored as an interval, e.g. '2:58' becomes 2 minutes 58 seconds)
    ctrl                    INT,

    PRIMARY KEY (fight_id, fighter_id)
);


CREATE TABLE round_stats (
    fight_id                    TEXT REFERENCES fights(fight_id),
    fighter_id                  TEXT REFERENCES fighters(fighter_id),
    round_number                INT,
    
    -- Knockdowns for the round
    kd                          INT,
    
    -- Overall Significant Strikes (aggregated)
    sig_strikes_landed          INT,
    sig_strikes_attempted       INT,
    sig_strikes_accuracy      NUMERIC,
    
    -- Breakdown by strike type
    head_strikes_landed         INT,
    head_strikes_attempted      INT,
    
    body_strikes_landed         INT,
    body_strikes_attempted      INT,
    
    leg_strikes_landed          INT,
    leg_strikes_attempted       INT,
    
    distance_strikes_landed     INT,
    distance_strikes_attempted  INT,
    
    clinch_strikes_landed       INT,
    clinch_strikes_attempted    INT,
    
    ground_strikes_landed       INT,
    ground_strikes_attempted    INT,
    
    -- Total Strikes
    total_strikes_landed        INT,
    total_strikes_attempted     INT,
    
    -- Takedowns
    td_landed                   INT,
    td_attempted                INT,
    td_accuracy               NUMERIC,
    
    -- Submission Attempts and Reversals
    sub_att                     INT,
    reversals                   INT,
    
    -- Control Time: stored as an INTERVAL (e.g., converting "129" seconds into an interval)
    ctrl                   INT,
    
    PRIMARY KEY (fight_id, fighter_id, round_number)
);


CREATE TABLE live_stats (
    fight_id                    TEXT REFERENCES fights(fight_id),
    fighter_id                  TEXT REFERENCES fighters(fighter_id),
    round_number                INT,
    time                        INT,
    pre_fight_odds_espn         TEXT,
    kd                          INT,
    sig_strikes_landed          INT,
    sig_strikes_attempted       INT,
    sig_strikes_accuracy        NUMERIC,
    head_strikes_landed         INT,
    head_strikes_attempted      INT,
    body_strikes_landed         INT,
    body_strikes_attempted      INT,
    leg_strikes_landed          INT,
    leg_strikes_attempted       INT,
    -- distance_strikes_landed     INT,
    -- distance_strikes_attempted  INT,
    -- clinch_strikes_landed       INT,
    -- clinch_strikes_attempted    INT,
    -- ground_strikes_landed       INT,
    -- ground_strikes_attempted    INT,
    total_strikes_landed        INT,
    total_strikes_attempted     INT,
    total_strikes_accuracy      NUMERIC,
    td_landed                   INT,
    td_attempted                INT,
    td_accuracy               NUMERIC,
    sub_att                     INT,
    reversals                   INT,
    ctrl                        INT,
    PRIMARY KEY (fight_id, fighter_id, round_number, timestamp)
)