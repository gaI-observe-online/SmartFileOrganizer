"""Ollama AI provider."""

import json
import logging
from typing import Dict, List, Optional

try:
    import ollama
except ImportError:
    ollama = None

from ..utils.errors import ConnectionError, AIProviderError
from ..utils.retry import retry_with_backoff, RetryConfig, ConnectionMonitor, ConnectionState


logger = logging.getLogger(__name__)


class OllamaProvider:
    """Ollama AI provider for file organization."""
    
    def __init__(
        self,
        endpoint: str = "http://localhost:11434",
        model: str = "llama3.3",
        fallback_model: str = "qwen2.5",
        timeout: int = 30
    ):
        """Initialize Ollama provider.
        
        Args:
            endpoint: Ollama API endpoint
            model: Primary model name
            fallback_model: Fallback model name
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint
        self.model = model
        self.fallback_model = fallback_model
        self.timeout = timeout
        
        # Initialize connection monitor
        self.connection_monitor = ConnectionMonitor(
            check_interval=5.0,
            retry_config=RetryConfig(max_attempts=3, initial_delay=1.0)
        )
        
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Ollama is available.
        
        Returns:
            True if Ollama is available
        """
        if not ollama:
            logger.warning("Ollama Python library not installed")
            self.connection_monitor.state = ConnectionState.OFFLINE
            return False
        
        try:
            # Try to list models to verify connection
            ollama.list()
            logger.info(f"Ollama is available at {self.endpoint}")
            self.connection_monitor.state = ConnectionState.ONLINE
            return True
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self.connection_monitor.state = ConnectionState.OFFLINE
            return False
    
    @retry_with_backoff(RetryConfig(max_attempts=3, initial_delay=2.0))
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        json_mode: bool = False
    ) -> Optional[str]:
        """Generate response from Ollama.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            json_mode: Whether to request JSON output
            
        Returns:
            Generated response or None if failed
        """
        if not self.available:
            # Try to reconnect
            logger.info("Ollama not available, attempting to reconnect...")
            self.available = self._check_availability()
            
            if not self.available:
                raise ConnectionError(
                    service="Ollama",
                    endpoint=self.endpoint,
                    original_error=None
                )
        
        try:
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Try primary model
            try:
                response = ollama.chat(
                    model=self.model,
                    messages=messages,
                    options={
                        "temperature": 0.7,
                        "num_predict": 2000
                    },
                    format="json" if json_mode else ""
                )
                
                return response['message']['content']
            
            except Exception as e:
                logger.warning(f"Primary model {self.model} failed: {e}, trying fallback")
                
                # Try fallback model
                response = ollama.chat(
                    model=self.fallback_model,
                    messages=messages,
                    options={
                        "temperature": 0.7,
                        "num_predict": 2000
                    },
                    format="json" if json_mode else ""
                )
                
                return response['message']['content']
        
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            self.connection_monitor.state = ConnectionState.OFFLINE
            raise AIProviderError(
                provider="Ollama",
                operation="generation",
                original_error=e
            )
    
    def analyze_files(
        self,
        file_list: List[Dict],
        system_prompt: str,
        user_prompt_template: str
    ) -> Optional[Dict]:
        """Analyze files and get organization suggestions.
        
        Args:
            file_list: List of file information dicts
            system_prompt: System prompt
            user_prompt_template: User prompt template
            
        Returns:
            Analysis results as dict or None if failed
        """
        from datetime import datetime
        
        # Build file list string
        file_list_str = "\n".join([
            f"- {f['path']} (Type: {f.get('doc_type', 'unknown')}, Size: {f.get('size', 0)} bytes)"
            for f in file_list[:20]  # Limit to first 20 files to avoid token limits
        ])
        
        # Format prompt
        user_prompt = user_prompt_template.format(
            file_list=file_list_str,
            current_date=datetime.now().strftime('%Y-%m-%d')
        )
        
        try:
            # Generate response
            response = self.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                json_mode=True
            )
            
            if not response:
                return None
            
            # Parse JSON response
            try:
                return json.loads(response)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.debug(f"Response was: {response}")
                return None
        
        except (ConnectionError, AIProviderError) as e:
            # Log but don't crash - caller will fall back to rule-based
            logger.warning(f"AI analysis failed: {e.message}")
            return None
    
    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry.
        
        Args:
            model_name: Name of model to pull
            
        Returns:
            True if successful
        """
        if not self.available:
            return False
        
        try:
            ollama.pull(model_name)
            logger.info(f"Successfully pulled model: {model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
