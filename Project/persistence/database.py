"""The connection and the session factory, built once when the module is first imported.

Importing this module creates no table and writes nothing.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import config

database_engine = create_engine(config.APPLICATION_DATABASE_URL,
                                connect_args={"check_same_thread": False})

SessionFactory = sessionmaker(bind=database_engine, expire_on_commit=False)
