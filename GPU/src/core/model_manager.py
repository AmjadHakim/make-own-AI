import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import gc
import re

def get_model_name():
    """Return the name of a powerful multilingual model"""
    return "bigscience/bloom-3b"  # 3B parameter multilingual model

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
            gc.collect()
        
        return True
    except Exception as e:
        print(f"❌ GPU Error: {e}")
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

def generate_response(model, tokenizer, user_input, chat_history="", search_results=None, detected_lang='en'):
    """Generate multilingual response"""
    device = next(model.parameters()).device
    print("🔄 Thinking...")
    
    # Prepare response
    if chat_history:
        last_exchange = chat_history.split('\n')[-4:]  # Keep last 2 Q&A pairs
        chat_history = '\n'.join(last_exchange)
    
    from ..utils.conversation import get_conversation_style
    style_guide = get_conversation_style(detected_lang)
    
    # Prepare prompt based on available context
    if search_results:
        # Format prompt with search results
        prompt_templates = {
            'en': f"{style_guide}\nPrevious conversation:\n{chat_history}\nUser: {user_input}\nHere's what I found: {search_results}\nRespond naturally in the same language. Include sources at the end.\nAssistant:",
            'es': f"{style_guide}\nConversación anterior:\n{chat_history}\nUsuario: {user_input}\nEsto es lo que encontré: {search_results}\nResponde naturalmente en el mismo idioma. Incluye las fuentes al final.\nAsistente:",
            'fr': f"{style_guide}\nConversation précédente:\n{chat_history}\nUtilisateur: {user_input}\nVoici ce que j'ai trouvé: {search_results}\nRépondez naturellement dans la même langue. Incluez les sources à la fin.\nAssistant:"
        }
        input_text = prompt_templates.get(detected_lang, prompt_templates['en'])
    else:
        # Regular conversation prompts
        prompt_templates = {
            'en': f"{style_guide}\nPrevious conversation:\n{chat_history}\nUser: {user_input}\nRespond naturally in the same language.\nAssistant:",
            'es': f"{style_guide}\nConversación anterior:\n{chat_history}\nUsuario: {user_input}\nResponde naturalmente en el mismo idioma.\nAsistente:",
            'fr': f"{style_guide}\nConversation précédente:\n{chat_history}\nUtilisateur: {user_input}\nRépondez naturellement dans la même langue.\nAssistant:"
        }
        input_text = prompt_templates.get(detected_lang, prompt_templates['en'])
    
    # Generate response
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
