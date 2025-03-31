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
    
    cur = conn.cursor()
    return conn, cur

def close_db(conn):
    conn.commit()
    conn.close()

def check_dupe(casenumber, password):
    # Start connection
    conn, cur = startup_db(password)

    # Check if casenumber already exists
    cur.execute(f"""
    SELECT * FROM register_data
    WHERE casenumber = '{casenumber}';
    """)
    rows = cur.fetchall()

    # if we don't get an empty list when querying the database, return true
    if not rows:
        check = False
    else:
        check = True
    
    # Close connection
    close_db(conn)

    return check

def save_to_db(password):
    pass