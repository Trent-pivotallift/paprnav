from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.core import Aircraft, AircraftAssignment, LogbookSection, Organization, OrganizationMembership, User


TEST_PASSWORD = "test-password"


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as session:
        yield session

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def client(db_session: Session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("PAPRNAV_LOCAL_STORAGE_PATH", str(tmp_path / "uploads"))
    monkeypatch.setenv("PAPRNAV_MAX_UPLOAD_SIZE_BYTES", "1048576")
    get_settings.cache_clear()

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    get_settings.cache_clear()


def create_user(db: Session, email: str, name: str) -> User:
    user = User(email=email, name=name, password_hash=hash_password(TEST_PASSWORD), status="active")
    db.add(user)
    db.flush()
    return user


def create_organization(db: Session, name: str, org_type: str) -> Organization:
    organization = Organization(name=name, type=org_type)
    db.add(organization)
    db.flush()
    return organization


def add_membership(db: Session, organization: Organization, user: User, role: str) -> OrganizationMembership:
    membership = OrganizationMembership(organization_id=organization.id, user_id=user.id, role=role, status="active")
    db.add(membership)
    db.flush()
    return membership


def create_aircraft(db: Session, owner: Organization, created_by: User, n_number: str = "N123AB") -> Aircraft:
    normalized = n_number.upper().replace("-", "").replace(" ", "")
    aircraft = Aircraft(
        owner_organization_id=owner.id,
        n_number_raw=n_number,
        n_number_normalized=normalized,
        make="Cessna",
        model="172R",
        serial_number="17280001",
        year=2003,
        status="active",
        created_by_user_id=created_by.id,
        airframe_serial_number="17280001",
        engine_make="Lycoming",
        engine_model="IO-360-L2A",
        engine_serial_number="L-12345-51A",
        propeller_make="McCauley",
        propeller_model="1A170",
        propeller_serial_number="P-54321",
    )
    db.add(aircraft)
    db.flush()
    return aircraft


def assign_aircraft(db: Session, aircraft: Aircraft, organization: Organization, assigned_by: User) -> AircraftAssignment:
    assignment = AircraftAssignment(
        aircraft_id=aircraft.id,
        organization_id=organization.id,
        assigned_by_user_id=assigned_by.id,
        role="maintainer",
        status="active",
    )
    db.add(assignment)
    db.flush()
    return assignment


def seed_logbook_sections(db: Session) -> None:
    db.add_all(
        [
            LogbookSection(key="airframe", name="Airframe", sort_order=1),
            LogbookSection(key="engine", name="Engine", sort_order=2),
            LogbookSection(key="propeller", name="Propeller", sort_order=3),
        ]
    )
    db.flush()


@pytest.fixture()
def demo_data(db_session: Session) -> dict[str, object]:
    owner_user = create_user(db_session, "owner.test@paprnav.local", "Olivia Owner")
    shop_user = create_user(db_session, "shop.test@paprnav.local", "Miles Mechanic")
    stranger_user = create_user(db_session, "stranger.test@paprnav.local", "Una Stranger")

    owner_org = create_organization(db_session, "Owner Hangar", "owner")
    shop_org = create_organization(db_session, "Maintenance Shop", "maintenance_shop")
    stranger_org = create_organization(db_session, "Other Hangar", "owner")

    add_membership(db_session, owner_org, owner_user, "owner_admin")
    add_membership(db_session, shop_org, shop_user, "maintenance_admin")
    add_membership(db_session, stranger_org, stranger_user, "owner_admin")
    seed_logbook_sections(db_session)

    aircraft = create_aircraft(db_session, owner_org, owner_user)
    assign_aircraft(db_session, aircraft, shop_org, owner_user)
    db_session.commit()

    return {
        "aircraft": aircraft,
        "owner_user": owner_user,
        "shop_user": shop_user,
        "stranger_user": stranger_user,
    }


def login(client: TestClient, email: str) -> TestClient:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": TEST_PASSWORD})
    assert response.status_code == 200
    return client
