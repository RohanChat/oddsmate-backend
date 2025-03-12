from sqlalchemy import Column, String, Date, Integer, Numeric, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime

from ..base import Base
from ..session import get_session
from .fights import Fight

class Fighter(Base):
    __tablename__ = 'fighters'
    
    fighter_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    nickname = Column(String)
    dob = Column(Date)
    height = Column(Integer)  # Height in inches
    weight = Column(Integer)  # Weight in pounds
    reach = Column(Integer)   # Reach in inches
    stance = Column(String)
    
    # Relationships
    stats = relationship("FighterStats", back_populates="fighter")
    fighter1_fights = relationship("Fight", foreign_keys="Fight.fighter1_id", back_populates="fighter1")
    fighter2_fights = relationship("Fight", foreign_keys="Fight.fighter2_id", back_populates="fighter2")
    fight_stats = relationship("FightStats", back_populates="fighter")
    round_stats = relationship("RoundStats", back_populates="fighter")
    live_stats = relationship("LiveStats", back_populates="fighter")
    
    @hybrid_property
    def age(self):
        if self.dob:
            today = datetime.now().date()
            return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        return None
    
    @property
    def all_fights(self):
        return self.fighter1_fights + self.fighter2_fights
    
    @classmethod
    def get_by_id(cls, fighter_id):
        with get_session() as session:
            return session.query(cls).filter_by(fighter_id=fighter_id).first()
    
    @classmethod
    def get_by_name(cls, name):
        with get_session() as session:
            return session.query(cls).filter(cls.name.ilike(f"%{name}%")).all()
    
    @classmethod
    def get_by_stance(cls, stance):
        with get_session() as session:
            return session.query(cls).filter(cls.stance.ilike(stance)).all()
    
    def get_latest_stats(self):
        with get_session() as session:
            return session.query(FighterStats).filter_by(fighter_id=self.fighter_id)\
                .order_by(FighterStats.timestamp.desc()).first()
    
    def get_win_loss_record(self):
        wins, losses, draws = 0, 0, 0
        
        with get_session() as session:
            # Count wins as fighter1
            f1_wins = session.query(Fight).filter_by(fighter1_id=self.fighter_id, fighter1_result='W').count()
            # Count wins as fighter2
            f2_wins = session.query(Fight).filter_by(fighter2_id=self.fighter_id, fighter2_result='W').count()
            # Count losses as fighter1
            f1_losses = session.query(Fight).filter_by(fighter1_id=self.fighter_id, fighter1_result='L').count()
            # Count losses as fighter2
            f2_losses = session.query(Fight).filter_by(fighter2_id=self.fighter_id, fighter2_result='L').count()
            # Count draws
            f1_draws = session.query(Fight).filter_by(fighter1_id=self.fighter_id).filter(
                Fight.fighter1_result.not_in(['W', 'L'])).count()
            f2_draws = session.query(Fight).filter_by(fighter2_id=self.fighter_id).filter(
                Fight.fighter2_result.not_in(['W', 'L'])).count()
            
        wins = f1_wins + f2_wins
        losses = f1_losses + f2_losses
        draws = f1_draws + f2_draws
        
        return {"wins": wins, "losses": losses, "draws": draws}
    
    def __repr__(self):
        return f"<Fighter(id={self.fighter_id}, name='{self.name}')>"


class FighterStats(Base):
    __tablename__ = 'fighter_stats'
    
    fighter_id = Column(String, ForeignKey('fighters.fighter_id'), primary_key=True)
    timestamp = Column(TIMESTAMP, primary_key=True)
    
    # Basic record stats
    wins = Column(Integer)
    losses = Column(Integer)
    draws = Column(Integer)
    win_streak = Column(Integer)
    prev_fights = Column(Integer)
    
    # A lot of statistical columns - partial listing for brevity
    knockdowns_avg = Column(Numeric)
    knockdowns_diff = Column(Numeric)
    sub_attempts_avg = Column(Numeric)
    sub_attempts_diff = Column(Numeric)
    
    # Many more stats...
    
    # Relationships
    fighter = relationship("Fighter", back_populates="stats")
    
    @classmethod
    def get_fighter_stats(cls, fighter_id, latest=True):
        with get_session() as session:
            query = session.query(cls).filter_by(fighter_id=fighter_id)
            if latest:
                return query.order_by(cls.timestamp.desc()).first()
            return query.order_by(cls.timestamp).all()