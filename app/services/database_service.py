import sqlite3
from sqlite3 import Connection
from datetime import datetime
from pathlib import Path
from statistics import mean

DB_PATH = Path(__file__).parent.parent / "image_pipeline.db"

def get_connection() -> Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS images (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        status TEXT NOT NULL,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        width INTEGER,
        height INTEGER,
        format TEXT,
        size_bytes INTEGER,
        caption TEXT,
        small_thumb TEXT,
        medium_thumb TEXT
    )
    """)
    conn.commit()
    conn.close()

def get_all_images():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM images")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_image_by_id(image_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM images WHERE id = ?", (image_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def insert_image(image_id: str, filename: str, status: str = "processing"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO images (id, filename, status)
        VALUES (?, ?, ?)
    """, (image_id, filename, status))
    conn.commit()
    conn.close()

def update_image_metadata(image_id: str, width: int, height: int, fmt: str, size_bytes: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE images
        SET width=?, height=?, format=?, size_bytes=?, status='processed'
        WHERE id=?
    """, (width, height, fmt, size_bytes, image_id))
    conn.commit()
    conn.close()

def update_image_thumbnails(image_id: str, small_thumb: str, medium_thumb: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE images
        SET small_thumb=?, medium_thumb=?
        WHERE id=?
    """, (small_thumb, medium_thumb, image_id))
    conn.commit()
    conn.close()

def update_image_caption(image_id: str, caption: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE images
        SET caption=?
        WHERE id=?
    """, (caption, image_id))
    conn.commit()
    conn.close()

def update_image_status(image_id: str, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE images
        SET status = ?
        WHERE id = ?
    """, (status, image_id))
    conn.commit()
    conn.close()

import json

def update_image_exif(image_id: str, exif_data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE images
        SET exif = ?
        WHERE id = ?
    """, (json.dumps(exif_data), image_id))
    conn.commit()
    conn.close()

def mark_image_processed(image_id: str):
    """
    Mark an image as processed and update the processed_at timestamp.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE images
        SET status = ?, processed_at = ?
        WHERE id = ?
    """, ("processed", datetime.utcnow().isoformat(), image_id))
    conn.commit()
    conn.close()

def get_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM images")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM images WHERE status = 'processed'")
    success = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM images WHERE status = 'failed'")
    failed = cursor.fetchone()[0]

    cursor.execute("""
        SELECT uploaded_at, processed_at
        FROM images
        WHERE processed_at IS NOT NULL
    """)
    rows = cursor.fetchall()

    times = []
    for row in rows:
        if row["uploaded_at"] and row["processed_at"]:
            from datetime import datetime
            start = datetime.fromisoformat(row["uploaded_at"])
            end = datetime.fromisoformat(row["processed_at"])
            times.append((end - start).total_seconds())

    avg_time = mean(times) if times else 0

    conn.close()
    return {
        "total": total,
        "success": success,
        "failed": failed,
        "avg_time": avg_time
    }



