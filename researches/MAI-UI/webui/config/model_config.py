"""
Model configuration management module.
Handles loading, saving, and managing model configurations.
"""

import os
from typing import Any, Dict, List, Optional, Tuple

import yaml


class ModelManager:
    """
    Model configuration and management.
    Provides methods to load, save, and switch between different model providers.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize ModelManager.
        
        Args:
            config_path: Path to model config file. If None, uses default path.
        """
        if config_path is None:
            config_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(config_dir, "model_config.yaml")
        
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._current_provider: Optional[str] = None
        self._current_model: Optional[str] = None
        
        # Load config on init
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Returns:
            Configuration dictionary
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"[ModelManager] Failed to load config: {e}")
                self._config = self._get_default_config()
        else:
            self._config = self._get_default_config()
            self.save_config(self._config)
        
        return self._config.copy()
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """
        Save configuration to YAML file.
        
        Args:
            config: Configuration to save. If None, saves current config.
            
        Returns:
            Whether save was successful
        """
        if config is not None:
            self._config = config
        
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write("# MAI-UI Model Configuration\n")
                f.write("# Edit this file to configure model providers\n\n")
                yaml.dump(self._config, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
            return True
        except Exception as e:
            print(f"[ModelManager] Failed to save config: {e}")
            return False
    
    def get_available_providers(self) -> List[str]:
        """
        Get list of available model provider IDs.
        
        Returns:
            List of provider IDs
        """
        providers = []
        for key, value in self._config.items():
            if isinstance(value, dict) and "api_base" in value:
                providers.append(key)
        return providers
    
    def get_provider_config(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific provider.
        
        Args:
            provider_id: Provider ID
            
        Returns:
            Provider configuration or None
        """
        return self._config.get(provider_id)
    
    def get_provider_display_names(self) -> Dict[str, str]:
        """
        Get mapping of provider IDs to display names.
        
        Returns:
            Dictionary of {provider_id: display_name}
        """
        result = {}
        for provider_id in self.get_available_providers():
            config = self._config.get(provider_id, {})
            result[provider_id] = config.get("display_name", provider_id)
        return result
    
    def switch_model(self, provider_id: str, model_name: str = None) -> Tuple[bool, str]:
        """
        Switch to a different model provider.
        
        Args:
            provider_id: Provider ID to switch to
            model_name: Optional model name override
            
        Returns:
            Tuple of (success, message)
        """
        if provider_id not in self.get_available_providers():
            return False, f"Provider not found: {provider_id}"
        
        config = self._config.get(provider_id, {})
        self._current_provider = provider_id
        self._current_model = model_name or config.get("default_model", "")
        
        return True, f"Switched to {config.get('display_name', provider_id)}: {self._current_model}"
    
    def get_current_config(self) -> Dict[str, Any]:
        """
        Get current active model configuration.
        
        Returns:
            Current model configuration including api_base, api_key, model_name
        """
        if not self._current_provider:
            # Use first available provider
            providers = self.get_available_providers()
            if providers:
                self._current_provider = providers[0]
        
        if not self._current_provider:
            return {}
        
        config = self._config.get(self._current_provider, {})
        return {
            "provider_id": self._current_provider,
            "api_base": config.get("api_base", ""),
            "api_key": config.get("api_key", ""),
            "model_name": self._current_model or config.get("default_model", ""),
            "display_name": config.get("display_name", self._current_provider),
        }
    
    def test_connection(self, provider_id: str = None) -> Tuple[bool, str]:
        """
        Test connection to a model provider.
        
        Args:
            provider_id: Provider ID to test. If None, tests current provider.
            
        Returns:
            Tuple of (success, message)
        """
        if provider_id is None:
            provider_id = self._current_provider
        
        if not provider_id:
            return False, "No provider specified"
        
        config = self._config.get(provider_id, {})
        api_base = config.get("api_base", "")
        api_key = config.get("api_key", "")
        model_name = config.get("default_model", "")
        
        if not api_base:
            return False, "API base URL not configured"
        
        try:
            from openai import OpenAI
            
            client = OpenAI(
                base_url=api_base,
                api_key=api_key or "no-key"
            )
            
            # Try to list models or make a simple request
            try:
                models = client.models.list()
                model_list = [m.id for m in models.data] if models.data else []
                return True, f"Connection OK. Models: {', '.join(model_list[:5])}"
            except Exception:
                # Some providers don't support model listing
                pass
            
            # Try a simple completion
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            return True, f"Connection OK. Model: {model_name}"
            
        except ImportError:
            return False, "OpenAI library not installed"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def add_model_provider(self, provider_id: str, config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Add a new model provider.
        
        Args:
            provider_id: Unique provider ID
            config: Provider configuration
            
        Returns:
            Tuple of (success, message)
        """
        if provider_id in self._config:
            return False, f"Provider already exists: {provider_id}"
        
        required_fields = ["display_name", "api_base"]
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"
        
        self._config[provider_id] = config
        self.save_config()
        
        return True, f"Added provider: {config.get('display_name', provider_id)}"
    
    def update_model_provider(self, provider_id: str, config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update an existing model provider.
        
        Args:
            provider_id: Provider ID to update
            config: New configuration
            
        Returns:
            Tuple of (success, message)
        """
        if provider_id not in self._config:
            return False, f"Provider not found: {provider_id}"
        
        self._config[provider_id].update(config)
        self.save_config()
        
        return True, f"Updated provider: {provider_id}"
    
    def remove_model_provider(self, provider_id: str) -> Tuple[bool, str]:
        """
        Remove a model provider.
        
        Args:
            provider_id: Provider ID to remove
            
        Returns:
            Tuple of (success, message)
        """
        if provider_id not in self._config:
            return False, f"Provider not found: {provider_id}"
        
        del self._config[provider_id]
        self.save_config()
        
        if self._current_provider == provider_id:
            self._current_provider = None
            self._current_model = None
        
        return True, f"Removed provider: {provider_id}"
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "vllm_local": {
                "display_name": "vLLM Local",
                "api_base": "http://localhost:8000/v1",
                "api_key": "",
                "default_model": "MAI-UI-8B",
            },
            "ollama_local": {
                "display_name": "Ollama Local",
                "api_base": "http://localhost:11434/v1",
                "api_key": "ollama",
                "default_model": "MAI-UI-8B",
            },
            "openai_compatible": {
                "display_name": "OpenAI Compatible",
                "api_base": "",
                "api_key": "",
                "default_model": "",
            },
        }


# Global instance
_model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Get global ModelManager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager
