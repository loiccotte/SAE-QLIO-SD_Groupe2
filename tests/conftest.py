"""Fixtures de test pour T'ELEFAN MES 4.0."""

import pytest
from app import create_app, db as _db


@pytest.fixture(scope='session')
def app():
    """Cree une app Flask de test avec SQLite en memoire."""
    import os
    os.environ['DATABASE_URL'] = 'sqlite://'
    os.environ['SECRET_KEY'] = 'test-secret-key'

    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        _db.create_all()
        _seed_test_data(_db)

    yield app

    with app.app_context():
        _db.drop_all()


@pytest.fixture
def client(app):
    """Client HTTP de test."""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Client connecte en tant qu'admin."""
    client.post('/login', data={
        'identifiant': 'admin',
        'mot_de_passe': 'admin123'
    })
    return client


@pytest.fixture
def employe_client(client):
    """Client connecte en tant qu'employe."""
    client.post('/login', data={
        'identifiant': 'operateur',
        'mot_de_passe': 'oper123'
    })
    return client


def _seed_test_data(db):
    """Injecte des donnees minimales de test."""
    from datetime import datetime, timedelta
    from app.models import (
        Order, OrderPosition, Step, MachineReport,
        ResourceOperation, Resource, PartsReport,
        Buffer, BufferPosition
    )

    # Machines
    for i in range(1, 9):
        db.session.add(Resource(
            ResourceID=i,
            ResourceName=f'Machine_{i}',
            Description=f'Machine de test {i}'
        ))

    # Ordres de fabrication
    now = datetime(2025, 3, 15, 10, 0, 0)
    for i in range(1, 6):
        start = now + timedelta(hours=i)
        end = start + timedelta(hours=2)
        db.session.add(Order(
            ONo=i, Start=start, End=end,
            PlannedStart=start, PlannedEnd=end,
            CNo=1, State=3, Enabled=True
        ))
        db.session.add(OrderPosition(
            ONo=i, OPos=1, Start=start, End=end,
            WPNo=1, StepNo=1, State=3, ResourceID=1,
            OpNo=100, PNo=1, Error=(1 if i == 5 else 0), OrderPNo=1
        ))

    # Etapes de production
    for i in range(1, 11):
        start = now + timedelta(minutes=i * 10)
        end = start + timedelta(seconds=30)
        db.session.add(Step(
            StepNo=i, ONo=1, OPos=1, WPNo=1, OpNo=100,
            Start=start, End=end, ResourceID=1,
            ElectricEnergyCalc=100, ElectricEnergyReal=0,
            CompressedAirCalc=50, CompressedAirReal=0,
            ErrorStep=False, Active=False
        ))

    # Etapes buffer (OpNo 210-215)
    for i in range(11, 16):
        start = now + timedelta(minutes=i * 10)
        end = start + timedelta(seconds=120)
        db.session.add(Step(
            StepNo=i, ONo=1, OPos=1, WPNo=1, OpNo=212,
            Start=start, End=end, ResourceID=1,
            ElectricEnergyCalc=0, ElectricEnergyReal=0,
            CompressedAirCalc=0, CompressedAirReal=0,
            ErrorStep=False, Active=False
        ))

    # Machine reports
    for i in range(20):
        ts = now + timedelta(minutes=i * 5)
        db.session.add(MachineReport(
            ResourceID=1, TimeStamp=ts, ID=i + 1,
            AutomaticMode=True, ManualMode=False,
            Busy=(i % 3 != 0), Reset=False,
            ErrorL0=(1 if i == 10 else 0),
            ErrorL1=False, ErrorL2=False
        ))

    # ResourceOperation (temps nominaux)
    db.session.add(ResourceOperation(
        ResourceID=1, OpNo=100,
        WorkingTime=25, OffsetTime=5,
        ElectricEnergy=500, CompressedAir=200
    ))

    # PartsReport
    for i in range(10):
        db.session.add(PartsReport(
            ResourceID=1,
            TimeStamp=now + timedelta(minutes=i * 15),
            ID=i + 1, PNo=1,
            ErrorID=(1 if i == 9 else 0)
        ))

    # Buffers
    db.session.add(Buffer(
        ResourceId=9, BufNo=1, Description='Buffer Entree',
        Type=1, Sides=1, Rows=2, Columns=4
    ))
    db.session.add(Buffer(
        ResourceId=10, BufNo=1, Description='Buffer Sortie',
        Type=1, Sides=1, Rows=2, Columns=4
    ))

    # Buffer positions
    for i in range(1, 5):
        db.session.add(BufferPosition(
            ResourceId=9, BufNo=1, BufPos=i,
            PNo=(1 if i <= 3 else 0), Quantity=i,
            TimeStamp=now, ONo=1, OPos=1
        ))
    for i in range(1, 5):
        db.session.add(BufferPosition(
            ResourceId=10, BufNo=1, BufPos=i,
            PNo=(1 if i <= 2 else 0), Quantity=i,
            TimeStamp=now, ONo=1, OPos=1
        ))

    db.session.commit()
