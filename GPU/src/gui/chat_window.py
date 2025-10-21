import tkinter as tk
from tkinter import ttk, scrolledtext
from threading import Thread
import queue
import time
from ..utils.conversation import get_greeting
from ..utils.history_manager import process_response
from ..utils.search import search_internet
from ..utils.conversation import detect_language
from ..core.model_manager import generate_response

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
                
                # Detect language
                detected_lang = detect_language(message)
                
                # Check if search is needed
                search_keywords = {
                    'en': ['what', 'how', 'why', 'where', 'when', 'who', 'search', 'find'],
                    'es': ['qué', 'cómo', 'por qué', 'dónde', 'cuándo', 'quién', 'buscar', 'encontrar'],
                    'fr': ['quoi', 'comment', 'pourquoi', 'où', 'quand', 'qui', 'chercher', 'trouver']
                }.get(detected_lang, ['what', 'how', 'why', 'where', 'when', 'who', 'search', 'find'])
                
                search_results = None
                if any(keyword in message.lower() for keyword in search_keywords):
                    search_results = search_internet(message)
                
                # Generate response
                response = generate_response(
                    self.model,
                    self.tokenizer,
                    message,
                    chat_history="",  # We'll implement history later
                    search_results=search_results,
                    detected_lang=detected_lang
                )
                
                # Process response (add sources, save history)
                response = process_response(response, message, search_results, None)
                
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
