from app.db.session import engine
from app.db.base import Base
from app.models import workspace, user, service, contact, booking, inventory, conversation, communication_log, audit_log, form

print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)
print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("Database reset complete.")
