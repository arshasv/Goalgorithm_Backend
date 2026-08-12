"""
Database migration script to:
1. Add missing columns to matches table (round, external_api_id, competition_name, external_sync_status)
2. Deduplicate match_numbers
3. Add UNIQUE constraint on match_number
4. Add missing columns to actual_results table (result_source, last_synced_at)
"""
import sqlite3
import sys

import os
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fifa_dev.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ---- matches table ----
    c.execute("PRAGMA table_info(matches)")
    existing_cols = {row[1] for row in c.fetchall()}

    # Add missing columns
    if "round" not in existing_cols:
        print("Adding column: matches.round")
        c.execute("ALTER TABLE matches ADD COLUMN round VARCHAR(100)")
    if "external_api_id" not in existing_cols:
        print("Adding column: matches.external_api_id")
        c.execute("ALTER TABLE matches ADD COLUMN external_api_id VARCHAR(255)")
    if "competition_name" not in existing_cols:
        print("Adding column: matches.competition_name")
        c.execute("ALTER TABLE matches ADD COLUMN competition_name VARCHAR(255)")
    if "external_sync_status" not in existing_cols:
        print("Adding column: matches.external_sync_status")
        c.execute("ALTER TABLE matches ADD COLUMN external_sync_status VARCHAR(20)")

    # Deduplicate match_numbers before adding unique constraint
    c.execute(
        """
        SELECT match_number, COUNT(*) as cnt
        FROM matches
        GROUP BY match_number
        HAVING cnt > 1
        """
    )
    dups = c.fetchall()
    for match_num, cnt in dups:
        print(f"Deduplicating match_number {match_num} ({cnt} copies)")
        # Keep row with lowest rowid, delete others
        c.execute(
            """
            DELETE FROM matches
            WHERE match_number = ?
            AND rowid NOT IN (
                SELECT MIN(rowid) FROM matches WHERE match_number = ?
            )
            """,
            (match_num, match_num),
        )

    # Add unique index on match_number (SQLite compatible — replaces CREATE UNIQUE CONSTRAINT)
    c.execute("PRAGMA index_list(matches)")
    existing_idx = {row[1] for row in c.fetchall()}
    if "uq_matches_match_number" not in existing_idx:
        print("Creating unique index: uq_matches_match_number")
        c.execute("CREATE UNIQUE INDEX uq_matches_match_number ON matches(match_number)")

    # ---- actual_results table ----
    c.execute("PRAGMA table_info(actual_results)")
    existing_result_cols = {row[1] for row in c.fetchall()}
    if "result_source" not in existing_result_cols:
        print("Adding column: actual_results.result_source")
        c.execute(
            "ALTER TABLE actual_results ADD COLUMN result_source VARCHAR(50) DEFAULT 'MANUAL' NOT NULL"
        )
    if "last_synced_at" not in existing_result_cols:
        print("Adding column: actual_results.last_synced_at")
        c.execute("ALTER TABLE actual_results ADD COLUMN last_synced_at DATETIME")

    conn.commit()
    conn.close()
    print("Migration complete!")


if __name__ == "__main__":
    migrate()
