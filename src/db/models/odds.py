from sqlalchemy import Column, String, Integer, ForeignKey, Numeric, TIMESTAMP, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from ..base import Base
from ..session import get_session

class OddsEvent(Base):
    __tablename__ = 'odds_events'
    
    odds_event_id = Column(String, primary_key=True)
    event_id = Column(String, ForeignKey('events.event_id'))
    fight_id = Column(String, ForeignKey('fights.fight_id'))
    odds_timestamp = Column(TIMESTAMP)
    sport_key = Column(Text)
    sport_title = Column(Text)
    commence_time = Column(TIMESTAMP)
    home_team = Column(Text)
    away_team = Column(Text)
    
    # Relationships
    event = relationship("Event", back_populates="odds_events")
    fight = relationship("Fight", back_populates="odds_events")
    
    @classmethod
    def get_by_id(cls, odds_event_id):
        with get_session() as session:
            return session.query(cls).filter_by(odds_event_id=odds_event_id).first()
    
    @classmethod
    def get_by_event(cls, event_id):
        with get_session() as session:
            return session.query(cls).filter_by(event_id=event_id).all()
    
    @classmethod
    def get_by_fight(cls, fight_id):
        with get_session() as session:
            return session.query(cls).filter_by(fight_id=fight_id).all()
    
    @classmethod
    def get_recent(cls, limit=20):
        with get_session() as session:
            now = datetime.now()
            return session.query(cls).filter(cls.commence_time <= now)\
                .order_by(cls.commence_time.desc()).limit(limit).all()
    
    @classmethod
    def get_upcoming(cls, limit=20):
        with get_session() as session:
            now = datetime.now()
            return session.query(cls).filter(cls.commence_time > now)\
                .order_by(cls.commence_time).limit(limit).all()
    
    def get_bookmakers(self):
        with get_session() as session:
            return session.query(Bookmaker).join(OddsMarket)\
                .filter(OddsMarket.market_id.in_(
                    session.query(OddsOutcome.market_id).filter_by(odds_event_id=self.odds_event_id)
                )).distinct().all()
    
    def __repr__(self):
        return f"<OddsEvent(id='{self.odds_event_id}', home='{self.home_team}', away='{self.away_team}')>"


class Bookmaker(Base):
    __tablename__ = 'bookmakers'
    
    bookmaker_id = Column(Integer, primary_key=True)
    bookmaker_key = Column(Text)
    title = Column(Text)
    last_update = Column(TIMESTAMP)
    link = Column(Text)
    sid = Column(Text)
    
    # Relationships
    markets = relationship("OddsMarket", back_populates="bookmaker")
    
    @classmethod
    def get_by_id(cls, bookmaker_id):
        with get_session() as session:
            return session.query(cls).filter_by(bookmaker_id=bookmaker_id).first()
    
    @classmethod
    def get_by_key(cls, bookmaker_key):
        with get_session() as session:
            return session.query(cls).filter_by(bookmaker_key=bookmaker_key).first()
    
    @classmethod
    def get_all(cls):
        with get_session() as session:
            return session.query(cls).order_by(cls.title).all()
    
    def get_markets(self):
        with get_session() as session:
            return session.query(OddsMarket).filter_by(bookmaker_id=self.bookmaker_id).all()
    
    def __repr__(self):
        return f"<Bookmaker(id={self.bookmaker_id}, title='{self.title}')>"


class OddsMarket(Base):
    __tablename__ = 'odds_markets'
    
    market_id = Column(Integer, primary_key=True)
    bookmaker_id = Column(Integer, ForeignKey('bookmakers.bookmaker_id'))
    market_key = Column(Text)
    last_update = Column(TIMESTAMP)
    link = Column(Text)
    sid = Column(Text)
    
    # Relationships
    bookmaker = relationship("Bookmaker", back_populates="markets")
    outcomes = relationship("OddsOutcome", back_populates="market")
    
    @classmethod
    def get_by_id(cls, market_id):
        with get_session() as session:
            return session.query(cls).filter_by(market_id=market_id).first()
    
    @classmethod
    def get_by_bookmaker(cls, bookmaker_id):
        with get_session() as session:
            return session.query(cls).filter_by(bookmaker_id=bookmaker_id).all()
    
    @classmethod
    def get_by_key(cls, market_key):
        with get_session() as session:
            return session.query(cls).filter_by(market_key=market_key).all()
    
    def get_outcomes(self):
        with get_session() as session:
            return session.query(OddsOutcome).filter_by(market_id=self.market_id).all()
    
    def __repr__(self):
        return f"<OddsMarket(id={self.market_id}, key='{self.market_key}')>"


class OddsOutcome(Base):
    __tablename__ = 'odds_outcomes'
    
    outcome_id = Column(Integer, primary_key=True)
    market_id = Column(Integer, ForeignKey('odds_markets.market_id'))
    outcome_name = Column(Text)
    price = Column(Numeric)
    link = Column(Text)
    sid = Column(Text)
    bet_limit = Column(Text)
    
    # Relationships
    market = relationship("OddsMarket", back_populates="outcomes")
    
    @classmethod
    def get_by_id(cls, outcome_id):
        with get_session() as session:
            return session.query(cls).filter_by(outcome_id=outcome_id).first()
    
    @classmethod
    def get_by_market(cls, market_id):
        with get_session() as session:
            return session.query(cls).filter_by(market_id=market_id).all()
    
    @classmethod
    def get_by_fighter_name(cls, fighter_name):
        with get_session() as session:
            return session.query(cls).filter(cls.outcome_name.ilike(f"%{fighter_name}%")).all()
    
    def decimal_odds(self):
        """Convert American odds to decimal format"""
        if self.price is None:
            return None
        
        if self.price > 0:
            return 1 + (self.price / 100)
        else:
            return 1 + (100 / abs(self.price))
    
    def implied_probability(self):
        """Calculate implied probability from odds"""
        if self.decimal_odds:
            return 1 / self.decimal_odds
        return None
    
    def __repr__(self):
        return f"<OddsOutcome(id={self.outcome_id}, name='{self.outcome_name}', price={self.price})>"