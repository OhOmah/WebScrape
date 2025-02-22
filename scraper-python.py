from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from case_scrape import case_split, case_scrape, go_to_next_page, convert_date_range, grab_overall_table

import re
import time
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup

'''
PURPOSE OF THIS SCRAPER:
This is designed to go into the ventura county court database to collect court data. 
Saves the data to a data frame for analysis. 
'''

def scrape():
    # Enter date range here
    start_date = '06/04/2024'
    end_date = '12/31/2024'

    # convert date range
    date_range = convert_date_range(start_date=start_date, end_date=end_date)


    # Create final dataframe to store all the data. 
    all_cases = pd.DataFrame(columns=['Name', 'PartyType', 'Representation', "CaseNumber", 'CaseName', 'CaseType', 'DateFiled', 'AdditionalInfo'])
    cases = pd.DataFrame(columns=['Name', 'PartyType', 'Representation', "CaseNumber", 'CaseName', 'CaseType', 'DateFiled', 'AdditionalInfo'])
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
    

    # Loop through a list of dates 
    # Query date
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
            date_table = grab_overall_table(driver)
            links = driver.find_elements(By.XPATH, "//*[contains(@href, '?q=node/391/')]") 
            # TODO: update the saving of the dateframe to account for days now. 
            cases = case_scrape(driver,cases,links)
            all_cases = pd.concat([all_cases, cases], ignore_index=True)

            if not go_to_next_page(driver):
                break
        time.sleep(5)
        all_cases.to_csv(f'data/{date}_data.csv', index=False)

    # Create a loop to get a count of all clickable links in a webpage: 
    # 1. Get the original list of elements, get the count of each element.
    

    # 2. Then loop on the length of the list
    

    
    # if arrow is found redo loop
    all_cases.to_csv('data/data.csv', index=False)

if __name__ == '__main__':
    scrape()

