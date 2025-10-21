import aiohttp
import asyncio
import json

async def invoke_chute():
	api_token = "cpk_8b30895959b44f25a773581f46264d2b.5588cb0143e65c21abf0d71d72dbf6a6.SoRJmHjQLjUPxl134d60OeUWXhjx6KDM"  # Replace with your actual API token

	# Get user input
	user_prompt = input("What would you like to ask? ")
	
	headers = {
		"Authorization": "Bearer " + api_token,
		"Content-Type": "application/json"
	}
	
	body =     {
      "model": "deepseek-ai/DeepSeek-R1",
      "messages": [
        {
          "role": "user",
          "content": user_prompt
        }
      ],
      "stream": True,
      "max_tokens": 1024,
      "temperature": 0.7
    }

	async with aiohttp.ClientSession() as session:
		async with session.post(
			"https://llm.chutes.ai/v1/chat/completions", 
			headers=headers,
			json=body
		) as response:
			async for line in response.content:
				line = line.decode("utf-8").strip()
				if line.startswith("data: "):
					data = line[6:]
					if data == "[DONE]":
						break
					try:
						chunk_json = json.loads(data.strip())
						# Extract the actual chat content
						if 'choices' in chunk_json and len(chunk_json['choices']) > 0:
							delta = chunk_json['choices'][0].get('delta', {})
							if 'content' in delta:
								content = delta['content']
								print(content, end='', flush=True)
					except Exception as e:
						print(f"Error parsing chunk: {e}")

asyncio.run(invoke_chute())