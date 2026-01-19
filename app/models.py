from . import db

class Order(db.Model):
    __tablename__ = 'tblfinorder'
    ONo = db.Column(db.Integer, primary_key=True)
    Start = db.Column(db.DateTime)
    End = db.Column(db.DateTime)

class Step(db.Model):
    __tablename__ = 'tblfinstep'
    Id = db.Column(db.Integer, primary_key=True)
    Start = db.Column(db.DateTime)
    End = db.Column(db.DateTime)
    ElectricEnergyReal = db.Column(db.Float)