from sqlalchemy import text

from app.infrastructure.database import SessionLocal, engine


try:
    with SessionLocal() as session:
        result = session.execute(
            text("SELECT current_user, current_database()")
        )

        user, database = result.one()

        print(f"Usuario: {user}")
        print(f"Base de datos: {database}")
finally:
    engine.dispose()