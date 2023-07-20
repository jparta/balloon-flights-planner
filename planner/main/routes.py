import folium
import geopandas as gpd
import pandas as pd
from flask import render_template, current_app
from folium import plugins, map as fol_map
from sqlalchemy import func

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


def mapready_geojson_from_geoseries(geoseries, layer_name):
    layer_joined = join_list_of_geoseries(geoseries)
    if layer_joined is None:
        return None
    layer_json = layer_joined.to_json(to_wgs84=True)
    return layer_json


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
    latest_run = db.session.query(func.max(TrajectoryPredictionData.run_at))
    for prediction_data in db.session.query(TrajectoryPredictionData).filter(TrajectoryPredictionData.run_at == latest_run).all():
        gs = prediction_data.to_GeoSeries()
        kdes.append(gs["kde"])
        bad_landing_areas.append(gs["bad_landing_areas"])
        landing_points.append(gs["landing_points"])

    landing_layer = fol_map.FeatureGroup(name="Predicted landing locations")
    landing_xys = join_list_of_geoseries(landing_points).to_crs("4326").get_coordinates()
    for loc in zip(landing_xys['y'], landing_xys['x']):
        folium.CircleMarker(loc, radius=1, color="black", fill=True).add_to(landing_layer)
    landing_layer.add_to(m)
    # plugins.MarkerCluster(landing_xys[['y', 'x']], name="Predicted landing locations").add_to(m)

    folium.Choropleth(
        name="Kernel density estimate",
        geo_data=join_list_of_geoseries(kdes),
        fill_color="yellow",
        fill_opacity=0.5,
        line_color="black",
        line_weight=1,
        highlight=False,
    ).add_to(m)

    folium.Choropleth(
        name="Bad landing areas",
        geo_data=join_list_of_geoseries(bad_landing_areas),
        fill_color="red",
        highlight=False,
    ).add_to(m)
    
    """
    for layer_name, layer_geometry in layer_data.items():
        geojson = mapready_geojson_from_geoseries(layer_geometry, layer_name)
        if geojson is not None:
            folium.GeoJson(geojson, name=layer_name).add_to(m)
    """

    folium.LayerControl(collapsed=False).add_to(m)

    m.fit_bounds(m.get_bounds(), padding=(30, 30))

    iframe = m.get_root()._repr_html_()
    return render_template('index.html', iframe=iframe)
