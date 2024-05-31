from dagster import ConfigurableResource, InitResourceContext, resource, EnvVar
import requests
import time
import json
from datetime import datetime
from decimal import Decimal
import pandas as pd


class WeatherAPIResource(ConfigurableResource):
    api_token: str
    base_url: str

    def get_weather_timeline(self, lat: str, lon: str) -> pd.DataFrame:
        headers = {
            "accept": "application/json",
            "Accept-Encoding": "gzip",
            "content-type": "application/json"
        }
        # get hourly data from 1 day in the past to 5 days in the future
        payload = {
            "location": f"{lat}, {lon}",
            "fields": ["temperature", "windSpeed"],
            "units": "imperial",
            "timesteps": ["1h"],
            "startTime": "nowMinus1d",
            "endTime": "nowPlus5d",
            "timezone": "UTC"
        }
        url = f"{self.base_url}?apikey={self.api_token}"
        request_timestamp = datetime.utcnow()
        max_retries = 5
        backoff_factor = 3
        attempt = 0

        while attempt < max_retries:
            try:
                response = requests.post(url, json=payload, headers=headers)
                response.raise_for_status()
                break
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:
                    attempt += 1
                    sleep_time = backoff_factor ** attempt
                    time.sleep(sleep_time)
                else:
                    raise
            except requests.RequestException as e:
                raise

        if attempt == max_retries:
            raise ValueError(f"Max retries exceeded for {lat}, {lon}")

        response_json = response.json()
        hourly_data = response_json.get("data", {}).get("timelines", [])[0].get("intervals", [])
        data = [{
            "latitude": Decimal(lat),
            "longitude": Decimal(lon),
            "request_timestamp": request_timestamp,
            "time": entry.get("startTime"),
            "temperature": entry.get("values", {}).get('temperature'),
            "wind_speed": entry.get("values", {}).get('windSpeed')
        } for entry in hourly_data]

        df = pd.DataFrame(data)
        df["request_timestamp"] = pd.to_datetime(df["request_timestamp"], utc=True)
        df["time"] = pd.to_datetime(df["time"], utc=True)
        return df