from db.firestore_client import FirestoreClient
import structlog

log = structlog.get_logger()
_db_instance = None

def get_db():
    global _db_instance
    if _db_instance is None:
        _db_instance = FirestoreClient()
    return _db_instance
