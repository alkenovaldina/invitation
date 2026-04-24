import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import hashlib
import shutil

URL = "https://tilda.waqyru.kz/alfiya"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
}

def clean_tilda_url(url):
    # Remove /-/resize/20x/ or similar to always get the original image
    return re.sub(r'/-/resize/[0-9]+x/', '/', url)

def get_safe_filename(url, prefix='file', ext=''):
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    
    h = hashlib.md5(url.encode()).hexdigest()[:8]
    
    safe_name = "".join([c if c.isalnum() or c in ".-_" else "_" for c in filename])
    if not safe_name or safe_name == '_':
        safe_name = f"{prefix}_{h}{ext}"
    else:
        name, extension = os.path.splitext(safe_name)
        if not extension: extension = ext
        safe_name = f"{name}_{h}{extension}"
        
    return safe_name

def download_file(url, folder):
    if not url or url.startswith('data:') or url.startswith('#'):
        return url
        
    # Always fetch original resolution
    url = clean_tilda_url(url)
        
    safe_name = get_safe_filename(url)
    filepath = os.path.join(folder, safe_name)
    
    if not os.path.exists(filepath):
        print(f"Downloading {url} to {filepath}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(resp.content)
            else:
                print(f"  -> Failed: HTTP {resp.status_code}")
                return url
        except Exception as e:
            print(f"  -> Error: {e}")
            return url
            
    return f"{folder}/{safe_name}"

def download_css_and_parse(url, folder):
    if not url or url.startswith('data:'): return url
    
    safe_name = get_safe_filename(url, prefix='style', ext='.css')
    filepath = os.path.join(folder, safe_name)
    
    if not os.path.exists(filepath):
        print(f"Downloading CSS {url} to {filepath}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                css_content = resp.text
                
                # find all url()
                urls = re.findall(r'url\([\'"]?([^\'"\)]+)[\'"]?\)', css_content)
                for u in urls:
                    if u.startswith('data:'): continue
                    full_u = urljoin(url, u)
                    full_u = clean_tilda_url(full_u)
                    
                    subfolder = 'assets/fonts' if any(ext in u.lower() for ext in ['.woff', '.ttf', '.eot']) else 'assets/img'
                    
                    local_u = download_file(full_u, subfolder)
                    if local_u.startswith('assets/'):
                        rel_u = "../" + local_u[len('assets/'):]
                        css_content = css_content.replace(u, rel_u)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(css_content)
            else:
                return url
        except Exception as e:
            print(f"  -> CSS Error: {e}")
            return url
            
    return f"{folder}/{safe_name}"

def main():
    if os.path.exists('assets'):
        shutil.rmtree('assets')
        
    os.makedirs('assets/css', exist_ok=True)
    os.makedirs('assets/js', exist_ok=True)
    os.makedirs('assets/img', exist_ok=True)
    os.makedirs('assets/fonts', exist_ok=True)

    print("Fetching main HTML...")
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')

    for tag in soup.find_all('link', rel='stylesheet'):
        href = tag.get('href')
        if href:
            full_url = urljoin(URL, href)
            local_path = download_css_and_parse(full_url, 'assets/css')
            tag['href'] = local_path

    for tag in soup.find_all('script'):
        src = tag.get('src')
        if src:
            full_url = urljoin(URL, src)
            local_path = download_file(full_url, 'assets/js')
            tag['src'] = local_path

    for tag in soup.find_all(['img', 'source']):
        src = tag.get('src')
        if src:
            full_url = urljoin(URL, src)
            local_path = download_file(full_url, 'assets/img')
            tag['src'] = local_path
            
        data_original = tag.get('data-original')
        if data_original:
            full_url = urljoin(URL, data_original)
            local_path = download_file(full_url, 'assets/img')
            tag['data-original'] = local_path

    for tag in soup.find_all(style=True):
        style = tag['style']
        urls = re.findall(r'url\([\'"]?([^\'"\)]+)[\'"]?\)', style)
        for u in urls:
            if u.startswith('data:'): continue
            full_url = urljoin(URL, u)
            full_url = clean_tilda_url(full_url)
            local_path = download_file(full_url, 'assets/img')
            style = style.replace(u, local_path)
        tag['style'] = style

    # Remove the anti-bot script that might hide elements
    # It sets opacity to 0 and relies on sessionStorage to fade in
    anti_bot_script = soup.find('script', string=re.compile('visits'))
    if anti_bot_script:
        anti_bot_script.decompose()

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(str(soup))
        
    print("Scraping completed!")

if __name__ == '__main__':
    main()
