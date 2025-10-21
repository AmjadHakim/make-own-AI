import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import sys
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
import time
import random
from langdetect import detect, LangDetectException
import tkinter as tk
from tkinter import ttk, scrolledtext
from threading import Thread
import queue

class ChatGUI:
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self.message_queue = queue.Queue()
        self.setup_gui()
        
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("🤖 GPU-Powered AI Chat")
        self.root.geometry("800x600")
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Create chat display
        self.chat_display = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=20)
        self.chat_display.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.chat_display.configure(state='disabled')
        
        # Create input field
        self.input_field = ttk.Entry(main_frame)
        self.input_field.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        self.input_field.bind("<Return>", self.send_message)
        
        # Create send button
        send_button = ttk.Button(main_frame, text="Send", command=self.send_message)
        send_button.grid(row=1, column=1, sticky=(tk.E), padx=5, pady=5)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Add system message
        self.add_message("System", get_greeting())
        
        # Start message processing thread
        self.processing = True
        self.process_thread = Thread(target=self.process_messages)
        self.process_thread.daemon = True
        self.process_thread.start()
        
    def add_message(self, sender, message):
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, f"\n{sender}: {message}\n")
        self.chat_display.see(tk.END)
        self.chat_display.configure(state='disabled')
        
    def send_message(self, event=None):
        message = self.input_field.get().strip()
        if message:
            self.input_field.delete(0, tk.END)
            self.add_message("You", message)
            self.message_queue.put(message)
            
    def process_messages(self):
        while self.processing:
            try:
                message = self.message_queue.get(timeout=0.1)
                self.chat_display.configure(state='normal')
                self.chat_display.insert(tk.END, "AI: ")
                self.chat_display.configure(state='disabled')
                
                # Generate response
                response = generate_response(self.model, self.tokenizer, message)
                
                # Display response with typing effect
                for char in response:
                    self.chat_display.configure(state='normal')
                    self.chat_display.insert(tk.END, char)
                    self.chat_display.see(tk.END)
                    self.chat_display.configure(state='disabled')
                    self.root.update()
                    if char in ['.', '!', '?', '\n']:
                        time.sleep(0.05)
                    else:
                        time.sleep(0.01)
                
                self.chat_display.configure(state='normal')
                self.chat_display.insert(tk.END, "\n\n")
                self.chat_display.configure(state='disabled')
                
            except queue.Empty:
                continue
            except Exception as e:
                self.add_message("System", f"Error: {str(e)}")
                
    def run(self):
        self.root.mainloop()
        self.processing = False

def detect_language(text):
    """Detect the language of input text"""
    try:
        return detect(text)
    except LangDetectException:
        return 'en'  # Default to English if detection fails

def get_model_name():
    """Return the name of a powerful multilingual model"""
    # Using BLOOM, one of the best open multilingual models
    return "bigscience/bloom-3b"  # 3B parameter multilingual model
    # Alternative models:
    # - "facebook/mbart-large-50-many-to-many-mmt" (good for translation)
    # - "xlm-roberta-large" (good for understanding)
    # - "google/mt5-large" (good for generation)

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

