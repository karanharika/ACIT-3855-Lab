from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime


class GateRequest(Base):
    """ Requests for gate assignment """

    __tablename__ = "gate_request"

    id = Column(Integer, primary_key=True)
    truck_id = Column(String(250), nullable=False)
    license_plate = Column(String(250), nullable=False)
    trailer_type = Column(String(250), nullable=False)
    date_created = Column(DateTime, nullable=False)

    def __init__(self, truck_id, license_plate, trailer_type):
        """ Initializer for a gate assignment request """
        self.truck_id = truck_id
        self.license_plate = license_plate
        self.trailer_type = trailer_type
        self.date_created = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        """ Dictionary representation for a gate assignment request """
        dict = {}

        dict['id'] = self.id
        dict['truck_id'] = self.truck_id
        dict['license_plate'] = self.license_plate
        dict['trailer_type'] = self.trailer_type
        dict['date_created'] = self.date_created

        return dict