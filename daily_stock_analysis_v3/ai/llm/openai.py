"""
OpenAI LLM Provider

OpenAI API integration (also works with OpenAI-compatible APIs like DeepSeek).
"""

from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai.llm.base import LLMProvider, LLMRegistry
from exceptions import AIError, LLMError


class OpenAIProvider(LLMProvider):
    """OpenAI API provider (also supports DeepSeek, etc.)"""
    
    name = "openai"
    description = "OpenAI API and compatible providers"
    supports_streaming = True
    supports_vision = True
    max_tokens = 128000
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.model = self.config.get('model', 'gpt-4o-mini')
        self.base_url = self.config.get('base_url', 'https://api.openai.com/v1')
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate OpenAI configuration"""
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY or pass api_key in config.")
    
    def _get_client(self):
        """Get or create OpenAI client"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError:
                raise LLMError(
                    "OpenAI package not installed. Run: pip install openai",
                    model=self.model,
                    provider=self.name,
                )
            except Exception as e:
                raise LLMError(
                    f"Failed to initialize OpenAI client: {e}",
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
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Generate
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                timeout=self.timeout * 1000,  # Convert to ms
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise LLMError(
                    "Empty response from OpenAI",
                    model=self.model,
                    provider=self.name,
                )
            
            content = response.choices[0].message.content
            logger.debug(f"OpenAI generated {len(content)} chars")
            return content
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
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
        
        # Add JSON format instruction
        json_prompt = f"""{prompt}

Respond with valid JSON only. No markdown, no explanations.
Format:
{json.dumps(schema, indent=2)}
"""
        
        # Use system prompt to enforce JSON mode
        json_system = "You are a JSON API. Respond with valid JSON only."
        if system_prompt:
            json_system = f"{system_prompt}\n\n{json_system}"
        
        response_text = self.generate(
            prompt=json_prompt,
            system_prompt=json_system,
            **kwargs,
        )
        
        # Parse JSON
        try:
            response_text = response_text.strip()
            if response_text.startswith('```'):
                response_text = '\n'.join(response_text.split('\n')[1:-1])
            
            return json.loads(response_text)
        except Exception as e:
            raise LLMError(
                f"Failed to parse JSON: {e}",
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
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Stream
            stream = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
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
OpenAIProvider.register()
