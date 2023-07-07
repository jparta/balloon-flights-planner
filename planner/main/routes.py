import folium
import geopandas as gpd
from flask import render_template
import pandas as pd

from planner import db
from planner.main import bp
from planner.models import TrajectoryPredictionData


@bp.route('/')
def index():
    m = folium.Map()
    # set the iframe width and height
    m.get_root().width = "100%"
    m.get_root().height = "100%"

    # query all the TrajectoryPredictionData objects from the database
    kdes = []
    bad_landing_areas = []
    landing_points = []
    for prediction_data in db.session.query(TrajectoryPredictionData).all():
        gs = prediction_data.to_GeoSeries()
        kdes.append(gs["kde"])
        bad_landing_areas.append(gs["bad_landing_areas"])
        landing_points.append(gs["landing_points"])
    for layer in [kdes, bad_landing_areas, landing_points]:
        layer = [geoseries for geoseries in layer if geoseries is not None]
        if not layer:
            continue
        shared_crs = layer[0].crs
        if not all([geoseries.crs == shared_crs for geoseries in layer]):
            raise ValueError(f"All GeoSeries must have the same crs, but got {[geoseries.crs for geoseries in layer]}")
        # concatenate the lit of GeoDataSeries into a single GeoDataFrame
        layer = gpd.GeoDataFrame(geometry=pd.concat(layer, ignore_index=True), crs=shared_crs)
        layer_json = layer.to_json(to_wgs84=True)
        folium.GeoJson(layer_json).add_to(m)
    folium.LayerControl().add_to(m)

    iframe = m.get_root()._repr_html_()
    return render_template('index.html', iframe=iframe)
