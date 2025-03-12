from sqlalchemy.exc import SQLAlchemyError
from ..session import get_session

class BaseRepository:
    """Base repository with common operations for all entities"""
    
    model = None
    
    @classmethod
    def get_by_id(cls, id_value, id_field='id'):
        """Generic method to get an entity by its ID"""
        if cls.model is None:
            raise NotImplementedError("Repository class must define 'model' attribute")
        
        with get_session() as session:
            filter_kwargs = {id_field: id_value}
            return session.query(cls.model).filter_by(**filter_kwargs).first()
    
    @classmethod
    def get_all(cls, limit=100, offset=0):
        """Generic method to get all entities with pagination"""
        if cls.model is None:
            raise NotImplementedError("Repository class must define 'model' attribute")
        
        with get_session() as session:
            return session.query(cls.model).limit(limit).offset(offset).all()
    
    @classmethod
    def create(cls, data):
        """Generic method to create an entity"""
        if cls.model is None:
            raise NotImplementedError("Repository class must define 'model' attribute")
        
        try:
            with get_session() as session:
                entity = cls.model(**data)
                session.add(entity)
                session.commit()
                return entity
        except SQLAlchemyError as e:
            print(f"Error creating {cls.model.__name__}: {str(e)}")
            return None
    
    @classmethod
    def update(cls, id_value, data, id_field='id'):
        """Generic method to update an entity"""
        if cls.model is None:
            raise NotImplementedError("Repository class must define 'model' attribute")
        
        try:
            with get_session() as session:
                filter_kwargs = {id_field: id_value}
                entity = session.query(cls.model).filter_by(**filter_kwargs).first()
                if not entity:
                    return None
                
                for key, value in data.items():
                    if hasattr(entity, key):
                        setattr(entity, key, value)
                
                session.commit()
                return entity
        except SQLAlchemyError as e:
            print(f"Error updating {cls.model.__name__}: {str(e)}")
            return None
    
    @classmethod
    def delete(cls, id_value, id_field='id'):
        """Generic method to delete an entity"""
        if cls.model is None:
            raise NotImplementedError("Repository class must define 'model' attribute")
        
        try:
            with get_session() as session:
                filter_kwargs = {id_field: id_value}
                entity = session.query(cls.model).filter_by(**filter_kwargs).first()
                if entity:
                    session.delete(entity)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            print(f"Error deleting {cls.model.__name__}: {str(e)}")
            return False