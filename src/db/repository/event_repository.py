from sqlalchemy.exc import SQLAlchemyError
from ..models.events import Event
from ..session import get_session
from datetime import datetime

class EventRepository:
    """Repository for Event entity operations"""
    
    @classmethod
    def get_by_id(cls, event_id):
        """Get event by ID"""
        return Event.get_by_id(event_id)
    
    @classmethod
    def get_by_name(cls, name):
        """Get events by name (partial match)"""
        return Event.search_by_name(name)
    
    @classmethod
    def get_all(cls, limit=100, offset=0):
        """Get all events with pagination"""
        with get_session() as session:
            return session.query(Event).order_by(Event.date.desc()).limit(limit).offset(offset).all()
    
    @classmethod
    def get_recent(cls, limit=5):
        """Get recent events"""
        return Event.get_recent(limit)
    
    @classmethod
    def get_upcoming(cls, limit=5):
        """Get upcoming events"""
        return Event.get_upcoming(limit)
    
    @classmethod
    def get_by_date_range(cls, start_date, end_date):
        """Get events within a date range"""
        return Event.get_by_date_range(start_date, end_date)
    
    @classmethod
    def create(cls, data):
        """Create a new event"""
        try:
            with get_session() as session:
                event = Event(**data)
                session.add(event)
                session.commit()
                return event
        except SQLAlchemyError as e:
            print(f"Error creating event: {str(e)}")
            return None
    
    @classmethod
    def update(cls, event_id, data):
        """Update an existing event"""
        try:
            with get_session() as session:
                event = session.query(Event).filter_by(event_id=event_id).first()
                if not event:
                    return None
                
                for key, value in data.items():
                    if hasattr(event, key):
                        setattr(event, key, value)
                
                session.commit()
                return event
        except SQLAlchemyError as e:
            print(f"Error updating event: {str(e)}")
            return None
    
    @classmethod
    def delete(cls, event_id):
        """Delete an event"""
        try:
            with get_session() as session:
                event = session.query(Event).filter_by(event_id=event_id).first()
                if event:
                    session.delete(event)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            print(f"Error deleting event: {str(e)}")
            return False