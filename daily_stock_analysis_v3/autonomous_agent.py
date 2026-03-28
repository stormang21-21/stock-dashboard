"""
Autonomous Research Agent

Inspired by Dexter - breaks complex queries into steps, validates work, and iterates.
"""

from typing import List, Dict, Any, Optional, Generator
from datetime import datetime
import json
import logging
import re
from pathlib import Path
from agent_tools import get_agent_tools

logger = logging.getLogger(__name__)


class TaskPlanner:
    """Break complex queries into structured research steps"""
    
    def __init__(self):
        self.max_steps = 10
    
    def plan(self, query: str) -> List[Dict[str, Any]]:
        """
        Break down complex query into research steps.
        
        Example:
        Query: "Compare AAPL vs MSFT financials"
        Steps: [
            {"tool": "get_financials", "args": {"symbol": "AAPL"}},
            {"tool": "get_financials", "args": {"symbol": "MSFT"}},
            {"tool": "compare_metrics", "args": {"symbols": ["AAPL", "MSFT"]}},
            {"tool": "generate_report", "args": {}}
        ]
        """
        # Simple rule-based planning (can be enhanced with LLM)
        query_lower = query.lower()
        
        steps = []
        
        # Detect comparison queries
        if 'compare' in query_lower or 'vs' in query_lower or 'versus' in query_lower:
            # Extract symbols (simple regex)
            symbols = re.findall(r'\b[A-Z]{2,5}\b', query)
            symbols = [s for s in symbols if len(s) <= 5]
            
            if len(symbols) >= 2:
                # Add steps for each symbol
                for symbol in symbols[:3]:  # Max 3 symbols
                    steps.append({
                        'tool': 'get_stock_data',
                        'args': {'symbol': symbol},
                        'status': 'pending'
                    })
                
                # Add comparison step
                steps.append({
                    'tool': 'compare_stocks',
                    'args': {'symbols': symbols[:3]},
                    'status': 'pending'
                })
                
                # Add report generation
                steps.append({
                    'tool': 'generate_research_report',
                    'args': {'query': query},
                    'status': 'pending'
                })
        
        # Detect single stock research
        elif 'analyze' in query_lower or 'research' in query_lower:
            symbols = re.findall(r'\b[A-Z]{2,5}\b', query)
            if symbols:
                symbol = symbols[0]
                steps.append({
                    'tool': 'get_stock_data',
                    'args': {'symbol': symbol},
                    'status': 'pending'
                })
                steps.append({
                    'tool': 'get_news',
                    'args': {'symbol': symbol},
                    'status': 'pending'
                })
                steps.append({
                    'tool': 'get_technical_analysis',
                    'args': {'symbol': symbol},
                    'status': 'pending'
                })
                steps.append({
                    'tool': 'generate_research_report',
                    'args': {'query': query},
                    'status': 'pending'
                })
        
        # Default: simple analysis
        else:
            symbols = re.findall(r'\b[A-Z]{2,5}\b', query)
            if symbols:
                steps.append({
                    'tool': 'analyze_stock',
                    'args': {'symbol': symbols[0]},
                    'status': 'pending'
                })
        
        return steps[:self.max_steps]


class SelfValidator:
    """Check work and iterate until confident"""
    
    def __init__(self):
        self.confidence_threshold = 0.8
    
    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate result and return confidence score.
        
        Returns:
        {
            'valid': bool,
            'confidence': float,
            'issues': List[str],
            'suggestions': List[str]
        }
        """
        issues = []
        suggestions = []
        confidence = 1.0
        
        # Check if result has required fields
        if 'data' not in result:
            issues.append('Missing data field')
            confidence -= 0.3
        
        # Check data quality
        if 'data' in result:
            data = result['data']
            
            # Check for empty data
            if isinstance(data, dict) and not data:
                issues.append('Empty data returned')
                confidence -= 0.5
            
            # Check for error messages
            if isinstance(data, dict) and 'error' in data:
                issues.append(f"Error in data: {data['error']}")
                confidence -= 0.4
        
        # Check completeness
        if 'summary' not in result:
            suggestions.append('Add summary')
            confidence -= 0.1
        
        return {
            'valid': confidence >= self.confidence_threshold,
            'confidence': confidence,
            'issues': issues,
            'suggestions': suggestions
        }


class ScratchpadLogger:
    """JSONL logging for all actions (like Dexter)"""
    
    def __init__(self, log_dir: str = '.dexter/scratchpad'):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_log = None
    
    def start_session(self, query: str) -> str:
        """Start new session log"""
        timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
        import uuid
        session_id = uuid.uuid4().hex[:12]
        
        log_file = self.log_dir / f"{timestamp}_{session_id}.jsonl"
        self.current_log = open(log_file, 'w')
        
        # Log initialization
        self.log('init', {
            'query': query,
            'timestamp': datetime.now().isoformat()
        })
        
        return str(log_file)
    
    def log(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log event to current session"""
        if self.current_log:
            entry = {
                'type': event_type,
                'timestamp': datetime.now().isoformat(),
                **data
            }
            self.current_log.write(json.dumps(entry) + '\n')
            self.current_log.flush()
    
    def log_tool_result(self, tool_name: str, args: Dict, result: Any, summary: str) -> None:
        """Log tool execution"""
        self.log('tool_result', {
            'toolName': tool_name,
            'args': args,
            'result': result if isinstance(result, (dict, list)) else str(result),
            'llmSummary': summary
        })
    
    def log_thinking(self, thought: str) -> None:
        """Log agent reasoning"""
        self.log('thinking', {'thought': thought})
    
    def close(self) -> None:
        """Close current session log"""
        if self.current_log:
            self.current_log.close()
            self.current_log = None


