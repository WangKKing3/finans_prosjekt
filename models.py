import os
from sqlalchemy import Column, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class ArticleModel(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    url = Column(String(255), unique=True)
    content = Column(Text)
    published_date = Column(String(50))
    source = Column(String(100))
    sentiment_score = Column(Float, nullable=True)
    AI_generated_summary = Column(Text, nullable=True)
    predicted_impact = Column(String(20), nullable=True)


# Database-oppsett
DB_FOLDER = r"F:\SQlitel"
os.makedirs(DB_FOLDER, exist_ok=True)
DB_PATH = f"sqlite:///{DB_FOLDER}/articles.db"

engine = create_engine(DB_PATH)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)