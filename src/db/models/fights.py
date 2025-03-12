from sqlalchemy import Column, String, Integer, ForeignKey, Numeric, TIMESTAMP, Text
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime

from ..base import Base
from ..session import get_session
from .events import Event

class Fight(Base):
    __tablename__ = 'fights'
    
    fight_id = Column(String, primary_key=True)
    event_id = Column(String, ForeignKey('events.event_id'))
    fight_url = Column(String)
    status = Column(String)
    curr_round = Column(String)
    curr_time = Column(String)
    last_updated = Column(TIMESTAMP)
    referee = Column(String)
    fighter1_id = Column(String, ForeignKey('fighters.fighter_id'))
    fighter2_id = Column(String, ForeignKey('fighters.fighter_id'))
    fighter1_result = Column(String)
    fighter2_result = Column(String)
    final_method = Column(String)
    
    # Relationships
    event = relationship("Event", back_populates="fights")
    fighter1 = relationship("Fighter", foreign_keys=[fighter1_id], back_populates="fighter1_fights")
    fighter2 = relationship("Fighter", foreign_keys=[fighter2_id], back_populates="fighter2_fights")
    fight_stats = relationship("FightStats", back_populates="fight")
    round_stats = relationship("RoundStats", back_populates="fight")
    fight_scores = relationship("FightScore", back_populates="fight")
    round_scores = relationship("RoundScore", back_populates="fight")
    odds_events = relationship("OddsEvent", back_populates="fight")
    live_stats = relationship("LiveStats", back_populates="fight")
    
    @hybrid_property
    def is_finished(self):
        return self.status == 'finished'
    
    @hybrid_property
    def winner_id(self):
        if self.fighter1_result == 'W':
            return self.fighter1_id
        elif self.fighter2_result == 'W':
            return self.fighter2_id
        return None
    
    @classmethod
    def get_by_id(cls, fight_id):
        with get_session() as session:
            return session.query(cls).filter_by(fight_id=fight_id).first()
    
    @classmethod
    def get_by_event(cls, event_id):
        with get_session() as session:
            return session.query(cls).filter_by(event_id=event_id).all()
    
    @classmethod
    def get_recent(cls, limit=10):
        with get_session() as session:
            return session.query(cls).join(cls.event).filter(cls.status == 'finished')\
                .order_by(Event.date.desc()).limit(limit).all()
    
    @classmethod
    def get_upcoming(cls, limit=10):
        with get_session() as session:
            return session.query(cls).join(cls.event).filter(cls.status != 'finished')\
                .order_by(Event.date).limit(limit).all()
    
    def get_fighter_stats(self, fighter_id):
        with get_session() as session:
            return session.query(FightStats).filter_by(fight_id=self.fight_id, fighter_id=fighter_id).first()
    
    def get_round_stats(self, fighter_id=None):
        with get_session() as session:
            query = session.query(RoundStats).filter_by(fight_id=self.fight_id)
            if fighter_id:
                query = query.filter_by(fighter_id=fighter_id)
            return query.order_by(RoundStats.round_number).all()
    
    def __repr__(self):
        return f"<Fight(id='{self.fight_id}', fighter1='{self.fighter1.name if self.fighter1 else None}', fighter2='{self.fighter2.name if self.fighter2 else None}')>"


class FightStats(Base):
    __tablename__ = 'fight_stats'
    
    fight_id = Column(String, ForeignKey('fights.fight_id'), primary_key=True)
    fighter_id = Column(String, ForeignKey('fighters.fighter_id'), primary_key=True)
    
    # Knockdowns
    kd = Column(Integer)
    
    # Significant Strikes
    sig_strikes_landed = Column(Integer)
    sig_strikes_attempted = Column(Integer)
    sig_strikes_accuracy = Column(Numeric)
    
    # Strike breakdowns
    head_strikes_landed = Column(Integer)
    head_strikes_attempted = Column(Integer)
    body_strikes_landed = Column(Integer)
    body_strikes_attempted = Column(Integer)
    leg_strikes_landed = Column(Integer)
    leg_strikes_attempted = Column(Integer)
    
    # Position breakdowns
    distance_strikes_landed = Column(Integer)
    distance_strikes_attempted = Column(Integer)
    clinch_strikes_landed = Column(Integer)
    clinch_strikes_attempted = Column(Integer)
    ground_strikes_landed = Column(Integer)
    ground_strikes_attempted = Column(Integer)
    
    # Total strikes
    total_strikes_landed = Column(Integer)
    total_strikes_attempted = Column(Integer)
    total_strikes_accuracy = Column(Numeric)
    
    # Takedowns
    td_landed = Column(Integer)
    td_attempted = Column(Integer)
    td_accuracy = Column(Numeric)
    
    # Submissions and control
    sub_att = Column(Integer)
    reversals = Column(Integer)
    ctrl = Column(Integer)  # Control time in seconds
    
    # Relationships
    fight = relationship("Fight", back_populates="fight_stats")
    fighter = relationship("Fighter", back_populates="fight_stats")
    
    @hybrid_property
    def control_time_str(self):
        """Format control time as MM:SS"""
        if self.ctrl is not None:
            minutes = self.ctrl // 60
            seconds = self.ctrl % 60
            return f"{minutes}:{seconds:02d}"
        return "0:00"
    
    @classmethod
    def get_fight_stats(cls, fight_id):
        with get_session() as session:
            return session.query(cls).filter_by(fight_id=fight_id).all()
    
    def __repr__(self):
        return f"<FightStats(fight_id='{self.fight_id}', fighter_id='{self.fighter_id}')>"


