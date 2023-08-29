import time
import folium
import geopandas as gpd
import pandas as pd
from datetime import datetime, timezone, timedelta
from flask import render_template, current_app
from sqlalchemy import and_

from planner import db
from planner.main import bp
from planner.models import TrajectoryPredictionData
from planner.tasks import make_launch_inputs


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


def one_prediction_per_time_block(predictions: list[TrajectoryPredictionData], block_width_hours: float | int):
    """For each time block on the launch time axis, return the prediction with the latest run_at time"""
    predictions_by_block = {}
    current_app.logger.debug(f"Predictions count: {len(predictions)}")
    for prediction in predictions:
        launch_time = prediction.launch_time
        block_start_hour = launch_time.hour - launch_time.hour % block_width_hours
        block_start = launch_time.replace(hour=block_start_hour, minute=0, second=0, microsecond=0)
        block_start = launch_time - timedelta(hours=launch_time.hour % block_width_hours, minutes=launch_time.minute, seconds=launch_time.second, microseconds=launch_time.microsecond)
        block_end = block_start + timedelta(hours=block_width_hours)
        if block_start not in predictions_by_block:
            predictions_by_block[block_start] = prediction
        else:
            existing_prediction = predictions_by_block[block_start]
            if existing_prediction.run_at < prediction.run_at:
                predictions_by_block[block_start] = prediction
    blocked_predictions = list(predictions_by_block.values())
    current_app.logger.debug(f"Blocked predictions count: {len(blocked_predictions)}")
    return blocked_predictions

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
    query = db.session.query(TrajectoryPredictionData).filter(
        and_(
            TrajectoryPredictionData.launch_time >= datetime.now(timezone.utc),
            TrajectoryPredictionData.run_at >= datetime.now(timezone.utc) + timedelta(hours=-6)
        )
    )

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

    def bad_landing_proportion_okay(bad_landing_proportion):
        threshold = 0.05
        return bad_landing_proportion < threshold
    
    def kde_color(landing_okay: bool):
        return "#4dac26" if landing_okay else "#d01c8b"


    def kde_style_function(feature):
        bad_landing_proportion = feature['properties']['bad_landing_proportion']
        landing_okay = bad_landing_proportion_okay(bad_landing_proportion)
        return {
            "fillColor":    kde_color(landing_okay),
            "fillOpacity":  0.5,
            "color":        "black",
            "weight":       1,
        }
    
    fg_name = f'<span style="background-color: {kde_color(landing_okay=False)}; color: white">{"Bad landing"}</span>'
    bad_landing_feature_group = folium.FeatureGroup(name=fg_name).add_to(m)

    predictions = query.all()
    predictions_time_blocked = one_prediction_per_time_block(predictions, block_width_hours=3)

    layer_add_start = time.time()
    for prediction_data in predictions_time_blocked:
        prediction_df = prediction_data.to_gdf()
        prediction_df["launch_time"] = prediction_df["launch_time"].map(lambda dt: dt.round(freq='min').isoformat())
        prediction_df["sim_count"] = prediction_df["landing_points"].map(lambda points: len(points.geoms))
        prediction_df["bad_landing_proportion"] = prediction_df["bad_landing_proportion"].round(3)

        # current_app.logger.info(f"Prediction data: \n{prediction_df.dtypes}")
        kde_gdf = prediction_df[["kde", "launch_time", "bad_landing_proportion", "sim_count"]].set_geometry("kde")
        for row_index in range(len(kde_gdf)):
            kde_row = kde_gdf.iloc[[row_index]]
            kde_json = kde_row.to_json(to_wgs84=True)
            """
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
            """
            tooltip = folium.GeoJsonTooltip(
                fields=["launch_time", "bad_landing_proportion", "sim_count"],
                aliases=["Launch time", "Bad landing proportion", "Simulation count"],
            )
            name_template = '<span style="background-color: {color}; color: white">{content}</span>'
            landing_okay = bad_landing_proportion_okay(kde_row["bad_landing_proportion"].item())
            color = kde_color(landing_okay)
            content = f"{kde_row['launch_time'].item()} UTC"
            name_html = name_template.format(color=color, content=content)
            kde_layer = folium.GeoJson(
                data=kde_json,
                style_function=kde_style_function,
                name=name_html,
                tooltip=tooltip,
            )
            if landing_okay:
                kde_layer.add_to(m)
            else:
                kde_layer.add_to(bad_landing_feature_group)
    
    # Add the launch spot
    launch_inputs = make_launch_inputs()
    launch_spot = folium.Marker(
        launch_inputs.launch_coords_WGS84,
        tooltip="Launch location",
        icon=folium.Icon(color="purple", icon="rocket", prefix="fa"),
    ).add_to(m)
    layer_add_end = time.time()
    current_app.logger.info(f"Layer add took {layer_add_end - layer_add_start} seconds")

    folium.LayerControl(collapsed=False, sortLayers=True).add_to(m)
    
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