class AutonomousAgent:
    """
    Autonomous research agent inspired by Dexter.
    
    Features:
    - Task planning (break complex queries into steps)
    - Self-validation (check work and iterate)
    - Scratchpad logging (JSONL audit trail)
    - Tool execution (automatic tool selection)
    """
    
    def __init__(self):
        self.planner = TaskPlanner()
        self.validator = SelfValidator()
        self.logger = ScratchpadLogger()
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, callable]:
        """Register available tools (uses real APIs when available)"""
        agent_tools = get_agent_tools()
        return {
            'get_stock_data': agent_tools.get_stock_data,
            'get_news': agent_tools.get_news,
            'get_technical_analysis': agent_tools.get_technical_analysis,
            'analyze_stock': agent_tools.analyze_stock,
            'compare_stocks': agent_tools.compare_stocks,
            'generate_research_report': agent_tools.generate_research_report,
        }
    
    def execute(self, query: str) -> Generator[Dict[str, Any], None, None]:
        """
        Execute research query autonomously.
        
        Yields events for real-time UI updates:
        - {'type': 'planning', 'steps': [...]}
        - {'type': 'executing', 'tool': '...', 'args': {...}}
        - {'type': 'validating', 'confidence': 0.95}
        - {'type': 'result', 'data': {...}}
        """
        # Start scratchpad logging
        log_file = self.logger.start_session(query)
        self.logger.log_thinking(f"Starting research: {query}")
        
        try:
            # Step 1: Plan
            self.logger.log_thinking("Planning research steps...")
            steps = self.planner.plan(query)
            
            yield {
                'type': 'planning',
                'steps': steps,
                'log_file': log_file
            }
            
            # Step 2: Execute steps
            results = {}
            for i, step in enumerate(steps):
                tool_name = step['tool']
                args = step['args']
                
                self.logger.log_thinking(f"Executing step {i+1}/{len(steps)}: {tool_name}")
                
                yield {
                    'type': 'executing',
                    'step': i + 1,
                    'total': len(steps),
                    'tool': tool_name,
                    'args': args
                }
                
                # Execute tool
                if tool_name in self.tools:
                    tool_func = self.tools[tool_name]
                    result = tool_func(**args)
                    results[tool_name] = result
                    
                    # Log tool result
                    self.logger.log_tool_result(
                        tool_name,
                        args,
                        result,
                        f"Executed {tool_name}"
                    )
                    
                    yield {
                        'type': 'tool_result',
                        'tool': tool_name,
                        'result': result
                    }
            
            # Step 3: Validate
            self.logger.log_thinking("Validating results...")
            validation = self.validator.validate({'data': results})
            
            yield {
                'type': 'validating',
                'confidence': validation['confidence'],
                'valid': validation['valid'],
                'issues': validation['issues']
            }
            
            # Step 4: Generate final result
            final_result = {
                'query': query,
                'results': results,
                'validation': validation,
                'log_file': log_file
            }
            
            self.logger.log('result', final_result)
            
            yield {
                'type': 'result',
                'data': final_result
            }
            
        except Exception as e:
            self.logger.log('error', {'error': str(e)})
            yield {
                'type': 'error',
                'error': str(e)
            }
        
        finally:
            self.logger.close()


# Singleton instance
agent = AutonomousAgent()


def run_research(query: str):
    """Run autonomous research"""
    return agent.execute(query)


if __name__ == "__main__":
    # Test
    print("Testing autonomous agent...")
    
    query = "Compare AAPL vs MSFT"
    print(f"Query: {query}\n")
    
    for event in run_research(query):
        event_type = event.get('type')
        
        if event_type == 'planning':
            print(f"📋 Planning {len(event['steps'])} steps...")
            for i, step in enumerate(event['steps']):
                print(f"   {i+1}. {step['tool']}: {step['args']}")
        
        elif event_type == 'executing':
            print(f"🔧 Executing {event['tool']} ({event['step']}/{event['total']})...")
        
        elif event_type == 'validating':
            print(f"✅ Validating (confidence: {event['confidence']:.2f})...")
        
        elif event_type == 'result':
            print(f"📊 Research complete!")
            print(f"   Log file: {event['data']['log_file']}")
        
        elif event_type == 'error':
            print(f"❌ Error: {event['error']}")
