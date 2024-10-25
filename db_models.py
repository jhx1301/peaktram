from sqlalchemy import Column, DateTime, Date, Float, create_engine
from sqlalchemy.dialects.mysql import LONGBLOB, MEDIUMTEXT, BLOB
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import json

Base = declarative_base()
class DetectionData(Base):
    __tablename__ = 'nums_tcp'

    detection_date = Column(Date, primary_key=True)
    position = Column(Float, primary_key=True)
    sensor1 = Column(Float)
    sensor2 = Column(Float)
    sensor3 = Column(Float)
    sensor4 = Column(Float)
    sensor5 = Column(Float)
    sensor6 = Column(Float)

class PictureData(Base):
    __tablename__ = 'picture_cv'
    meter = Column(Float, primary_key=True)
    date = Column(Date, primary_key=True)
    picture = Column(BLOB, nullable=False)

class Event7Data(Base):
    __tablename__ = 'event7_data'
    time = Column(Date, primary_key=True, nullable=False)
    data = Column(MEDIUMTEXT, nullable=False)

class Event9Data(Base):
    __tablename__ = 'event9_data'
    time = Column(Date, primary_key=True)
    flawPos = Column(Float, nullable=False)
    photo_data = Column(LONGBLOB, nullable=False)

# Updated DATABASE_URL to use pymysql
DATABASE_URL = 'mysql+pymysql://root:123321@localhost/data_learn'
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

def save_event7_data(timestamp: int, full_data: list) -> None:
    session = Session()
    try:
        detection_date = datetime.fromtimestamp(timestamp).date()
        position = 0.0  # 从0开始

        for sensor_data in full_data:
            if len(sensor_data) == 6:  # 确保每个传感器数据有六个值
                detection_entry = DetectionData(
                    detection_date=detection_date,
                    position=position,
                    sensor1=sensor_data[0],
                    sensor2=sensor_data[1],
                    sensor3=sensor_data[2],
                    sensor4=sensor_data[3],
                    sensor5=sensor_data[4],
                    sensor6=sensor_data[5]
                )
                session.add(detection_entry)
                position += 0.1  # 每次加0.1

        session.commit()
        print(f"Successfully saved {len(full_data)} records for {detection_date}.")
    except Exception as e:
        session.rollback()
        print(f"Error saving DetectionData: {e}")
    finally:
        session.close()

def save_event9_data(timestamp: int, flawPos: float, photo_data: bytes) -> None:
    session = Session()
    try:
        date_only = datetime.fromtimestamp(timestamp).date()
        # 使用 flawPos 作为 meter，date 为 date_only
        picture_data = PictureData(meter=flawPos, date=date_only, picture=photo_data)
        session.add(picture_data)
        session.commit()
        print(flawPos)
        print(date_only)
        print(picture_data)
        print(f"Data for date {date_only} with meter {flawPos} saved.")
    except Exception as e:
        session.rollback()
        print(f"Error saving PictureData: {e}")
    finally:
        session.close()
