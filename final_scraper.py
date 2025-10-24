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

def get_all_product_urls():
    """Get all product URLs from the main page and category pages"""
    product_urls = set()
    
    try:
        # Get main page
        response = session.get(base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all links that might be product links
        links = soup.find_all('a', href=True)
        
        # Pattern to identify product URLs
        product_patterns = [
            r'/[^/]+-[^/]+-[^/]+$',  # URLs ending with three parts separated by dashes
            r'/urun/',
            r'/product/',
            r'/p/'
        ]
        
        for link in links:
            href = str(link['href'])  # Convert to string
            # Check if it's a relative URL starting with /
            if href.startswith('/'):
                # Check if it matches product patterns
                for pattern in product_patterns:
                    if re.search(pattern, href) and not href.endswith(('.jpg', '.png', '.gif', '.css', '.js')):
                        full_url = urljoin(base_url, href)
                        product_urls.add(full_url)
        
        print(f"Found {len(product_urls)} potential product URLs from main page")
        
        # Also check some category pages if needed
        category_selectors = [
            'a[href*="kategori"]',
            'a[href*="category"]',
            'a[href*="elbise"]',
            'a[href*="bluz"]',
            'a[href*="takim"]'
        ]
        
        for selector in category_selectors:
            category_links = soup.select(selector)
            for cat_link in category_links[:3]:  # Limit to first 3 categories
                try:
                    cat_href = str(cat_link['href'])  # Convert to string
                    if cat_href.startswith('/'):
                        cat_url = urljoin(base_url, cat_href)
                        print(f"Checking category: {cat_url}")
                        cat_response = session.get(cat_url)
                        cat_response.raise_for_status()
                        cat_soup = BeautifulSoup(cat_response.content, 'html.parser')
                        
                        cat_links = cat_soup.find_all('a', href=True)
                        for link in cat_links:
                            href = str(link['href'])  # Convert to string
                            for pattern in product_patterns:
                                if re.search(pattern, href) and not href.endswith(('.jpg', '.png', '.gif', '.css', '.js')):
                                    full_url = urljoin(base_url, href)
                                    product_urls.add(full_url)
                        time.sleep(1)  # Be respectful
                except Exception as e:
                    print(f"Error checking category: {e}")
                    continue
        
        return list(product_urls)
    except Exception as e:
        print(f"Error getting product URLs: {e}")
        return list(product_urls)

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
        size_selectors = [
            'select[name*="size"]',
            'select[name*="beden"]',
            '.size-options',
            '.sizes',
            '[class*="size"]',
            '.size-selector',
            '[data-option*="size"]',
            '.bedenSecenekleri'
        ]
        
        for selector in size_selectors:
            size_elements = soup.select(selector)
            for elem in size_elements:
                if elem.name == 'select':
                    options = elem.find_all('option')
                    for option in options:
                        value = option.get_text(strip=True)
                        if value and value not in ['Seçiniz', 'Select', 'Choose', ''] and value not in product_info['sizes']:
                            product_info['sizes'].append(value)
                else:
                    # For divs with size options
                    buttons = elem.find_all(['button', 'a', 'div', 'span'])
                    for button in buttons:
                        text = button.get_text(strip=True)
                        if text and text not in ['Seçiniz', 'Select', 'Choose', ''] and text not in product_info['sizes']:
                            product_info['sizes'].append(text)
        
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
                if elem.name == 'select':
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

def get_sample_products():
    """Get a sample of product URLs for testing"""
    # These are some actual product URLs we found earlier
    sample_urls = [
        "https://www.bbeox.com/kadife-gold-detay-elbise-siyah",
        "https://www.bbeox.com/kolsuz-balikci-yumos-triko-bordo",
        "https://www.bbeox.com/asimetrik-yaka-poliamid-bluz-kahverengi",
        "https://www.bbeox.com/gofre-halter-yaka-uzun-elbise-821",
        "https://www.bbeox.com/askili-pole-premium-elbise-809",
        "https://www.bbeox.com/interlok-hirka-tayt-takim-siyah",
        "https://www.bbeox.com/tek-serit-hirka-takim-lacivert",
        "https://www.bbeox.com/kemerli-vatka-detay-elbise-kahverengi",
        "https://www.bbeox.com/triko-bodysuit-sort-takim-kahverengi",
        "https://www.bbeox.com/kare-yaka-premium-crop-kahverengi"
    ]
    return sample_urls

def save_to_csv(products_data, filename='bbeox_all_products.csv'):
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
    print("Starting final scraping of bbeox.com...")
    
    # Get ALL product URLs instead of just sample ones
    print("Getting ALL product URLs...")
    product_urls = get_all_product_urls()
    print(f"Found {len(product_urls)} product URLs")
    
    # Limit to a reasonable number to avoid taking too long
    # Remove this limit if you want to scrape all products
    # product_urls = product_urls[:50]  # Process first 50 products
    
    # Extract product information
    products_data = []
    for i, url in enumerate(product_urls):
        print(f"Processing product {i+1}/{len(product_urls)}: {url}")
        product_info = get_product_details(url)
        if product_info:
            products_data.append(product_info)
        time.sleep(1)  # Be respectful with requests
    
    # Save to CSV
    if products_data:
        filename = save_to_csv(products_data)
        print(f"Successfully scraped {len(products_data)} products and saved to {filename}")
        
        # Display summary
        print("\nScraping Summary:")
        for product in products_data:
            if product:
                print(f"- {product.get('name', 'Unknown')}: {product.get('price', 'No price')}")
    else:
        print("No product data was extracted")

if __name__ == "__main__":
    main()