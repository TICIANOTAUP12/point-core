import os
import sqlite3
from datetime import datetime
from pathlib import Path

from models.conversation import ConversationRecord
from models.nlu import SlotsGlobales

DEFAULT_DB_PATH = Path(
    os.getenv("CORE_DB_PATH", str(Path(__file__).resolve().parent.parent / "data" / "conversations.db"))
)


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection | None = None) -> None:
    close_after = conn is None
    db = conn or get_connection()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            phone TEXT PRIMARY KEY,
            state TEXT NOT NULL DEFAULT 'idle',
            combo_id TEXT,
            cantidad INTEGER,
            modulo TEXT,
            needs_human INTEGER NOT NULL DEFAULT 0,
            last_message_at TEXT NOT NULL,
            message_count INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    db.commit()
    if close_after:
        db.close()


def _parse_dt(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def _row_to_record(row: sqlite3.Row) -> ConversationRecord:
    return ConversationRecord(
        phone=row["phone"],
        state=row["state"],  # type: ignore[arg-type]
        slots=SlotsGlobales(
            combo_id=row["combo_id"],
            cantidad=row["cantidad"],
            modulo=row["modulo"],
        ),
        needs_human=bool(row["needs_human"]),
        last_message_at=_parse_dt(row["last_message_at"]),
        message_count=row["message_count"],
    )


def get_conversation(phone: str, conn: sqlite3.Connection | None = None) -> ConversationRecord:
    close_after = conn is None
    db = conn or get_connection()
    row = db.execute("SELECT * FROM conversations WHERE phone = ?", (phone,)).fetchone()
    if row is None:
        record = ConversationRecord(phone=phone)
        save_conversation(record, db)
        if close_after:
            db.close()
        return record
    if close_after:
        db.close()
    return _row_to_record(row)


def save_conversation(record: ConversationRecord, conn: sqlite3.Connection | None = None) -> None:
    close_after = conn is None
    db = conn or get_connection()
    db.execute(
        """
        INSERT INTO conversations (
            phone, state, combo_id, cantidad, modulo,
            needs_human, last_message_at, message_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(phone) DO UPDATE SET
            state = excluded.state,
            combo_id = excluded.combo_id,
            cantidad = excluded.cantidad,
            modulo = excluded.modulo,
            needs_human = excluded.needs_human,
            last_message_at = excluded.last_message_at,
            message_count = excluded.message_count
        """,
        (
            record.phone,
            record.state,
            record.slots.combo_id,
            record.slots.cantidad,
            record.slots.modulo,
            int(record.needs_human),
            record.last_message_at.isoformat(),
            record.message_count,
        ),
    )
    db.commit()
    if close_after:
        db.close()


def reset_conversation(phone: str, conn: sqlite3.Connection | None = None) -> ConversationRecord:
    record = ConversationRecord(phone=phone)
    save_conversation(record, conn)
    return record
