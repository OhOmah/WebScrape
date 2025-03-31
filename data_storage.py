'''
PURPOSE OF THIS FILE:
Contains all the functions and libaries needed to boot up, call and maintain local db
'''

import psycopg2

from sqlalchemy import create_engine

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

def save_to_db(which_table, df, password):
    '''
    GOAL OF THIS FUNCTION:
    1. Save the party information dataframe to the party table 
    2. Save the register notes dataframe to the regsiter table
    3. Save the main page dataframe to the overall table

    we use an if statment to check which table and save accordingly
    '''
    # Start up instance
    conn, cur = startup_db(password)
    
    # create engine
    create_engine(f'postgresql+psycopg2://postgres:{password}@localhost:5432/database')

    if which_table == "party":
        df.to_sql('party_data')
    elif which_table == "register":
        df.to_sql('register_data')
    elif which_table == "overall":
        pass
    else:
        print("no table was passed, no information saved.")

    # Close the db
    close_db(conn)
    