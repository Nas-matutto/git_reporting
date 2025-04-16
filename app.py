from flask import Flask, render_template, request, redirect, session, jsonify, url_for
import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
from flask_cors import CORS

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS
app.secret_key = os.urandom(24)  # For session management

# Calendly API constants
CALENDLY_CLIENT_ID = os.getenv('CALENDLY_CLIENT_ID')
CALENDLY_CLIENT_SECRET = os.getenv('CALENDLY_CLIENT_SECRET')
CALENDLY_REDIRECT_URI = os.getenv('CALENDLY_REDIRECT_URI')
CALENDLY_AUTH_URL = 'https://auth.calendly.com/oauth/authorize'
CALENDLY_TOKEN_URL = 'https://auth.calendly.com/oauth/token'
CALENDLY_API_BASE = os.getenv('CALENDLY_API_BASE', 'https://api.calendly.com')

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/login')
def login():
    """Redirect to Calendly for OAuth authentication."""
    auth_params = {
        'client_id': CALENDLY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': CALENDLY_REDIRECT_URI
    }
    
    auth_url = f"{CALENDLY_AUTH_URL}?{'&'.join([f'{k}={v}' for k, v in auth_params.items()])}"
    return redirect(auth_url)

@app.route('/oauth/callback')
def oauth_callback():
    """Handle the OAuth callback from Calendly."""
    code = request.args.get('code')
    
    if not code:
        return "Authentication failed", 400
    
    # Exchange code for access token
    token_data = {
        'client_id': CALENDLY_CLIENT_ID,
        'client_secret': CALENDLY_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': CALENDLY_REDIRECT_URI
    }
    
    response = requests.post(CALENDLY_TOKEN_URL, data=token_data)
    
    if response.status_code != 200:
        return f"Failed to get access token: {response.text}", 400
    
    # Save tokens in session
    tokens = response.json()
    session['access_token'] = tokens.get('access_token')
    session['refresh_token'] = tokens.get('refresh_token')
    session['expires_at'] = datetime.now().timestamp() + tokens.get('expires_in', 3600)
    
    # Get user info and store organization URI
    user_response = requests.get(
    f"{CALENDLY_API_BASE}/users/me", 
    headers={'Authorization': f'Bearer {tokens.get("access_token")}'}
    )
    if user_response.status_code == 200:
        user_data = user_response.json()
        session['organization_uri'] = user_data['resource']['current_organization']

    return redirect('/')

@app.route('/api/check-availability', methods=['POST'])
def check_availability():
    """Check availability across multiple Calendly links."""
    if not session.get('access_token'):
        return jsonify({'error': 'Not authenticated with Calendly'}), 401
    
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    calendly_links = data.get('links', [])
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    
    if not calendly_links or not start_date or not end_date:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # Process the links to extract usernames and event types
    processed_links = []
    for link in calendly_links:
        parts = link.strip('/').split('/')
        if len(parts) < 5 or 'calendly.com' not in link:  # Make sure it's a valid Calendly URL
            continue
        
        # For a URL like https://calendly.com/username/30min
        # parts will be ['https:', '', 'calendly.com', 'username', '30min']
        username = parts[3]  # Typically the 4th part of the URL
        event_type = parts[4]  # Typically the 5th part
        
        processed_links.append({
            'username': username,
            'event_type': event_type
        })
    
    if not processed_links:
        return jsonify({'error': 'No valid Calendly links provided'}), 400
    
    # Find common availability
    try:
        common_availability = find_common_availability(processed_links, start_date, end_date)
        return jsonify(common_availability)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def find_common_availability(links, start_date, end_date):
    """Find common availability across multiple Calendly links."""
    print(f"Finding availability for {len(links)} links from {start_date} to {end_date}")
    
    # Convert date strings to datetime objects
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    # Headers for API requests
    headers = {
        'Authorization': f'Bearer {session["access_token"]}',
        'Content-Type': 'application/json'
    }
    
    all_availabilities = {}
    
    # For each link, fetch availability
    for link_data in links:
        username = link_data['username']
        event_type_slug = link_data['event_type']
        
        print(f"Processing link for {username}/{event_type_slug}")
        
        try:
            # First, we need to find the correct event type URI
            # This requires getting the user's UUID from their username
            
            # 1. Search for user by username (this endpoint may vary based on Calendly API)
            user_search_url = f"{CALENDLY_API_BASE}/users"
            # Note: Calendly API doesn't directly support looking up users by username
            # You may need to use a different approach or endpoint
            
            # For demonstration purposes, we'll query the event_types directory
            # You'll need to adjust this based on Calendly's API capabilities
            
            # 2. Get event types for the user
            event_types_url = f"{CALENDLY_API_BASE}/scheduled_events"
            params = {
                'user': username,
                'event_type': event_type_slug
            }
            
            # This is a simplified approach - in reality, you might need to
            # use a different approach to find the specific event type
            
            # Fetch available times for each day in the range
            current_date = start
            while current_date <= end:
                next_date = current_date + timedelta(days=1)
                date_key = current_date.date().isoformat()
                
                print(f"Checking availability for {username}/{event_type_slug} on {date_key}")
                
                # Use the Calendly API to get available times
                # The exact endpoint and parameters depend on Calendly's API
                available_times_url = f"{CALENDLY_API_BASE}/event_types/{username}/{event_type_slug}/available_times"
                params = {
                    'start_time': current_date.isoformat(),
                    'end_time': next_date.isoformat(),
                    'timezone': 'UTC'  # You may want to make this configurable
                }
                
                available_times_response = requests.get(
                    available_times_url,
                    params=params,
                    headers=headers
                )
                
                if available_times_response.status_code == 200:
                    availability_data = available_times_response.json()
                    available_times = availability_data.get('available_times', [])
                    
                    if date_key not in all_availabilities:
                        all_availabilities[date_key] = {}
                    
                    for slot in available_times:
                        # Adjust this based on the actual response structure
                        slot_time = slot.get('start_time') or slot.get('time')
                        
                        if slot_time not in all_availabilities[date_key]:
                            all_availabilities[date_key][slot_time] = 0
                        all_availabilities[date_key][slot_time] += 1
                else:
                    print(f"Failed to get available times: {available_times_response.status_code} - {available_times_response.text}")
                
                current_date = next_date
                
        except Exception as e:
            print(f"Error processing link: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Find slots available in all calendars
    print("Finding common availability...")
    common_slots = {}
    for date, slots in all_availabilities.items():
        common_for_date = []
        for slot_time, count in slots.items():
            if count == len(links):  # Available in all calendars
                common_for_date.append(slot_time)
        
        if common_for_date:
            common_slots[date] = sorted(common_for_date)
    
    print(f"Found common slots for {len(common_slots)} dates")
    return common_slots
    

# checking calendly authentication status
@app.route('/auth-status')
def auth_status():
    """Check and display authentication status."""
    if 'access_token' not in session:
        return jsonify({'authenticated': False, 'message': 'Not authenticated'})
    
    # Test the token with a simple API call
    headers = {
        'Authorization': f'Bearer {session["access_token"]}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{CALENDLY_API_BASE}/users/me", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            return jsonify({
                'authenticated': True,
                'user': user_data['resource']['name'],
                'email': user_data['resource']['email'],
                'token_expires_at': session.get('expires_at')
            })
        else:
            return jsonify({
                'authenticated': False,
                'error': f"API Error: {response.status_code}",
                'details': response.text
            })
    except Exception as e:
        return jsonify({
            'authenticated': False,
            'error': f"Exception: {str(e)}"
        })