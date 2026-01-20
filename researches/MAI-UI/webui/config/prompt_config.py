"""
Prompt configuration management module.
Handles loading, saving, and managing prompt templates.
"""

import os
import re
from typing import Any, Dict, List, Optional, Tuple

import yaml
from jinja2 import Template, Environment, meta, TemplateSyntaxError


class PromptManager:
    """
    Prompt template management.
    Provides methods to load, save, edit, and render prompt templates.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize PromptManager.
        
        Args:
            config_path: Path to prompt templates config file.
        """
        if config_path is None:
            config_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(config_dir, "prompt_templates.yaml")
        
        self.config_path = config_path
        self._templates: Dict[str, Dict[str, Any]] = {}
        self._current_template: str = "default"
        self._jinja_env = Environment()
        
        # Load templates on init
        self.load_templates()
    
    def load_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Load templates from YAML file.
        
        Returns:
            Templates dictionary
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._templates = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"[PromptManager] Failed to load templates: {e}")
                self._templates = self._get_default_templates()
        else:
            self._templates = self._get_default_templates()
            self.save_templates()
        
        return self._templates.copy()
    
    def save_templates(self, templates: Dict[str, Dict[str, Any]] = None) -> bool:
        """
        Save templates to YAML file.
        
        Args:
            templates: Templates to save. If None, saves current templates.
            
        Returns:
            Whether save was successful
        """
        if templates is not None:
            self._templates = templates
        
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write("# MAI-UI Prompt Templates Configuration\n")
                f.write("# Edit this file to customize prompt templates\n\n")
                yaml.dump(
                    self._templates, f, 
                    allow_unicode=True, 
                    sort_keys=False, 
                    default_flow_style=False,
                    width=1000  # Prevent line wrapping for long templates
                )
            return True
        except Exception as e:
            print(f"[PromptManager] Failed to save templates: {e}")
            return False
    
    def get_template_names(self) -> List[str]:
        """
        Get list of available template names.
        
        Returns:
            List of template names
        """
        return list(self._templates.keys())
    
    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific template by name.
        
        Args:
            name: Template name
            
        Returns:
            Template dictionary or None
        """
        return self._templates.get(name)
    
    def get_template_content(self, name: str) -> str:
        """
        Get template content string.
        
        Args:
            name: Template name
            
        Returns:
            Template content string
        """
        template = self._templates.get(name, {})
        return template.get("template", "")
    
    def save_template(self, name: str, content: str, metadata: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Save or update a template.
        
        Args:
            name: Template name
            content: Template content (Jinja2 template string)
            metadata: Optional metadata (description, variables, etc.)
            
        Returns:
            Tuple of (success, message)
        """
        # Validate template first
        is_valid, error = self.validate_template(content)
        if not is_valid:
            return False, f"Invalid template: {error}"
        
        if name in self._templates:
            self._templates[name]["template"] = content
            if metadata:
                self._templates[name].update(metadata)
        else:
            self._templates[name] = {
                "name": metadata.get("name", name) if metadata else name,
                "description": metadata.get("description", "") if metadata else "",
                "template": content,
                "variables": metadata.get("variables", []) if metadata else [],
            }
        
        self.save_templates()
        return True, f"Template '{name}' saved successfully"
    
    def render_template(self, name: str, **kwargs) -> str:
        """
        Render a template with given variables.
        
        Args:
            name: Template name
            **kwargs: Template variables
            
        Returns:
            Rendered template string
        """
        template_data = self._templates.get(name, {})
        template_str = template_data.get("template", "")
        
        if not template_str:
            return ""
        
        try:
            template = Template(template_str)
            return template.render(**kwargs)
        except Exception as e:
            print(f"[PromptManager] Failed to render template: {e}")
            return template_str
    
    def validate_template(self, content: str) -> Tuple[bool, str]:
        """
        Validate a Jinja2 template.
        
        Args:
            content: Template content string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self._jinja_env.parse(content)
            return True, ""
        except TemplateSyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.message}"
        except Exception as e:
            return False, str(e)
    
    def get_template_variables(self, name: str = None, content: str = None) -> List[str]:
        """
        Get variables used in a template.
        
        Args:
            name: Template name (if content not provided)
            content: Template content string
            
        Returns:
            List of variable names
        """
        if content is None:
            if name is None:
                return []
            template_data = self._templates.get(name, {})
            content = template_data.get("template", "")
        
        if not content:
            return []
        
        try:
            ast = self._jinja_env.parse(content)
            variables = meta.find_undeclared_variables(ast)
            return sorted(list(variables))
        except Exception as e:
            print(f"[PromptManager] Failed to extract variables: {e}")
            return []
    
    def preview_template(self, name: str, **kwargs) -> str:
        """
        Preview a rendered template with example values.
        
        Args:
            name: Template name
            **kwargs: Override variables
            
        Returns:
            Preview string
        """
        template_data = self._templates.get(name, {})
        variables = self.get_template_variables(name)
        
        # Use provided kwargs or generate example values
        preview_vars = {}
        for var in variables:
            if var in kwargs:
                preview_vars[var] = kwargs[var]
            else:
                # Generate example values based on common variable names
                if var == "tools":
                    preview_vars[var] = "[{\"name\": \"example_tool\", \"description\": \"...\"}]"
                elif var == "goal":
                    preview_vars[var] = "Complete the given task on the mobile device"
                elif var == "instruction":
                    preview_vars[var] = "Open Settings and check Wi-Fi status"
                elif var == "steps":
                    preview_vars[var] = "Step 1: Click Settings icon"
                else:
                    preview_vars[var] = f"<{var}>"
        
        return self.render_template(name, **preview_vars)
    
    def restore_default_template(self, name: str) -> Tuple[bool, str]:
        """
        Restore a template to its default value.
        
        Args:
            name: Template name
            
        Returns:
            Tuple of (success, message)
        """
        defaults = self._get_default_templates()
        if name in defaults:
            self._templates[name] = defaults[name].copy()
            self.save_templates()
            return True, f"Template '{name}' restored to default"
        return False, f"No default available for template '{name}'"
    
    def set_current_template(self, name: str) -> Tuple[bool, str]:
        """
        Set the current active template.
        
        Args:
            name: Template name
            
        Returns:
            Tuple of (success, message)
        """
        if name not in self._templates:
            return False, f"Template not found: {name}"
        
        self._current_template = name
        return True, f"Current template set to: {name}"
    
    def get_current_template_name(self) -> str:
        """Get the name of the current active template."""
        return self._current_template
    
    def get_current_template(self) -> Dict[str, Any]:
        """Get the current active template."""
        return self._templates.get(self._current_template, {})
    
    def _get_default_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get default prompt templates."""
        return {
            "default": {
                "name": "MAI Mobile System Prompt",
                "description": "Default MAI-UI system prompt with MCP tool support",
                "template": MAI_MOBILE_SYS_PROMPT_ASK_USER_MCP,
                "variables": [
                    {"name": "tools", "description": "MCP tools JSON string", "example": "[]"},
                ],
            },
            "qwen3vl": {
                "name": "Qwen3-VL Prompt",
                "description": "Prompt template optimized for Qwen3-VL models",
                "template": MOBILE_QWEN3VL_PROMPT_WITH_ASK_USER,
                "variables": [
                    {"name": "tools", "description": "MCP tools JSON string", "example": "[]"},
                ],
            },
            "planner_executor": {
                "name": "Planner Executor Prompt",
                "description": "Prompt template for planner-executor architecture",
                "template": PLANNER_EXECUTOR_PROMPT_TEMPLATE,
                "variables": [
                    {"name": "tools", "description": "MCP tools JSON string", "example": "[]"},
                    {"name": "goal", "description": "Task goal", "example": "Open Settings"},
                ],
            },
        }


