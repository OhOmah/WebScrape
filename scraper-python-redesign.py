from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from case_scrape import case_split, case_scrape, go_to_next_page, convert_date_range, grab_overall_table

import re
import time
import logging
import pandas as pd
import datefinder
from bs4 import BeautifulSoup

'''
PURPOSE OF THIS SCRAPER:
This is designed to go into the ventura county court database to collect court data. 
Saves the data to a data frame for analysis. 
'''

def scrape():
    
    # Define the date range to scrape
    start_date = '06/05/2024'
    end_date = '12/31/2024'


    # convert date range
    date_range, month_range = convert_date_range(start_date=start_date, end_date=end_date)


    # Create final dataframe to store all the data. 
    all_party = pd.DataFrame(columns=['Name', 'PartyType', 'Representation', "CaseNumber", 'CaseName', 'CaseType', 'DateFiled', 'AdditionalInfo'])
    all_register = pd.DataFrame(columns=['Date', 'RegisterNotes', 'CaseNumber'])
    cases = pd.DataFrame(columns=['Name', 'PartyType', 'Representation', "CaseNumber", 'CaseName', 'CaseType', 'DateFiled', 'AdditionalInfo'])
    register = pd.DataFrame(columns=['Date', 'RegisterNotes', 'CaseNumber'])
    all_page_data = pd.DataFrame(columns=["Date", "Time", "CaseNumber", "CaseName", "HearingDescription", "Department", "ResultType"])
    password = open("data/password.txt", "r")
    driver = webdriver.Chrome()
    # Log into website
    driver.get("https://ventura.ecourt.com/public-portal/?q=node/390")
    username_input = driver.find_element(By.ID, "edit-name")
    password_input = driver.find_element(By.ID, "edit-pass")

    username_input.send_keys("OhOmah")
    password_input.send_keys(password)
    login = driver.find_element(By.ID, "edit-submit")
    login.click()
    time.sleep(5)
    
    '''
    GOAL:
    Reduce the bloat of repeated cases, reducing file size. 

    CHANGES TO BE NOTED: 
    1. Change the for loop to loop through months on top of days DONE
    2. main files to export will be based on month instead of day DONE
    3. Purge repeat case numbers at the end of each month. DONE 
    4. Export the pandas dataframe to a postgres database
    5. Log dates that have pulled cases.  
    '''
    # Loop through a list of dates 
    # Query date
    for month in month_range:
        for date in date_range: 
            # Wait until date box pops up
            revealed = driver.find_element(By.ID, "21966")

            wait = WebDriverWait(driver, timeout=10)
            wait.until(lambda d: revealed.is_displayed())
            revealed.clear()
            revealed.send_keys(date)
            submit = driver.find_element(By.ID, 'edit-submit')
            submit.click()



            # Grab the data needed 
            while True:
                links = driver.find_elements(By.XPATH, "//*[contains(@href, '?q=node/391/')]") 
                # TODO: update the saving of the dateframe to account for days now. 
                party, register = case_scrape(driver,cases,links, register)
                all_party = pd.concat([all_party, party], ignore_index=True)
                all_register = pd.concat([all_register, register])
                try:
                    # Grab all page data
                    page_data = grab_overall_table(driver)
                    all_page_data = pd.concat([all_page_data, page_data], ignore_index=True)
                except:
                    print("no cases this date")


                if not go_to_next_page(driver):
                    break
            time.sleep(5)
            # Drop any duplicates that may popup
            all_page_data.drop_duplicates(inplace=True)
            all_party.drop_duplicates(inplace=True)
            all_register.drop_duplicates(inplace=True)

            # Export the cases. TODO: Instead let's focus on the month instead. 
        all_page_data.to_csv(f'data/{month}_overall_page_data.csv', index=False)
        all_party.to_csv(f'data/{month}_party_information.csv', index=False)
        all_register.to_csv(f'data/{month}_register_notes.csv')
    '''
    TODO: Need to restructure for loop export data as months, helps with thinning data down. 
    '''

    # Create a loop to get a count of all clickable links in a webpage: 
    # 1. Get the original list of elements, get the count of each element.
    

    # 2. Then loop on the length of the list
    

    
    # if arrow is found redo loop

if __name__ == '__main__':
    scrape()

