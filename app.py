import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==============================================================================
# CONFIGURATION & ENVIRONMENT VARIABLES
# ==============================================================================
# Make sure these are set in your Render dashboard environment variables,
# or replace them here directly with your specific string values.
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "EAAcW8Oqgq3cBRsEy1K3VxZCwzf9pc7vyYoCZCHf81SPW8QiawreDEZCXmRPiNEIMLlV3mR3zBjMaaSFHP25DtBJJrrJtFgcO6RAkNHHpcLLTBwPG4WaS469vZB5mTZAykxklZCYQtuNQJriXvUh6fyaxtM7dS8kNBTxCtZAuinG2Y9fJBonoqxhjBZAiZC6Ks5LsuKScT3LfpZA8QPG0Y3vx0wwL4oRXc9mN4ZCVAKgZCwADLEjQi9PVLqUypqiL2psZD")
TRIGGER_KEYWORD = os.environ.get("TRIGGER_KEYWORD", "safe").lower().strip()
SHIELDCAL_LINK = os.environ.get("SHIELDCAL_LINK", "https://shieldcal.lunaticmarbles.com/")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "shieldcal_verification_secure")


# ==============================================================================
# WEBHOOK VALIDATION (For Meta Setup)
# ==============================================================================
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Handles the initial handshake validation from Meta."""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("Webhook verified successfully!")
            return challenge, 200
        else:
            return "Verification token mismatch", 403
    return "Hello World", 200


# ==============================================================================
# MAIN WEBHOOK ROUTER (The Interactive Funnel)
# ==============================================================================
@app.route('/webhook', methods=['POST'])
def handle_instagram_events():
    """Listens for comments and DM replies to run the multi-step funnel."""
    data = request.json
    
    # Log incoming payload structure for debugging in Render logs
    if not data or 'entry' not in data:
        return jsonify({"status": "ignored"}), 200

    for entry in data['entry']:
        
        # --- STEP 1: Catch Public Comments ---
        if 'changes' in entry:
            for change in entry['changes']:
                if change.get('field') == 'comments':
                    comment_data = change.get('value', {})
                    comment_text = comment_data.get('text', '').strip().lower()
                    comment_id = comment_data.get('id')
                    
                    if TRIGGER_KEYWORD in comment_text and comment_id:
                        print(f"Trigger keyword detected in comment: '{comment_text}'")
                        send_initial_private_reply(comment_id)
                        
        # --- STEPS 2 & 3: Catch Direct Messages (DMs) ---
        if 'messaging' in entry:
            for message_event in entry['messaging']:
                # Skip delivery receipts, read notifications, or echoes from your own bot
                if 'message' not in message_event or message_event.get('read') or message_event.get('delivery'):
                    continue
                    
                sender_id = message_event.get('sender', {}).get('id')
                message = message_event.get('message', {})
                
                # Extract typed text string OR the hidden payload data from a quick reply button click
                msg_text = message.get('text', '').strip().lower()
                quick_reply_payload = message.get('quick_reply', {}).get('payload')
                
                # Check user action
                if msg_text == 'yes':
                    print(f"User {sender_id} requested link. Sending follow gate...")
                    send_follow_gate(sender_id)
                elif msg_text == 'i followed!' or quick_reply_payload == 'USER_CLICKED_FOLLOWED':
                    print(f"User {sender_id} confirmed follow status. Delivering final card...")
                    send_final_link_card(sender_id)

    return jsonify({"status": "success"}), 200


# ==============================================================================
# FUNNEL CORE FUNCTIONS
# ==============================================================================

def send_initial_private_reply(comment_id):
    """Step 1: Plain-text private reply targeting the comment ID to open the DM window."""
    url = f"https://graph.facebook.com/v25.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"comment_id": comment_id},
        "message": {
            "text": "Hey! 👋 I've got the Shieldcal risk calculator ready for you.\n\nJust reply to this message with the word 'YES' and I'll send it right over!"
        }
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"Successfully sent initial reply for comment {comment_id}")
        else:
            print(f"Step 1 failed. Meta Error: {response.json()}")
    except Exception as e:
        print(f"Exception in Step 1: {str(e)}")


def send_follow_gate(sender_id):
    """Step 2: Sends a message asking the user to follow, equipped with a Quick Reply button."""
    url = f"https://graph.facebook.com/v25.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": sender_id},
        "message": {
            "text": "Awesome! 📈\n\nBefore I hand over the link, please make sure you follow the page so you don't miss future trading setups and tools.\n\nTap the button below once you're following!",
            "quick_replies": [
                {
                    "content_type": "text",
                    "title": "✅ I Followed!",
                    "payload": "USER_CLICKED_FOLLOWED"
                }
            ]
        }
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"Successfully sent follow gate to user {sender_id}")
        else:
            print(f"Step 2 failed. Meta Error: {response.json()}")
    except Exception as e:
        print(f"Exception in Step 2: {str(e)}")


def send_final_link_card(sender_id):
    """Step 3: Delivers a clean visual Generic Template card containing the clickable link button."""
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
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"Successfully delivered final link card to user {sender_id}")
        else:
            print(f"Step 3 failed. Meta Error: {response.json()}")
    except Exception as e:
        print(f"Exception in Step 3: {str(e)}")


if __name__ == '__main__':
    # Binds to 0.0.0.0 and reads port environment variables assigned by Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
