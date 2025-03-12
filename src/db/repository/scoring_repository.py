from sqlalchemy.exc import SQLAlchemyError
from ..models.scoring import RoundScore
from ..session import get_session
from ..models.scoring import FightScore


class RoundScoreRepository:
    """Repository for RoundScore entity operations"""
    
    @classmethod
    def get_by_primary_key(cls, fight_id, judge_id, event_id, round_number):
        """Get round score by primary key"""
        with get_session() as session:
            return session.query(RoundScore).filter_by(
                fight_id=fight_id,
                judge_id=judge_id,
                event_id=event_id,
                round_number=round_number
            ).first()
    
    @classmethod
    def get_by_fight(cls, fight_id):
        """Get all round scores for a fight"""
        with get_session() as session:
            return session.query(RoundScore).filter_by(fight_id=fight_id).all()
    
    @classmethod
    def get_by_fight_and_judge(cls, fight_id, judge_id):
        """Get all round scores for a fight by a judge"""
        with get_session() as session:
            return session.query(RoundScore).filter_by(
                fight_id=fight_id,
                judge_id=judge_id
            ).order_by(RoundScore.round_number).all()
    
    @classmethod
    def get_by_event(cls, event_id):
        """Get all round scores for an event"""
        with get_session() as session:
            return session.query(RoundScore).filter_by(event_id=event_id).all()
    
    @classmethod
    def create(cls, data):
        """Create a new round score"""
        try:
            with get_session() as session:
                round_score = RoundScore(**data)
                session.add(round_score)
                session.commit()
                return round_score
        except SQLAlchemyError as e:
            print(f"Error creating round score: {str(e)}")
            return None
    
    @classmethod
    def update(cls, fight_id, judge_id, event_id, round_number, data):
        """Update an existing round score"""
        try:
            with get_session() as session:
                round_score = session.query(RoundScore).filter_by(
                    fight_id=fight_id,
                    judge_id=judge_id,
                    event_id=event_id,
                    round_number=round_number
                ).first()
                if not round_score:
                    return None
                
                for key, value in data.items():
                    if hasattr(round_score, key):
                        setattr(round_score, key, value)
                
                session.commit()
                return round_score
        except SQLAlchemyError as e:
            print(f"Error updating round score: {str(e)}")
            return None
    
    @classmethod
    def delete(cls, fight_id, judge_id, event_id, round_number):
        """Delete a round score"""
        try:
            with get_session() as session:
                round_score = session.query(RoundScore).filter_by(
                    fight_id=fight_id,
                    judge_id=judge_id,
                    event_id=event_id,
                    round_number=round_number
                ).first()
                if round_score:
                    session.delete(round_score)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            print(f"Error deleting round score: {str(e)}")
            return False

class FightScoreRepository:
    """Repository for FightScore entity operations"""
    
    @classmethod
    def get_by_fight_and_judge(cls, fight_id, judge_id):
        """Get fight score by fight ID and judge ID"""
        with get_session() as session:
            return session.query(FightScore).filter_by(
                fight_id=fight_id,
                judge_id=judge_id
            ).first()
    
    @classmethod
    def get_by_fight(cls, fight_id):
        """Get all scores for a fight"""
        with get_session() as session:
            return session.query(FightScore).filter_by(fight_id=fight_id).all()
    
    @classmethod
    def get_by_judge(cls, judge_id, limit=20):
        """Get scores by a judge with pagination"""
        return FightScore.get_by_judge(judge_id, limit)
    
    @classmethod
    def get_by_event(cls, event_id):
        """Get all scores for an event"""
        with get_session() as session:
            return session.query(FightScore).filter_by(event_id=event_id).all()
    
    @classmethod
    def create(cls, data):
        """Create a new fight score"""
        try:
            with get_session() as session:
                fight_score = FightScore(**data)
                session.add(fight_score)
                session.commit()
                return fight_score
        except SQLAlchemyError as e:
            print(f"Error creating fight score: {str(e)}")
            return None
    
    @classmethod
    def update(cls, fight_id, judge_id, data):
        """Update an existing fight score"""
        try:
            with get_session() as session:
                fight_score = session.query(FightScore).filter_by(
                    fight_id=fight_id,
                    judge_id=judge_id
                ).first()
                if not fight_score:
                    return None
                
                for key, value in data.items():
                    if hasattr(fight_score, key):
                        setattr(fight_score, key, value)
                
                session.commit()
                return fight_score
        except SQLAlchemyError as e:
            print(f"Error updating fight score: {str(e)}")
            return None
    
    @classmethod
    def delete(cls, fight_id, judge_id):
        """Delete a fight score"""
        try:
            with get_session() as session:
                fight_score = session.query(FightScore).filter_by(
                    fight_id=fight_id,
                    judge_id=judge_id
                ).first()
                if fight_score:
                    session.delete(fight_score)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            print(f"Error deleting fight score: {str(e)}")
            return False