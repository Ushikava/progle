ALTER TABLE words ADD COLUMN IF NOT EXISTS second_hint_position integer;
ALTER TABLE words DROP COLUMN IF EXISTS description;
