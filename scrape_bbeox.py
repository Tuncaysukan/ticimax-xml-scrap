import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from urllib.parse import urljoin, urlparse

# Website URL
base_url = "https://www.bbeox.com"

# Create a session
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

def get_product_links():
    """Get all product links from the website"""
    try:
        response = session.get(base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find product links - this selector might need adjustment based on site structure
        product_links = []
        # Look for common product link patterns
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            # Check for various product URL patterns
            if any(keyword in href.lower() for keyword in ['/product/', '/urun/', '/p/']):
                full_url = urljoin(base_url, href)
                if full_url not in product_links:
                    product_links.append(full_url)
            
            # Also check if the link text suggests it's a product
            text = link.get_text(strip=True).lower()
            if any(keyword in text for keyword in ['ürün', 'product', 'shop', 'ürünler']):
                full_url = urljoin(base_url, href)
                if full_url not in product_links:
                    product_links.append(full_url)
        
        # If still no links found, try to find category pages
        if not product_links:
            print("No direct product links found, looking for category pages...")
            category_links = []
            for link in links:
                href = link['href']
                text = link.get_text(strip=True).lower()
                if any(keyword in text for keyword in ['kategori', 'category', 'koleksiyon', 'collection']):
                    full_url = urljoin(base_url, href)
                    if full_url not in category_links:
                        category_links.append(full_url)
            
            # Try to get products from category pages
            for category_url in category_links[:3]:  # Limit to first 3 categories
                print(f"Checking category: {category_url}")
                try:
                    cat_response = session.get(category_url)
                    cat_response.raise_for_status()
                    cat_soup = BeautifulSoup(cat_response.content, 'html.parser')
                    
                    cat_links = cat_soup.find_all('a', href=True)
                    for link in cat_links:
                        href = link['href']
                        if any(keyword in href.lower() for keyword in ['/product/', '/urun/', '/p/']):
                            full_url = urljoin(base_url, href)
                            if full_url not in product_links:
                                product_links.append(full_url)
                except Exception as e:
                    print(f"Error checking category {category_url}: {e}")
                time.sleep(1)  # Be respectful with requests
        
        return product_links
    except Exception as e:
        print(f"Error getting product links: {e}")
        return []

def extract_product_info(product_url):
    """Extract product information from a product page"""
    try:
        response = session.get(product_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract product information - selectors will need adjustment based on actual site structure
        product_info = {
            'product_url': product_url,
            'name': '',
            'price': '',
            'description': '',
            'images': [],
            'variations': [],
            'sizes': []
        }
        
        # Product name (common selectors)
        name_selectors = [
            'h1.product-title',
            'h1.product_name',
            '.product-title',
            '.product-name',
            'h1',
            '[class*="product"] h1',
            '[class*="title"]'
        ]
        
        for selector in name_selectors:
            name_elem = soup.select_one(selector)
            if name_elem:
                product_info['name'] = name_elem.get_text(strip=True)
                if product_info['name']:  # If we found a name, break
                    break
        
        # Product price (common selectors)
        price_selectors = [
            '.price',
            '.product-price',
            '.price-current',
            '[class*="price"]',
            '.price-wrapper',
            '.product-info .price'
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                product_info['price'] = price_elem.get_text(strip=True)
                if product_info['price']:  # If we found a price, break
                    break
        
        # Product description (common selectors)
        desc_selectors = [
            '.product-description',
            '.description',
            '[class*="description"]',
            '.product-details',
            '.product-info .description'
        ]
        
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                product_info['description'] = desc_elem.get_text(strip=True)
                if product_info['description']:  # If we found a description, break
                    break
        
        # Product images (common selectors)
        image_selectors = [
            '.product-image img',
            '.product-img img',
            '.image img',
            'img[class*="product"]',
            '.product-gallery img',
            '.product-images img'
        ]
        
        for selector in image_selectors:
            img_elements = soup.select(selector)
            for img in img_elements:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy')
                if src:
                    full_img_url = urljoin(product_url, src)
                    if full_img_url not in product_info['images']:
                        product_info['images'].append(full_img_url)
        
        # If no images found, try to get any images
        if not product_info['images']:
            img_elements = soup.find_all('img')
            for img in img_elements:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy')
                if src and ('product' in src.lower() or 'image' in src.lower() or 'photo' in src.lower()):
                    full_img_url = urljoin(product_url, src)
                    if full_img_url not in product_info['images']:
                        product_info['images'].append(full_img_url)
        
        # Product variations and sizes would typically be in select dropdowns or buttons
        # Look for size options
        size_selectors = [
            'select[name*="size"]',
            'select[name*="beden"]',
            '.size-options',
            '.sizes',
            '[class*="size"]',
            '.size-selector',
            '[data-option*="size"]'
        ]
        
        for selector in size_selectors:
            size_elements = soup.select(selector)
            for elem in size_elements:
                if elem.name == 'select':
                    options = elem.find_all('option')
                    for option in options:
                        value = option.get_text(strip=True)
                        if value and value not in ['Seçiniz', 'Select', 'Choose'] and value not in product_info['sizes']:
                            product_info['sizes'].append(value)
                else:
                    # For divs with size options
                    buttons = elem.find_all(['button', 'a', 'div', 'span'], 
                                          class_=lambda x: x and ('size' in x or 'beden' in x.lower()))
                    for button in buttons:
                        text = button.get_text(strip=True)
                        if text and text not in ['Seçiniz', 'Select', 'Choose'] and text not in product_info['sizes']:
                            product_info['sizes'].append(text)
        
        # Look for variations (color, style, etc.)
        variation_selectors = [
            'select[name*="color"]',
            'select[name*="renk"]',
            '.color-options',
            '.variations',
            '[class*="variation"]',
            '.color-selector',
            '[data-option*="color"]'
        ]
        
        for selector in variation_selectors:
            var_elements = soup.select(selector)
            for elem in var_elements:
                if elem.name == 'select':
                    options = elem.find_all('option')
                    for option in options:
                        value = option.get_text(strip=True)
                        if value and value not in ['Seçiniz', 'Select', 'Choose'] and value not in product_info['variations']:
                            product_info['variations'].append(value)
                else:
                    # For divs with variation options
                    buttons = elem.find_all(['button', 'a', 'div', 'span'])
                    for button in buttons:
                        text = button.get_text(strip=True)
                        if text and text not in ['Seçiniz', 'Select', 'Choose'] and text not in product_info['variations']:
                            product_info['variations'].append(text)
        
        return product_info
    except Exception as e:
        print(f"Error extracting product info from {product_url}: {e}")
        return None

def save_to_csv(products_data, filename='bbeox_products.csv'):
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
    print("Starting to scrape bbeox.com...")
    
    # Get product links
    print("Getting product links...")
    product_links = get_product_links()
    print(f"Found {len(product_links)} product links")
    
    # Limit for testing - remove this limit to scrape all products
    # product_links = product_links[:10]  # Remove this line to scrape all products
    
    # Extract product information
    products_data = []
    for i, link in enumerate(product_links):
        print(f"Processing product {i+1}/{len(product_links)}: {link}")
        product_info = extract_product_info(link)
        if product_info:
            products_data.append(product_info)
        # Be respectful - add delay between requests
        time.sleep(1)
    
    # Save to CSV
    if products_data:
        filename = save_to_csv(products_data)
        print(f"Successfully scraped {len(products_data)} products and saved to {filename}")
    else:
        print("No product data was extracted")
        # Try a different approach - save what we have
        filename = save_to_csv(products_data)
        print(f"Saved empty dataset to {filename}")

if __name__ == "__main__":
    main()