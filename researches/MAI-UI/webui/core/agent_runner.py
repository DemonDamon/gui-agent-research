"""
Agent runner module.
Integrates MAI-UI Agent with ADB operations for automated task execution.
Supports dynamic model switching and configurable prompts.
"""

import os
import sys
import json
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Generator, List, Optional
from PIL import Image

from .adb_utils import (
    take_screenshot_file_mode,
    tap_device,
    long_press_device,
    swipe_direction,
    input_text_yadb,
    press_system_button,
    open_app,
    device_cache,
)
from config.model_config import get_model_manager
from config.prompt_config import get_prompt_manager


def format_user_intervention(user_input: str) -> str:
    """
    Format user intervention instruction with high priority prompt.
    
    Args:
        user_input: User input instruction
    
    Returns:
        Formatted high-priority prompt
    """
    return f"""[URGENT USER INTERVENTION - HIGHEST PRIORITY]
User Request: {user_input}

Important Notes:
1. Immediately stop current task execution
2. Prioritize executing user's new instruction
3. Do not output terminate/COMPLETE unless new instruction is completed
4. Execute user's new requirement based on current screen state"""


@dataclass
class StepResult:
    """Single step execution result."""
    step_index: int
    screenshot: Image.Image
    thinking: str
    action: Dict[str, Any]
    action_type: str
    success: bool
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_index": self.step_index,
            "thinking": self.thinking,
            "action": self.action,
            "action_type": self.action_type,
            "success": self.success,
            "message": self.message,
            "timestamp": self.timestamp
        }