# Default template strings (from trainer/mobile_world/agents/utils/prompts.py)
MAI_MOBILE_SYS_PROMPT_ASK_USER_MCP = """You are a GUI agent. You are given a task and your action history, with screenshots. You need to perform the next action to complete the task. 

## Output Format
For each function call, return the thinking process in <thinking> </thinking> tags, and a json object with function name and arguments within <tool_call></tool_call> XML tags:
```
<thinking>
...
</thinking>
<tool_call>
{"name": "mobile_use", "arguments": <args-json-object>}
</tool_call>
```

## Action Space

{"action": "click", "coordinate": [x, y]}
{"action": "long_press", "coordinate": [x, y]}
{"action": "type", "text": ""}
{"action": "swipe", "direction": "up or down or left or right", "coordinate": [x, y]} # "coordinate" is optional. Use the "coordinate" if you want to swipe a specific UI element.
{"action": "open", "text": "app_name"}
{"action": "drag", "start_coordinate": [x1, y1], "end_coordinate": [x2, y2]}
{"action": "system_button", "button": "button_name"} # Options: back, home, menu, enter 
{"action": "wait"}
{"action": "terminate", "status": "success or fail"} 
{"action": "answer", "text": "xxx"} # Use escape characters \\', \\", and \\n in text part to ensure we can parse the text in normal python string format.
{"action": "ask_user", "text": "xxx"} # you can ask user for more information to complete the task.
{"action": "double_click", "coordinate": [x, y]}

{% if tools -%}
## MCP Tools
You are also provided with MCP tools, you can use them to complete the task.
{{ tools }}

If you want to use MCP tools, you must output as the following format:
```
<thinking>
...
</thinking>
<tool_call>
{"name": <function-name>, "arguments": <args-json-object>}
</tool_call>
```
{% endif -%}


## Note
- Available Apps: `["微信", "抖音", "QQ", "支付宝", "淘宝", "小红书", "飞猪旅行"]`.
- Write a small plan and finally summarize your next action (with its target element) in one sentence in <thinking></thinking> part."""


