from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Room(Base):
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True)
    room_number = Column(String, unique=True)  # A101
    building = Column(String)                  # A1,A2,B1,B2,N1
    floor = Column(Integer)
    room_type = Column(String)                 # Standard,Twin,Suite
    price_night = Column(Float, default=400)
    price_month = Column(Float)
    status = Column(String, default='available')  # available/occupied/maintenance/monthly

class Booking(Base):
    __tablename__ = 'bookings'
    id = Column(Integer, primary_key=True)
    booking_number = Column(String, unique=True)
    room_number = Column(String)
    guest_name = Column(String)
    guest_id_card = Column(String)
    guest_phone = Column(String)
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    payment_method = Column(String)  # cash/transfer/cheque
    total_amount = Column(Float)
    status = Column(String, default='confirmed')  # confirmed/departed/cancelled
    created_at = Column(DateTime, default=datetime.now)

class Guest(Base):
    __tablename__ = 'guests'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    id_card = Column(String, unique=True)
    phone = Column(String)
    visit_count = Column(Integer, default=1)
    last_visit = Column(DateTime)

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    type = Column(String)      # income/expense
    category = Column(String)  # room/electric/water/other
    amount = Column(Float)
    date = Column(DateTime, default=datetime.now)
    booking_id = Column(Integer)
    note = Column(Text)

engine = create_engine('sqlite:///hotel.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
