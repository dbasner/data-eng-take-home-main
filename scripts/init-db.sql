CREATE TABLE raw_weather_data (
    id SERIAL PRIMARY KEY,
    latitude DECIMAL(8,6) NOT NULL,
    longitude DECIMAL(8,6) NOT NULL,
    request_timestamp TIMESTAMPTZ NOT NULL,
    time TIMESTAMPTZ NOT NULL,
    temperature FLOAT,
    wind_speed FLOAT,
    UNIQUE (latitude, longitude, time)
);

CREATE INDEX idx_lat_long_request_time ON raw_weather_data (latitude, longitude, request_timestamp DESC);
CREATE INDEX idx_time ON raw_weather_data (time);


CREATE VIEW latest_weather_conditions AS
WITH hourly_weather_ranked_by_latest AS (
    SELECT 
        latitude,
        longitude,
        temperature,
        wind_speed,
        time,
 		request_timestamp,
        ROW_NUMBER() OVER (PARTITION BY latitude, longitude ORDER BY time DESC) AS rn
    FROM 
        raw_weather_data
    WHERE 
        time <= NOW() 
  		AND time <= request_timestamp --using both clauses may be redundant, together they presume we want latest weather measurement relative to now, not forecast
)
SELECT 
    latitude,
    longitude,
    temperature,
    wind_speed,
    time,
    request_timestamp
FROM 
    hourly_weather_ranked_by_latest
WHERE 
    rn = 1;


CREATE OR REPLACE FUNCTION get_time_series(lat DECIMAL(8,6), lon DECIMAL(8,6))
RETURNS TABLE (
    latitude DECIMAL(8,6),
    longitude DECIMAL(8,6),
    "time" TIMESTAMPTZ,
    temperature FLOAT,
    wind_speed FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        r.latitude,
        r.longitude,
        r."time",
        r.temperature,
        r.wind_speed
    FROM
        raw_weather_data r
    WHERE
        r.latitude = lat AND
        r.longitude = lon AND
        r."time" BETWEEN NOW() - INTERVAL '1 day' AND NOW() + INTERVAL '5 days'
    ORDER BY
        r."time";
END;
$$ LANGUAGE plpgsql;


