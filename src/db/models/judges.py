from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.models.scoring import FightScore

from ..base import Base
from ..session import get_session

class Judge(Base):
    __tablename__ = 'judges'
    
    judge_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    
    # Relationships
    fight_scores = relationship("FightScore", back_populates="judge")
    round_scores = relationship("RoundScore", back_populates="judge")
    
    @classmethod
    def get_by_id(cls, judge_id):
        with get_session() as session:
            return session.query(cls).filter_by(judge_id=judge_id).first()
    
    @classmethod
    def get_by_name(cls, name):
        with get_session() as session:
            return session.query(cls).filter(cls.name.ilike(f"%{name}%")).all()
    
    @classmethod
    def get_all(cls):
        with get_session() as session:
            return session.query(cls).order_by(cls.name).all()
    
    def get_fight_count(self):
        with get_session() as session:
            return session.query(func.count(FightScore.fight_id))\
                .filter(FightScore.judge_id == self.judge_id).scalar()
    
    def __repr__(self):
        return f"<Judge(id={self.judge_id}, name='{self.name}')>"