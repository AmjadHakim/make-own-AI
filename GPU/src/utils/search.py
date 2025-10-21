import requests
from bs4 import BeautifulSoup
import re
from .conversation import detect_language

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
