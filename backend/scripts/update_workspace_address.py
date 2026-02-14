from app.db.session import SessionLocal
from app.models.workspace import Workspace

def update_address():
    db = SessionLocal()
    try:
        workspace = db.query(Workspace).filter(Workspace.slug == "demo-spa").first()
        if workspace:
            workspace.address = "123 Wellness Way, Mumbai, Maharashtra 400001, India"
            db.commit()
            print(f"Updated address for {workspace.name} to: {workspace.address}")
        else:
            print("Workspace 'demo-spa' not found.")
    finally:
        db.close()

if __name__ == "__main__":
    update_address()
