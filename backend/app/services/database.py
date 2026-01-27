"""
MongoDB Database Service

Handles connection to MongoDB Atlas and provides database operations.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure

from app.config import get_settings


class Database:
    """
    MongoDB database connection manager.

    Uses Motor for async MongoDB operations.
    Collections:
    - files: Stores file metadata (uploads)
    - messages: Stores chat history
    - sessions: Stores session data
    """

    def __init__(self):
        self.client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None
        self._connected = False

    async def connect(self) -> None:
        """
        Establish connection to MongoDB Atlas.
        """
        if self._connected:
            return

        settings = get_settings()

        try:
            self.client = AsyncIOMotorClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=5000,
            )

            # Verify connection
            await self.client.admin.command("ping")

            # Get database (extracted from URI or default)
            self.db = self.client.get_default_database()
            if self.db is None:
                self.db = self.client["intelligent_data_room"]

            self._connected = True
            print("✅ Connected to MongoDB Atlas")

        except ConnectionFailure as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self) -> None:
        """
        Close MongoDB connection.
        """
        if self.client:
            self.client.close()
            self._connected = False
            print("📤 Disconnected from MongoDB")

    @property
    def files_collection(self):
        """Get the files collection."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db["files"]

    @property
    def messages_collection(self):
        """Get the messages collection."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db["messages"]

    @property
    def sessions_collection(self):
        """Get the sessions collection."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db["sessions"]

    async def create_indexes(self) -> None:
        """
        Create database indexes for optimized queries.
        """
        if self.db is None:
            raise RuntimeError("Database not connected")

        try:
            # Files collection indexes
            await self.files_collection.create_index("file_id", unique=True)
            await self.files_collection.create_index("session_id")

            # Messages collection indexes
            await self.messages_collection.create_index("session_id")
            await self.messages_collection.create_index(
                [("session_id", 1), ("timestamp", -1)]
            )

            # Sessions collection indexes
            await self.sessions_collection.create_index("session_id", unique=True)

            print("✅ Database indexes created")
        except Exception as e:
            print(f"⚠️ Index creation warning: {e}")


# Global database instance
_database: Database | None = None


async def get_database() -> Database:
    """
    Get or create database instance.

    Returns:
        Connected Database instance
    """
    global _database

    if _database is None:
        _database = Database()
        await _database.connect()
        try:
            await _database.create_indexes()
        except Exception as e:
            print(f"⚠️ Index creation skipped: {e}")

    return _database


async def close_database() -> None:
    """
    Close the database connection.
    """
    global _database

    if _database:
        await _database.disconnect()
        _database = None
