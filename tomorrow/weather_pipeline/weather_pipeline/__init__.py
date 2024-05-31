from dagster import (
    AssetSelection,
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_modules,
    DefaultScheduleStatus,
    DefaultSensorStatus,
    sensor,
    SensorEvaluationContext,
    RunRequest,
    EnvVar
)

from . import assets
from .resources.postgres_resource import PostgresResource
from .resources.weather_api_resource import WeatherAPIResource


all_assets = load_assets_from_modules([assets])

weather_timeline_job = define_asset_job("weather_timeline_job", selection=AssetSelection.all())

@sensor(job=weather_timeline_job, default_status=DefaultSensorStatus.RUNNING)
def immediate_run_sensor(context: SensorEvaluationContext):
    # This sensor will trigger the job immediately when Dagster starts up
    if context.last_completion_time is None:
        return RunRequest(run_key="initial_run")
    return None

weather_timeline_schedule = ScheduleDefinition(
    job=weather_timeline_job,
    cron_schedule="0 * * * *",  # every hour at minute 0
    default_status=DefaultScheduleStatus.RUNNING,
)

defs = Definitions(
    assets=all_assets,
    schedules=[weather_timeline_schedule],
    resources={
        "postgres_resource": PostgresResource(
            username=EnvVar("PGUSER").get_value(), 
            password=EnvVar("PGPASSWORD").get_value(), 
            host="postgres", #keeping this hardcoded for now--some things are easier to debug locally with "localhost"
            port=EnvVar("PGPORT").get_value(), 
            database=EnvVar("PGDATABASE").get_value()
        ),
        "weather_api_resource": WeatherAPIResource(
            api_token=EnvVar("TOMORROW_API_KEY").get_value(),
            base_url="https://api.tomorrow.io/v4/timelines"
        )
    },
    sensors=[immediate_run_sensor]
)
