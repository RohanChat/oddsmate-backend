from sqlalchemy.exc import SQLAlchemyError
from ..models.judges import Judge
from ..session import get_session

class JudgeRepository:
    """Repository for Judge entity operations"""
    
    @classmethod
    def get_by_id(cls, judge_id):
        """Get judge by ID"""
        return Judge.get_by_id(judge_id)
    
    @classmethod
    def get_by_name(cls, name):
        """Get judges by name (partial match)"""
        return Judge.get_by_name(name)
    
    @classmethod
    def get_all(cls):
        """Get all judges"""
        return Judge.get_all()
    
    @classmethod
    def create(cls, data):
        """Create a new judge"""
        try:
            with get_session() as session:
                judge = Judge(**data)
                session.add(judge)
                session.commit()
                return judge
        except SQLAlchemyError as e:
            print(f"Error creating judge: {str(e)}")
            return None
    
    @classmethod
    def update(cls, judge_id, data):
        """Update an existing judge"""
        try:
            with get_session() as session:
                judge = session.query(Judge).filter_by(judge_id=judge_id).first()
                if not judge:
                    return None
                
                for key, value in data.items():
                    if hasattr(judge, key):
                        setattr(judge, key, value)
                
                session.commit()
                return judge
        except SQLAlchemyError as e:
            print(f"Error updating judge: {str(e)}")
            return None
    
    @classmethod
    def delete(cls, judge_id):
        """Delete a judge"""
        try:
            with get_session() as session:
                judge = session.query(Judge).filter_by(judge_id=judge_id).first()
                if judge:
                    session.delete(judge)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            print(f"Error deleting judge: {str(e)}")
            return False
    
    @classmethod
    def get_judge_scoring_history(cls, judge_id, limit=20):
        """Get scoring history for a judge"""
        from ..models.scoring import FightScore
        with get_session() as session:
            return session.query(FightScore).filter_by(judge_id=judge_id).limit(limit).all()