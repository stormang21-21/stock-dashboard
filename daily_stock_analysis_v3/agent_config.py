"""
Agent Configuration

Optional API integrations - enable only what you need.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class AgentConfig:
    """Configuration for autonomous agent"""
    
    def __init__(self, config_file: str = 'agent_config.json'):
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        
        # Create default config
        default_config = {
            'apis': {
                'yfinance': {'enabled': True, 'api_key': None},
                'newsapi': {'enabled': False, 'api_key': None},
                'financial_datasets': {'enabled': False, 'api_key': None},
                'alpha_vantage': {'enabled': False, 'api_key': None},
            },
            'features': {
                'task_planning': True,
                'self_validation': True,
                'scratchpad_logging': True,
                'llm_enhanced': False,  # Requires OpenAI/Anthropic key
            },
            'limits': {
                'max_steps': 10,
                'max_retries': 3,
                'confidence_threshold': 0.8,
            }
        }
        
        # Save default config
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info(f"Created default config: {self.config_file}")
        return default_config
    
    def is_api_enabled(self, api_name: str) -> bool:
        """Check if API is enabled"""
        api_config = self.config['apis'].get(api_name, {})
        enabled = api_config.get('enabled', False)
        has_key = api_config.get('api_key') is not None
        return enabled and has_key
    
    def get_api_key(self, api_name: str) -> Optional[str]:
        """Get API key"""
        api_config = self.config['apis'].get(api_name, {})
        return api_config.get('api_key')
    
    def update_api(self, api_name: str, enabled: bool, api_key: Optional[str] = None) -> None:
        """Update API configuration"""
        if api_name not in self.config['apis']:
            self.config['apis'][api_name] = {'enabled': False, 'api_key': None}
        
        self.config['apis'][api_name]['enabled'] = enabled
        if api_key:
            self.config['apis'][api_name]['api_key'] = api_key
        
        self._save_config()
    
    def _save_config(self) -> None:
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_feature(self, feature_name: str) -> bool:
        """Check if feature is enabled"""
        return self.config['features'].get(feature_name, False)
    
    def get_limit(self, limit_name: str) -> Any:
        """Get limit value"""
        return self.config['limits'].get(limit_name)
    
    def to_dict(self) -> Dict[str, Any]:
        """Get config as dict (without API keys)"""
        config_copy = self.config.copy()
        # Hide API keys
        for api in config_copy['apis'].values():
            if api.get('api_key'):
                api['api_key'] = '***configured***'
        return config_copy


# Singleton instance
config = AgentConfig()


def get_agent_config() -> AgentConfig:
    """Get agent configuration"""
    return config


if __name__ == "__main__":
    # Test
    print("Agent Configuration:")
    print(config.to_dict())
    
    print("\nAPI Status:")
    for api_name in config.config['apis']:
        enabled = config.is_api_enabled(api_name)
        print(f"  {api_name}: {'✅ Enabled' if enabled else '❌ Disabled'}")
