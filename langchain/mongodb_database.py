"""PyMongo wrapper around a MongoDB database."""
from __future__ import annotations

import warnings
from typing import Any, Iterable, List, Optional
from pymongo import MongoClient, errors
from pymongo.collection import Collection
from bson.son import SON

from langchain import utils


class MongoDBDatabase:
    """PyMongo wrapper around a MongoDB database."""

    def __init__(
        self,
        client: MongoClient,
        db_name: str,
        ignore_collections: Optional[List[str]] = None,
        include_collections: Optional[List[str]] = None,
        sample_docs_in_collection_info: int = 3,
        max_string_length: int = 300,
    ):
        """Create client from MongoDB URI."""
        self._client = client
        self._db = self._client[db_name]
        self._db_name = db_name
        if include_collections and ignore_collections:
            raise ValueError("Cannot specify both include_collections and ignore_collections")

        self._all_collections = set(self._db.list_collection_names())
        
        self._include_collections = set(include_collections) if include_collections else set()
        if self._include_collections:
            missing_collections = self._include_collections - self._all_collections
            if missing_collections:
                raise ValueError(
                    f"include_collections {missing_collections} not found in database"
                )
        self._ignore_collections = set(ignore_collections) if ignore_collections else set()
        if self._ignore_collections:
            missing_collections = self._ignore_collections - self._all_collections
            if missing_collections:
                raise ValueError(
                    f"ignore_collections {missing_collections} not found in database"
                )

        usable_collections = self.get_usable_collection_names()
        self._usable_collections = set(usable_collections) if usable_collections else self._all_collections

        if not isinstance(sample_docs_in_collection_info, int):
            raise TypeError("sample_docs_in_collection_info must be an integer")

        self._sample_docs_in_collection_info = sample_docs_in_collection_info
        self._max_string_length = max_string_length

    @classmethod
    def from_uri(
        cls, database_uri: str, db_name: str, client_args: Optional[dict] = None, **kwargs: Any
    ) -> MongoDBDatabase:
        """Construct a PyMongo client from URI."""
        _client_args = client_args or {}
        return cls(MongoClient(database_uri, **_client_args), db_name, **kwargs)

    def get_usable_collection_names(self) -> Iterable[str]:
        """Get names of collections available."""
        if self._include_collections:
            return self._include_collections
        return self._all_collections - self._ignore_collections

    @property
    def collection_info(self) -> str:
        """Information about all collections in the database."""
        return self.get_collection_info()

    def get_collection_info(self, collection_names: Optional[List[str]] = None) -> str:
        """Get information about specified collections.

        If `sample_docs_in_collection_info`, the specified number of sample documents will be
        appended to each collection description. 
        """
        all_collection_names = self.get_usable_collection_names()
        if collection_names is not None:
            missing_collections = set(collection_names).difference(all_collection_names)
            if missing_collections:
                raise ValueError(f"collection_names {missing_collections} not found in database")
            all_collection_names = collection_names

        collections_info = []
        for collection_name in all_collection_names:
            collection = self._db[collection_name]
            collection_info = f"Collection Name: {collection_name}"
            collection_info += f"\nCount: {collection.count_documents({})}"
            
            sample_docs = collection.find().limit(self._sample_docs_in_collection_info)
            collection_info += "\nSample Documents:"
            for doc in sample_docs:
                collection_info += f"\n{doc}"
                
            collections_info.append(collection_info)
        final_str = "\n\n".join(collections_info)
        return final_str

    def run(self, command: str, fetch: str = "all") -> str:
        """Execute a MongoDB command and return a string representing the results.

        If the statement returns documents, a string of the results is returned.
        If the statement returns no documents, an empty string is returned.

        """
        try:
            # MongoDB commands are expressed as BSON, so we should use SON to keep keys order
            cmd = SON(command)
            cursor = self._db.command(cmd)
            if fetch == "all":
                result = list(cursor)
            elif fetch == "one":
                result = cursor.next()
            else:
                raise ValueError("Fetch parameter must be either 'one' or 'all'")

            # Convert documents values to string to avoid issues with text trunacating
            if isinstance(result, list):
                return str(
                    [
                        {k: truncate_word(v, length=self._max_string_length) for k, v in doc.items()}
                        for doc in result
                    ]
                )

            return str(
                {k: truncate_word(v, length=self._max_string_length) for k, v in result.items()}
            )
        except errors.PyMongoError as e:
            return f"Error: {e}"
