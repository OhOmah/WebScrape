'''
PURPOSE OF THIS FILE:
Contains all the functions and libaries needed to boot up, call and maintain local db
'''

import psycopg2

def startup_db(password):
    # Establish connection to database
    conn = psycopg2.connect(database = "lawsuit_data",
                            user = "postgres",
                            host = "localhost",
                            password = password,
                            port = 5432)
    return conn