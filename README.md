# balloon-flights-planner
Planner for launches and flights of high-altitude balloons

To start, follow these steps:
1. Set up Python environment with `pip` and `requirements.txt`
2. Make sure you have Docker and Docker Compose installed
3. In the root directory, run `docker compose up`
4. Run `flask db upgrade` to initialize database
5. Run `python -m flask run --debug` to start a development server

A scheduled task, starting trajectory simulations, runs immediately after starting running Flask.

Here's the scheduled task overview:

![app_high_level_structure_scheduled_task](https://github.com/jparta/balloon-flights-planner/assets/25590558/aab48437-f0e6-40db-b79a-c28bda24de69)

Here's the map fetch overview:

![app_high_level_structure_map_fetch](https://github.com/jparta/balloon-flights-planner/assets/25590558/a339a686-c505-420c-ad78-2051e97a33b0)
