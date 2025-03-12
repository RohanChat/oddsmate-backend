from sqlalchemy.exc import SQLAlchemyError
from ..models.fights import FightStats
from ..session import get_session

class FightStatsRepository:
    """Repository for FightStats entity operations"""
    
    @classmethod
    def get_by_fight_and_fighter(cls, fight_id, fighter_id):
        """Get fight stats by fight ID and fighter ID"""
        with get_session() as session:
            return session.query(FightStats).filter_by(
                fight_id=fight_id,
                fighter_id=fighter_id
            ).first()
    
    @classmethod
    def get_by_fight(cls, fight_id):
        """Get all stats for a fight"""
        with get_session() as session:
            return session.query(FightStats).filter_by(fight_id=fight_id).all()
    
    @classmethod
    def get_by_fighter(cls, fighter_id, limit=20):
        """Get stats for a fighter with pagination"""
        with get_session() as session:
            return session.query(FightStats).filter_by(fighter_id=fighter_id).limit(limit).all()
    
    @classmethod
    def create(cls, data):
        """Create new fight stats"""
        try:
            with get_session() as session:
                fight_stats = FightStats(**data)
                session.add(fight_stats)
                session.commit()
                return fight_stats
        except SQLAlchemyError as e:
            print(f"Error creating fight stats: {str(e)}")
            return None
    
    @classmethod
    def update(cls, fight_id, fighter_id, data):
        """Update existing fight stats"""
        try:
            with get_session() as session:
                fight_stats = session.query(FightStats).filter_by(
                    fight_id=fight_id,
                    fighter_id=fighter_id
                ).first()
                if not fight_stats:
                    return None
                
                for key, value in data.items():
                    if hasattr(fight_stats, key):
                        setattr(fight_stats, key, value)
                
                session.commit()
                return fight_stats
        except SQLAlchemyError as e:
            print(f"Error updating fight stats: {str(e)}")
            return None
    
    @classmethod
    def delete(cls, fight_id, fighter_id):
        """Delete fight stats"""
        try:
            with get_session() as session:
                fight_stats = session.query(FightStats).filter_by(
                    fight_id=fight_id,
                    fighter_id=fighter_id
                ).first()
                if fight_stats:
                    session.delete(fight_stats)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            print(f"Error deleting fight stats: {str(e)}")
            return False