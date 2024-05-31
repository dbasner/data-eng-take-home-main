from dagster import ConfigurableResource, InitResourceContext
from pydantic import PrivateAttr
from sqlalchemy import create_engine, text, Engine
import pandas as pd


class PostgresResource(ConfigurableResource):
    username: str
    password: str
    host: str
    port: str
    database: str
    _engine: Engine = PrivateAttr()
    _connection_string: str = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._connection_string = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        self._engine = create_engine(self._connection_string)

    def run_query(self, query: str) -> pd.DataFrame:
        with self._engine.connect() as connection:
            result = connection.execute(text(query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        return df

    def insert_dataframe(self, df: pd.DataFrame, table_name: str, if_exists: str = 'append'):
        df.to_sql(table_name, con=self._engine, if_exists=if_exists, index=False)

    def upsert_weather_data(self, data_frame: pd.DataFrame):
        with self._engine.connect() as conn:
            trans = conn.begin()
            try:
                for index, row in data_frame.iterrows():
                    row_dict = row.to_dict()
                    conn.execute(text("""
                        INSERT INTO raw_weather_data (latitude, longitude, request_timestamp, time, temperature, wind_speed)
                        VALUES (:latitude, :longitude, :request_timestamp, :time, :temperature, :wind_speed)
                        ON CONFLICT (latitude, longitude, time)
                        DO UPDATE SET temperature = EXCLUDED.temperature,
                                      wind_speed = EXCLUDED.wind_speed,
                                      request_timestamp = EXCLUDED.request_timestamp;
                    """), row_dict)
                trans.commit() 
            except Exception as e:
                print(f"Exception: {e}")
                trans.rollback()
                raise 

    def execute_sql(self, sql: str):
        with self._engine.connect() as connection:
            connection.execute(text(sql))
   
   