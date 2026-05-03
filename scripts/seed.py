from app.auth.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models.rbac import Role, UserRole
from app.models.user import User
from app.services.rbac_service import RBACService


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        RBACService(db).seed_defaults()
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            admin = User(
                email="admin@example.com",
                full_name="System Admin",
                hashed_password=hash_password("Admin@12345"),
            )
            db.add(admin)
            db.flush()
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        if admin_role:
            exists = db.query(UserRole).filter(UserRole.user_id == admin.id, UserRole.role_id == admin_role.id).first()
            if not exists:
                db.add(UserRole(user_id=admin.id, role_id=admin_role.id))
        db.commit()
        print("Seed complete: admin@example.com / Admin@12345")
    finally:
        db.close()


if __name__ == "__main__":
    main()
