from datetime import datetime, timezone
from pprint import pformat
import time
import folium
import geopandas as gpd
import pandas as pd
from flask import render_template, current_app
from folium import features
from sqlalchemy import and_, func

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

    kdes = []
    bad_landing_areas = []
    landing_points = []

    query_start = time.time()
    # query the latest trajectory predictions for each launch time
    subq = db.session.query(
        TrajectoryPredictionData.launch_time,
        func.max(TrajectoryPredictionData.run_at).label("max_run_at")
    ).group_by(TrajectoryPredictionData.launch_time).subquery()
    query = db.session.query(TrajectoryPredictionData).join(
        subq,
        and_(
            TrajectoryPredictionData.launch_time == subq.c.launch_time,
            TrajectoryPredictionData.run_at == subq.c.max_run_at
        )
    ).filter(TrajectoryPredictionData.launch_time >= datetime.now(timezone.utc))

    # load to GeoPandas
    # gpd.read_postgis(query.statement, query.session.get_bind(), geom_col='kde')

    """
    for prediction_data in query.all():
        gs = prediction_data.to_GeoSeries()
        kdes.append(gs["kde"])
        bad_landing_areas.append(gs["bad_landing_areas"])
        landing_points.append(gs["landing_points"])
    query_end = time.time()
    current_app.logger.info(f"Query took {query_end - query_start} seconds")

    # compare size of kde and bad landing areas in bytes
    kde_size = sum([kde.to_json().encode('utf-8').__sizeof__() for kde in kdes])
    current_app.logger.info(f"KDE size: \n{kde_size:>20} bytes")
    bad_landing_size = sum([bad_landing.to_json().encode('utf-8').__sizeof__() for bad_landing in bad_landing_areas if bad_landing is not None])
    current_app.logger.info(f"Bad landing size: \n{bad_landing_size:>20} bytes")
    """

    layer_add_start = time.time()
    for prediction_data in query.all():
        prediction_df = prediction_data.to_gdf()
        prediction_df["launch_time"] = prediction_df["launch_time"].map(lambda dt: dt.isoformat())

        # current_app.logger.info(f"Prediction data: \n{prediction_df.dtypes}")
        kde_json = prediction_df[["launch_time", "kde"]].set_geometry("kde").to_json(to_wgs84=True)
        # current_app.logger.info(f"KDE json: \n{pformat(kde_json)}")
        kde_layer = folium.Choropleth(
            name="Kernel density estimate",
            geo_data=kde_json,
            fill_color="yellow",
            fill_opacity=0.5,
            line_color="black",
            line_weight=1,
            highlight=False,
        )
        kde_layer.geojson.add_child(features.GeoJsonTooltip(["launch_time"]))
        kde_layer.add_to(m)

        """
        landing_layer = fol_map.FeatureGroup(name="Predicted landing locations")
        landing_xys = join_list_of_geoseries(landing_points).to_crs("4326").get_coordinates()
        for loc in zip(landing_xys['y'], landing_xys['x']):
            folium.CircleMarker(loc, radius=0.5, color="black", fill=True).add_to(landing_layer)
        landing_layer.add_to(m)

        folium.Choropleth(
            name="Bad landing areas",
            geo_data=join_list_of_geoseries(bad_landing_areas),
            fill_color="red",
            highlight=False,
        ).add_to(m)
        """
    layer_add_end = time.time()
    current_app.logger.info(f"Layer add took {layer_add_end - layer_add_start} seconds")

    folium.LayerControl(collapsed=False).add_to(m)
    
    m.fit_bounds(m.get_bounds(), padding=(30, 30))

    getting_iframe_start = time.time()
    iframe = m.get_root()._repr_html_()
    getting_iframe_end = time.time()
    current_app.logger.info(f"Getting iframe took {getting_iframe_end - getting_iframe_start} seconds")

    template_render_start = time.time()
    resp_content = render_template('index.html', iframe=iframe)
    template_render_end = time.time()
    current_app.logger.info(f"Template render took {template_render_end - template_render_start} seconds")
    return resp_content



@bp.route('/sites')
def sites():
    pass