class AgentRunner:
    """
    Agent runner.
    Manages MAI-UI Agent lifecycle, executes tasks and records trajectory.
    Supports dynamic model and prompt configuration.
    """
    
    def __init__(
        self,
        device_id: Optional[str] = None,
        logs_dir: str = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        return_to_desktop_on_start: bool = True,
    ):
        """
        Initialize AgentRunner.
        
        Args:
            device_id: Device ID (optional)
            logs_dir: Logs directory path
            tools: MCP tools list
            return_to_desktop_on_start: Whether to return to desktop on new task
        """
        # Get managers
        self.model_manager = get_model_manager()
        self.prompt_manager = get_prompt_manager()
        
        # Configuration
        self.device_id = device_id
        self.logs_dir = logs_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "logs"
        )
        self.tools = tools
        self.auto_reply_enabled = False
        self.return_to_desktop_on_start = return_to_desktop_on_start
        
        # State
        self.is_running = False
        self.is_paused = False
        self.should_stop = False
        self.waiting_for_input = False
        self.user_input: Optional[str] = None
        self.pending_user_feedback: Optional[str] = None
        self.paused_session_id: Optional[str] = None
        self.injected_instruction: Optional[str] = None
        
        # Current task
        self.current_instruction: Optional[str] = None
        self.session_id: Optional[str] = None
        self.step_count = 0
        self.trajectory: List[StepResult] = []
        
        # Agent instance
        self.agent = None
        self.llm_client = None
        
        # Callbacks
        self.on_step_complete: Optional[Callable[[StepResult], None]] = None
        self.on_status_change: Optional[Callable[[str], None]] = None
        
        # Thread lock
        self._lock = threading.Lock()
        
        # Ensure logs directory exists
        os.makedirs(self.logs_dir, exist_ok=True)
    
    def _init_agent(self) -> bool:
        """
        Initialize Agent with current model configuration.
        
        Returns:
            Whether initialization was successful
        """
        config = self.model_manager.get_current_config()
        
        if not config.get("api_base"):
            self._notify_status("Model not configured. Please configure a model provider.")
            return False
        
        try:
            from openai import OpenAI
            
            self.llm_client = OpenAI(
                base_url=config["api_base"],
                api_key=config.get("api_key") or "no-key",
            )
            
            # Try to load MAI-UI Agent if available
            try:
                # Add parent directory to path for MAI-UI agent import
                src_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "MAI-UI-WebUI", "src"
                )
                if src_dir not in sys.path:
                    sys.path.insert(0, src_dir)
                
                from mai_naivigation_agent import MAIUINaivigationAgent
                
                self.agent = MAIUINaivigationAgent(
                    llm_base_url=config["api_base"],
                    model_name=config["model_name"],
                    runtime_conf={
                        "history_n": 3,
                        "temperature": 0.0,
                        "top_k": -1,
                        "top_p": 1.0,
                        "max_tokens": 2048,
                    },
                    tools=self.tools
                )
                print(f"[AgentRunner] MAI-UI Agent initialized: {config['model_name']}")
                return True
                
            except ImportError:
                # Use simple agent mode
                print("[AgentRunner] MAI-UI Agent not found, using simple mode")
                return True
                
        except ImportError:
            self._notify_status("OpenAI library not installed. Please install: pip install openai")
            return False
        except Exception as e:
            self._notify_status(f"Failed to initialize agent: {e}")
            return False
    
    def get_system_prompt(self) -> str:
        """
        Get current system prompt from prompt manager.
        
        Returns:
            System prompt string
        """
        template = self.prompt_manager.get_current_template()
        template_str = template.get("template", "")
        
        # Render with tools if available
        tools_str = json.dumps(self.tools, ensure_ascii=False) if self.tools else ""
        
        try:
            return self.prompt_manager.render_template(
                self.prompt_manager.get_current_template_name(),
                tools=tools_str,
            )
        except Exception:
            return template_str
    
    def start_task(self, instruction: str) -> str:
        """
        Start new task.
        
        Args:
            instruction: Task instruction
        
        Returns:
            session_id
        """
        with self._lock:
            if self.is_running:
                raise RuntimeError("Task already running")
            
            # Initialize agent
            if not self._init_agent():
                raise RuntimeError("Failed to initialize agent")
            
            # Generate Session ID
            self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_instruction = instruction
            self.step_count = 0
            self.trajectory = []
            self.is_running = True
            self.is_paused = False
            self.should_stop = False
            self.waiting_for_input = False
            
            # Reset agent if available
            if self.agent:
                self.agent.reset()
            
            # Return to desktop
            if self.return_to_desktop_on_start:
                self._notify_status("Returning to desktop...")
                try:
                    success = press_system_button("home", self.device_id)
                    if success:
                        time.sleep(0.5)
                        print("[AgentRunner] Returned to desktop")
                except Exception as e:
                    print(f"[AgentRunner] Failed to return to desktop: {e}")
            
            self._notify_status("Task started")
            return self.session_id
    
    def step(self) -> Optional[StepResult]:
        """
        Execute single step.
        
        Returns:
            StepResult or None if cannot execute
        """
        if not self.is_running:
            return None
        
        if self.is_paused:
            return None
        
        if self.should_stop:
            self._finish_task("stopped")
            return None
        
        try:
            # 1. Take screenshot
            print(f"[AgentRunner] Step {self.step_count + 1}: Taking screenshot...")
            self.step_count += 1
            screenshot = take_screenshot_file_mode(self.device_id)
            print(f"[AgentRunner] Screenshot captured: {screenshot.size}")
            
            # 2. Call Agent/LLM for prediction
            action, thinking = self._predict_action(screenshot)
            action_type = action.get("action", "unknown")
            
            # Check pause/stop before executing
            if self.is_paused or self.should_stop:
                return None
            
            # 3. Execute action
            print(f"[AgentRunner] Executing action: {action_type}")
            success, message = self._execute_action(action, screenshot)
            print(f"[AgentRunner] Action result: success={success}, message={message}")
            
            # 4. Create result
            result = StepResult(
                step_index=self.step_count,
                screenshot=screenshot,
                thinking=thinking,
                action=action,
                action_type=action_type,
                success=success,
                message=message
            )
            
            self.trajectory.append(result)
            
            # 5. Save log
            self._save_step_log(result)
            
            # 6. Callback
            if self.on_step_complete:
                self.on_step_complete(result)
            
            # 7. Check termination conditions
            if action_type == "terminate":
                status = action.get("status", "unknown")
                self._finish_task(status)
            elif action_type == "answer":
                self._finish_task("done")
                self._notify_status(f"Task completed: {action.get('text', '')}")
            elif action_type == "ask_user":
                question = action.get("text", "Please provide more information")
                if self.auto_reply_enabled:
                    self._handle_auto_reply(screenshot, question)
                else:
                    self._wait_for_user_input(question)
            
            return result
            
        except Exception as e:
            result = StepResult(
                step_index=self.step_count,
                screenshot=Image.new("RGB", (100, 100)),
                thinking="",
                action={"action": "error"},
                action_type="error",
                success=False,
                message=f"Execution error: {str(e)}"
            )
            self.trajectory.append(result)
            self._notify_status(f"Error: {e}")
            return result
    
    def _predict_action(self, screenshot: Image.Image) -> tuple:
        """
        Predict next action using agent or LLM.
        
        Args:
            screenshot: Current screenshot
            
        Returns:
            Tuple of (action_dict, thinking_str)
        """
        # Resize screenshot to reduce tokens
        pred_screenshot = screenshot.copy()
        max_dim = 1024
        if max(pred_screenshot.size) > max_dim:
            ratio = max_dim / max(pred_screenshot.size)
            new_size = (int(pred_screenshot.width * ratio), int(pred_screenshot.height * ratio))
            pred_screenshot = pred_screenshot.resize(new_size, Image.LANCZOS)
        
        # Get user feedback if any
        feedback = self.pending_user_feedback or self.user_input
        if feedback:
            priority_feedback = format_user_intervention(feedback)
            self.pending_user_feedback = None
            self.user_input = None
        else:
            priority_feedback = None
        
        # Use MAI-UI Agent if available
        if self.agent:
            obs = {"screenshot": pred_screenshot}
            if priority_feedback:
                obs["user_feedback"] = priority_feedback
            
            prediction, action = self.agent.predict(self.current_instruction, obs)
            
            # Parse thinking
            thinking = ""
            if "<thinking>" in prediction:
                thinking = prediction.split("<thinking>")[1].split("</thinking>")[0].strip()
            
            return action, thinking
        
        # Use simple LLM mode
        if self.llm_client:
            return self._predict_with_llm(pred_screenshot, priority_feedback)
        
        # No agent/LLM available
        return {"action": "terminate", "status": "fail"}, "No agent initialized"
    
    def _predict_with_llm(self, screenshot: Image.Image, feedback: str = None) -> tuple:
        """
        Predict action using direct LLM call.
        
        Args:
            screenshot: Current screenshot
            feedback: Optional user feedback
            
        Returns:
            Tuple of (action_dict, thinking_str)
        """
        import base64
        from io import BytesIO
        
        # Convert image to base64
        buffer = BytesIO()
        screenshot.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        # Build messages
        system_prompt = self.get_system_prompt()
        
        user_content = f"Task: {self.current_instruction}"
        if feedback:
            user_content = f"{feedback}\n\n{user_content}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_content},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                    }
                ]
            }
        ]
        
        try:
            config = self.model_manager.get_current_config()
            response = self.llm_client.chat.completions.create(
                model=config["model_name"],
                messages=messages,
                max_tokens=2048,
                temperature=0.0,
            )
            
            content = response.choices[0].message.content
            
            # Parse response
            thinking = ""
            action = {"action": "wait"}
            
            if "<thinking>" in content:
                thinking = content.split("<thinking>")[1].split("</thinking>")[0].strip()
            
            if "<tool_call>" in content:
                tool_call_str = content.split("<tool_call>")[1].split("</tool_call>")[0].strip()
                try:
                    tool_call = json.loads(tool_call_str)
                    if "arguments" in tool_call:
                        action = tool_call["arguments"]
                except json.JSONDecodeError:
                    pass
            
            return action, thinking
            
        except Exception as e:
            print(f"[AgentRunner] LLM prediction failed: {e}")
            return {"action": "wait"}, f"Prediction error: {e}"
    
    def _execute_action(self, action: Dict[str, Any], screenshot: Image.Image) -> tuple:
        """
        Execute action.
        
        Args:
            action: Action dictionary
            screenshot: Current screenshot
            
        Returns:
            Tuple of (success, message)
        """
        action_type = action.get("action", "unknown")
        img_width, img_height = screenshot.size
        
        try:
            if action_type == "click":
                coords = action.get("coordinate", [0.5, 0.5])
                x = int(coords[0] * img_width)
                y = int(coords[1] * img_height)
                success = tap_device(x, y, self.device_id)
                return success, f"Click ({x}, {y})"
            
            elif action_type == "long_press":
                coords = action.get("coordinate", [0.5, 0.5])
                x = int(coords[0] * img_width)
                y = int(coords[1] * img_height)
                success = long_press_device(x, y, device_id=self.device_id)
                return success, f"Long press ({x}, {y})"
            
            elif action_type == "swipe":
                direction = action.get("direction", "up")
                coords = action.get("coordinate")
                x, y = None, None
                if coords:
                    x = int(coords[0] * img_width)
                    y = int(coords[1] * img_height)
                success = swipe_direction(direction, x, y, device_id=self.device_id)
                return success, f"Swipe {direction}"
            
            elif action_type == "type":
                text = action.get("text", "")
                success = input_text_yadb(text, self.device_id)
                return success, f"Type: {text[:20]}..."
            
            elif action_type == "system_button":
                button = action.get("button", "home")
                success = press_system_button(button, self.device_id)
                return success, f"Press {button}"
            
            elif action_type == "open":
                app_name = action.get("text", "")
                success, msg = open_app(app_name, self.device_id, prefer_awake=True)
                return success, msg
            
            elif action_type == "wait":
                time.sleep(2)
                return True, "Wait 2 seconds"
            
            elif action_type == "terminate":
                status = action.get("status", "unknown")
                return True, f"Terminate: {status}"
            
            elif action_type == "answer":
                text = action.get("text", "")
                return True, f"Answer: {text}"
            
            elif action_type == "ask_user":
                text = action.get("text", "")
                return True, f"Ask user: {text}"
            
            elif action_type == "mcp_call":
                return self._handle_mcp_call(action)
            
            else:
                return False, f"Unknown action type: {action_type}"
                
        except Exception as e:
            return False, f"Action execution failed: {str(e)}"
    
    def _handle_mcp_call(self, action: Dict[str, Any]) -> tuple:
        """Handle MCP tool call."""
        tool_name = action.get("name", "unknown")
        arguments = action.get("arguments", {})
        
        self._notify_status(f"MCP tool call: {tool_name}")
        
        # TODO: Implement actual MCP call
        return True, f"MCP call: {tool_name}({arguments})"
    
    def _wait_for_user_input(self, prompt: str):
        """Wait for user input."""
        self.waiting_for_input = True
        self.is_paused = True
        self._notify_status(f"Waiting for user input: {prompt}")
    
    def provide_user_input(self, text: str):
        """Provide user input."""
        with self._lock:
            if self.waiting_for_input:
                self.user_input = text
                self.waiting_for_input = False
                self.is_paused = False
                self._notify_status("User input received, continuing execution")
    
    def _handle_auto_reply(self, screenshot: Image.Image, question: str):
        """Generate and apply auto reply."""
        self._notify_status(f"Generating auto reply: {question}")
        
        try:
            # Use LLM to generate reply
            import base64
            from io import BytesIO
            
            buffer = BytesIO()
            screenshot.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            
            prompt = f"""# Role
You are a user interacting with a GUI Agent to complete a task.

# Task
Read the background information below and generate a brief, direct answer to the Agent's clarification question.

# Background
- **Original Task:** {self.current_instruction}
- **Agent's Question:** {question}

# Output Requirements
- Your answer must be extremely brief and clear.
- Answer the core of the question directly.
- Do not provide explanations, dialogue, or polite phrases.
- Output only the answer itself."""
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                        }
                    ]
                }
            ]
            
            config = self.model_manager.get_current_config()
            response = self.llm_client.chat.completions.create(
                model=config["model_name"],
                messages=messages,
                max_tokens=200,
                temperature=0.0
            )
            
            reply = response.choices[0].message.content.strip()
            print(f"[AgentRunner] Auto-reply generated: {reply}")
            
            self.user_input = reply
            self._notify_status(f"Auto-reply generated: {reply}")
            
        except Exception as e:
            print(f"[AgentRunner] Auto-reply failed: {e}")
            self._wait_for_user_input(question)
    
    def auto_run(self, max_steps: int = 50, step_delay: float = 1.0) -> Generator[StepResult, None, None]:
        """
        Auto-run until termination.
        
        Args:
            max_steps: Maximum steps
            step_delay: Delay between steps (seconds)
        
        Yields:
            StepResult
        """
        for _ in range(max_steps):
            if self.should_stop or not self.is_running:
                break
            
            if self.is_paused:
                print("[AgentRunner] auto_run: Paused, exiting generator")
                return
            
            result = self.step()
            if result:
                yield result
                
                if result.action_type == "terminate":
                    break
            else:
                if self.is_paused or self.should_stop:
                    return
            
            # Delay with interruption check
            delay_elapsed = 0.0
            while delay_elapsed < step_delay:
                if self.should_stop or self.is_paused:
                    break
                time.sleep(0.1)
                delay_elapsed += 0.1
    
    def pause(self) -> str:
        """Pause task."""
        with self._lock:
            if self.is_running:
                self.is_paused = True
                self.paused_session_id = self.session_id
                status = f"Paused (Session: {self.session_id[:8] if self.session_id else 'unknown'}...)"
                self._notify_status(status)
                return status
            return "No running task"
    
    def resume(self, injection: str = None):
        """Resume task with optional instruction injection."""
        with self._lock:
            if self.is_running and self.is_paused:
                if injection:
                    old_instruction = self.current_instruction
                    self.current_instruction = injection
                    self.pending_user_feedback = injection
                    self.injected_instruction = injection
                    print(f"[AgentRunner] Instruction injected: {injection}")
                self.is_paused = False
                self.paused_session_id = None
                self._notify_status("Task resumed")
    
    def stop(self):
        """Stop task."""
        with self._lock:
            self.should_stop = True
            self.is_running = False
            self.is_paused = False
            self.paused_session_id = None
            self.pending_user_feedback = None
            self.injected_instruction = None
            self._notify_status("Task stopped")
    
    def _finish_task(self, status: str):
        """Finish task."""
        with self._lock:
            self.is_running = False
            self.is_paused = False
            self._notify_status(f"Task completed: {status}")
    
    def _save_step_log(self, result: StepResult):
        """Save step log."""
        if not self.session_id:
            return
        
        session_dir = os.path.join(self.logs_dir, self.session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Save screenshot
        screenshot_path = os.path.join(session_dir, f"step_{result.step_index:03d}.png")
        result.screenshot.save(screenshot_path)
        
        # Save log
        log_path = os.path.join(session_dir, "trajectory.jsonl")
        log_entry = result.to_dict()
        log_entry["screenshot_path"] = screenshot_path
        log_entry["instruction"] = self.current_instruction
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    def _notify_status(self, status: str):
        """Notify status change."""
        if self.on_status_change:
            self.on_status_change(status)
        print(f"[AgentRunner] {status}")
    
    def get_trajectory(self) -> List[StepResult]:
        """Get current trajectory."""
        return self.trajectory.copy()
    
    def get_status(self) -> str:
        """Get current status."""
        if self.waiting_for_input:
            return "Waiting for input"
        elif self.is_paused:
            return "Paused"
        elif self.is_running:
            return "Running"
        else:
            return "Ready"
    
    def is_waiting_for_input(self) -> bool:
        """Check if waiting for user input."""
        return self.waiting_for_input


# Global singleton
_runner: Optional[AgentRunner] = None


def get_runner() -> AgentRunner:
    """Get global AgentRunner instance."""
    global _runner
    if _runner is None:
        _runner = AgentRunner()
    return _runner


def reset_runner(**kwargs) -> AgentRunner:
    """Reset global AgentRunner."""
    global _runner
    _runner = AgentRunner(**kwargs)
    return _runner
