from google.cloud import firestore
from typing import List, Optional
import structlog
import os
from dotenv import load_dotenv

log = structlog.get_logger()


class FirestoreClient:
    """Singleton-friendly Firestore async client."""

    def __init__(self):
        load_dotenv()
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        database = os.getenv("FIRESTORE_DATABASE", "dakshgrid")
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        if creds_path and os.path.exists(creds_path):
            self.db = firestore.AsyncClient.from_service_account_json(
                creds_path, 
                project=project, 
                database=database
            )
        else:
            self.db = firestore.AsyncClient(project=project, database=database)
            
        log.info("firestore.connected", project=project, database=database, auth="explicit" if creds_path else "adc")

    # ──────────────────────────────────────────
    # CREATE
    # ──────────────────────────────────────────
    async def create(self, collection: str, data: dict) -> str:
        """
        Create a new document with an auto-generated ID.
        Returns the new document ID.
        """
        ref = self.db.collection(collection).document()
        await ref.set({
            **data,
            "created_at": firestore.SERVER_TIMESTAMP,
        })
        log.info("db.create", collection=collection, id=ref.id)
        return ref.id

    # ──────────────────────────────────────────
    # GET (single doc)
    # ──────────────────────────────────────────
    async def get(self, collection: str, doc_id: str) -> Optional[dict]:
        """Return a single document by ID, or None if not found."""
        doc = await self.db.collection(collection).document(doc_id).get()
        if doc.exists:
            return {"id": doc.id, **doc.to_dict()}
        log.warning("db.get.not_found", collection=collection, id=doc_id)
        return None

    # ──────────────────────────────────────────
    # UPDATE
    # ──────────────────────────────────────────
    async def update(self, collection: str, doc_id: str, data: dict) -> None:
        """Merge-update specific fields on an existing document."""
        await self.db.collection(collection).document(doc_id).update({
            **data,
            "updated_at": firestore.SERVER_TIMESTAMP,
        })
        log.info("db.update", collection=collection, id=doc_id)

    # ──────────────────────────────────────────
    # DELETE
    # ──────────────────────────────────────────
    async def delete(self, collection: str, doc_id: str) -> None:
        """Hard-delete a document."""
        await self.db.collection(collection).document(doc_id).delete()
        log.info("db.delete", collection=collection, id=doc_id)

    # ──────────────────────────────────────────
    # QUERY  (filter-based listing)
    # ──────────────────────────────────────────
    async def query(
        self,
        collection: str,
        filters: List[tuple],
        limit: int = 50,
        order_by: str = None,
    ) -> List[dict]:
        """
        Query with Firestore where-clauses.
        filters: list of (field, operator, value) tuples
            e.g. [("user_id", "==", "abc"), ("status", "==", "pending")]
        """
        ref = self.db.collection(collection)
        for field, op, val in filters:
            ref = ref.where(field, op, val)
        if order_by:
            ref = ref.order_by(order_by)
        ref = ref.limit(limit)
        docs = await ref.get()
        result = [{"id": d.id, **d.to_dict()} for d in docs]
        log.info("db.query", collection=collection, count=len(result))
        return result

    # ──────────────────────────────────────────
    # SET (explicit ID — used for user prefs)
    # ──────────────────────────────────────────
    async def set_doc(self, collection: str, doc_id: str, data: dict) -> None:
        """Create or completely overwrite a document at a known ID."""
        await self.db.collection(collection).document(doc_id).set({
            **data,
            "updated_at": firestore.SERVER_TIMESTAMP,
        })
        log.info("db.set", collection=collection, id=doc_id)
