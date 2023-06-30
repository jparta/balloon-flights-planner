import io
import logging
from datetime import datetime, timedelta
from pathlib import Path
import typing

import numpy as np
from astra.simulator import flight, forecastEnvironment


logging.basicConfig(level=logging.DEBUG)

np.random.seed(42)

output_path = Path("astra_out")
days_to_launch = 1
launch_datetime = datetime.now() + timedelta(days=days_to_launch)


LAUNCH = {
    "launchSiteLat": 60.157502,
    "launchSiteLon": 24.654051,
    "launchSiteElev": 40,
    "launchTime": launch_datetime,
    "inflationTemperature": 10,
    "forceNonHD": False,
}

FLIGHT_SIM = {
    "balloonGasType": "gt96He",
    "balloonModel": "SFB800",
    "nozzleLift": 1.6,
    "payloadTrainWeight": 0.664,
    "parachuteModel": "",
    "numberOfSimRuns": 10,
    "trainEquivSphereDiam": 0.285,  # Styrox probe cuboid area-equivalent diameter
    "outputPath": output_path.absolute(),
    #    "debugging": True,
    "log_to_file": True,
}


def run_sim(
    program_out_redirect_buffer: typing.TextIO | None = None, progress_handler=None
):
    sim_environment = forecastEnvironment(**LAUNCH, progressHandler=progress_handler)
    the_flight = flight(
        **FLIGHT_SIM,
        environment=sim_environment,
        progress_stream=program_out_redirect_buffer
    )
    the_flight.run()


if __name__ == "__main__":
    run_sim()
