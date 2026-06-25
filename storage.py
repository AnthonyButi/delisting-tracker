import sqlite3
import pandas as pd
from fred_client import build_panel

DB_PATH = "delisting.sqlite"


def init_db(db_path=DB_PATH):
    """Create the observations table if it doesn't already exist."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS observations (
            date      TEXT NOT NULL,
            series_id TEXT NOT NULL,
            value     REAL,
            PRIMARY KEY (date, series_id)
        )
        """
    )
    conn.commit()
    conn.close()


def save_panel(panel, db_path=DB_PATH):
    """Write a wide panel (date index, one column per series) to the database.
    Idempotent: re-running updates existing rows instead of duplicating them."""
    long = (
        panel.reset_index()
        .melt(id_vars="date", var_name="series_id", value_name="value")
        .dropna(subset=["value"])
    )
    long["date"] = long["date"].astype(str)

    conn = sqlite3.connect(db_path)
    conn.executemany(
        "INSERT OR REPLACE INTO observations (date, series_id, value) VALUES (?, ?, ?)",
        long[["date", "series_id", "value"]].itertuples(index=False, name=None),
    )
    conn.commit()
    conn.close()
    return len(long)


def load_panel(db_path=DB_PATH):
    """Read all stored observations back into a wide panel."""
    conn = sqlite3.connect(db_path)
    long = pd.read_sql("SELECT date, series_id, value FROM observations", conn)
    conn.close()
    panel = long.pivot(index="date", columns="series_id", values="value")
    panel.index = pd.to_datetime(panel.index)
    return panel.sort_index()


if __name__ == "__main__":
    init_db()
    panel = build_panel()
    n = save_panel(panel)
    print(f"Saved {n} observations.")

    stored = load_panel()
    print(stored.tail())
    print("Shape:", stored.shape)