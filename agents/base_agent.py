"""
Base Agent Class for VaultZero
Provides common functionality for all agents in the system
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import logging
from datetime import datetime
import os

# LangChain/LangGraph imports
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

class BaseAgent(ABC):
    """
    Abstract base class for all VaultZero agents.
    Implements Google Enterprise Agent Architecture patterns.
    """
    
    def __init__(
        self,
        name: str,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.0,
        api_key: Optional[str] = None
    ):
        """
        Initialize base agent.
        
        Args:
            name: Agent name for logging and identification
            model: Claude model to use (default: Sonnet 4)
            temperature: Model temperature (0.0 for deterministic)
            api_key: Anthropic API key (defaults to env var)
        """
        self.name = name
        self.model = model
        self.temperature = temperature
        self.logger = self._setup_logger()
        
        # Initialize Claude client
        self.llm = ChatAnthropic(
            model=model,
            temperature=temperature,
            anthropic_api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=4096
        )
        
        self.logger.info(f"Initialized {name} with model {model}")
    
    def _setup_logger(self) -> logging.Logger:
        """Set up agent-specific logger."""
        logger = logging.getLogger(f"vaultzero.agents.{self.name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.name} - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method - must be implemented by subclasses.
        
        Args:
            state: Current workflow state from LangGraph
            
        Returns:
            Updated state dictionary
        """
        pass
    
    def create_prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List:
        """
        Create structured prompt for Claude.
        
        Args:
            system_prompt: System instructions
            user_prompt: User query/task
            context: Optional context data
            
        Returns:
            List of messages for Claude API
        """
        messages = [SystemMessage(content=system_prompt)]
        
        # Add context if provided
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            user_prompt = f"Context:\n{context_str}\n\nTask:\n{user_prompt}"
        
        messages.append(HumanMessage(content=user_prompt))
        return messages
    
    async def call_claude(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Call Claude API with error handling.
        
        Args:
            system_prompt: System instructions
            user_prompt: User query/task
            context: Optional context data
            
        Returns:
            Claude's response text
        """
        try:
            self.logger.info(f"Calling Claude API with {len(user_prompt)} char prompt")
            
            messages = self.create_prompt(system_prompt, user_prompt, context)
            response = await self.llm.ainvoke(messages)
            
            result = response.content
            self.logger.info(f"Received response: {len(result)} chars")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Claude API error: {str(e)}")
            raise
    
    def extract_structured_data(
        self,
        text: str,
        fields: List[str]
    ) -> Dict[str, Any]:
        """
        Extract structured data from text response.
        
        Args:
            text: Response text from Claude
            fields: List of field names to extract
            
        Returns:
            Dictionary of extracted fields
        """
        # Simple extraction - can be enhanced with JSON parsing
        result = {}
        
        for field in fields:
            # Look for field: value patterns
            import re
            pattern = rf"{field}:\s*(.+?)(?:\n|$)"
            match = re.search(pattern, text, re.IGNORECASE)
            
            if match:
                result[field] = match.group(1).strip()
            else:
                result[field] = None
        
        return result
    
    def validate_state(
        self,
        state: Dict[str, Any],
        required_keys: List[str]
    ) -> bool:
        """
        Validate that state contains required keys.
        
        Args:
            state: Current state dictionary
            required_keys: List of required keys
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        missing = [key for key in required_keys if key not in state]
        
        if missing:
            raise ValueError(f"{self.name} missing required keys: {missing}")
        
        return True
    
    def update_state(
        self,
        state: Dict[str, Any],
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Safely update state with new data.
        
        Args:
            state: Current state
            updates: New data to add
            
        Returns:
            Updated state dictionary
        """
        new_state = state.copy()
        new_state.update(updates)
        new_state['last_updated'] = datetime.now().isoformat()
        new_state['last_agent'] = self.name
        
        self.logger.info(f"Updated state with {len(updates)} new fields")
        
        return new_state
