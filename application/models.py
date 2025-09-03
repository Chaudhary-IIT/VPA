from .database import db

class User(db.Model):
    __tablename__='user'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(),nullable=False)
    email=db.Column(db.String(),unique=True,nullable=False)
    password=db.Column(db.String(),nullable=False)
    address=db.Column(db.String(),nullable=True)
    dob=db.Column(db.String(),nullable=True)
    type=db.Column(db.String(),default='General')
    parking=db.relationship('Reserve_Spot',backref='bearer')

class Parking_Lot(db.Model):
    __tablename__='parking_lot'
    id=db.Column(db.Integer,primary_key=True)
    location_name = db.Column(db.String(), nullable=False)
    price=db.Column(db.Integer,nullable=False)
    address=db.Column(db.String())
    pincode=db.Column(db.Integer,nullable=False)
    max_spots=db.Column(db.Integer,nullable=False)
    #user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    spots=db.relationship('Parking_Spot', backref='main')

class Parking_Spot(db.Model):
    __tablename__='parking_spot'
    id=db.Column(db.Integer, primary_key=True)
    status=db.Column(db.String(), default='A')
    lot_id=db.Column(db.Integer, db.ForeignKey('parking_lot.id'),nullable=False)
    reserved_spot=db.relationship('Reserve_Spot',backref='holder')

class Reserve_Spot(db.Model):
    __tablename__='reserve_spot'
    id=db.Column(db.Integer, primary_key=True)
    parking_timestamp=db.Column(db.Integer, nullable=False)
    leaving_timestamp=db.Column(db.Integer, nullable=True)
    cost=db.Column(db.Integer)
    vehicle_no=db.Column(db.String(),nullable=False)
    spot_id=db.Column(db.Integer, db.ForeignKey('parking_spot.id'),nullable=True)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'),nullable=True)

class Reserved_History(db.Model):
    __tablename__='reserved_history'
    id=db.Column(db.Integer, primary_key=True)
    parking_timestamp=db.Column(db.Integer, nullable=False)
    leaving_timestamp=db.Column(db.Integer, nullable=True)
    cost=db.Column(db.Integer)
    vehicle_no=db.Column(db.String(),nullable=False)
    spot_id=db.Column(db.Integer,nullable=False)
    user_id=db.Column(db.Integer,nullable=False)
    address=db.Column(db.String())
    status=db.Column(db.String(),default='B')