class RoundStats(Base):
    __tablename__ = 'round_stats'
    
    fight_id = Column(String, ForeignKey('fights.fight_id'), primary_key=True)
    fighter_id = Column(String, ForeignKey('fighters.fighter_id'), primary_key=True)
    round_number = Column(Integer, primary_key=True)
    
    # Knockdowns
    kd = Column(Integer)
    
    # Significant Strikes
    sig_strikes_landed = Column(Integer)
    sig_strikes_attempted = Column(Integer)
    sig_strikes_accuracy = Column(Numeric)
    
    # Strike breakdowns
    head_strikes_landed = Column(Integer)
    head_strikes_attempted = Column(Integer)
    body_strikes_landed = Column(Integer)
    body_strikes_attempted = Column(Integer)
    leg_strikes_landed = Column(Integer)
    leg_strikes_attempted = Column(Integer)
    
    # Position breakdowns
    distance_strikes_landed = Column(Integer)
    distance_strikes_attempted = Column(Integer)
    clinch_strikes_landed = Column(Integer)
    clinch_strikes_attempted = Column(Integer)
    ground_strikes_landed = Column(Integer)
    ground_strikes_attempted = Column(Integer)
    
    # Total strikes
    total_strikes_landed = Column(Integer)
    total_strikes_attempted = Column(Integer)
    
    # Takedowns
    td_landed = Column(Integer)
    td_attempted = Column(Integer)
    td_accuracy = Column(Numeric)
    
    # Submissions and control
    sub_att = Column(Integer)
    reversals = Column(Integer)
    ctrl = Column(Integer)  # Control time in seconds
    
    # Relationships
    fight = relationship("Fight", back_populates="round_stats")
    fighter = relationship("Fighter", back_populates="round_stats")
    
    @hybrid_property
    def control_time_str(self):
        """Format control time as MM:SS"""
        if self.ctrl is not None:
            minutes = self.ctrl // 60
            seconds = self.ctrl % 60
            return f"{minutes}:{seconds:02d}"
        return "0:00"
    
    @classmethod
    def get_round_stats(cls, fight_id, round_number=None):
        with get_session() as session:
            query = session.query(cls).filter_by(fight_id=fight_id)
            if round_number:
                query = query.filter_by(round_number=round_number)
            return query.order_by(cls.round_number, cls.fighter_id).all()
    
    def __repr__(self):
        return f"<RoundStats(fight_id='{self.fight_id}', fighter_id='{self.fighter_id}', round_number={self.round_number})>"


class LiveStats(Base):
    __tablename__ = 'live_stats'
    
    fight_id = Column(String, ForeignKey('fights.fight_id'), primary_key=True)
    fighter_id = Column(String, ForeignKey('fighters.fighter_id'), primary_key=True)
    round_number = Column(Integer, primary_key=True)
    time = Column(Integer, primary_key=True)  # Time in seconds elapsed in the round
    
    pre_fight_odds_espn = Column(Text)
    kd = Column(Integer)
    sig_strikes_landed = Column(Integer)
    sig_strikes_attempted = Column(Integer)
    sig_strikes_accuracy = Column(Numeric)
    head_strikes_landed = Column(Integer)
    head_strikes_attempted = Column(Integer)
    body_strikes_landed = Column(Integer)
    body_strikes_attempted = Column(Integer)
    leg_strikes_landed = Column(Integer)
    leg_strikes_attempted = Column(Integer)
    total_strikes_landed = Column(Integer)
    total_strikes_attempted = Column(Integer)
    total_strikes_accuracy = Column(Numeric)
    td_landed = Column(Integer)
    td_attempted = Column(Integer)
    td_accuracy = Column(Numeric)
    sub_att = Column(Integer)
    reversals = Column(Integer)
    ctrl = Column(Integer)
    
    # Relationships
    fight = relationship("Fight", back_populates="live_stats")
    fighter = relationship("Fighter", back_populates="live_stats")
    
    @hybrid_property
    def time_str(self):
        """Format time as M:SS"""
        if self.time is not None:
            minutes = self.time // 60
            seconds = self.time % 60
            return f"{minutes}:{seconds:02d}"
        return "0:00"
    
    @classmethod
    def get_by_fight(cls, fight_id):
        with get_session() as session:
            return session.query(cls).filter_by(fight_id=fight_id)\
                .order_by(cls.round_number, cls.time).all()
    
    def __repr__(self):
        return f"<LiveStats(fight_id='{self.fight_id}', fighter_id='{self.fighter_id}', round={self.round_number}, time={self.time_str})>"