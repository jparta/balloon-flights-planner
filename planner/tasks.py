from datetime import datetime, timedelta, timezone
from pprint import pformat
from typing import Any

from find_launch_time.logic import find_time
from find_launch_time.logic.proportion_of_kde import EnhancedEnsembleOutputs
from geoalchemy2.shape import from_shape
from shapely.geometry import MultiPolygon, MultiPoint

from planner.extensions import scheduler, db
from planner.models import TrajectoryPredictionData


def save_simulation_results_to_db(
    prediction: EnhancedEnsembleOutputs,
    start_time: datetime,
):
    geometry_name_conversion = {
        "predicted_landing_sites": "landing_points",
        "kde": "kde",
        "bad_landing_areas": "bad_landing_areas",
    }
    other_fields_name_conversion = {
        "proportion_of_bad_landing_to_kde": "bad_landing_proportion",
        "launch_time": "launch_time",
    }
    # map EnhancedEnsembleOutputs attributes to TrajectoryPredictionData db fields
    out_data: dict[str, Any] = {}
    out_data["run_at"] = start_time
    for from_name, to_name in geometry_name_conversion.items():
        gdf = getattr(prediction, from_name)
        if gdf is not None:
            # Make sure we have the right geometry types
            geometry = gdf.geometry.unary_union
            if geometry is None or geometry.is_empty:
                continue
            if to_name == 'landing_points' and geometry.geom_type == 'Point':
                geometry = MultiPoint([geometry])
            elif to_name in ('kde', 'bad_landing_areas') and geometry.geom_type == 'Polygon':
                geometry = MultiPolygon([geometry])
            out_data[to_name] = from_shape(geometry, srid=gdf.crs.to_epsg(), extended=True)
    for from_name, to_name in other_fields_name_conversion.items():
        field_value = getattr(prediction, from_name)
        if field_value is not None:
            out_data[to_name] = field_value
    prediction_object = TrajectoryPredictionData(**out_data)
    with scheduler.app.app_context():
        db.session.add(prediction_object)
        db.session.commit()
    scheduler.app.logger.debug(f"Saved prediction data to db")


def make_launch_inputs():
    launch_coords_possibilities = {
        "Kartanonrannan_koulu": (60.153144, 24.551671),
        "Vantinlaakso": (60.184101, 24.623690)
    }
    launch_coords = launch_coords_possibilities["Vantinlaakso"]
    flight_train_mass_kg = 0.770
    flight_train_equiv_sphere_diam = 0.285
    balloon = "TA350"
    nozzle_lift_kg = 1.46
    parachute = "SFP800"

    launch_inputs = find_time.LaunchInputs(
        launch_coords_WGS84=launch_coords,
        flight_train_mass_kg=flight_train_mass_kg,
        flight_train_equiv_sphere_diam=flight_train_equiv_sphere_diam,
        balloon=balloon,
        nozzle_lift_kg=nozzle_lift_kg,
        parachute=parachute,
    )
    return launch_inputs


@scheduler.task('date', id='test_task', run_date=datetime.now(timezone.utc) + timedelta(seconds=5), timezone='UTC')
@scheduler.task('cron', id='run_astra_sims', hour='0,6,12,18', minute='30', timezone='UTC')
def run_astra_sims():
    scheduler.app.logger.info("Running astra sims")
    time_finder = find_time.FindTime(debug=scheduler.app.debug)
    start_time = datetime.now(timezone.utc)

    launch_inputs = make_launch_inputs()

    prediction_data = time_finder.get_prediction_geometries(
        launch_inputs=launch_inputs,
        prediction_window_length=timedelta(days=7),
        launch_time_increment=timedelta(hours=3),
        sims_per_launch_time=25,
    )
    for prediction in prediction_data:
        save_simulation_results_to_db(prediction, start_time)
    scheduler.app.logger.info("Finished running astra sims in background and saved results to db")
