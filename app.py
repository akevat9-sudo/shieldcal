# Qwen 3 Coder: Optimized Webhook Listener and Auto-DM Sender
from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# CONFIGURATION
# Paste your long Page Access Token from the Graph API Explorer here
PAGE_ACCESS_TOKEN = "EAAcW8Oqgq3cBRlfnKlMRWe45IBqUZBfJKAzYMk5NmrtnpyTq2Qo5en0AZBl8siP8SN9VcDtKCrBZA2qzaVHXq6yFPcu7G66iIheYa680wBtQCAZAN0LTBvOxokL9ZAyX37tnH4vQ7LiUOVmfZCp9YFQakL6O4gXhFoBa43ikJenAeluFdbNObrZBbIPhBm5DTZCAeZBbVOfFGv0atRZBg8XRZB2a5cLWGEr55IAiAB0q7G5G3QMEaruqq1OdDwgZACb29zhZAn4N4yWf6jiplKNtJbWMCQd0rNTWfE3U8phhtwAZDZD"
# Must match whatever you typed in the Meta Developer settings
VERIFY_TOKEN = "shieldcal_verification_secure" 
# The exact keyword you want to listen for
TRIGGER_KEYWORD = "safe"
# Your app link to send to the user
SHIELDCAL_LINK = "https://shieldcal.lunaticmarbles.com/"

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Handles the initial Meta verification challenge."""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return challenge, 200
    return 'Verification failed', 403


@app.route('/webhook', methods=['POST'])
def handle_instagram_events():
    """Listens for new comments and automatically sends a DM."""
    data = request.json
    
    if not data or 'entry' not in data:
        return jsonify({"status": "ignored"}), 200

    for entry in data['entry']:
        if 'changes' in entry:
            for change in entry['changes']:
                if change.get('field') == 'comments':
                    comment_data = change.get('value', {})
                    comment_text = comment_data.get('text', '').strip().lower()
                    
                    if TRIGGER_KEYWORD in comment_text:
                        # CRITICAL FIX: Extract the comment_id, not the user_id
                        comment_id = comment_data.get('id')
                        
                        if comment_id:
                            send_automated_dm(comment_id)
                            
    return jsonify({"status": "success"}), 200

    for entry in data['entry']:
        # Look for changes/comments in the payload
        if 'changes' in entry:
            for change in entry['changes']:
                if change.get('field') == 'comments':
                    comment_data = change.get('value', {})
                    comment_text = comment_data.get('text', '').strip().lower()
                    
                    # 1. Check if the comment matches your trigger keyword
                    if TRIGGER_KEYWORD in comment_text:
                        # Extract user details to send them the DM
                        # For IG Graph API, we need the media/post owner context or user id
                        from_user = comment_data.get('from', {})
                        user_id = from_user.get('id')
                        
                        if user_id:
                            # 2. Fire the DM with your link
                            send_automated_dm(user_id)
                            
    return jsonify({"status": "success"}), 200

def send_automated_dm(comment_id):
    """Fires a POST request to the Instagram Messages API endpoint."""
    url = f"https://graph.facebook.com/v25.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    
    message_text = (
        f"Hey! Thanks for the comment. Here is your link to the free Shieldcal Risk Calculator "
        f"to help protect your trading margin: {SHIELDCAL_LINK}"
    )
    
    # CRITICAL FIX: Pass the comment_id to authorize the Private Reply
    payload = {
        "recipient": {"comment_id": comment_id},
        "message": {"text": message_text}
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"Successfully sent DM for Comment ID: {comment_id}")
        else:
            # This will print the exact reason if Meta blocks it again
            print(f"Failed to send DM. Meta error: {response.json()}")
    except Exception as e:
        print(f"Error firing DM request: {str(e)}")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