MOBILE_QWEN3VL_PROMPT_WITH_ASK_USER = """# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{"type": "function", "function": {"name": "mobile_use", "description": "Use a touchscreen to interact with a mobile device, and take screenshots.\\n* This is an interface to a mobile device with touchscreen. You can perform actions like clicking, typing, swiping, etc.\\n* Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to see the results of your actions.\\n* The screen's resolution is 999x999.\\n* Make sure to click any buttons, links, icons, etc with the cursor tip in the center of the element. Don't click boxes on their edges unless asked.", "parameters": {"properties": {"action": {"description": "The action to perform. The available actions are:\\n* `click`: Click the point on the screen with coordinate (x, y).\\n* `long_press`: Press the point on the screen with coordinate (x, y) for specified seconds.\\n* `swipe`: Swipe from the starting point with coordinate (x, y) to the end point with coordinates2 (x2, y2).\\n* `type`: Input the specified text into the activated input box.\\n* `answer`: Output the answer.\\n* `system_button`: Press the system button.\\n* `wait`: Wait specified seconds for the change to happen.\\n* `terminate`: Terminate the current task and report its completion status.\\n* `ask_user`: Ask user for clarification.", "enum": ["click", "long_press", "swipe", "type", "answer", "system_button", "wait", "ask_user", "terminate"], "type": "string"}, "coordinate": {"description": "(x, y): The x (pixels from the left edge) and y (pixels from the top edge) coordinates to move the mouse to. Required only by `action=click`, `action=long_press`, and `action=swipe`.", "type": "array"}, "coordinate2": {"description": "(x, y): The x (pixels from the left edge) and y (pixels from the top edge) coordinates to move the mouse to. Required only by `action=swipe`.", "type": "array"}, "text": {"description": "Required only by `action=type`, `action=ask_user` and `action=answer`.", "type": "string"}, "time": {"description": "The seconds to wait. Required only by `action=long_press` and `action=wait`.", "type": "number"}, "button": {"description": "Back means returning to the previous interface, Home means returning to the desktop, Menu means opening the application background menu, and Enter means pressing the enter. Required only by `action=system_button`", "enum": ["Back", "Home", "Menu", "Enter"], "type": "string"}, "status": {"description": "The status of the task. Required only by `action=terminate`.", "type": "string", "enum": ["success", "failure"]}}, "required": ["action"], "type": "object"}}}
{% if tools %}
{{ tools }}
{% endif -%}
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{"name": <function-name>, "arguments": <args-json-object>}
</tool_call>

# Response format

Response format for every step:
1) Thought: one concise sentence explaining the next move (no multi-step reasoning).
2) Action: a short imperative describing what to do.
3) A single <tool_call>...</tool_call> block containing only the JSON: {"name": <function-name>, "arguments": <args-json-object>}.

Rules:
- Output exactly in the order: Thought, Action, <tool_call>.
- Be brief: one sentence for Thought, one for Action.
- Do not output anything else outside those three parts.
- If finishing, use mobile_use with action=terminate in the tool call."""


PLANNER_EXECUTOR_PROMPT_TEMPLATE = """# Role: Android Phone Operator AI
You are an AI that controls an Android phone to complete user requests. Your responsibilities:
- Answer questions by retrieving information from the phone.
- Perform tasks by executing precise actions.

# Action Framework
Respond with EXACT JSON format for one of these actions:
| Action          | Description                              | JSON Format Example                                                         |
|-----------------|----------------------------------------- |-----------------------------------------------------------------------------|
| `click`         | Tap visible element (describe clearly)   | `{"action_type": "click", "target": "blue circle button at top-right"}`   |
| `double_tap`    | Double-tap visible element               | `{"action_type": "double_tap", "target": "..."}`   |
| `long_press`    | Long-press visible element               | `{"action_type": "long_press", "target": "message from John"}`            |
| `drag`          | Drag between two elements                | `{"action_type": "drag", "target_start": "...", "target_end": "..."}`     |
| `input_text`    | Type into field                          | `{"action_type":"input_text", "text":"Hello"}`                            |
| `answer`        | Respond to user                          | `{"action_type":"answer", "text":"It's 25 degrees today."}`               |
| `navigate_home` | Return to home screen                    | `{"action_type": "navigate_home"}`                                        |
| `navigate_back` | Navigate back                            | `{"action_type": "navigate_back"}`                                        |
| `scroll`        | Scroll direction (up/down/left/right)    | `{"action_type":"scroll", "direction":"down"}`                            |
| `status`        | Mark task as complete or infeasible      | `{"action_type":"status", "goal_status":"complete"}`                      |
| `wait`          | Wait for screen to update                | `{"action_type":"wait"}`                                                  |
| `ask_user`      | Ask user for information                 | `{"action_type":"ask_user", "text":"..."}`                                |

# Execution Principles
1. Communication Rule:
   - ALWAYS use 'answer' action to reply to users
   - NEVER use 'answer' to indicate waiting - use 'wait' instead
   - Note that `answer` will terminate the task immediately.

2. Efficiency First:
   - Choose simplest path to complete tasks
   - If action fails twice, try alternatives

3. Smart Navigation:
   - Gather information when needed
   - For scrolling: scroll down to see lower content

4. Ask User:
   - Use `ask_user` if you need more information

# Expected Output Format:
Thought: [Analysis]
Action: [Single JSON action]

{% if tools -%}
# Available MCP Tools
{{ tools }}
{% endif -%}

# User Goal
{{ goal }}"""


# Global instance
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """Get global PromptManager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
