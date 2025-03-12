from sqlalchemy.exc import SQLAlchemyError
from ..models.fights import Fight
from ..session import get_session

class FightRepository:
    """Repository for Fight entity operations"""
    
    @classmethod
    def get_by_id(cls, fight_id):
        """Get fight by ID"""
        return Fight.get_by_id(fight_id)
    
    @classmethod
    def get_by_event(cls, event_id):
        """Get all fights for an event"""
        return Fight.get_by_event(event_id)
    
    @classmethod
    def get_all(cls, limit=100, offset=0):
        """Get all fights with pagination"""
        with get_session() as session:
            return session.query(Fight).limit(limit).offset(offset).all()
    
    @classmethod
    def get_recent(cls, limit=10):
        """Get recent fights"""
        return Fight.get_recent(limit)
    
    @classmethod
    def get_upcoming(cls, limit=10):
        """Get upcoming fights"""
        return Fight.get_upcoming(limit)
    
    @classmethod
    def get_by_fighter(cls, fighter_id):
        """Get all fights for a fighter"""
        with get_session() as session:
            return session.query(Fight).filter(
                (Fight.fighter1_id == fighter_id) | (Fight.fighter2_id == fighter_id)
            ).all()
    
    @classmethod
    def create(cls, data):
        """Create a new fight"""
        try:
            with get_session() as session:
                fight = Fight(**data)
                session.add(fight)
                session.commit()
                return fight
        except SQLAlchemyError as e:
            print(f"Error creating fight: {str(e)}")
            return None
    
    @classmethod
    def update(cls, fight_id, data):
        """Update an existing fight"""
        try:
            with get_session() as session:
                fight = session.query(Fight).filter_by(fight_id=fight_id).first()
                if not fight:
                    return None
                
                for key, value in data.items():
                    if hasattr(fight, key):
                        setattr(fight, key, value)
                
                session.commit()
                return fight
        except SQLAlchemyError as e:
            print(f"Error updating fight: {str(e)}")
            return None
    
    @classmethod
    def delete(cls, fight_id):
        """Delete a fight"""
        try:
            with get_session() as session:
                fight = session.query(Fight).filter_by(fight_id=fight_id).first()
                if fight:
                    session.delete(fight)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            print(f"Error deleting fight: {str(e)}")
            return False