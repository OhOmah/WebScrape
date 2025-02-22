from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

import re
import time
from datetime import datetime
import pandas as pd 

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

def case_scrape(driver, cases, links):
    '''
    PURPOSE OF THIS FUNCTION: 
    This will take any given case and save into 2 tables, one for general information
    another for more case specific information. 
    '''

    for i in range(len(links)):
        # 3. Click and get information of the first element in list, store in dataframe then go back
        link = links[0]
        link.click()
        try:
            parties = driver.find_element(By.XPATH, '//*[contains(text(), "PARTIES")]')
            parties.click()
            time.sleep(5)
        except:
            pass

        # Scrape the type of case. 
        table = driver.find_elements(By.XPATH, "//*[contains(@id, 'forms_table')]")
        columns = table[0].find_elements(By.TAG_NAME, 'td')
        case_info_df = case_split(columns[0].text)

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
        case_df['CaseNumber'] = casenumber
        case_df['CaseNumber'].fillna(case_info_df['CaseNumber'][0], inplace=True)

        # Merge data
        combined_data = case_df.merge(case_info_df, how="left")
        driver.back()

        # 4. Get new list of elements, this time subtract first x amount of objects
        links = driver.find_elements(By.XPATH, "//*[contains(@href, '?q=node/391/')]")
        time.sleep(5)
        links = links[(i+1):]

        # 5. continue loop. 
        
        cases = pd.concat([cases, combined_data], ignore_index=True)
    return cases

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

    # Take the range and convert to a list
    date_range = date_range.astype(str).to_list()

    # Convert the format of the dates to fit the website
    formatted_dates = [datetime.strptime(date, "%Y-%m-%d").strftime("%m%d%Y") for date in date_range]

    return formatted_dates 

def grab_overall_table(driver):
    '''
    PURPOSE OF THIS FUNCTION: 
    Grabs the table for each page, saves into a dataframe then exports data to loop where
    once we get through the date, saves into a larger dataframe. 
    '''
    # find the main table
    table = driver.find_elements(By.XPATH, "//*[contains(@id, 'form.searchPage')]")

    # Split 
    raw_data = table[0].text
    lines = raw_data.split("\n")
    headers = [
        'Date',
        'Time',
        'CaseNumber',
        'CaseName',
        'HearingDescription',
        'Department',
        'ResultType'
        ]

    data = [line.splie(" ", maxsplit=0) for line in lines[1:]]

    # Create dataframe
    overall_data = pd.DataFrame(data, columns= headers)
    

    print("hi")
    return table
    
