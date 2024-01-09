from selenium import webdriver;
from selenium.webdriver.firefox.options import Options as FirefoxOptions;
from selenium.webdriver.common.by import By;
import time;
import csv;
from selenium.webdriver.support.ui import WebDriverWait;
from selenium.webdriver.support import expected_conditions as EC;
import re;
import datetime;
import os;

csvFileHeader = ['Dealer ID', 'Destination url', 'Title', 'Price', 'Make', 'Model', 'Year', 'Body style', 'Odometer',
                'Transmission', 'Engine', 'Engine Size', 'Driveline', 'Exterior', 'Interior', 'Doors', 'Passengers', 'Fuel Type',
                'City Fuel', 'Hwy Fuel', 'Stock Number', 'VIN', 'description', 'Photo_urls', 'Options'];

dealerID = "44813";

def getDetailsOfVehicle(driver, url):
    driver.get(url);
    driver.implicitly_wait(30);

    csvFileRow = [];

    # Add Dealer id
    csvFileRow.append(dealerID.strip());

    # Add Destination
    csvFileRow.append(url.strip());

    # Add Title 
    titleValue = "";
    try:
        titleElement  = driver.find_element(By.XPATH, "//h2[contains(@class, 'vehicleName')]");
        titleValue    = titleElement.text.strip();
    except Exception as error:
        print("Title not found !");
    csvFileRow.append(titleValue);
    
    # Add price
    priceValue = "";
    try:
        priceElement  = driver.find_element(By.XPATH, "//span[contains(@class, 'PriceValue')]");
        pricePattern  = r'\$\s*([\d,]+\.?\d*)';
        priceValue    = priceElement.text.strip();
        match         = re.search(pricePattern, priceValue);
        if match:
            priceValue = match.group(1).replace(',', '');
            if(float(priceValue) < 1000):
                priceValue = "1000";
        else:
            priceValue  = "1000";
    except Exception as error:
        print("Price not found !");
        priceValue = "1000";

    csvFileRow.append(priceValue);
    
    # Add Caractéristiques
    for index in range(1, 19):

        try:
            wait = WebDriverWait(driver, 10);
            element  = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'VehicleInfoDetails')]/div[{}]/div/span[2]".format(index))));
            value    = element.text.strip();
            if( index == 5 ):
                value = re.sub(r'[^\d]', '', value);
            csvFileRow.append(value);
        except Exception as error:
            csvFileRow.append("");
            pass

    # Add Description
    descriptionValue  = getCleanDescription(driver);
    csvFileRow.append(descriptionValue);

    # Add Photo urls
    photoUrls = getImagesLink(driver);
    csvFileRow.append(photoUrls);

    # Add options
    options = getOptions(driver);
    csvFileRow.append(options);

    return csvFileRow;

# [END  : getDetailsOfVehicle]

def getCleanDescription(driver):
    descriptionValue = "";
    try:
        descriptionElement = driver.find_element(By.XPATH, "//div[contains(@class, 'seller_comments')]");
        descriptionValue   = str(descriptionElement.get_attribute('outerHTML'));
    except Exception as error:
        pass
    return str(descriptionValue).strip();

# [END : getCleanDescription]

def getImagesLink(driver):
    imagesUrl = "";
    try:
        mainImagesElement = driver.find_element(By.XPATH, "//*[@id='carousel']/div/ul");
        imagesElements    = mainImagesElement.find_elements(By.TAG_NAME, "li");
        for image in imagesElements:
            if(imagesUrl == "") :
                imagesUrl = re.sub(r'/thumb-', '/pic-', image.get_attribute('data-thumb'));
            else:
                imagesUrl += "," + re.sub(r'/thumb-', '/pic-', image.get_attribute('data-thumb'));
    except:
        pass
    return str(imagesUrl).strip();

# [END : getImagesLink]

def getOptions(driver):
    options = "";
    try:
        mainOptionsElement  = driver.find_element(By.XPATH, "//ul[contains(@class, 'VehicleOptions')]");
        optionsElements     = mainOptionsElement.find_elements(By.TAG_NAME, "li");
        for option in optionsElements:
                if(options == "") :
                    options = option.text;
                else:
                    options += "," + option.text;
    except:
        pass
    return str(options).strip();

# [END : getOptions]

# [================================================================================]
if __name__ == "__main__":
    try:
        print("Start Scraping at ["+ str(datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S')) +"] :");
        #object of FirefoxOptions
        options = webdriver.FirefoxOptions();
        options.headless = True;
        driver = webdriver.Firefox(options=options);

        driver.get("https://www.peelcarsales.com/used-cars/?sold=&ViewMode=vGrid&featured=&location=&make=&model=&min_price=&max_price=&min_year=&max_year=&min_kilometers=&max_kilometers=&body_style=&engine=&transmission=&exteriorcolor=&sortby=Price-DESC&compare=");
        driver.implicitly_wait(30);

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);");
        time.sleep(5);
        
        pleaseWait = driver.find_element(By.XPATH, '//*[@id="load_data_message"]/span').text;
        while(pleaseWait != ""):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);");
            time.sleep(5);
            pleaseWait = driver.find_element(By.XPATH, '//*[@id="load_data_message"]/span').text;
        

        allCars  = driver.find_element(By.XPATH, '//*[@id="load_data"]');
        gridCars = allCars.find_elements(By.CLASS_NAME, "vehicle-grid");

        carUrls = [];
        for index in range(1, len(gridCars) + 1):   
            carUrl = driver.find_element(By.XPATH, '//*[@id="load_data"]/div[{}]/div/div/div[2]/div/div[1]/a'.format(index)).get_attribute('href');
            carUrls.append(carUrl);

        outputFolderName = "output";
        if not os.path.exists(outputFolderName):
            os.makedirs(outputFolderName)

        current_date = datetime.datetime.now().strftime("%Y.%m.%d");
        outputCsvFile = f"./{outputFolderName}/feed_dealerid_{dealerID}_{current_date}.csv";
        
        print("\n\nNumber of vehicles : " + str(len(carUrls)));
        # Sava new data in output file
        with open(outputCsvFile, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile);
            csv_writer.writerow(csvFileHeader);

            nb = 1;
            print('----------------------------------------');
            for urlCar in carUrls:
                print(str(nb) + ' - Add a new vehicle');
                row = getDetailsOfVehicle(driver, urlCar);
                csv_writer.writerow(row);
                print("The vehicle has been added successfully.");
                print('----------------------------------------');
                if(nb == len(gridCars)):
                    break;
                nb = nb + 1;

        driver.quit();
        print("Scraping finish successfully at ["+ str(datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S')) +"].");
    
    except Exception as error:
        print(error);
