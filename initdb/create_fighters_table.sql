DROP TABLE IF EXISTS fighters;
DROP TABLE IF EXISTS fighter_stats;
DROP TABLE IF EXISTS pre_comp_stats;

CREATE TABLE fighters (
  fighter_id TEXT PRIMARY KEY,    
  name TEXT NOT NULL,
  nickname TEXT,
  dob DATE,
  height INT,
  weight INT,
  reach INT,
  stance TEXT
);

CREATE TABLE fighter_stats {
    fighter_id TEXT REFERENCES fighters(fighter_id),
    timestamp TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (fighter_id, timestamp),
    wins INT,
    losses INT,
    draws INT,
    win_streak INT,
    prev_fights INT,
    sig_strikes_landed_per_min NUMERIC,
    sig_strikes_accuracy NUMERIC,
    sig_strikes_absorbed_permin NUMERIC,
    td_landed_avg NUMERIC,
    td_accuracy NUMERIC,
    td_def NUMERIC,
    sub_attempts_avg NUMERIC
}

CREATE INDEX idx_fighter_stats_fighter_id ON fighter_stats(fighter_id);
CREATE INDEX idx_fighter_stats_timestamp ON fighter_stats(timestamp);

CREATE TABLE pre_comp_stats (
    fight_id                TEXT REFERENCES fights(fight_id),
    fighter_id              TEXT REFERENCES fighters(fighter_id),
    stat_type               TEXT NOT NULL,  -- e.g. 'overall' or 'recent'
    
    -- Knockdowns
    knockdowns_avg          NUMERIC,
    knockdowns_diff         NUMERIC,
    
    -- Submission Attempts
    sub_attempts_avg        NUMERIC,
    sub_attempts_diff       NUMERIC,
    sub_attempts_per_min    NUMERIC,
    
    -- Reversals
    reversals_avg           NUMERIC,
    reversals_diff          NUMERIC,
    
    -- Control Time
    ctrl_avg             NUMERIC,
    ctrl_diff            NUMERIC,
    
    -- td
    td_landed_avg    NUMERIC,
    td_landed_diff   NUMERIC,
    td_landed_per_min NUMERIC,
    td_attempts_avg  NUMERIC,
    td_attempts_diff NUMERIC,
    td_attempts_per_min NUMERIC,
    td_accuracy  NUMERIC,
    td_accuracy_diff NUMERIC,
    td_def       NUMERIC,
    td_def_diff      NUMERIC,
    
    -- Significant Strikes
    sig_strikes_landed_avg  NUMERIC,
    sig_strikes_landed_diff NUMERIC,
    sig_strikes_landed_per_min NUMERIC,
    sig_strikes_attempts_avg NUMERIC,
    sig_strikes_attempts_diff NUMERIC,
    sig_strikes_attempts_per_min NUMERIC,
    sig_strikes_accuracy NUMERIC,
    sig_strikes_accuracy_diff NUMERIC,
    sig_strikes_def_avg     NUMERIC,
    sig_strikes_def_diff    NUMERIC,
    
    -- Total Strikes
    total_strikes_landed_avg NUMERIC,
    total_strikes_landed_diff NUMERIC,
    total_strikes_landed_per_min NUMERIC,
    total_strikes_attempts_avg NUMERIC,
    total_strikes_attempts_diff NUMERIC,
    total_strikes_attempts_per_min NUMERIC,
    total_strikes_accuracy_avg NUMERIC,
    total_strikes_accuracy_diff NUMERIC,
    total_strikes_def_avg   NUMERIC,
    total_strikes_def_diff  NUMERIC,
    
    -- Head Strikes
    head_strikes_landed_avg NUMERIC,
    head_strikes_landed_diff NUMERIC,
    head_strikes_landed_per_min NUMERIC,
    head_strikes_attempts_avg NUMERIC,
    head_strikes_attempts_diff NUMERIC,
    head_strikes_attempts_per_min NUMERIC,
    head_strikes_accuracy_avg NUMERIC,
    head_strikes_accuracy_diff NUMERIC,
    head_strikes_def_avg    NUMERIC,
    head_strikes_def_diff   NUMERIC,
    
    -- Body Strikes
    body_strikes_landed_avg NUMERIC,
    body_strikes_landed_diff NUMERIC,
    body_strikes_landed_per_min NUMERIC,
    body_strikes_attempts_avg NUMERIC,
    body_strikes_attempts_diff NUMERIC,
    body_strikes_attempts_per_min NUMERIC,
    body_strikes_accuracy_avg NUMERIC,
    body_strikes_accuracy_diff NUMERIC,
    body_strikes_def_avg    NUMERIC,
    body_strikes_def_diff   NUMERIC,
    
    -- Leg Strikes
    leg_strikes_landed_avg  NUMERIC,
    leg_strikes_landed_diff NUMERIC,
    leg_strikes_landed_per_min NUMERIC,
    leg_strikes_attempts_avg NUMERIC,
    leg_strikes_attempts_diff NUMERIC,
    leg_strikes_attempts_per_min NUMERIC,
    leg_strikes_accuracy_avg NUMERIC,
    leg_strikes_accuracy_diff NUMERIC,
    leg_strikes_def_avg     NUMERIC,
    leg_strikes_def_diff    NUMERIC,
    
    -- Distance Strikes
    distance_strikes_landed_avg NUMERIC,
    distance_strikes_landed_diff NUMERIC,
    distance_strikes_landed_per_min NUMERIC,
    distance_strikes_attempts_avg NUMERIC,
    distance_strikes_attempts_diff NUMERIC,
    distance_strikes_attempts_per_min NUMERIC,
    distance_strikes_accuracy_avg NUMERIC,
    distance_strikes_accuracy_diff NUMERIC,
    distance_strikes_def_avg NUMERIC,
    distance_strikes_def_diff NUMERIC,
    
    -- Clinch Strikes
    clinch_strikes_landed_avg NUMERIC,
    clinch_strikes_landed_diff NUMERIC,
    clinch_strikes_landed_per_min NUMERIC,
    clinch_strikes_attempts_avg NUMERIC,
    clinch_strikes_attempts_diff NUMERIC,
    clinch_strikes_attempts_per_min NUMERIC,
    clinch_strikes_accuracy_avg NUMERIC,
    clinch_strikes_accuracy_diff NUMERIC,
    clinch_strikes_def_avg  NUMERIC,
    clinch_strikes_def_diff NUMERIC,
    
    -- Ground Strikes
    ground_strikes_landed_avg NUMERIC,
    ground_strikes_landed_diff NUMERIC,
    ground_strikes_landed_per_min NUMERIC,
    ground_strikes_attempts_avg NUMERIC,
    ground_strikes_attempts_diff NUMERIC,
    ground_strikes_attempts_per_min NUMERIC,
    ground_strikes_accuracy_avg NUMERIC,
    ground_strikes_accuracy_diff NUMERIC,
    ground_strikes_def_avg  NUMERIC,
    ground_strikes_def_diff NUMERIC,
    
    -- Physicals (differences only)
    physicals_reach_diff    NUMERIC,
    physicals_height_diff   NUMERIC,
    physicals_age_diff      NUMERIC,
    
    PRIMARY KEY (fight_id, fighter_id, stat_type)
);
