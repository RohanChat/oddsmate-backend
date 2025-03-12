from sqlalchemy.exc import SQLAlchemyError
from ..models.odds import OddsEvent, Bookmaker, OddsMarket, OddsOutcome
from ..session import get_session
from datetime import datetime

class OddsRepository:
    """Repository for Odds entity operations"""
    
    @classmethod
    def get_odds_event_by_id(cls, odds_event_id):
        """Get odds event by ID"""
        with get_session() as session:
            return session.query(OddsEvent).filter_by(odds_event_id=odds_event_id).first()
    
    @classmethod
    def get_odds_events_by_fight(cls, fight_id):
        """Get all odds events for a fight"""
        with get_session() as session:
            return session.query(OddsEvent).filter_by(fight_id=fight_id).all()
    
    @classmethod
    def get_latest_odds_by_fight(cls, fight_id):
        """Get latest odds for a fight"""
        with get_session() as session:
            return session.query(OddsEvent).filter_by(fight_id=fight_id)\
                .order_by(OddsEvent.odds_timestamp.desc()).first()
    
    @classmethod
    def get_upcoming_odds_events(cls, limit=20):
        """Get upcoming odds events"""
        with get_session() as session:
            now = datetime.now()
            return session.query(OddsEvent).filter(OddsEvent.commence_time > now)\
                .order_by(OddsEvent.commence_time).limit(limit).all()
    
    @classmethod
    def get_bookmaker_by_id(cls, bookmaker_id):
        """Get bookmaker by ID"""
        with get_session() as session:
            return session.query(Bookmaker).filter_by(bookmaker_id=bookmaker_id).first()
    
    @classmethod
    def get_bookmakers(cls):
        """Get all bookmakers"""
        with get_session() as session:
            return session.query(Bookmaker).all()
    
    @classmethod
    def get_market_by_id(cls, market_id):
        """Get market by ID"""
        with get_session() as session:
            return session.query(OddsMarket).filter_by(market_id=market_id).first()
    
    @classmethod
    def get_markets_by_bookmaker(cls, bookmaker_id):
        """Get all markets for a bookmaker"""
        with get_session() as session:
            return session.query(OddsMarket).filter_by(bookmaker_id=bookmaker_id).all()
    
    @classmethod
    def get_outcome_by_id(cls, outcome_id):
        """Get outcome by ID"""
        return OddsOutcome.get_by_id(outcome_id)
    
    @classmethod
    def get_outcomes_by_market(cls, market_id):
        """Get all outcomes for a market"""
        return OddsOutcome.get_by_market(market_id)
    
    @classmethod
    def get_outcomes_by_fighter_name(cls, fighter_name):
        """Get outcomes by fighter name"""
        return OddsOutcome.get_by_fighter_name(fighter_name)
    
    @classmethod
    def create_odds_event(cls, data):
        """Create a new odds event"""
        try:
            with get_session() as session:
                odds_event = OddsEvent(**data)
                session.add(odds_event)
                session.commit()
                return odds_event
        except SQLAlchemyError as e:
            print(f"Error creating odds event: {str(e)}")
            return None
    
    @classmethod
    def create_bookmaker(cls, data):
        """Create a new bookmaker"""
        try:
            with get_session() as session:
                bookmaker = Bookmaker(**data)
                session.add(bookmaker)
                session.commit()
                return bookmaker
        except SQLAlchemyError as e:
            print(f"Error creating bookmaker: {str(e)}")
            return None
    
    @classmethod
    def create_market(cls, data):
        """Create a new market"""
        try:
            with get_session() as session:
                market = OddsMarket(**data)
                session.add(market)
                session.commit()
                return market
        except SQLAlchemyError as e:
            print(f"Error creating market: {str(e)}")
            return None
    
    @classmethod
    def create_outcome(cls, data):
        """Create a new outcome"""
        try:
            with get_session() as session:
                outcome = OddsOutcome(**data)
                session.add(outcome)
                session.commit()
                return outcome
        except SQLAlchemyError as e:
            print(f"Error creating outcome: {str(e)}")
            return None