from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class StockSignal(Base):
    __tablename__ = "stock_signals"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String)
    name = Column(String)
    breakout_date = Column(String)
    breakout_price = Column(Float)
    pullback_date = Column(String)
    pullback_price = Column(Float)
    ma5_price = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AppConfig(Base):
    __tablename__ = "app_config"
    key = Column(String, primary_key=True)
    value = Column(String)

DATABASE_URL = "sqlite:///./stock_scanner.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
