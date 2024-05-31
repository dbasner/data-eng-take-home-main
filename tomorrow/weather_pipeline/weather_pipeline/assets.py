import pandas as pd
from pandas import DataFrame
from typing import List, Tuple
from dagster import AssetExecutionContext, Output, asset
from .resources.postgres_resource import PostgresResource
from .resources.weather_api_resource import WeatherAPIResource

@asset
def lat_lon_pairs() -> List[Tuple[str, str]]:
    return [
        ("25.8600", "-97.4200")
        ,("25.9000", "-97.5200")
        ,("25.9000", "-97.4800")
        ,("25.9000", "-97.4400")
        ,("25.9000", "-97.4000")
        ,("25.9200", "-97.3800")
        ,("25.9400", "-97.5400")
        ,("25.9400", "-97.5200")
        ,("25.9400", "-97.4800")
        ,("25.9400", "-97.4400")
    ]

@asset
def get_weather_timeline(context: AssetExecutionContext, lat_lon_pairs: List[Tuple[str, str]], weather_api_resource: WeatherAPIResource) -> Output:
    context.log.info(f"lat lon pairs: {lat_lon_pairs}")
    weather_data = []

    for lat, lon in lat_lon_pairs:
        context.log.info(f"getting data for: {lat}, {lon}")
        df = weather_api_resource.get_weather_timeline(lat, lon)
        context.log.info(f"head of timeline data:\n {df.head()}")
        weather_data.append(df)

    weather_data = pd.concat(weather_data, ignore_index=True)

    # Add metadata to be displayed in Dagster UI
    metadata = {
        "lat_lon_pairs": lat_lon_pairs,
        "dataframe_size": weather_data.size
    }

    return Output(weather_data, metadata=metadata)

@asset
def save_weather_timeline(context: AssetExecutionContext, get_weather_timeline: DataFrame, postgres_resource: PostgresResource) -> None:
    context.log.info(f"saving data to db")
    postgres_resource.upsert_weather_data(get_weather_timeline)
    context.log.info(f"data saved to db")
    

