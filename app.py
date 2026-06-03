import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==============================================================================
# CONFIGURATION & ENVIRONMENT VARIABLES
# ==============================================================================
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "EAAcW8Oqgq3cBRiqTLWsZBOCLbnwJMyonslFQOcTjDAHKBBeeQZCZAXZC5NHZBgZAZBiDl6vmUHbW6adcq0FeKibBOvyX1wiXC0WoPVdbasOKHTgppF16mZBQwZBemlbASFMfJDAZCSsDIUsWLOLA5slQoAKOSxCO8rbfB6z4khhw9Bp27UfuDy7HgdLnJNZC272ZBZCtTpkm6L9E6C4Ysf1lYSj3x")
SHIELDCAL_LINK = os.environ.get("SHIELDCAL_LINK", "https://shieldcal.lunaticmarbles.com/")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "shieldcal_verification_secure")

# ==============================================================================
# WEBHOOK VALIDATION (Meta Setup)
# ==============================================================================
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification token mismatch", 403
    return "Hello World", 200

# ==============================================================================
# MAIN WEBHOOK ROUTER (The Interactive Funnel)
# ==============================================================================
@app.route('/webhook', methods=['POST'])
def handle_instagram_events():
    data = request.json
    
    if not data or 'entry' not in data:
        return jsonify({"status": "ignored"}), 200

    for entry in data['entry']:
        
        # --- STEP 1: Catch ALL Public Comments ---
        if 'changes' in entry:
            for change in entry['changes']:
                if change.get('field') == 'comments':
                    comment_data = change.get('value', {})
                    comment_id = comment_data.get('id')
                    
                    if comment_id:
                        print("Comment detected. Sending auto-reply with button...")
                        send_initial_private_reply(comment_id)
                        
        # --- STEPS 2 & 3: Catch Direct Messages & Button Clicks ---
        if 'messaging' in entry:
            for message_event in entry['messaging']:
                if message_event.get('read') or message_event.get('delivery') or message_event.get('message', {}).get('is_echo'):
                    continue
                    
                sender_id = message_event.get('sender', {}).get('id')
                
                # Check messages and quick reply buttons
                if 'message' in message_event:
                    msg_text = message_event['message'].get('text', '').strip().lower()
                    quick_reply_payload = message_event['message'].get('quick_reply', {}).get('payload')
                    
                    # 1. User clicked the "Get the link" Quick Reply button (or typed it manually)
                    if quick_reply_payload == 'USER_CLICKED_GET_LINK' or any(word in msg_text for word in ['yes', 'yeah', 'yup', 'send', 'get the link']):
                        print(f"User {sender_id} requested link. Sending follow gate...")
                        send_follow_gate_card(sender_id)
                        
                    # 2. Flexible Followed Check (Fallback for desktop users)
                    elif any(word in msg_text for word in ['follow', 'done', 'did', 'ok']):
                        print(f"User {sender_id} typed they followed. Delivering final link...")
                        send_final_link_card(sender_id)
                
                # Check for Card Button clicks (Postbacks for Mobile Users)
                if 'postback' in message_event:
                    postback_payload = message_event['postback'].get('payload')
                    if postback_payload == 'USER_CLICKED_FOLLOWED':
                        print(f"User {sender_id} clicked Followed. Delivering final link...")
                        send_final_link_card(sender_id)

    return jsonify({"status": "success"}), 200

# ==============================================================================
# FUNNEL CORE FUNCTIONS
# ==============================================================================

def send_initial_private_reply(comment_id):
    """Step 1: Reply targeting the comment ID with a Quick Reply button."""
    url = f"https://graph.facebook.com/v25.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"comment_id": comment_id},
        "message": {
            "text": "Hey! 👋 I've got the risk calculator ready for you. Tap the button below to grab it!",
            "quick_replies": [
                {
                    "content_type": "text",
                    "title": "🔗 Get the link",
                    "payload": "USER_CLICKED_GET_LINK"
                }
            ]
        }
    }
    requests.post(url, json=payload, headers={"Content-Type": "application/json"})

def send_follow_gate_card(sender_id):
    """Step 2: A visual Generic Template card asking the user to follow."""
    url = f"https://graph.facebook.com/v25.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": sender_id},
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [
                        {
                            "title": "One Last Step! 📈",
                            "subtitle": "Please follow the page so you don't miss future trading setups. Tap below when done!",
                            "buttons": [
                                {
                                    "type": "postback",
                                    "title": "✅ I Followed!",
                                    "payload": "USER_CLICKED_FOLLOWED"
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }
    requests.post(url, json=payload, headers={"Content-Type": "application/json"})

def send_final_link_card(sender_id):
    """Step 3: Delivers the final generic template card containing the URL link."""
    url = f"https://graph.facebook.com/v25.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": sender_id},
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [
                        {
                            "title": "Shieldcal Risk Calculator",
                            "subtitle": "Calculate position sizing and manage your trading margin safely.",
                            "buttons": [
                                {
                                    "type": "web_url",
                                    "url": SHIELDCAL_LINK,
                                    "title": "🔗 Open Shieldcal"
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }
    requests.post(url, json=payload, headers={"Content-Type": "application/json"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
