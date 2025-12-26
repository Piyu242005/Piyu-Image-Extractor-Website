from flask import Flask, render_template, request, jsonify, send_file, Response
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import io
import zipfile
import os
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Standard browser user-agent to avoid 403s on some sites
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
}

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

import base64

def get_image_details(img_url):
    """
    Head request to get image size and type without downloading the whole thing initially.
    """
    if img_url.startswith('data:'):
        try:
           header, encoded = img_url.split(',', 1)
           data = base64.b64decode(encoded)
           content_type = header.split(':')[1].split(';')[0]
           return {
               'url': img_url,
               'type': content_type.split('/')[-1],
               'size': len(data),
               'status': 200
           }
        except:
           return None

    try:
        r = requests.head(img_url, headers=HEADERS, timeout=5)
        if r.status_code != 200:
            # Fallback to GET if HEAD is forbidden or fails
            r = requests.get(img_url, headers=HEADERS, stream=True, timeout=5)
            r.close() # Close connection immediately after headers
        
        content_type = r.headers.get('Content-Type', '')
        content_length = r.headers.get('Content-Length', 0)
        
        if not content_type.startswith('image'):
            return None
            
        return {
            'url': img_url,
            'type': content_type.split('/')[-1], # e.g., jpeg, png
            'size': int(content_length) if content_length else 0,
            'status': r.status_code
        }
    except:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/extract', methods=['POST'])
def extract_images():
    data = request.json
    target_url = data.get('url')
    
    if not target_url:
        return jsonify({'error': 'No URL provided'}), 400
        
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url

    try:
        response = requests.get(target_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        images = []
        
        # Find all image tags
        for img in soup.find_all('img'):
            src = img.get('src')
            if not src:
                src = img.get('data-src') # Lazy loading support common pattern
            
            if src:
                if src.startswith('data:'):
                    full_url = src
                else:
                    # Resolve relative URLs
                    full_url = urljoin(target_url, src)
                    # Basic cleanup
                    full_url = full_url.split('?')[0]
                
                if full_url not in [i['url'] for i in images]:
                    images.append({'url': full_url})

        # Also look for CSS background images or meta tags (og:image)
        for meta in soup.find_all('meta', property='og:image'):
            img_url = meta.get('content')
            if img_url:
                full_url = urljoin(target_url, img_url)
                if full_url not in [i['url'] for i in images]:
                    images.append({'url': full_url})
                    
        return jsonify({
            'success': True,
            'url': target_url,
            'images': images,
            'count': len(images)
        })

    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/proxy-image')
def proxy_image():
    """
    Proxy image requests to avoid CORS issues on the frontend.
    Handles both remote URLs and Data URIs.
    """
    url = request.args.get('url')
    if not url:
        return "Missing URL", 400
    
    if url.startswith('data:'):
        try:
            header, encoded = url.split(',', 1)
            data = base64.b64decode(encoded)
            mimetype = header.split(':')[1].split(';')[0]
            return Response(data, mimetype=mimetype)
        except Exception as e:
             return f"Error decoding base64: {e}", 400

    try:
        r = requests.get(url, headers=HEADERS, stream=True, timeout=10)
        return Response(r.iter_content(chunk_size=1024), content_type=r.headers.get('Content-Type'))
    except:
        return "Error fetching image", 404

@app.route('/download-zip', methods=['POST'])
def download_zip():
    data = request.json
    image_urls = data.get('images', [])
    
    if not image_urls:
         return jsonify({'error': 'No images selected'}), 400

    # In-memory ZIP creation
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Separate data URIs from remote URLs
        remote_urls = [u for u in image_urls if not u.startswith('data:')]
        data_uris = [u for u in image_urls if u.startswith('data:')]

        # Process Remote URLs
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(requests.get, url, headers=HEADERS, timeout=10): url for url in remote_urls}
            
            for i, future in enumerate(future_to_url):
                url = future_to_url[future]
                try:
                    r = future.result()
                    if r.status_code == 200:
                        parsed = urlparse(url)
                        filename = os.path.basename(parsed.path)
                        if not filename: filename = f"image_{i+1}"
                        
                        _, ext = os.path.splitext(filename)
                        if not ext:
                            content_type = r.headers.get('Content-Type', '')
                            if 'jpeg' in content_type: ext = '.jpg'
                            elif 'png' in content_type: ext = '.png'
                            elif 'webp' in content_type: ext = '.webp'
                            else: ext = '.bin'
                            filename += ext
                        
                        filename = f"remote_{i}_{filename}"
                        zip_file.writestr(filename, r.content)
                except Exception as e:
                    print(f"Failed to download {url}: {e}")
                    continue
        
        # Process Data URIs
        for i, uri in enumerate(data_uris):
            try:
                header, encoded = uri.split(',', 1)
                data = base64.b64decode(encoded)
                
                # Guess extension
                mime = header.split(':')[1].split(';')[0]
                ext = '.bin'
                if 'jpeg' in mime: ext = '.jpg'
                elif 'png' in mime: ext = '.png'
                elif 'webp' in mime: ext = '.webp'
                elif 'svg' in mime: ext = '.svg'
                
                filename = f"embedded_{i}{ext}"
                zip_file.writestr(filename, data)
            except Exception as e:
                print(f"Failed to process data URI: {e}")

    zip_buffer.seek(0)
    
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='extracted_images.zip'
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)
