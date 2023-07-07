from datetime import timedelta

from find_launch_time.logic import find_time
from geoalchemy2.shape import from_shape
from find_launch_time.logic.proportion_of_kde import EnhancedEnsembleOutputs

from planner import scheduler, db
from planner.models import TrajectoryPredictionData


def run_astra_sims_background():
    scheduler.app.logger.info("Running astra sims in background")
    prediction_data: list[EnhancedEnsembleOutputs] = find_time.get_prediction_geometries(
        prediction_window_length=timedelta(hours=6),
        launch_time_increment=timedelta(days=1),
    )
    field_name_conversion = {
        "predicted_landing_sites": "landing_points",
        "kde": "kde",
        "bad_landing_areas": "bad_landing_areas",
    }
    prediction_db_objects = []
    for prediction in prediction_data:
        # map EnhancedEnsembleOutputs attributes to TrajectoryPredictionData db fields
        out_data = {
            field_name_conversion[name]: from_shape(gdf.geometry.unary_union, srid=gdf.crs.to_epsg(), extended=True)
            for name, gdf in prediction.__dict__.items()
            if name in field_name_conversion and gdf is not None
        }
        prediction_data = TrajectoryPredictionData(**out_data)
        prediction_db_objects.append(prediction_data)
    with scheduler.app.app_context():
        db.session.add_all(prediction_db_objects)
        db.session.commit()
    scheduler.app.logger.info("Finished running astra sims in background and saved results to db")
