import numpy as np
import pandas as pd
import re
import requests
import time

from bs4 import BeautifulSoup
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_table(table):
    '''
    Scrapes a html table and return the table as a list of lists.
    '''
    data = []
    for row in table.find_all("tr")[1:]:  # Skip the header row
        cells = row.find_all("td")
        row_data = [cell.text.strip() for cell in cells]
        data.append(row_data)
    return data

def get_ticker_smart_score(exch = "sp500", top_k = 20):
    '''
    exch: One of ["sp500", "nyse"]
    '''

    if exch == "sp500":
        link = "https://stockanalysis.com/list/sp-500-stocks/"
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(link)

    columns_dropdown_button = driver.find_element(By.XPATH, "/html/body/div/div[1]/div[2]/main/div/div/div/div[3]/div[2]/div[3]/button")
    columns_dropdown_button.click()
    sector_checkbox_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div/div[1]/div[2]/main/div/div/div/div[3]/div[2]/div[3]/div/div[2]/div[10]/input"))
    )
    sector_checkbox_button.click()
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    table = soup.find("table", {"id":"main-table"})
    data = scrape_table(table)
    df = pd.DataFrame(data, columns=["No.", "Symbol", "Company Name", "Market Cap", "Stock Price", "% Change", "Revenue", "Sector"], )
    top_k_stock_ticker = df.iloc[:top_k].Symbol

    driver = webdriver.Chrome(options=chrome_options)
    smart_score_results = []

    for stock_ticker in top_k_stock_ticker:
        try:
            driver.get(f"https://www.tipranks.com/stocks/{stock_ticker}")
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/div[4]"))
            )
            smart_score = re.search(r"Stock Smart Score\s*(\d+)", element.text).group(1)
            smart_score_results.append((stock_ticker, smart_score))
        except:
            print(f"Error printing smart score for {stock_ticker}")
            continue
    return sorted(smart_score_results, key=lambda x: int(x[1]), reverse=True)