def check_gpu():
    """Check if CUDA is available and display GPU info and diagnostics"""
    print("[PyTorch Version]", torch.__version__)
    print("[CUDA in PyTorch]", torch.version.cuda)
    print("[torch.cuda.is_available()]", torch.cuda.is_available())
    try:
        import subprocess
        print("[nvidia-smi output]:")
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        print(result.stdout)
        if "Game Ready" in result.stdout or "Studio" in result.stdout:
            print("[INFO] Detected NVIDIA driver type: Game Ready or Studio. Both are supported for AI and CUDA.")
        else:
            print("[INFO] Could not determine driver type from nvidia-smi output. If you see your GPU listed, your driver is fine.")
    except Exception as e:
        print(f"[nvidia-smi not available or failed: {e}]")
    if torch.cuda.is_available():
        print(f"✅ GPU Available: {torch.cuda.get_device_name(0)}")
        print(f"🔥 CUDA Version: {torch.version.cuda}")
        print(f"💾 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        return True
    else:
        print("❌ No GPU available. Running on CPU.")
        return False

def load_model():
    """Load a powerful multilingual model"""
    print("📥 Loading multilingual model...")
    
    model_name = get_model_name()
    
    try:
        # Clear CUDA cache first
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print(f"💾 Available GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if torch.cuda.is_available():
            print("🚀 Loading model on GPU with optimizations...")
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                load_in_8bit=True,  # Enable 8-bit quantization
                low_cpu_mem_usage=True,
                offload_folder="offload"  # Offload to disk if needed
            )
            
            # Force garbage collection
            import gc
            gc.collect()
            torch.cuda.empty_cache()
            
        else:
            print("⚠️ CUDA not available, loading model on CPU (may be slow)...")
            model = AutoModelForCausalLM.from_pretrained(model_name)
            
        # Add padding token if needed
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            
        print(f"✅ Model loaded successfully! Device: {next(model.parameters()).device}")
        if torch.cuda.is_available():
            print(f"💾 GPU Memory Used: {torch.cuda.memory_allocated() / 1e9:.1f} GB")
        return model, tokenizer
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None, None

def get_conversation_style(lang='en'):
    """Return conversation style guide based on detected language"""
    styles = {
        'en': """You are a helpful and friendly AI assistant who can communicate in many languages. When responding:
    - Use a casual, warm tone
    - Be concise but informative
    - Use natural language and contractions
    - Express empathy and understanding
    - Include light conversational elements
    - Break up long responses into readable chunks
    - Use appropriate emotional indicators (e.g., 😊, 👍)
    - Respond in the same language as the user's query""",
        
        'es': """Eres un asistente de IA amigable y servicial que puede comunicarse en muchos idiomas. Al responder:
    - Usa un tono casual y cálido
    - Sé conciso pero informativo
    - Usa lenguaje natural
    - Expresa empatía y comprensión
    - Incluye elementos conversacionales ligeros
    - Divide las respuestas largas en fragmentos legibles
    - Usa indicadores emocionales apropiados (e.g., 😊, 👍)""",
        
        'fr': """Vous êtes un assistant IA serviable et amical qui peut communiquer dans plusieurs langues. En répondant:
    - Utilisez un ton décontracté et chaleureux
    - Soyez concis mais informatif
    - Utilisez un langage naturel
    - Exprimez de l'empathie et de la compréhension
    - Incluez des éléments de conversation légers
    - Divisez les longues réponses en morceaux lisibles
    - Utilisez des indicateurs émotionnels appropriés (e.g., 😊, 👍)"""
    }
    return styles.get(lang, styles['en'])

def generate_response(model, tokenizer, user_input, chat_history=""):
    """Generate multilingual response"""
    device = next(model.parameters()).device
    print("🔄 Thinking...")
    
    # Detect input language
    input_lang = detect_language(user_input)
    
    # Get conversation style in detected language
    style_guide = get_conversation_style(input_lang)
    
    # Prepare prompt in detected language
    if chat_history:
        last_exchange = chat_history.split('\n')[-4:]
        chat_history = '\n'.join(last_exchange)
    
    # Search if needed (using multilingual keywords)
    search_keywords = {
        'en': ['what', 'how', 'why', 'where', 'when', 'who', 'search', 'find'],
        'es': ['qué', 'cómo', 'por qué', 'dónde', 'cuándo', 'quién', 'buscar', 'encontrar'],
        'fr': ['quoi', 'comment', 'pourquoi', 'où', 'quand', 'qui', 'chercher', 'trouver'],
    }
    
    # Get keywords for detected language, fallback to English
    keywords = search_keywords.get(input_lang, search_keywords['en'])
    
    if any(keyword in user_input.lower() for keyword in keywords):
        search_result = search_internet(user_input)
        search_lines = search_result.split('\n')[:6]
        search_result = '\n'.join(search_lines)
        
        # Multilingual prompt templates
        prompt_templates = {
            'en': f"{style_guide}\nPrevious conversation:\n{chat_history}\nUser: {user_input}\nHere's what I found: {search_result}\nRespond naturally in the same language. Include sources at the end.\nAssistant:",
            'es': f"{style_guide}\nConversación anterior:\n{chat_history}\nUsuario: {user_input}\nEsto es lo que encontré: {search_result}\nResponde naturalmente en el mismo idioma. Incluye las fuentes al final.\nAsistente:",
            'fr': f"{style_guide}\nConversation précédente:\n{chat_history}\nUtilisateur: {user_input}\nVoici ce que j'ai trouvé: {search_result}\nRépondez naturellement dans la même langue. Incluez les sources à la fin.\nAssistant:"
        }
        input_text = prompt_templates.get(input_lang, prompt_templates['en'])
    else:
        # Regular conversation prompts
        prompt_templates = {
            'en': f"{style_guide}\nPrevious conversation:\n{chat_history}\nUser: {user_input}\nRespond naturally in the same language.\nAssistant:",
            'es': f"{style_guide}\nConversación anterior:\n{chat_history}\nUsuario: {user_input}\nResponde naturalmente en el mismo idioma.\nAsistente:",
            'fr': f"{style_guide}\nConversation précédente:\n{chat_history}\nUtilisateur: {user_input}\nRépondez naturellement dans la même langue.\nAssistant:"
        }
        input_text = prompt_templates.get(input_lang, prompt_templates['en'])

    # Generate response with language-aware settings
    inputs = tokenizer(
        input_text,
        return_tensors="pt",
        truncation=True,
        max_length=1024,
        padding=True
    ).to(device)
    
    with torch.no_grad():
        outputs = model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_new_tokens=512,
            min_length=50,
            do_sample=True,
            temperature=0.85,
            top_p=0.92,
            top_k=50,
            repetition_penalty=1.2,
            no_repeat_ngram_size=3,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response = re.sub(r'User:|Human:|Bot:|Assistant:|Asistente:|Assistant:', '', response).strip()
    
    return response

def search_internet(query, num_results=3):
    """Enhanced multilingual internet search"""
    try:
        # Detect query language
        query_lang = detect_language(query)
        
        # Clean and enhance the search query
        search_query = query.replace("?", "").strip()
        
        # Multilingual search keywords based on detected language
        search_keywords = {
            'en': {
                "how to": "tutorial guide steps",
                "what is": "definition explanation",
                "when": "date time history",
                "where": "location place",
                "why": "reason explanation cause",
                "recipe": "ingredients instructions cooking",
                "news": "latest news recent update"
            },
            'es': {
                "cómo": "tutorial guía pasos",
                "qué es": "definición explicación",
                "cuándo": "fecha tiempo historia",
                "dónde": "ubicación lugar",
                "por qué": "razón explicación causa",
                "receta": "ingredientes instrucciones cocina",
                "noticias": "últimas noticias actualidad"
            },
            'fr': {
                "comment": "tutoriel guide étapes",
                "qu'est-ce": "définition explication",
                "quand": "date temps histoire",
                "où": "lieu endroit",
                "pourquoi": "raison explication cause",
                "recette": "ingrédients instructions cuisine",
                "actualités": "dernières nouvelles"
            }
        }
        
        # Get keywords for detected language, fallback to English
        lang_keywords = search_keywords.get(query_lang, search_keywords['en'])
        
        # Add language-specific keywords
        for indicator, keywords in lang_keywords.items():
            if indicator.lower() in query.lower():
                search_query += f" {keywords}"
        
        # Add language to search query if not English
        if query_lang != 'en':
            search_query += f" lang:{query_lang}"
        
        # Perform the search with language-aware headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': f"{query_lang},en;q=0.9"
        }
        search_url = f"https://duckduckgo.com/html/?q={search_query}"
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        result_elements = soup.find_all('div', {'class': 'result__body'})
        
        for element in result_elements[:num_results]:
            title_elem = element.find('a', {'class': 'result__a'})
            snippet_elem = element.find('a', {'class': 'result__snippet'})
            
            if title_elem and snippet_elem:
                title = title_elem.get_text().strip()
                snippet = snippet_elem.get_text().strip()
                url = title_elem.get('href')
                
                try:
                    page_response = requests.get(url, headers=headers, timeout=5)
                    page_soup = BeautifulSoup(page_response.text, 'html.parser')
                    
                    # Remove script and style elements
                    for script in page_soup(["script", "style"]):
                        script.decompose()
                        
                    # Get main content
                    main_content = page_soup.find('main') or page_soup.find('article') or page_soup.find('div', {'class': re.compile(r'content|main|article', re.I)})
                    if main_content:
                        content = main_content.get_text()
                    else:
                        content = page_soup.get_text()
                    
                    # Clean and truncate content
                    content = ' '.join(content.split())[:1000]
                except:
                    content = snippet
                
                results.append({
                    'title': title,
                    'content': content,
                    'url': url
                })
        
        # Format results in the detected language
        source_labels = {
            'en': 'Source',
            'es': 'Fuente',
            'fr': 'Source',
            'de': 'Quelle',
            'it': 'Fonte',
            'pt': 'Fonte',
            'nl': 'Bron',
            'pl': 'Źródło',
            'ru': 'Источник',
            'ja': '出典',
            'zh': '来源',
            'ko': '출처'
        }
        
        source_label = source_labels.get(query_lang, 'Source')
        formatted_results = []
        for idx, result in enumerate(results, 1):
            formatted_results.append(f"{source_label} {idx}: {result['title']}\nURL: {result['url']}\nContent: {result['content']}\n")
        
        return "\n".join(formatted_results)
    except Exception as e:
        # Error messages in multiple languages
        error_messages = {
            'en': f"Sorry, I couldn't search the internet right now. Error: {str(e)}",
            'es': f"Lo siento, no pude buscar en internet ahora. Error: {str(e)}",
            'fr': f"Désolé, je ne peux pas effectuer la recherche pour le moment. Erreur: {str(e)}",
        }
        return error_messages.get(detect_language(query), error_messages['en'])

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

