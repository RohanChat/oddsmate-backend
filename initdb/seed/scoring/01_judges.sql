-- Seed data for judges table
-- Generated on 2025-02-27 17:38:29

-- First clear any existing data
TRUNCATE judges CASCADE;

-- Insert judges data
INSERT INTO judges (name) VALUES ('Judge1') ON CONFLICT (name) DO NOTHING;
INSERT INTO judges (name) VALUES ('Judge2') ON CONFLICT (name) DO NOTHING;
INSERT INTO judges (name) VALUES ('Judge3') ON CONFLICT (name) DO NOTHING;
INSERT INTO judges (name) VALUES ('Unknown Judge') ON CONFLICT (name) DO NOTHING;
