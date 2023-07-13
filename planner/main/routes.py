import folium
import geopandas as gpd
from flask import render_template, current_app
import pandas as pd

from planner import db
from planner.main import bp
from planner.models import TrajectoryPredictionData


def join_list_of_geoseries(geolist) -> gpd.GeoDataFrame:
    geolist = [geoseries for geoseries in geolist if geoseries is not None]
    if not geolist:
        return None
    shared_crs = geolist[0].crs
    if not all([geoseries.crs == shared_crs for geoseries in geolist]):
        raise ValueError(f"All GeoSeries must have the same crs, but got {[geoseries.crs for geoseries in geolist]}")
    # concatenate the lit of GeoDataSeries into a single GeoDataFrame
    joined = gpd.GeoDataFrame(geometry=pd.concat(geolist, ignore_index=True), crs=shared_crs)
    return joined


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
    layer_data = {
        "Kernel density estimate": kdes,
        "Bad landing areas": bad_landing_areas,
        "Predicted landing locations": landing_points,
    }
    for layer_name, layer_geometry in layer_data.items():
        layer_joined = join_list_of_geoseries(layer_geometry)
        if layer_joined is None:
            continue
        layer_json = layer_joined.to_json(to_wgs84=True)
        folium.GeoJson(
            layer_json,
            name=layer_name,
        ).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    m.fit_bounds(m.get_bounds(), padding=(30, 30))

    iframe = m.get_root()._repr_html_()
    return render_template('index.html', iframe=iframe)
