import socket
import threading
import json
import time
from typing import Dict, Optional
import tkinter as tk
from tkinter import ttk, scrolledtext
import queue
from ..utils.conversation import detect_language, get_greeting
from ..utils.search import search_internet
from ..utils.history_manager import process_response
from ..core.model_manager import generate_response

class ChatServer:
    def __init__(self, host: str, port: int, model, tokenizer):
        self.host = host
        self.port = port
        self.model = model
        self.tokenizer = tokenizer
        self.clients: Dict[socket.socket, dict] = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = False
        
    def start(self):
        """Start the chat server"""
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            print(f"🚀 Server started on {self.host}:{self.port}")
            print(f"💡 You can connect to this chat server from other computers using this address")
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"📡 New connection from {address}")
                    
                    # Create a new client handler thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:  # Only show error if we're still meant to be running
                        print(f"Error accepting connection: {e}")
                        
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.stop()
            
    def stop(self):
        """Stop the chat server"""
        self.running = False
        # Close all client connections
        for client_socket in list(self.clients.keys()):
            client_socket.close()
        self.clients.clear()
        # Close server socket
        self.server_socket.close()
        print("Server stopped")
        
    def handle_client(self, client_socket: socket.socket, address):
        """Handle individual client connections"""
        try:
            # Send welcome message
            welcome_msg = {
                "type": "system",
                "content": get_greeting()
            }
            client_socket.send(json.dumps(welcome_msg).encode() + b"\n")
            
            # Add client to active clients
            self.clients[client_socket] = {"address": address}
            
            # Handle client messages
            while self.running:
                try:
                    # Receive message
                    data = client_socket.recv(4096)
                    if not data:
                        break
                        
                    # Parse message
                    message = json.loads(data.decode())
                    if message["type"] == "message":
                        user_input = message["content"]
                        
                        # Send typing indicator
                        typing_msg = {"type": "typing", "content": "AI is thinking..."}
                        client_socket.send(json.dumps(typing_msg).encode() + b"\n")
                        
                        # Process message
                        detected_lang = detect_language(user_input)
                        
                        # Check if search is needed
                        search_keywords = {
                            'en': ['what', 'how', 'why', 'where', 'when', 'who', 'search', 'find'],
                            'es': ['qué', 'cómo', 'por qué', 'dónde', 'cuándo', 'quién', 'buscar', 'encontrar'],
                            'fr': ['quoi', 'comment', 'pourquoi', 'où', 'quand', 'qui', 'chercher', 'trouver']
                        }.get(detected_lang, ['what', 'how', 'why', 'where', 'when', 'who', 'search', 'find'])
                        
                        search_results = None
                        if any(keyword in user_input.lower() for keyword in search_keywords):
                            search_results = search_internet(user_input)
                        
                        # Generate response
                        response = generate_response(
                            self.model,
                            self.tokenizer,
                            user_input,
                            chat_history="",  # We'll implement history later
                            search_results=search_results,
                            detected_lang=detected_lang
                        )
                        
                        # Process response (add sources, save history)
                        response = process_response(response, user_input, search_results, None)
                        
                        # Send response
                        response_msg = {"type": "message", "content": response}
                        client_socket.send(json.dumps(response_msg).encode() + b"\n")
                        
                except json.JSONDecodeError:
                    print(f"Invalid message format from {address}")
                except Exception as e:
                    print(f"Error handling message from {address}: {e}")
                    error_msg = {"type": "error", "content": str(e)}
                    client_socket.send(json.dumps(error_msg).encode() + b"\n")
                    
        except Exception as e:
            print(f"Client handler error for {address}: {e}")
        finally:
            # Clean up client connection
            if client_socket in self.clients:
                del self.clients[client_socket]
            client_socket.close()
            print(f"Connection closed for {address}")

class NetworkedChatGUI:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.message_queue = queue.Queue()
        self.response_thread: Optional[threading.Thread] = None
        self.running = False
        self.setup_gui()
        
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title(f"🤖 GPU-Powered AI Chat - {self.host}:{self.port}")
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
        
        # Start response handling thread
        self.running = True
        self.response_thread = threading.Thread(target=self.handle_responses, daemon=True)
        self.response_thread.start()
        
        # Connect to server when GUI starts
        self.root.after(100, self.connect_to_server)
        
    def connect_to_server(self):
        """Connect to the chat server"""
        try:
            self.socket.connect((self.host, self.port))
            print(f"Connected to server at {self.host}:{self.port}")
            
            # Start listening for server messages
            self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.receive_thread.start()
            
        except Exception as e:
            self.add_message("System", f"Failed to connect to server: {e}")
            # Try to reconnect after 5 seconds
            self.root.after(5000, self.connect_to_server)
            
    def add_message(self, sender, message):
        """Add a message to the chat display"""
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, f"\n{sender}: {message}\n")
        self.chat_display.see(tk.END)
        self.chat_display.configure(state='disabled')
        
    def send_message(self, event=None):
        """Send a message to the server"""
        message = self.input_field.get().strip()
        if message:
            try:
                self.input_field.delete(0, tk.END)
                self.add_message("You", message)
                
                # Send message to server
                msg_data = {
                    "type": "message",
                    "content": message
                }
                self.socket.send(json.dumps(msg_data).encode() + b"\n")
                
            except Exception as e:
                self.add_message("System", f"Failed to send message: {e}")
                
    def receive_messages(self):
        """Receive messages from the server"""
        buffer = ""
        while self.running:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                    
                buffer += data.decode()
                
                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1)
                    self.message_queue.put(json.loads(message))
                    
            except Exception as e:
                if self.running:
                    print(f"Error receiving message: {e}")
                    self.message_queue.put({"type": "error", "content": str(e)})
                break
                
        # If we're still running, try to reconnect
        if self.running:
            self.root.after(5000, self.connect_to_server)
            
    def handle_responses(self):
        """Handle messages from the server"""
        while self.running:
            try:
                message = self.message_queue.get(timeout=0.1)
                
                if message["type"] == "system":
                    self.add_message("System", message["content"])
                elif message["type"] == "message":
                    self.add_message("AI", message["content"])
                elif message["type"] == "typing":
                    # Could add a typing indicator here
                    pass
                elif message["type"] == "error":
                    self.add_message("Error", message["content"])
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error handling response: {e}")
                
    def run(self):
        """Start the GUI"""
        self.root.mainloop()
        self.running = False
        self.socket.close()
