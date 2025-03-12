from sqlalchemy.exc import SQLAlchemyError
from ..models.fighters import Fighter
from ..session import get_session

class FighterRepository:
    """Repository for Fighter entity operations"""
    
    @classmethod
    def get_by_id(cls, fighter_id):
        """Get fighter by ID"""
        return Fighter.get_by_id(fighter_id)
    
    @classmethod
    def get_by_name(cls, name):
        """Get fighters by name (partial match)"""
        return Fighter.get_by_name(name)
    
    @classmethod
    def get_all(cls, limit=100, offset=0):
        """Get all fighters with pagination"""
        with get_session() as session:
            return session.query(Fighter).order_by(Fighter.name).limit(limit).offset(offset).all()
    
    @classmethod
    def create(cls, data):
        """Create a new fighter"""
        try:
            with get_session() as session:
                fighter = Fighter(**data)
                session.add(fighter)
                session.commit()
                return fighter
        except SQLAlchemyError as e:
            # Log the error
            print(f"Error creating fighter: {str(e)}")
            return None
    
    @classmethod
    def update(cls, fighter_id, data):
        """Update an existing fighter"""
        try:
            with get_session() as session:
                fighter = session.query(Fighter).filter_by(fighter_id=fighter_id).first()
                if not fighter:
                    return None
                
                for key, value in data.items():
                    if hasattr(fighter, key):
                        setattr(fighter, key, value)
                
                session.commit()
                return fighter
        except SQLAlchemyError as e:
            # Log the error
            print(f"Error updating fighter: {str(e)}")
            return None
    
    @classmethod
    def delete(cls, fighter_id):
        """Delete a fighter"""
        try:
            with get_session() as session:
                fighter = session.query(Fighter).filter_by(fighter_id=fighter_id).first()
                if fighter:
                    session.delete(fighter)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            # Log the error
            print(f"Error deleting fighter: {str(e)}")
            return False