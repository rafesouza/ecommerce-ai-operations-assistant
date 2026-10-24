
import os

from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from backend.app.models import Base


def main():
    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host="127.0.0.1",
        port=int(os.environ.get("POSTGRES_PORT", "5433")),
        database="ecommerce_ai_test",
    )

    engine = create_engine(database_url)

    try:
        Base.metadata.create_all(bind=engine)
        print("Test database tables created successfully.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
