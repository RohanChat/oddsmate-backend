from sqlalchemy import Column, String, Date, Numeric, func, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import cast
from sqlalchemy.ext.hybrid import hybrid_property
from geoalchemy2 import Geometry
from datetime import datetime

from ..base import Base
from ..session import get_session

class Event(Base):
    __tablename__ = 'events'
    
    event_id = Column(String, primary_key=True)
    date = Column(Date, nullable=False)
    name = Column(String, nullable=False)
    location_name = Column(String)
    location = Column(Geometry('POINT'))
    elevation = Column(Numeric)
    event_url = Column(String)
    
    # Relationships
    fights = relationship("Fight", back_populates="event")
    fight_scores = relationship("FightScore", back_populates="event")
    round_scores = relationship("RoundScore", back_populates="event")
    odds_events = relationship("OddsEvent", back_populates="event")
    
    @hybrid_property
    def latitude(self):
        if self.location:
            return float(self.location.y)
        return None
        
    @hybrid_property
    def longitude(self):
        if self.location:
            return float(self.location.x)
        return None
    
    # Class methods for common queries
    @classmethod
    def get_by_id(cls, event_id):
        with get_session() as session:
            return session.query(cls).filter_by(event_id=event_id).first()
    
    @classmethod
    def get_all(cls):
        with get_session() as session:
            return session.query(cls).order_by(cls.date.desc()).all()
    
    @classmethod
    def get_recent(cls, limit=5):
        with get_session() as session:
            return session.query(cls).filter(cls.date <= datetime.now().date()).order_by(cls.date.desc()).limit(limit).all()
        
    @classmethod
    def get_by_date_range(cls, start_date, end_date):
        with get_session() as session:
            return session.query(cls).filter(cls.date.between(start_date, end_date))\
                .order_by(cls.date).all()
        
    @classmethod
    def search_by_name(cls, search_term):
        with get_session() as session:
            return session.query(cls).filter(cls.name.ilike(f"%{search_term}%"))\
                .order_by(cls.date.desc()).all()

    @classmethod
    def get_upcoming(cls, limit=5):
        with get_session() as session:
            return session.query(cls).filter(cls.date >= datetime.now().date()).order_by(cls.date).limit(limit).all()
        
    def get_fights(self):
        from .fights import Fight
        with get_session() as session:
            return session.query(Fight).filter_by(event_id=self.event_id).all()

    def __repr__(self):
        return f"<Event(id={self.event_id}, name='{self.name}', date='{self.date}')>"