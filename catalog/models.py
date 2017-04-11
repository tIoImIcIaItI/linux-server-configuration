from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """
    Provides a representation of an application user,
    suitable for use with the sqlalchemy orm
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False, unique=True)
    picture = Column(String(250))


class Category(Base):
    """
    Provides a representation of a catalog category,
    suitable for use with the sqlalchemy orm
    """
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """
        Provides a representation of a category,
        suitable for conversion to JSON format
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name
        }


class Item(Base):
    """
    Provides a representation of a catalog item,
    suitable for use with the sqlalchemy orm
    """
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    title = Column(String(80), nullable=False)
    description = Column(String(250))

    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """
        Provides a representation of an item,
        suitable for conversion to JSON format
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'title': self.title,
            'description': self.description
        }

# TODO: get data store config external config/environment var/etc.

# SQLITE DATA STORE SETTINGS
#
#DATABASE = {
#    'drivername': 'sqlite',
#    'database': 'itemcatalog.db'
#}

# POSTGRES DATA STORE SETTINGS
DATABASE = {
    'drivername': 'postgres',
    'host': 'localhost',
    'port': '5432',
    'username': 'catalog',
    'password': 'TODO: INSERT DB PWD HERE',
    'database': 'itemcatalog'
}

engine = create_engine(URL(**DATABASE))
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()

