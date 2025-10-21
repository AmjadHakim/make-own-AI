import json
from datetime import datetime

def save_chat_history(chat_history):
    """Save chat history to a JSON file with timestamps"""
    try:
        # Load existing history if it exists
        try:
            with open('chat_history.json', 'r', encoding='utf-8') as f:
                history_data = json.load(f)
        except FileNotFoundError:
            history_data = []
        
        # Add new conversation with timestamp
        history_data.append({
            'timestamp': datetime.now().isoformat(),
            'conversation': chat_history.strip()
        })
        
        # Keep only last 100 conversations to manage file size
        if len(history_data) > 100:
            history_data = history_data[-100:]
            
        # Save updated history
        with open('chat_history.json', 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"Warning: Could not save chat history: {e}")

def load_chat_history():
    """Load recent chat history to help with context"""
    try:
        with open('chat_history.json', 'r', encoding='utf-8') as f:
            history_data = json.load(f)
            # Get the last 5 conversations
            recent_history = history_data[-5:]
            return "\n".join(item['conversation'] for item in recent_history)
    except FileNotFoundError:
        return ""
    except Exception as e:
        print(f"Warning: Could not load chat history: {e}")
        return ""

def process_response(response_text, query, search_results, chat_history):
    """Process and enhance the model's response"""
    # Add source citations if search results were used
    if search_results:
        response_text += "\n\nSources used:"
        for idx, line in enumerate(search_results.split('\n')):
            if line.startswith('URL:'):
                response_text += f"\n{line.replace('URL:', '[' + str(idx//3 + 1) + ']')}"
    
    # Save the conversation to history
    conversation = f"User: {query}\nAssistant: {response_text}\n"
    save_chat_history(conversation)
    
    return response_text
