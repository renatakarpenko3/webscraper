import requests
from bs4 import BeautifulSoup
import time
import datetime
import smtplib
import csv
import os
import logging

# Logging setup to track price checks and any errors
logging.basicConfig(filename='price_tracker.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Global constants
URL = 'https://www.amazon.com/Funny-Data-Systems-Business-Analyst/dp/B07FNW9FGJ/ref=sr_1_3?dchild=1&keywords=data%2Banalyst%2Btshirt&qid=1626655184&sr=8-3&customId=B0752XJYNL&th=1'

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1", "Connection": "close",
    "Upgrade-Insecure-Requests": "1"
}

CSV_FILE = 'AmazonWebScraperDataset.csv'

# Check if the CSV exists; if not, create it with headers
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerow(['Title', 'Price', 'Date'])


# Function to fetch product details
def fetch_product_data():
    try:
        page = requests.get(URL, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(page.content, "html.parser")

        # Fetch the title and price
        title = soup.find(id='productTitle').get_text().strip()
        price = soup.find(id='priceblock_ourprice')

        if price is None:  # Fall back to deal price if regular price is unavailable
            price = soup.find(id='priceblock_dealprice')

        if price:
            price = price.get_text().strip()[1:]  # Remove the currency symbol ($)
        else:
            raise ValueError("Price not found on the page")

        logging.info(f"Fetched data: {title}, Price: {price}")
        return title, price

    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None, None
    except Exception as e:
        logging.error(f"Failed to scrape data: {e}")
        return None, None


# Function to append the scraped data to CSV
def save_data(title, price):
    today = datetime.date.today()
    data = [title, price, today]
    with open(CSV_FILE, 'a+', newline='', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerow(data)


# Function to send email notification
def send_mail(price):
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login('your_email@gmail.com', 'your_app_password')  # Replace with your credentials

        subject = "Price Drop Alert: Your Shirt is below threshold!"
        body = f"The price of your shirt is now ${price}! Check it out here: {URL}"
        msg = f"Subject: {subject}\n\n{body}"

        server.sendmail(
            'your_email@gmail.com',  # Sender
            'recipient_email@gmail.com',  # Receiver
            msg
        )

        logging.info("Email has been sent successfully")
        server.quit()
    except Exception as e:
        logging.error(f"Failed to send email: {e}")


# Main function to check price and act based on conditions
def check_price(threshold):
    title, price = fetch_product_data()

    if title is None or price is None:
        logging.error("Skipping price check due to data scraping failure")
        return

    try:
        price = float(price)
        save_data(title, price)

        # Send an email if the price falls below the threshold
        if price < threshold:
            send_mail(price)
        else:
            logging.info(f"No alert triggered. Current price: ${price}, Threshold: ${threshold}")

    except ValueError as e:
        logging.error(f"Price conversion failed: {e}")


# Loop to run the price check once every day
def start_price_tracking(threshold):
    while True:
        check_price(threshold)
        time.sleep(86400)  # Wait 24 hours (86400 seconds) before running again


# Start tracking with the threshold set at $15
start_price_tracking(15.0)
