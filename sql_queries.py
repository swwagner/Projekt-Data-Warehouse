import configparser

# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

# DROP TABLES
staging_events_table_drop = "DROP TABLE IF EXISTS staging_events"
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs"
songplay_table_drop = "DROP TABLE IF EXISTS songplay"
user_table_drop = "DROP TABLE IF EXISTS users"
song_table_drop = "DROP TABLE IF EXISTS song"
artist_table_drop = "DROP TABLE IF EXISTS artist"
time_table_drop = "DROP TABLE IF EXISTS time"

# CREATE TABLES
# CREATE STAGING TABLES
staging_events_table_create= ("""CREATE TABLE IF NOT EXISTS staging_events(
                                artist VARCHAR(255),
                                auth VARCHAR(50),
                                first_name VARCHAR(255),
                                gender VARCHAR(1),
                                item_session INTEGER,
                                last_name VARCHAR(255),
                                length DOUBLE PRECISION,
                                level VARCHAR(50),
                                location VARCHAR(255),	
                                method VARCHAR(25),
                                page VARCHAR(35),	
                                registration VARCHAR(50),	
                                session_id	BIGINT,
                                song VARCHAR(255),
                                status INTEGER,
                                ts VARCHAR(50),
                                user_agent VARCHAR(255),
                                user_id INTEGER)
                                """)


staging_songs_table_create = ("""CREATE TABLE IF NOT EXISTS staging_songs(
                                song_id VARCHAR(100),
                                num_songs INTEGER,
                                artist_id VARCHAR(100),
                                artist_latitude DOUBLE PRECISION,
                                artist_longitude DOUBLE PRECISION,
                                artist_location VARCHAR(255),
                                artist_name VARCHAR(255),
                                title VARCHAR(255),
                                duration DOUBLE PRECISION,
                                year INTEGER)
                                """)

# CREATE FACT TABLE
songplay_table_create = ("""CREATE TABLE IF NOT EXISTS songplay(
                                songplay_id INT IDENTITY(0,1) PRIMARY KEY,
                                start_time TIMESTAMP,
                                user_id INTEGER NOT NULL,
                                level VARCHAR(50),
                                song_id VARCHAR(100),
                                artist_id VARCHAR(100),
                                session_id INTEGER,
                                location VARCHAR(255),
                                user_agent TEXT)
                                """)

# CREATE DIM TABLES
user_table_create = ("""CREATE TABLE IF NOT EXISTS users(
                        user_id INTEGER PRIMARY KEY,
                        first_name VARCHAR(255) NOT NULL,
                        last_name VARCHAR(255) NOT NULL,
                        gender VARCHAR(1),
                        level VARCHAR(50))
                        """)


song_table_create = ("""CREATE TABLE IF NOT EXISTS song(
                        song_id VARCHAR(100) PRIMARY KEY,
                        title VARCHAR(255),
                        artist_id VARCHAR(255),
                        year INTEGER,
                        duration DOUBLE PRECISION)
                        """)


artist_table_create = ("""CREATE TABLE IF NOT EXISTS artist(
                          artist_id VARCHAR(100) PRIMARY KEY,
                          name VARCHAR(255),
                          location VARCHAR(255),
                          latitude DOUBLE PRECISION,
                          longitude DOUBLE PRECISION)
                          """)


time_table_create = ("""CREATE TABLE IF NOT EXISTS time(
                        start_time TIMESTAMP PRIMARY KEY,
                        hour INTEGER,
                        day INTEGER,
                        week INTEGER,
                        month INTEGER,
                        year INTEGER,
                        weekDay INTEGER)
                        """)

# INSERT data into STAGING TABLES
# Parameters
IAM_ROLE = config['IAM_ROLE']['ARN']
LOG_DATA = config['S3']['LOG_DATA']
SONG_DATA = config['S3']['SONG_DATA']
LOG_JSONPATH = config['S3']['LOG_JSONPATH']

staging_events_copy = ("""copy staging_events 
                          from {}
                          iam_role {}
                          json {};
                        """).format(LOG_DATA, IAM_ROLE, LOG_JSONPATH)


staging_songs_copy = ("""copy staging_songs 
                          from {} 
                          iam_role {}
                          json 'auto';
                      """).format(SONG_DATA, IAM_ROLE)

# INSERT data into final tables from staging tables
# INSERT INTO FACT TABLE
songplay_table_insert = ("""INSERT INTO songplay(start_time, user_id, level, song_id, artist_id, session_id, location, user_agent)
                            SELECT  timestamp 'epoch' + se.ts/1000 * interval '1 second' as start_time, 
                            se.user_id, 
                            se.level, 
                            ss.song_id, 
                            ss.artist_id, 
                            se.session_id, 
                            se.location, 
                            se.user_agent
                            FROM staging_events se, staging_songs ss
                            WHERE se.page = 'NextSong' AND
                            se.song =ss.title AND
                            se.artist = ss.artist_name AND
                            se.length = ss.duration
                            """)

# INSERT INTO DIM TABLES
user_table_insert = ("""INSERT INTO users(user_id, first_name, last_name, gender, level)
                        SELECT distinct user_id, 
                        first_name, 
                        last_name, 
                        gender, 
                        level
                        FROM staging_events
                        WHERE page = 'NextSong'
                        """)


song_table_insert = ("""INSERT INTO song(song_id, title, artist_id, year, duration)
                        SELECT song_id, 
                        title, 
                        artist_id, 
                        year, 
                        duration
                        FROM staging_songs
                        WHERE song_id IS NOT NULL
                        """)

artist_table_insert = ("""INSERT INTO artist(artist_id, name, location, latitude, longitude)
                          SELECT distinct artist_id, 
                          artist_name, 
                          artist_location , 
                          artist_latitude, 
                          artist_longitude 
                          FROM staging_songs
                          WHERE artist_id IS NOT NULL
                          """)


time_table_insert = ("""INSERT INTO time(start_time, hour, day, week, month, year, weekDay)
                        SELECT start_time, 
                        extract(hour from start_time), 
                        extract(day from start_time),
                        extract(week from start_time), 
                        extract(month from start_time),
                        extract(year from start_time), 
                        extract(dayofweek from start_time)
                        FROM songplay
""")

# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create, songplay_table_create, user_table_create, song_table_create, artist_table_create, time_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]
