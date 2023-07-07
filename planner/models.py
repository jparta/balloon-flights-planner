from planner.extensions import db
from geoalchemy2 import Geometry


class TrajectoryPredictionData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    landing_points = db.Column(Geometry(geometry_type='MULTIPOINT'))
    kde = db.Column(Geometry(geometry_type='POLYGON'))
    bad_landing_areas = db.Column(Geometry(geometry_type='MULTIPOLYGON'), nullable=True)

    def __repr__(self):
        return f'<TrajectoryPredictionData {self.id}>'