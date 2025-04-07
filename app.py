from flask import Flask, render_template, request, redirect, session, jsonify, url_for
import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

app = Flask(__name__)
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
    
    # For each link, extract username and event type
    processed_links = []
    for link in calendly_links:
        parts = link.strip('/').split('/')
        if len(parts) < 5:  # Not a valid Calendly URL format
            continue
        
        username = parts[3]  # Typically the 4th part of the URL
        event_type = parts[4]  # Typically the 5th part
        
        processed_links.append({
            'username': username,
            'event_type': event_type
        })
    
    # This is where we would make API calls to Calendly for each link
    # For now, this is a placeholder implementation
    
    # Process the availability results
    # This is a simplified example
    common_availability = find_common_availability(processed_links, start_date, end_date)
    
    return jsonify(common_availability)

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
    for i, link in enumerate(links):
        print(f"Processing link {i+1}/{len(links)}: {link}")
        
        try:
            # Get user info
            me_response = requests.get(
                f"{CALENDLY_API_BASE}/users/me",
                headers=headers
            )
            
            if me_response.status_code != 200:
                print(f"Failed to get user info: {me_response.status_code} - {me_response.text}")
                continue
                
            user_data = me_response.json()
            user_uri = user_data['resource']['uri']
            
            # Get event types
            print(f"Fetching event types for user: {user_uri}")
            event_types_response = requests.get(
                f"{CALENDLY_API_BASE}/event_types",
                params={'user': user_uri},
                headers=headers
            )
            
            if event_types_response.status_code != 200:
                print(f"Failed to get event types: {event_types_response.status_code} - {event_types_response.text}")
                continue
            
            event_types = event_types_response.json()['collection']
            print(f"Found {len(event_types)} event types")
            
            event_type_uri = None
            for event_type in event_types:
                print(f"Checking event type: {event_type['slug']} vs {link['event_type']}")
                if event_type['slug'] == link['event_type']:
                    event_type_uri = event_type['uri']
                    break
            
            if not event_type_uri:
                print(f"Could not find matching event type for: {link['event_type']}")
                continue
            
            event_type_id = event_type_uri.split('/')[-1]
            print(f"Using event type ID: {event_type_id}")
            
            # Fetch available times
            current_date = start
            while current_date <= end:
                next_date = current_date + timedelta(days=1)
                
                date_key = current_date.date().isoformat()
                print(f"Checking availability for date: {date_key}")
                
                # Use the correct API endpoint for availability
                available_times_response = requests.get(
                    f"{CALENDLY_API_BASE}/event_types/{event_type_id}/available_times",
                    params={
                        'start_time': current_date.isoformat(),
                        'end_time': next_date.isoformat(),
                        'timezone': 'UTC'  # You may want to adjust this
                    },
                    headers=headers
                )
                
                if available_times_response.status_code == 200:
                    availability_data = available_times_response.json()
                    available_times = availability_data.get('available_times', [])
                    
                    if date_key not in all_availabilities:
                        all_availabilities[date_key] = {}
                    
                    for slot in available_times:
                        slot_time = slot['invitee_start_time']
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