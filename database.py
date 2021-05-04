from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Database:
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string)
        self.session = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
