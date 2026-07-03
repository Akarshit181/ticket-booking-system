# Why Repository Important?
# Repositories provide a way to abstract the data access layer, making the code more maintainable and testable. They encapsulate the logic for accessing and manipulating data, allowing the rest of the application to interact with the data without knowing the underlying implementation details.
# Imagine tomorrow your company says:

# "Move from MongoDB to PostgreSQL."

# Without a repository:

# You edit 20 service files.

# With a repository:

# You only replace the repository implementation.

# The service layer doesn't change.

# Route doesn't know MongoDB.
# Service doesn't know MongoDB.
# Only Repository knows MongoDB.

# This is called Separation of Concerns.

from app.database.mongodb import MongoDB
from app.utils.config import settings

class UserRepository: 
    def __init__(self):
        self.db = MongoDB.get_db()
        self.users = self.db[settings.collection_users]

    def get_by_username(self, username: str):
        return self.users.find_one({"username": username})

    def get_by_email(self, email: str):
        return self.users.find_one({"email": email})

    def create(self, user_document: dict):
        self.users.insert_one(user_document)
