import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import argparse
from typing import List, Set
import re

class SitemapGenerator:
    def __init__(self, base_url: str, max_pages: int = 50, ignore_urls: List[str] = None):
        """
        Initialize SitemapGenerator with base URL and maximum pages to crawl
        
        :param base_url: Starting URL to generate sitemap for
        :param max_pages: Maximum number of unique pages to include in sitemap
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.visited_urls: Set[str] = set()
        self.ignore_urls = set(ignore_urls) if ignore_urls else set()
        self.domain = urlparse(base_url).netloc

    def is_valid_url(self, url: str) -> bool:
        """
        Validate if a URL should be included in the sitemap
        
        :param url: URL to validate
        :return: Boolean indicating if URL is valid
        """
        parsed = urlparse(url)
        return (
            parsed.netloc == self.domain and
            parsed.scheme in ['http', 'https'] and
            not self._is_file_url(url) and
            url not in self.visited_urls and
            url not in self.ignore_urls and
            len(self.visited_urls) < self.max_pages
        )

    def _is_file_url(self, url: str) -> bool:
        """
        Check if URL points to a file that should be excluded
        
        :param url: URL to check
        :return: Boolean indicating if URL is a file
        """
        file_extensions = [
            '.pdf', '.jpg', '.jpeg', '.png', '.gif', 
            '.zip', '.csv', '.docx', '.xlsx', '.txt'
        ]
        return any(url.lower().endswith(ext) for ext in file_extensions)

    def crawl_urls(self) -> List[str]:
        """
        Crawl website and collect valid URLs
        
        :return: List of discovered URLs
        """
        urls_to_crawl = [self.base_url]
        
        while urls_to_crawl and len(self.visited_urls) < self.max_pages:
            current_url = urls_to_crawl.pop(0)
            
            if current_url in self.visited_urls:
                continue
            
            try:
                response = requests.get(current_url, timeout=5)
                
                if response.status_code == 200:
                    self.visited_urls.add(current_url)
                    print(f"Visited: {current_url}")
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    for link in soup.find_all('a', href=True):
                        absolute_url = urljoin(current_url, link['href'])
                        
                        if self.is_valid_url(absolute_url):
                            urls_to_crawl.append(absolute_url)
                
            except requests.RequestException:
                print(f"Could not fetch {current_url}")
        
        return list(self.visited_urls)

    def generate_sitemap(self, output_file: str = 'sitemap.xml') -> None:
        """
        Generate XML sitemap
        
        :param output_file: Path to save sitemap XML
        """
        urls = self.crawl_urls()
        
        # Create XML
        root = ET.Element('urlset', xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        
        for url in urls:
            url_elem = ET.SubElement(root, 'url')
            ET.SubElement(url_elem, 'loc').text = url
        
        # Create a prettified XML string
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        
        print(f"Sitemap generated: {output_file}")
        print(f"Total URLs discovered: {len(urls)}")

def main():
    parser = argparse.ArgumentParser(description='Generate XML Sitemap for a website')
    parser.add_argument('url', help='Base URL of the website')
    parser.add_argument('-m', '--max-pages', type=int, default=50, 
                        help='Maximum number of pages to crawl (default: 50)')
    parser.add_argument('-o', '--output', default='sitemap.xml', 
                        help='Output XML file name (default: sitemap.xml)')
    parser.add_argument('-i', '--ignore', nargs='*', default=[],
                        help='List of URLs to ignore')
    
    args = parser.parse_args()
    
    try:
        sitemap_gen = SitemapGenerator(args.url, args.max_pages, args.ignore)
        sitemap_gen.generate_sitemap(args.output)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()