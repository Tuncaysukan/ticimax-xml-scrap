import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin
import os

def setup_driver():
    """Setup Chrome driver with options"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Setup the driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def get_product_links_selenium(driver, base_url):
    """Get all product links using Selenium"""
    try:
        driver.get(base_url)
        time.sleep(5)  # Wait for page to load
        
        # Scroll to load all products (if there's infinite scroll)
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Find product links
        product_links = []
        links = driver.find_elements(By.TAG_NAME, "a")
        
        for link in links:
            try:
                href = link.get_attribute("href")
                if href and any(keyword in href.lower() for keyword in ["/product/", "/urun/", "/p/"]):
                    if href not in product_links:
                        product_links.append(href)
            except:
                continue
                
        return product_links
    except Exception as e:
        print(f"Error getting product links with Selenium: {e}")
        return []

def extract_product_info_selenium(driver, product_url):
    """Extract product information using Selenium"""
    try:
        driver.get(product_url)
        time.sleep(3)  # Wait for page to load
        
        product_info = {
            'product_url': product_url,
            'name': '',
            'price': '',
            'description': '',
            'images': [],
            'variations': [],
            'sizes': []
        }
        
        # Get product name
        try:
            name_element = driver.find_element(By.TAG_NAME, "h1")
            product_info['name'] = name_element.text.strip()
        except:
            pass
        
        # Get price
        try:
            price_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='price'], [class*='Price']")
            for elem in price_elements:
                price_text = elem.text.strip()
                if price_text and any(char.isdigit() for char in price_text):
                    product_info['price'] = price_text
                    break
        except:
            pass
        
        # Get description
        try:
            desc_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='description'], [class*='Description']")
            for elem in desc_elements:
                desc_text = elem.text.strip()
                if desc_text and len(desc_text) > 20:  # Assume description is longer than 20 chars
                    product_info['description'] = desc_text
                    break
        except:
            pass
        
        # Get images
        try:
            # Main product image
            img_elements = driver.find_elements(By.CSS_SELECTOR, "img")
            for img in img_elements:
                src = img.get_attribute("src") or img.get_attribute("data-src")
                if src and "product" in src.lower() and "blank" not in src.lower():
                    if src not in product_info['images']:
                        product_info['images'].append(src)
        except:
            pass
        
        # Get size options
        try:
            size_elements = driver.find_elements(By.CSS_SELECTOR, 
                "select[name*='size'], select[name*='beden'], [class*='size'], [class*='Size']")
            for elem in size_elements:
                if elem.tag_name == "select":
                    options = elem.find_elements(By.TAG_NAME, "option")
                    for option in options:
                        value = option.text.strip()
                        if value and value not in ["Seçiniz", "Select", "Choose"] and value not in product_info['sizes']:
                            product_info['sizes'].append(value)
                else:
                    # For divs with size options
                    buttons = elem.find_elements(By.CSS_SELECTOR, 
                        "button, a, div, span")
                    for button in buttons:
                        text = button.text.strip()
                        if text and text not in ["Seçiniz", "Select", "Choose"] and text not in product_info['sizes']:
                            product_info['sizes'].append(text)
        except:
            pass
        
        # Get variations (color, etc.)
        try:
            var_elements = driver.find_elements(By.CSS_SELECTOR, 
                "select[name*='color'], select[name*='renk'], [class*='color'], [class*='Color']")
            for elem in var_elements:
                if elem.tag_name == "select":
                    options = elem.find_elements(By.TAG_NAME, "option")
                    for option in options:
                        value = option.text.strip()
                        if value and value not in ["Seçiniz", "Select", "Choose"] and value not in product_info['variations']:
                            product_info['variations'].append(value)
                else:
                    # For divs with variation options
                    buttons = elem.find_elements(By.CSS_SELECTOR, 
                        "button, a, div, span")
                    for button in buttons:
                        text = button.text.strip()
                        if text and text not in ["Seçiniz", "Select", "Choose"] and text not in product_info['variations']:
                            product_info['variations'].append(text)
        except:
            pass
        
        return product_info
    except Exception as e:
        print(f"Error extracting product info from {product_url}: {e}")
        return None

def save_to_csv(products_data, filename='bbeox_products_detailed.csv'):
    """Save product data to CSV file"""
    # Flatten the data for CSV
    csv_data = []
    for product in products_data:
        if product:
            # Create a row for each product
            row = {
                'Product URL': product.get('product_url', ''),
                'Product Name': product.get('name', ''),
                'Price': product.get('price', ''),
                'Description': product.get('description', ''),
                'Images': '; '.join(product.get('images', [])),
                'Variations': '; '.join(product.get('variations', [])),
                'Sizes': '; '.join(product.get('sizes', []))
            }
            csv_data.append(row)
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(csv_data)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Data saved to {filename}")
    return filename

def main():
    base_url = "https://www.bbeox.com"
    
    print("Setting up Selenium driver...")
    driver = setup_driver()
    
    try:
        print("Getting product links...")
        product_links = get_product_links_selenium(driver, base_url)
        print(f"Found {len(product_links)} product links")
        
        # Limit for testing
        product_links = product_links[:10]  # Remove this line to scrape all products
        
        # Extract product information
        products_data = []
        for i, link in enumerate(product_links):
            print(f"Processing product {i+1}/{len(product_links)}: {link}")
            product_info = extract_product_info_selenium(driver, link)
            if product_info:
                products_data.append(product_info)
            time.sleep(2)  # Be respectful with requests
        
        # Save to CSV
        if products_data:
            filename = save_to_csv(products_data)
            print(f"Successfully scraped {len(products_data)} products and saved to {filename}")
        else:
            print("No product data was extracted")
    except Exception as e:
        print(f"Error in main process: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()