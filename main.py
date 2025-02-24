import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
from urllib.parse import urljoin
import mimetypes
import re

class WebpageCloner:
    def __init__(self, url, output_dir):
        self.url = url
        self.output_dir = output_dir
        self.base_url = '/'.join(url.split('/')[:3])
        self.domain = urllib.parse.urlparse(url).netloc
        self.downloaded_files = {}  # Changed from set to dictionary
        
    def download_asset(self, url, directory):
        """Download an asset and return its local path"""
        if not url or url.startswith('data:'):
            return url
            
        # Convert relative URLs to absolute
        if not url.startswith(('http://', 'https://')):
            url = urljoin(self.base_url, url)
            
        # Skip if already downloaded
        if url in self.downloaded_files:
            return self.downloaded_files[url]
            
        try:
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                return url
                
            # Determine filename
            content_type = response.headers.get('content-type', '')
            extension = mimetypes.guess_extension(content_type) or '.txt'
            filename = re.sub(r'[^\w\-_.]', '_', url.split('/')[-1])
            if not os.path.splitext(filename)[1]:
                filename += extension
                
            # Create directory if it doesn't exist
            os.makedirs(os.path.join(self.output_dir, directory), exist_ok=True)
            local_path = os.path.join(directory, filename)
            full_path = os.path.join(self.output_dir, local_path)
            
            # Save the file
            with open(full_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        
            # Store the mapping of URL to local path
            self.downloaded_files[url] = local_path
            return local_path
            
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return url
            
    def process_html(self, soup):
        """Process HTML and download all assets"""
        # Handle images
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                local_path = self.download_asset(src, 'images')
                img['src'] = local_path
                
        # Handle CSS files
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                local_path = self.download_asset(href, 'css')
                link['href'] = local_path
                
        # Handle JavaScript files
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                local_path = self.download_asset(src, 'js')
                script['src'] = local_path
                
        # Handle inline CSS with url()
        for style in soup.find_all('style'):
            if style.string:
                style.string = re.sub(
                    r'url\(["\']?([^)"\']+)["\']?\)',
                    lambda m: f'url({self.download_asset(m.group(1), "assets")})',
                    style.string
                )
                
        return soup
        
    def clone(self):
        """Main method to clone the webpage"""
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Download main page
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Process and download all assets
        processed_soup = self.process_html(soup)
        
        # Save the final HTML
        with open(os.path.join(self.output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(str(processed_soup))
            
        print(f"Website cloned successfully to {self.output_dir}")

# Example usage
if __name__ == "__main__":
    url = "https://example.com/"
    output_dir = "cloned_website"
    
    cloner = WebpageCloner(url, output_dir)
    cloner.clone()