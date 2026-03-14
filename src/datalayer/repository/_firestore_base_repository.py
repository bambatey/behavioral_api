from typing import Generic, TypeVar, List, Optional, Union, Type
from contextlib import asynccontextmanager
from firebase_admin import firestore_async

from ._repository_abc import AsyncRepositoryABC

T = TypeVar('T')
PrimaryKeyType = Union[int, str]


class FirestoreBaseRepository(AsyncRepositoryABC[T]):
    """Asynchronous Firestore repository implementation"""

    def __init__(self, db: AsyncClient, model_class: Type[T], collection_name: str):
        self.db = db
        self.model_class = model_class
        self._collection = collection_name

    async def get_by_id(self, id: PrimaryKeyType) -> Optional[T]:
        """Get entity by primary key (document ID)"""
        try:
            doc = await self.db.collection(self._collection).document(str(id)).get()
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                # Reconstruct from dict if model has from_dict method
                if hasattr(self.model_class, 'from_dict'):
                    return self.model_class.from_dict(data)
                return self.model_class(**data)
            return None
        except Exception as e:
            print(f"Error getting document {id}: {e}")
            return None

    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """Get all entities with optional pagination"""
        try:
            query = self.db.collection(self._collection)

            # Apply offset if provided
            if offset:
                # Firestore doesn't have offset, so we fetch and skip locally
                docs = query.limit(offset + (limit or 100)).stream()
                docs_list = [d async for d in docs]
                docs_list = docs_list[offset:]
            else:
                docs = query.limit(limit or 100000).stream()
                docs_list = [d async for d in docs]

            result = []
            for doc in docs_list:
                data = doc.to_dict()
                data['id'] = doc.id
                if hasattr(self.model_class, 'from_dict'):
                    result.append(self.model_class.from_dict(data))
                else:
                    result.append(self.model_class(**data))
            return result
        except Exception as e:
            print(f"Error getting all documents: {e}")
            return []

    async def find_by(self, **filters) -> List[T]:
        """Find entities by filter criteria"""
        try:
            query = self.db.collection(self._collection)

            for key, value in filters.items():
                if isinstance(value, dict) and 'op' in value:
                    # Support for complex operations: {'op': 'gt', 'value': 100}
                    op = value['op']
                    val = value['value']

                    if op == 'eq':
                        query = query.where(key, '==', val)
                    elif op == 'gt':
                        query = query.where(key, '>', val)
                    elif op == 'gte':
                        query = query.where(key, '>=', val)
                    elif op == 'lt':
                        query = query.where(key, '<', val)
                    elif op == 'lte':
                        query = query.where(key, '<=', val)
                    elif op == 'ne':
                        query = query.where(key, '!=', val)
                    elif op == 'in':
                        query = query.where(key, 'in', val)
                    elif op == 'array-contains':
                        query = query.where(key, 'array-contains', val)
                elif isinstance(value, (list, tuple)):
                    query = query.where(key, 'in', value)
                else:
                    query = query.where(key, '==', value)

            docs = query.stream()
            result = []
            async for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                if hasattr(self.model_class, 'from_dict'):
                    result.append(self.model_class.from_dict(data))
                else:
                    result.append(self.model_class(**data))
            return result
        except Exception as e:
            print(f"Error finding documents with filters {filters}: {e}")
            return []

    async def find_one_by(self, **filters) -> Optional[T]:
        """Find single entity by filter criteria"""
        results = await self.find_by(**filters)
        if len(results) > 1:
            raise ValueError(f"Multiple results found for {filters}")
        return results[0] if results else None

    async def save(self, entity: T) -> T:
        """Save (insert or update) entity"""
        try:
            entity_dict = entity.to_dict() if hasattr(entity, 'to_dict') else vars(entity)
            entity_id = entity_dict.get('id') or getattr(entity, 'id', None)

            if not entity_id:
                raise ValueError("Entity must have an 'id' field")

            await self.db.collection(self._collection).document(entity_id).set(entity_dict)
            return entity
        except Exception as e:
            print(f"Error saving entity: {e}")
            raise

    async def save_all(self, entities: List[T]) -> List[T]:
        """Save multiple entities (batch write)"""
        try:
            batch = self.db.batch()

            for entity in entities:
                entity_dict = entity.to_dict() if hasattr(entity, 'to_dict') else vars(entity)
                entity_id = entity_dict.get('id') or getattr(entity, 'id', None)

                if not entity_id:
                    raise ValueError("Entity must have an 'id' field")

                batch.set(self.db.collection(self._collection).document(entity_id), entity_dict)

            await batch.commit()
            return entities
        except Exception as e:
            print(f"Error saving multiple entities: {e}")
            raise

    async def delete(self, entity: T) -> None:
        """Delete entity"""
        try:
            entity_id = getattr(entity, 'id', None)
            if not entity_id:
                raise ValueError("Entity must have an 'id' field")

            await self.db.collection(self._collection).document(entity_id).delete()
        except Exception as e:
            print(f"Error deleting entity: {e}")
            raise

    async def delete_by_id(self, id: PrimaryKeyType) -> bool:
        """Delete entity by ID, returns True if deleted"""
        try:
            await self.db.collection(self._collection).document(str(id)).delete()
            return True
        except Exception as e:
            print(f"Error deleting document {id}: {e}")
            return False

    async def exists(self, id: PrimaryKeyType) -> bool:
        """Check if entity exists by ID"""
        try:
            doc = await self.db.collection(self._collection).document(str(id)).get()
            return doc.exists
        except Exception as e:
            print(f"Error checking existence of {id}: {e}")
            return False

    async def count(self, **filters) -> int:
        """Count entities with optional filters"""
        try:
            query = self.db.collection(self._collection)

            for key, value in filters.items():
                if isinstance(value, dict) and 'op' in value:
                    op = value['op']
                    val = value['value']
                    if op == 'eq':
                        query = query.where(key, '==', val)
                    elif op == 'gt':
                        query = query.where(key, '>', val)
                    elif op == 'gte':
                        query = query.where(key, '>=', val)
                    elif op == 'lt':
                        query = query.where(key, '<', val)
                    elif op == 'lte':
                        query = query.where(key, '<=', val)
                else:
                    query = query.where(key, '==', value)

            docs = query.stream()
            count = 0
            async for _ in docs:
                count += 1
            return count
        except Exception as e:
            print(f"Error counting documents: {e}")
            return 0

    @asynccontextmanager
    async def transaction(self):
        """Async context manager for handling transactions"""
        try:
            yield self
        except Exception as e:
            print(f"Transaction error: {e}")
            raise
