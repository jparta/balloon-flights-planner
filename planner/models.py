import geopandas as gpd
from geoalchemy2 import Geometry
from sqlalchemy.ext.hybrid import hybrid_property

from planner.extensions import db


class TrajectoryPredictionData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    run_at = db.Column(db.DateTime, nullable=False)
    launch_time = db.Column(db.DateTime, nullable=False)
    landing_points = db.Column(Geometry(geometry_type='MULTIPOINT'), nullable=False, )
    kde = db.Column(Geometry(geometry_type='MULTIPOLYGON'), nullable=False)
    bad_landing_areas = db.Column(Geometry(geometry_type='MULTIPOLYGON'), nullable=True)
    bad_landing_proportion = db.Column(db.Float, nullable=False)

    @staticmethod
    def geoalchemy_to_geoseries(obj):
        if obj is None:
            return None
        crs = obj.srid
        geoseries = gpd.GeoSeries.from_wkb([str(obj.as_ewkb())])
        geoseries = geoseries.set_crs(crs)
        return geoseries

    def __repr__(self):
        return f'<TrajectoryPredictionData {self.id}>'
    
    """
    @hybrid_property
    def landing_points(self):
        return self.geoalchemy_to_geoseries(self._landing_points)
    
    @hybrid_property
    def kde(self):
        return self.geoalchemy_to_geoseries(self._kde)
    
    @hybrid_property
    def bad_landing_areas(self):
        return self.geoalchemy_to_geoseries(self._bad_landing_areas)
    """

    def to_gdf(self):
        geom_fields_to_output = {
            "landing_points": self.landing_points,
            "kde": self.kde,
            "bad_landing_areas": self.bad_landing_areas,
        }
        other_fields_to_output = {
            "id": self.id,
            "run_at": self.run_at,
            "launch_time": self.launch_time,
            "bad_landing_proportion": self.bad_landing_proportion,
        }
        output = {}
        for name, geoset in geom_fields_to_output.items():
            if geoset is None:
                output[name] = None
                continue
            crs = geoset.srid
            geoseries = gpd.GeoSeries.from_wkb([str(geoset.as_ewkb())])
            geoseries = geoseries.set_crs(crs)
            output[name] = geoseries
        output.update(other_fields_to_output)
        return gpd.GeoDataFrame(output)
