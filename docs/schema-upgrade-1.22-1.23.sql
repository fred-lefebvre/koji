-- upgrade script to migrate the Koji database schema
-- from version 1.22 to 1.23


BEGIN;

CREATE INDEX task_by_no_parent_state_method ON task(parent, state, method) WHERE parent IS NULL;

COMMIT;