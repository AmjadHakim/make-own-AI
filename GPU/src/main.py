import socket
import argparse
from src.core.model_manager import check_gpu, load_model, monitor_gpu
from src.gui.chat_server import ChatServer, NetworkedChatGUI

def get_local_ip():
    """Get the local IP address"""
    try:
        # Create a temporary socket to get the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Connect to Google DNS (doesn't actually send data)
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"  # Fallback to localhost

def run_server(host, port):
    """Run the chat server"""
    print("🤖 GPU-Powered Local Chat Assistant - Server Mode")
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
    
    print("\n💬 Starting chat server...")
    server = ChatServer(host, port, model, tokenizer)
    server.start()

def run_client(host, port):
    """Run the chat client"""
    print(f"🤖 GPU-Powered Local Chat Assistant - Client Mode")
    print(f"Connecting to {host}:{port}...")
    
    client = NetworkedChatGUI(host, port)
    client.run()

def main():
    parser = argparse.ArgumentParser(description="GPU-Powered Local Chat Assistant")
    parser.add_argument("--mode", choices=["server", "client"], default="server",
                      help="Run as server or client (default: server)")
    parser.add_argument("--host", default=None,
                      help="Host IP address (default: local IP for server, localhost for client)")
    parser.add_argument("--port", type=int, default=5000,
                      help="Port number (default: 5000)")
    
    args = parser.parse_args()
    
    # Set default host based on mode
    if args.host is None:
        args.host = get_local_ip() if args.mode == "server" else "localhost"
    
    if args.mode == "server":
        run_server(args.host, args.port)
    else:
        run_client(args.host, args.port)

if __name__ == "__main__":
    main()