def chat_loop(model, tokenizer):
    print("💬 Hey there! I'm your AI assistant. What's on your mind? (type 'quit' to exit)")
    
    # Set maximum sequence length
    max_sequence_length = 1024
    
    # Track conversation state
    conversation_started = False
    user_name = None
    
    while True:
        try:
            # Get user input with appropriate prompt
            if not conversation_started:
                user_input = input("\nYou: ").strip()
                if user_input.lower() == 'quit':
                    print("\n👋 It was great chatting with you! Take care!")
                    break
                    
                # Try to extract name from first message
                if not user_name and len(user_input.split()) > 2:
                    name_patterns = [
                        r"(?i)(?:i am|i'm|name is|call me) ([A-Za-z]+)",
                        r"(?i)^([A-Za-z]+) here",
                        r"(?i)^hi|hey|hello,? (?:i'm|i am)? ?([A-Za-z]+)"
                    ]
                    for pattern in name_patterns:
                        match = re.search(pattern, user_input)
                        if match:
                            user_name = match.group(1).capitalize()
                            break
                conversation_started = True
            else:
                prompt = f"\n{'You' if not user_name else user_name}: "
                user_input = input(prompt).strip()
                if user_input.lower() == 'quit':
                    farewell = f"Goodbye{', ' + user_name if user_name else ''}! It was great chatting with you! 👋"
                    print(f"\n{farewell}")
                    break
            
            # Load and manage conversation context
            recent_history = load_chat_history()
            search_results = search_internet(user_input) if any(keyword in user_input.lower() 
                for keyword in ['what', 'how', 'why', 'where', 'when', 'who', 'search', 'find', 'tell me']) else ""
            
            # Prepare conversation context
            context = ""
            if recent_history:
                last_conv = recent_history.split('\n')[-4:]  # Keep last 2 Q&A pairs
                context = '\n'.join(last_conv) + '\n\n'
            
            # Add search results if available
            if search_results:
                search_lines = search_results.split('\n')[:6]
                search_results = '\n'.join(search_lines)
                context += f"Search results:\n{search_results}\n\n"
            
            # Create personalized prompt
            name_context = f" {user_name}" if user_name else ""
            prompt = f"{context}Human{name_context}: {user_input}\nAssistant: "
            
            # Generate and process response
            inputs = tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=max_sequence_length,
                padding=True
            ).to(model.device)
            
            # Generate response with personality
            output = model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                max_new_tokens=512,
                min_length=50,
                do_sample=True,
                temperature=0.85,
                top_p=0.92,
                top_k=50,
                repetition_penalty=1.2,
                no_repeat_ngram_size=3,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
            
            # Process and display response
            response = tokenizer.decode(output[0], skip_special_tokens=True)
            response = response.replace(prompt, "").strip()
            processed_response = process_response(response, user_input, search_results, recent_history)
            
            # Add typing effect
            print("\nAI: ", end="", flush=True)
            for char in processed_response:
                print(char, end="", flush=True)
                if char in ['.', '!', '?', '\n']:
                    time.sleep(0.1)
                else:
                    time.sleep(0.01)
            print("\n" + "="*50)
            
        except Exception as e:
            print(f"\nOops! 😅 Something went wrong: {str(e)}")
            print("Let me try to get back on track...")
            continue

