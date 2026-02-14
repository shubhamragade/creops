from app.db.base_class import Base

# Import models so Alembic can find them
from app.models.workspace import Workspace  # noqa
from app.models.user import User  # noqa
from app.models.service import Service  # noqa
from app.models.contact import Contact  # noqa
from app.models.booking import Booking  # noqa
from app.models.conversation import Conversation, Message  # noqa
from app.models.form import Form, FormSubmission  # noqa
from app.models.inventory import InventoryItem  # noqa
from app.models.communication_log import CommunicationLog  # noqa
from app.models.audit_log import AuditLog  # noqa
from app.models.email_integration import EmailIntegration # noqa

