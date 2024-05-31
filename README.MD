# Amperon Data Engineering Take Home Assignment


## Technologies Used
I decided to run this pipeline on the Dagster data pipeline orchestrator. I was choosing between that and a simple cron job, and while a cron job would have been simpler I liked the idea of using a tool explicitly built for data pipeline creation and management that used idioms for that work--for example Assets instead of vanilla python functions. Additionally I decided to save my data to the postgres database provided and connected to it with sqlalchemy and psycopg2. I also used pandas for data manipulation and matplotlib for visualization since they are both rock solid. 

## Installation and Setup
In order to set up you should be able to add env key and postgres related env info into the .env file in weather_pipeline/ and just run `docker compose up --build` like in the directions, should install all the deps (may take a while), and start up the Dagster instance. Due to issues with docker compose I ended up running this via Dagster's dev environment since that way it can run it in a single container. After it starts up it should run the initial run of the pipeline immediately and then every hour at minute 0 afterwards.
I'd recommend going into http://127.0.0.1:3000/assets and poking around, for example, I wrote it so that once materialized the get_weather_timeline asset in the UI can show you nice metadata such as which lat/lon pairs the asset retrieved data for.
```shell
TOMORROW_API_KEY=<API_KEY_HERE>
PGHOST=localhost
PGPORT=5432
PGDATABASE=tomorrow
PGUSER=postgres
PGPASSWORD=postgres
```

## Database 
Just stuck with Postgres since its pretty good at everything and was already setup. Considered switching to sqlite for very speedy results but it did not seem worth it. I walked through a number of possible options for database schema / storage setup in general. I considered storing every part of the 1 day forward 5 days back weather timeline on each request, each row differentiable by way of request timestamp. This would have let users decide if they wanted to know how a forecast changed as it got closer to the present time, or if tomorrow's api was reliable or undergone changes would allow a user to see if a historical measurement changed over time. Ultimately though that was not asked for and would take up too much space. It would have been a little over a million rows a year if running continously--10 locations, 144 rows per location in a request, 8670 hours in a year. I decided to go with only storing additional rows for previously unrecorded hours, and updating the values when a freshly retrieved timeline response had a lat/long and timestamp matching an existing record.

I decided to go with a simple view and postgres function in order to allow the user to get latest weather data and latest timeline. I considered having those operations be computed via a Dagster asset but since the number of rows was so low I realized the efficiency gains from running it that way would be negligible. If theres one row per location per hour in a year thats roughly 9000 rows a year if running continuously, and those rows are quite small, postgres functions told me less than 300 bytes per row.


## Uncertainties and Assumptions
I was not quite sure about the definition of latest weather at each location--is that the most recent temp measurement, or the furthest out temperature forecast, or the most recent measurement or forecast? I decided to go with most recent temperature measurement. Also, I decided to just hardcode the table creation code in init-db.sql along with the view and function creation--I wasn't sure if it would have been better to put the view and function into a Dagster asset that created them. Alternatively, I also considered doing the work those queries do inside of Dagster assets so that the queries worked faster.


## Future Improvements
I'd further refactor the pipeline out of __init__.py files and files with "general" names like "assets". I'd also clean up some residual dependencies that are not working. In a previous iteration I had tests for my assets and resources working but for whatever reason when I rewrote this to work via docker compose they no longer worked. Due to issues with secrets being committed I decided to just push up a version without all the git history.