def get_greeting():
    """Return a random friendly greeting"""
    greetings = [
        "👋 Hi there! I'm your friendly AI assistant!",
        "Hello! 😊 I'm here to chat and help out!",
        "Hey! 🌟 Ready for some interesting conversation?",
        "Hi! 💭 What's on your mind today?",
        "Welcome! 🎯 How can I help you today?"
    ]
    return random.choice(greetings)

def monitor_gpu():
    """Monitor GPU status and memory usage"""
    if not torch.cuda.is_available():
        print("❌ No GPU available")
        return False
        
    try:
        # Get GPU properties
        gpu_name = torch.cuda.get_device_name(0)
        total_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
        allocated_memory = torch.cuda.memory_allocated() / 1e9
        cached_memory = torch.cuda.memory_reserved() / 1e9
        free_memory = total_memory - allocated_memory
        
        print("\n🔍 GPU Status:")
        print(f"Device: {gpu_name}")
        print(f"Total Memory: {total_memory:.1f} GB")
        print(f"Used Memory: {allocated_memory:.1f} GB")
        print(f"Cached Memory: {cached_memory:.1f} GB")
        print(f"Free Memory: {free_memory:.1f} GB")
        
        # Check if we have enough memory
        if free_memory < 2.0:  # Less than 2GB free
            print("⚠️ Warning: Low GPU memory! Trying to free up space...")
            torch.cuda.empty_cache()
            import gc
            gc.collect()
        
        return True
    except Exception as e:
        print(f"❌ GPU Error: {e}")
        return False

def main():
    print("🤖 GPU-Powered Local Chat Assistant")
    print("=" * 40)
    
    # Check GPU
    gpu_available = check_gpu()
    if gpu_available:
        monitor_gpu()
    
    # Load model
    model, tokenizer = load_model()
    if model is None:
        print("Failed to load model. Exiting.")
        return
    
    # Load chat history
    chat_history = load_chat_history()
    if chat_history:
        print("🔄 Loaded recent chat history.")
    else:
        print("🗄️ No previous chat history found.")
    
    print("\n💬 Starting chat interface...")
    
    # Create and run GUI
    chat_gui = ChatGUI(model, tokenizer)
    chat_gui.run()

if __name__ == "__main__":
    main()
