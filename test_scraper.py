import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import urljoin

# Website URL
base_url = "https://www.bbeox.com"

# Create a session
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

def get_product_details(product_url):
    """Extract detailed product information with more specific selectors"""
    try:
        response = session.get(product_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Initialize product info
        product_info = {
            'product_url': product_url,
            'name': '',
            'price': '',
            'description': '',
            'images': [],
            'variations': [],
            'sizes': []
        }
        
        # Extract product name - more specific approach
        # Look for the product name in the breadcrumb or title
        title_elem = soup.find('title')
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            # Remove common suffixes
            title_text = re.sub(r'\s*\|.*$', '', title_text)
            title_text = re.sub(r'\s*-.*Bbeox.*$', '', title_text)
            product_info['name'] = title_text.strip()
        
        # If we couldn't get name from title, try other methods
        if not product_info['name']:
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
                if name_elem and name_elem.get_text(strip=True):
                    product_info['name'] = name_elem.get_text(strip=True)
                    break
        
        # Extract price - look for specific patterns
        # Try to find price in text content
        page_text = soup.get_text()
        price_patterns = [
            r'Fiyat\s*:?\s*[₺$€£¥]?\s*([\d.,]+)',
            r'₺\s*([\d.,]+)',
            r'[\d.,]+\s*₺',
            r'Price\s*:?\s*[₺$€£¥]?\s*([\d.,]+)'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                # Take the first match that looks like a reasonable price
                for match in matches:
                    price_value = re.sub(r'[^\d,.]', '', match)
                    # Handle Turkish number format (1.000,00)
                    if '.' in price_value and ',' in price_value:
                        # If both . and , exist, assume . is thousands separator
                        price_value = price_value.replace('.', '').replace(',', '.')
                    elif ',' in price_value:
                        # If only comma, assume it's decimal separator
                        price_value = price_value.replace(',', '.')
                    
                    try:
                        if float(price_value) > 10:
                            product_info['price'] = f"₺{match}"
                            break
                    except ValueError:
                        continue
                if product_info['price']:
                    break
        
        # If still no price, try specific elements
        if not product_info['price']:
            price_selectors = [
                '.price',
                '.product-price',
                '.price-current',
                '[class*="price"]',
                '.price-wrapper',
                '.urunFiyat',
                '.product-info .price'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem and price_elem.get_text(strip=True):
                    price_text = price_elem.get_text(strip=True)
                    # Clean up price text
                    price_text = re.sub(r'[^\d,₺$€£¥.]', '', price_text)
                    if price_text:
                        product_info['price'] = price_text
                        break
        
        # Extract description - look for product details
        desc_selectors = [
            '.product-description',
            '.description',
            '[class*="description"]',
            '.product-details',
            '.product-info .description',
            '.urunAciklama',
            '.product-detail'
        ]
        
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem and desc_elem.get_text(strip=True):
                desc_text = desc_elem.get_text(strip=True)
                if len(desc_text) > 20:  # Only consider substantial descriptions
                    product_info['description'] = desc_text
                    break
        
        # If no description found, try to get text from the main content area
        if not product_info['description']:
            content_area = soup.select_one('.content, .main-content, .product-content')
            if content_area:
                desc_text = content_area.get_text(strip=True)
                if len(desc_text) > 50:
                    product_info['description'] = desc_text
        
        # Extract images - try to get actual product images
        # Look for data attributes that might contain real image URLs
        img_elements = soup.find_all('img')
        for img in img_elements:
            # Try multiple attributes
            src_attrs = ['data-src', 'data-lazy', 'data-original', 'src']
            for attr in src_attrs:
                src = img.get(attr)
                if src:
                    src_str = str(src)  # Convert to string
                    if 'blank' not in src_str.lower() and 'placeholder' not in src_str.lower():
                        # Check if it looks like a real product image
                        if any(keyword in src_str.lower() for keyword in ['product', 'urun', 'upload', 'image']):
                            full_img_url = urljoin(product_url, src_str)
                            if full_img_url not in product_info['images']:
                                product_info['images'].append(full_img_url)
                                break  # Move to next image element
        
        # Extract sizes - look for size options
        # Updated to better detect size information from the specific HTML structure
        size_selectors = [
            'select[name*="size"]',
            'select[name*="beden"]',
            '.size-options',
            '.sizes',
            '[class*="size"]',
            '.size-selector',
            '[data-option*="size"]',
            '.bedenSecenekleri',
            '.beden',
            '[class*="beden"]',
            '#divUrunEkSecenek'  # Specific selector for the HTML structure you provided
        ]
        
        for selector in size_selectors:
            size_elements = soup.select(selector)
            for elem in size_elements:
                # Special handling for the specific HTML structure you provided
                if elem.get('id') == 'divUrunEkSecenek':
                    # Look for "Beden" label
                    beden_labels = elem.find_all(string=re.compile(r'Beden', re.I))
                    for label in beden_labels:
                        # Find the parent element and then look for size boxes
                        parent = label.parent
                        if parent:
                            # Look for size_box elements in the same container
                            size_boxes = parent.find_next_sibling().find_all(class_='size_box') if parent.find_next_sibling() else []
                            for box in size_boxes:
                                size_text = box.get_text(strip=True)
                                # Remove "GELİNCE HABERİN OLSUN" text if present
                                size_text = re.sub(r'GELİNCE HABERİN.*', '', size_text).strip()
                                if size_text and size_text not in ['Seçiniz', 'Select', 'Choose', ''] and size_text not in product_info['sizes']:
                                    # Filter to only include valid size values
                                    size_keywords = ['xs', 's', 'm', 'l', 'xl', 'xxl', '32', '34', '36', '38', '40', '42', '44', '46', '48', '50', '52', '54', '56', '58', '60']
                                    if any(keyword in size_text.lower() for keyword in size_keywords) or re.match(r'^\d+$', size_text):
                                        product_info['sizes'].append(size_text)
                elif elem.name == 'select':
                    options = elem.find_all('option')
                    for option in options:
                        value = option.get_text(strip=True)
                        if value and value not in ['Seçiniz', 'Select', 'Choose', ''] and value not in product_info['sizes']:
                            # Filter out non-size values
                            size_keywords = ['xs', 's', 'm', 'l', 'xl', 'xxl', '32', '34', '36', '38', '40', '42', '44', '46', '48', '50', '52', '54', '56', '58', '60']
                            if any(keyword in value.lower() for keyword in size_keywords) or re.match(r'^\d+$', value):
                                product_info['sizes'].append(value)
                else:
                    # For divs with size options
                    buttons = elem.find_all(['button', 'a', 'div', 'span'], class_=lambda x: x and 'size' in x.lower())
                    for button in buttons:
                        text = button.get_text(strip=True)
                        # Remove "GELİNCE HABERİN OLSUN" text if present
                        text = re.sub(r'GELİNCE HABERİN.*', '', text).strip()
                        if text and text not in ['Seçiniz', 'Select', 'Choose', ''] and text not in product_info['sizes']:
                            # Filter out non-size values
                            size_keywords = ['xs', 's', 'm', 'l', 'xl', 'xxl', '32', '34', '36', '38', '40', '42', '44', '46', '48', '50', '52', '54', '56', '58', '60']
                            if any(keyword in text.lower() for keyword in size_keywords) or re.match(r'^\d+$', text):
                                product_info['sizes'].append(text)
        
        # If no sizes found, try to extract from text content
        if not product_info['sizes']:
            # Look for size information in the page text
            size_patterns = [
                r'[Bb]eden\s*:\s*([A-Z0-9]+)',
                r'[Ss]ize\s*:\s*([A-Z0-9]+)',
                r'(XS|S|M|L|XL|XXL|32|34|36|38|40|42|44|46|48|50|52|54|56|58|60)'
            ]
            
            for pattern in size_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    if match and match not in product_info['sizes']:
                        product_info['sizes'].append(match)
        
        # Extract variations (color, style, etc.)
        variation_selectors = [
            'select[name*="color"]',
            'select[name*="renk"]',
            '.color-options',
            '.variations',
            '[class*="variation"]',
            '.color-selector',
            '[data-option*="color"]',
            '.renkSecenekleri'
        ]
        
        for selector in variation_selectors:
            var_elements = soup.select(selector)
            for elem in var_elements:
                # Special handling for the specific HTML structure you provided
                if elem.get('id') == 'divUrunEkSecenek':
                    # Look for "Renk" label
                    renk_labels = elem.find_all(string=re.compile(r'Renk', re.I))
                    for label in renk_labels:
                        # Find the parent element and then look for color boxes
                        parent = label.parent
                        if parent:
                            # Look for size_box elements in the same container
                            color_boxes = parent.find_next_sibling().find_all(class_='size_box') if parent.find_next_sibling() else []
                            for box in color_boxes:
                                color_text = box.get_text(strip=True)
                                if color_text and color_text not in ['Seçiniz', 'Select', 'Choose', ''] and color_text not in product_info['variations']:
                                    product_info['variations'].append(color_text)
                elif elem.name == 'select':
                    options = elem.find_all('option')
                    for option in options:
                        value = option.get_text(strip=True)
                        if value and value not in ['Seçiniz', 'Select', 'Choose', ''] and value not in product_info['variations']:
                            product_info['variations'].append(value)
                else:
                    # For divs with variation options
                    buttons = elem.find_all(['button', 'a', 'div', 'span'])
                    for button in buttons:
                        text = button.get_text(strip=True)
                        if text and text not in ['Seçiniz', 'Select', 'Choose', ''] and text not in product_info['variations']:
                            product_info['variations'].append(text)
        
        return product_info
    except Exception as e:
        print(f"Error extracting product details from {product_url}: {e}")
        return None

def save_to_csv(products_data, filename='test_product.csv'):
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
    # Test with the specific product URL you provided
    test_url = "https://www.bbeox.com/kemerli-vatka-detay-elbise-acikkahve"
    
    print("Testing scraper with specific product...")
    product_info = get_product_details(test_url)
    
    if product_info:
        print(f"Product Name: {product_info['name']}")
        print(f"Price: {product_info['price']}")
        print(f"Sizes: {product_info['sizes']}")
        print(f"Variations: {product_info['variations']}")
        print(f"Images: {len(product_info['images'])} images found")
        
        # Save to CSV
        filename = save_to_csv([product_info], 'test_product.csv')
        print(f"Test data saved to {filename}")
    else:
        print("Failed to extract product information")

if __name__ == "__main__":
    main()