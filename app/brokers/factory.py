"""
Broker Factory
Creates and manages different broker implementations
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import boto3

from .base import BaseBroker
from .tradelocker import TradeLockerBroker

logger = logging.getLogger(__name__)

class BrokerFactory:
    """Factory for creating broker instances"""
    
    def __init__(self):
        self.secrets_manager = boto3.client('secretsmanager')
        self.brokers = {}
    
    def get_broker(self, broker_type: str = None) -> BaseBroker:
        """Get a broker instance"""
        # Default to TradeLocker if no broker type specified
        if not broker_type:
            broker_type = os.environ.get('BROKER_TYPE', 'tradelocker')
        
        # Return cached broker if available
        if broker_type in self.brokers:
            return self.brokers[broker_type]
        
        # Get credentials for the broker
        credentials = self._get_broker_credentials(broker_type)
        
        # Create broker instance
        broker = self._create_broker(broker_type, credentials)
        
        # Cache the broker
        self.brokers[broker_type] = broker
        
        return broker
    
    def _get_broker_credentials(self, broker_type: str) -> Dict[str, Any]:
        """Get credentials for a specific broker"""
        try:
            # Try AWS Secrets Manager first
            secret_name = os.environ.get(f'{broker_type.upper()}_SECRET_NAME', f'{broker_type}/credentials')
            response = self.secrets_manager.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except Exception as e:
            logger.warning(f"Failed to get credentials from Secrets Manager: {e}")
            
            # Fall back to environment variables
            if broker_type == 'tradelocker':
                return {
                    'environment': os.environ.get('TRADELOCKER_ENVIRONMENT', 'https://demo.tradelocker.com'),
                    'username': os.environ.get('TRADELOCKER_USERNAME'),
                    'password': os.environ.get('TRADELOCKER_PASSWORD'),
                    'server': os.environ.get('TRADELOCKER_SERVER')
                }
            elif broker_type == 'oanda':
                return {
                    'api_key': os.environ.get('OANDA_API_KEY'),
                    'account_id': os.environ.get('OANDA_ACCOUNT_ID'),
                    'environment': os.environ.get('OANDA_ENVIRONMENT', 'practice')
                }
            elif broker_type == 'alpaca':
                return {
                    'api_key': os.environ.get('ALPACA_API_KEY'),
                    'secret_key': os.environ.get('ALPACA_SECRET_KEY'),
                    'paper': os.environ.get('ALPACA_PAPER', 'true').lower() == 'true'
                }
            elif broker_type == 'interactive_brokers':
                return {
                    'host': os.environ.get('IB_HOST', '127.0.0.1'),
                    'port': int(os.environ.get('IB_PORT', '7497')),
                    'client_id': int(os.environ.get('IB_CLIENT_ID', '1'))
                }
            else:
                raise ValueError(f"Unsupported broker type: {broker_type}")
    
    def _create_broker(self, broker_type: str, credentials: Dict[str, Any]) -> BaseBroker:
        """Create a broker instance based on type"""
        if broker_type == 'tradelocker':
            return TradeLockerBroker(credentials)
        elif broker_type == 'oanda':
            # TODO: Implement OANDA broker
            raise NotImplementedError("OANDA broker not yet implemented")
        elif broker_type == 'alpaca':
            # TODO: Implement Alpaca broker
            raise NotImplementedError("Alpaca broker not yet implemented")
        elif broker_type == 'interactive_brokers':
            # TODO: Implement Interactive Brokers broker
            raise NotImplementedError("Interactive Brokers broker not yet implemented")
        else:
            raise ValueError(f"Unsupported broker type: {broker_type}")
    
    def get_available_brokers(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available brokers and their status"""
        available_brokers = {
            'tradelocker': {
                'name': 'TradeLocker',
                'status': 'implemented',
                'description': 'TradeLocker CFD and forex trading'
            },
            'oanda': {
                'name': 'OANDA',
                'status': 'planned',
                'description': 'OANDA forex and CFD trading'
            },
            'alpaca': {
                'name': 'Alpaca',
                'status': 'planned',
                'description': 'Alpaca stock and crypto trading'
            },
            'interactive_brokers': {
                'name': 'Interactive Brokers',
                'status': 'planned',
                'description': 'Interactive Brokers multi-asset trading'
            }
        }
        
        return available_brokers 