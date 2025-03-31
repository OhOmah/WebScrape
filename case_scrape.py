from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from data_storage import check_dupe, save_to_db

import re
import time
import psycopg2
from datetime import datetime
import pandas as pd 
import numpy as np

'''
PURPOSE OF THIS FILE:
This file will take a case HTML table and convert into a pandas dataframe 
'''
def case_split(case):
    case_details_list = []
    case_parts = case.split("\n")
    case_number_name = case_parts[0].split(" ", 1)
     # Extract case type
    case_type = case_parts[1]
    # Extract filed date and additional info
    date_filed_info = case_parts[2].split(" ", 2)
    case_details_list.append({
        "CaseNumber": case_number_name[0],
        "CaseName": case_number_name[1],
        "CaseType": case_type,
        "DateFiled": date_filed_info[1],
        "AdditionalInfo": date_filed_info[2] if len(date_filed_info) > 2 else ''
    })
    df = pd.DataFrame(case_details_list)

    return df

def case_scrape(driver, party, links, register, password):
    '''
    PURPOSE OF THIS FUNCTION: 
    This will take any given case and save into 2 tables, one for general information
    another for more case specific information. 
    '''

    for i in range(len(links)):
        # 3. Click and get information of the first element in list, store in dataframe then go back
        # Crash happens here, I caught it once, I saw an error page and then it crashed out, would need 
        # to hit the back button to see if that issue needs to just be refreshed. 
        link = links[0]
        link.click()
        try:
            # Scrape the type of case. 
            table = driver.find_elements(By.XPATH, "//*[contains(@id, 'forms_table')]")
            columns = table[0].find_elements(By.TAG_NAME, 'td')
            case_info_df = case_split(columns[0].text)
            # Check if case number already exists
            check = check_dupe(casenumber = case_info_df['CaseNumber'], password= password)
            if check == False:
                # Pull data
                parties = driver.find_element(By.XPATH, '//*[contains(text(), "PARTIES")]')
                parties.click()
                time.sleep(5)
            else:
                print("case number already in database, skipping")
                pass
        except:
            pass
        
        if check == False:
            # Scrape the name of the people in the case and Representation
            # Regular expression pattern to extract Name, Party Type, and Representation
            pattern = r"\s{4}(.+?)\s+(Plaintiff|Defendant)(?:\s+(.+?\(Attorney\)))?"
            table = driver.find_element(By.ID, "paneArea.form663")
            rows = table.find_elements(By.TAG_NAME, 'tr')
            
            # Find all matches
            matches = re.findall(pattern, rows[0].text)

            # Convert matches into a structured DataFrame
            case_df = pd.DataFrame(matches, columns=["Name", "PartyType", "Representation"])

            # Create a merge variable to append new information 
            casenumber = case_info_df['CaseNumber'][0]
            # this code can be refined
            case_df['CaseNumber'] = np.nan
            case_df['CaseNumber'].fillna(casenumber, inplace=True)

            # Merge data
            combined_data = case_df.merge(case_info_df, how="left")

            # Grab Register information
            try:
                register_web = driver.find_element(By.XPATH, '//*[contains(text(), "REGISTER")]')
                register_web.click()
                time.sleep(5)
            except:
                pass

            # Now save to a table
            table = driver.find_elements(By.XPATH, '//*[contains(@id, "paneArea")]')
            df = table[0].get_attribute("outerHTML")

            # Save as a pandas dataframe
            register_df = pd.read_html(df)[0]

            # rename and drop unneeded columns. 
            register_df.drop(register_df.index[:2], inplace=True)
            register_df.drop(['Unnamed: 0'], axis=1, inplace=True)
            register_df.rename(columns={"Unnamed: 2": "registernotes"}, inplace=True)
            register_df.rename(columns={"Date": "date"}, inplace=True)
            register_df['casenumber'] = np.nan
            register_df['casenumber'].fillna(casenumber, inplace=True)

            save_to_db(which_table='register', df=register_df, password = password)
        else:
            pass

        driver.back()
        try:
            # 4. Get new list of elements, this time subtract first x amount of objects
            links = driver.find_elements(By.XPATH, "//*[contains(@href, '?q=node/391/')]")
            time.sleep(5)
            links = links[(i+1):]

            # 5. continue loop. 
            # 
            party = pd.concat([party, combined_data], ignore_index=True)
            register = pd.concat([register, register_df], ignore_index=True)
        
        except:
            pass 

    return party, register
'''
Logging changes made since last edit: 
    1. Added registry data
    2. export registry data to main function
'''

def go_to_next_page(driver):
    try:
        arrow_table = driver.find_element(By.CLASS_NAME, "glyphicon-triangle-right")
        arrow_table.click()
        time.sleep(3)
    except Exception as e:
        print("No More Pages", e)
        return False
    return True

def convert_date_range(start_date, end_date):
    # Get the date range 
    date_range = pd.date_range(start=start_date, end=end_date)
    month_range = pd.period_range(start=start_date, end=end_date, freq='M')

    # Take the range and convert to a list
    date_range = date_range.astype(str).to_list()
    month_range = month_range.astype(str).to_list()

    # Convert the format of the dates to fit the website
    # Month range does not need to be reformatted given no interaction with front facing website.
    formatted_dates = [datetime.strptime(date, "%Y-%m-%d").strftime("%m%d%Y") for date in date_range]

    return formatted_dates, month_range 

def grab_overall_table(driver):
    '''
    PURPOSE OF THIS FUNCTION: 
    Grabs the table for each page, saves into a dataframe then exports data to loop where
    once we get through the date, saves into a larger dataframe. 
    '''
    # find the main table
    table = driver.find_elements(By.XPATH, "//*[contains(@id, 'form.searchPage')]")

    # Split 
    raw_data = table[0].get_attribute("outerHTML")
    
    # Create Dataframe
    df_list = pd.read_html(raw_data) 
    df = df_list[0]

    # Convert names of columns to better match our main dataframe  
    df.rename(columns={'Case Number': "CaseNumber", 
                        'Case Name': 'CaseName',
                        'Hearing Description': 'HearingDescription',
                        'Result Type': 'ResultType' }, inplace=True)
    

    return df # pd.read_html returns a list of dataframe objects, return the first index 
    
def conn_to_db(database, password):
    '''
    PURPOSE OF THIS FUNCTION: 
    Connect to requested database to write data to. Given that we are connecting to 
    multiple databases with this project, it would save multiple lines if I save 
    this as a quick function to make the code more readable. 
    '''
    conn = psycopg2.connect(database = database,
                            user = "postgres",
                            host = "localhost",
                            password = password,
                            port = 5432)
    return conn