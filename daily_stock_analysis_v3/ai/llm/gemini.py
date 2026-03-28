"""
Gemini LLM Provider

Google's Gemini API integration.
"""

from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai.llm.base import LLMProvider, LLMRegistry
from exceptions import AIError, LLMError


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider"""
    
    name = "gemini"
    description = "Google Gemini models"
    supports_streaming = True
    supports_vision = True
    max_tokens = 32768
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.model = self.config.get('model', 'gemini-2.0-flash')
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate Gemini configuration"""
        if not self.api_key:
            raise ValueError("Gemini API key required. Set GEMINI_API_KEY or pass api_key in config.")
    
    def _get_client(self):
        """Get or create Gemini client"""
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model)
            except ImportError:
                raise LLMError(
                    "Google AI package not installed. Run: pip install google-generativeai",
                    model=self.model,
                    provider=self.name,
                )
            except Exception as e:
                raise LLMError(
                    f"Failed to initialize Gemini client: {e}",
                    model=self.model,
                    provider=self.name,
                )
        
        return self._client
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Generate text from prompt"""
        try:
            client = self._get_client()
            
            # Configure generation
            config = {
                'temperature': temperature or self.temperature,
                'max_output_tokens': max_tokens or self.max_tokens,
            }
            
            # Build full prompt with system instruction
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Generate
            response = client.generate_content(
                full_prompt,
                generation_config=config,
            )
            
            if not response.text:
                raise LLMError(
                    "Empty response from Gemini",
                    model=self.model,
                    provider=self.name,
                )
            
            logger.debug(f"Gemini generated {len(response.text)} chars")
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise LLMError(
                message=str(e),
                model=self.model,
                provider=self.name,
            )
    
    def generate_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate structured JSON output"""
        import json
        
        # Add JSON format instruction to prompt
        json_prompt = f"""{prompt}

Please respond with valid JSON only. No markdown, no explanations.
Expected format:
{json.dumps(schema, indent=2)}
"""
        
        response_text = self.generate(
            prompt=json_prompt,
            system_prompt=system_prompt,
            **kwargs,
        )
        
        # Parse JSON
        try:
            # Remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith('```'):
                response_text = '\n'.join(response_text.split('\n')[1:-1])
            
            return json.loads(response_text)
        except Exception as e:
            raise LLMError(
                f"Failed to parse JSON response: {e}",
                model=self.model,
                provider=self.name,
                details={'raw_response': response_text[:500]},
            )
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ):
        """Generate text with streaming"""
        try:
            client = self._get_client()
            
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Stream generation
            response = client.generate_content(
                full_prompt,
                stream=True,
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Gemini streaming failed: {e}")
            raise LLMError(
                message=str(e),
                model=self.model,
                provider=self.name,
            )
    
    @classmethod
    def register(cls):
        """Register provider"""
        LLMRegistry.register(cls)


# Auto-register on import
GeminiProvider.register()
