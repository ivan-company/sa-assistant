from sqlmodel import create_engine, SQLModel, Session

_engine_instance = None
_models_imported = False


def get_engine(database_url: str = "sqlite:///app.db"):
    """Get the singleton database engine"""
    global _engine_instance, _models_imported

    if _engine_instance is None:
        _engine_instance = create_engine(database_url, echo=False)
        SQLModel.metadata.create_all(_engine_instance)

    return _engine_instance


def get_session() -> Session:
    """Get a new database session"""
    return Session(get_engine())
