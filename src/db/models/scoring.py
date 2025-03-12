from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

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
    
    def __repr__(self):
        return f"<Judge(id={self.judge_id}, name='{self.name}')>"

class FightScore(Base):
    __tablename__ = 'fight_scores'
    
    fight_id = Column(String, ForeignKey('fights.fight_id'), primary_key=True)
    judge_id = Column(Integer, ForeignKey('judges.judge_id'), primary_key=True)
    event_id = Column(String, ForeignKey('events.event_id'), primary_key=True)
    
    total_fighter1 = Column(Integer)
    fighter1_name = Column(Text)
    total_fighter2 = Column(Integer)
    fighter2_name = Column(Text)
    
    # Relationships
    fight = relationship("Fight", back_populates="fight_scores")
    judge = relationship("Judge", back_populates="fight_scores")
    event = relationship("Event", back_populates="fight_scores")
    
    @hybrid_property
    def score_difference(self):
        """Calculate absolute score difference"""
        if self.total_fighter1 is not None and self.total_fighter2 is not None:
            return abs(self.total_fighter1 - self.total_fighter2)
        return None
    
    @hybrid_property
    def winner(self):
        """Determine which fighter won according to this judge"""
        if self.total_fighter1 > self.total_fighter2:
            return "fighter1"
        elif self.total_fighter2 > self.total_fighter1:
            return "fighter2"
        return "draw"
    
    @classmethod
    def get_by_fight(cls, fight_id):
        with get_session() as session:
            return session.query(cls).filter_by(fight_id=fight_id).all()
    
    @classmethod
    def get_by_judge(cls, judge_id, limit=20):
        with get_session() as session:
            return session.query(cls).filter_by(judge_id=judge_id)\
                .join(cls.event).order_by(cls.event.date.desc()).limit(limit).all()
    
    def get_round_scores(self):
        with get_session() as session:
            return session.query(RoundScore).filter_by(
                fight_id=self.fight_id, 
                judge_id=self.judge_id, 
                event_id=self.event_id
            ).order_by(RoundScore.round_number).all()
    
    def __repr__(self):
        return f"<FightScore(fight_id='{self.fight_id}', judge_id={self.judge_id})>"


class RoundScore(Base):
    __tablename__ = 'round_scores'
    
    fight_id = Column(String, ForeignKey('fights.fight_id'), primary_key=True)
    event_id = Column(String, ForeignKey('events.event_id'), primary_key=True)
    judge_id = Column(Integer, ForeignKey('judges.judge_id'), primary_key=True)
    round_number = Column(Integer, primary_key=True)
    
    fighter1_score = Column(Integer)
    fighter1_name = Column(Text)
    fighter2_score = Column(Integer)
    fighter2_name = Column(Text)
    
    # Relationships
    fight = relationship("Fight", back_populates="round_scores")
    judge = relationship("Judge", back_populates="round_scores")
    event = relationship("Event", back_populates="round_scores")
    
    @hybrid_property
    def score_difference(self):
        """Calculate absolute score difference"""
        if self.fighter1_score is not None and self.fighter2_score is not None:
            return abs(self.fighter1_score - self.fighter2_score)
        return None
    
    @hybrid_property
    def winner(self):
        """Determine which fighter won the round according to this judge"""
        if self.fighter1_score > self.fighter2_score:
            return "fighter1"
        elif self.fighter2_score > self.fighter1_score:
            return "fighter2"
        return "draw"
    
    @classmethod
    def get_by_fight(cls, fight_id):
        with get_session() as session:
            return session.query(cls).filter_by(fight_id=fight_id)\
                .order_by(cls.judge_id, cls.round_number).all()
    
    @classmethod
    def get_by_fight_and_round(cls, fight_id, round_number):
        with get_session() as session:
            return session.query(cls).filter_by(
                fight_id=fight_id, 
                round_number=round_number
            ).order_by(cls.judge_id).all()
    
    def __repr__(self):
        return f"<RoundScore(fight_id='{self.fight_id}', judge_id={self.judge_id}, round={self.round_number})>"