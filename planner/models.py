import geopandas as gpd
from geoalchemy2 import Geometry

from planner.extensions import db


class TrajectoryPredictionData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    run_at = db.Column(db.DateTime, nullable=False)
    bad_landing_areas = db.Column(Geometry(geometry_type='MULTIPOLYGON'), nullable=True)

    def __repr__(self):
        return f'<TrajectoryPredictionData {self.id}>'

    def to_GeoSeries(self):
        fields_to_output = {
            "landing_points": self.landing_points,
            "kde": self.kde,
            "bad_landing_areas": self.bad_landing_areas,
        }
        output = {}
        for name, geoset in fields_to_output.items():
            if geoset is None:
                output[name] = None
                continue
            crs = geoset.srid
            geoseries = gpd.GeoSeries.from_wkb([str(geoset.as_ewkb())])
            geoseries = geoseries.set_crs(crs)
            output[name] = geoseries
        return output
