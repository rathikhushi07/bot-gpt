import os
import logging
from typing import List, Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class LLMService:
    
    def __init__(self, provider: str = "groq", api_key: Optional[str] = None, max_tokens: int = 8000):
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY")
        self.max_tokens = max_tokens
        self.model = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
        
        self.provider_configs = {
            "groq": {
                "base_url": "https://api.groq.com/openai/v1",
                "chat_endpoint": "/chat/completions",
                "default_model": "llama-3.1-8b-instant"
            }
        }
        
        if self.provider == "groq" and not self.api_key:
            logger.warning("Groq API key not provided. Falling back to mock mode.")
            self.provider = "mock"
        
        logger.info(f"LLM Service initialized with provider: {self.provider}")
    
    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4
    
    def truncate_history(self, messages: List[Dict[str, str]], max_context_tokens: int = 6000) -> List[Dict[str, str]]:
        if not messages:
            return []
        
        system_messages = [m for m in messages if m.get("role") == "system"]
        non_system_messages = [m for m in messages if m.get("role") != "system"]
        
        system_tokens = sum(self.estimate_tokens(m.get("content", "")) for m in system_messages)
        available_tokens = max_context_tokens - system_tokens
        
        truncated = []
        current_tokens = 0
        
        for message in reversed(non_system_messages):
            message_tokens = self.estimate_tokens(message.get("content", ""))
            if current_tokens + message_tokens <= available_tokens:
                truncated.insert(0, message)
                current_tokens += message_tokens
            else:
                break
        
        result = system_messages + truncated
        logger.info(f"Truncated history: {len(messages)} -> {len(result)} messages ({current_tokens + system_tokens} tokens)")
        return result
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_response_tokens: int = 1000
    ) -> Dict[str, any]:
        truncated_messages = self.truncate_history(messages, max_context_tokens=self.max_tokens - max_response_tokens)
        
        if self.provider == "groq":
            return await self._call_groq_api(truncated_messages, temperature, max_response_tokens)
        else:
            return self._generate_mock_response(truncated_messages)
    
    async def _call_groq_api(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, any]:
        config = self.provider_configs["groq"]
        url = f"{config['base_url']}{config['chat_endpoint']}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                return {
                    "content": data["choices"][0]["message"]["content"],
                    "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                    "model": data.get("model", self.model)
                }
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Groq API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"LLM API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error calling Groq API: {str(e)}")
            raise Exception(f"LLM service error: {str(e)}")
    
    def _generate_mock_response(self, messages: List[Dict[str, str]]) -> Dict[str, any]:
        last_message = messages[-1]["content"] if messages else ""
        
        if "hello" in last_message.lower() or "hi" in last_message.lower():
            response = "Hello! I'm BOT GPT, your AI assistant. How can I help you today?"
        elif "?" in last_message:
            response = f"That's an interesting question! Based on your query '{last_message[:50]}...', here's my response: [Mock LLM Response] I would need more context to provide a complete answer."
        else:
            response = f"Thank you for your message. I understand you're asking about: '{last_message[:50]}...'. [Mock LLM Response] This is a simulated response for development purposes."
        
        tokens_used = self.estimate_tokens(last_message) + self.estimate_tokens(response)
        
        return {
            "content": response,
            "tokens_used": tokens_used,
            "model": "mock-model"
        }
    
    def create_system_prompt(self, mode: str, context: Optional[str] = None) -> str:
        if mode == "grounded_rag" and context:
            return f"""You are BOT GPT, a helpful AI assistant. You are having a conversation that is grounded in specific documents.

Use the following context from the documents to answer the user's questions. If the answer cannot be found in the context, say so clearly.

Context:
{context}

Answer the user's questions based on this context."""
        
        return "You are BOT GPT, a helpful and knowledgeable AI assistant. Provide clear, accurate, and helpful responses to the user's questions."
