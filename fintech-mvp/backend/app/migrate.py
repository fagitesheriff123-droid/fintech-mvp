"""
Tiny additive-only migration guard, used because this project has no Alembic.
add_missing_columns() inspects the live DB and ALTERs in any column present
in the SQLAlchemy models but missing from the table — safe to run on every
startup, and required here because Base.metadata.create_all() only creates
whole tables that don't exist yet; it never adds a column to a table that's
already there (which the deployed `users` table already is).
"""
from sqlalchemy import inspect, text


def add_missing_columns(engine, Base):
    insp = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if not insp.has_table(table.name):
                continue  # create_all will make this one from scratch
            existing = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name in existing:
                    continue
                ddl_type = col.type.compile(dialect=conn.dialect)
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {ddl_type}'))
