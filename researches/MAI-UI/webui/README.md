# MAI-UI WebUI

Modern web interface for Android GUI automation with AI agent.

## Features

- **Device Management**: USB and wireless ADB device connection
- **Task Execution**: Auto/single-step/pause/stop task control
- **Trajectory Visualization**: Chatbot-style trajectory display with action markers
- **Dynamic Model Configuration**: Support for vLLM, Ollama, OpenAI-compatible APIs
- **Configurable Prompts**: Edit and manage prompt templates via UI
- **One-Click Data Export**: Convert trajectory data to training formats (SFT/RL/OpenAI)
- **Modern UI**: Beautiful dark theme with responsive design

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Optional: Install reportlab for PDF export
pip install reportlab
```

## Quick Start

```bash
# Run the WebUI
python app.py

# Or with custom port
MAI_UI_PORT=8080 python app.py
```

Open `http://localhost:7860` in your browser.

## Directory Structure

```
webui/
├── app.py                    # Main application entry
├── requirements.txt          # Dependencies
├── config/
│   ├── model_config.py       # Model configuration management
│   ├── model_config.yaml     # Model provider settings
│   ├── prompt_config.py      # Prompt template management
│   ├── prompt_templates.yaml # Prompt templates
│   └── default_package_map.yaml  # App name to package mapping
├── core/
│   ├── agent_runner.py       # Agent execution controller
│   ├── adb_utils.py          # ADB utility functions
│   └── trajectory_utils.py   # Trajectory processing
├── ui/
│   ├── styles.py             # CSS and JavaScript
│   └── components/           # UI panel components
│       ├── device_panel.py
│       ├── task_panel.py
│       ├── trajectory_panel.py
│       ├── model_config_panel.py
│       ├── prompt_editor.py
│       └── data_export_panel.py
├── data/
│   ├── formats.py            # Data format definitions
│   └── converter.py          # Training data converter
├── utils/
│   └── package_map.py        # App package mapping
└── logs/                     # Session logs directory
```

## Usage Guide

### 1. Connect Device

1. Connect Android device via USB or wireless ADB
2. Click "Refresh" to detect devices
3. Select device from dropdown

### 2. Configure Model

1. Select model provider (vLLM/Ollama/OpenAI)
2. Enter API base URL and model name
3. Click "Test Connection" to verify
4. Click "Apply" to activate

### 3. Run Task

1. Enter task instruction (e.g., "Open WeChat and send message")
2. Click "Start Task" to begin
3. Use "Auto Run" for continuous execution
4. Use "Pause" to intervene and provide feedback
5. Use "Stop" to terminate

### 4. Export Training Data

1. Go to "Data Export" tab
2. Select sessions to export
3. Choose output format (SFT/RL/OpenAI)
4. Configure image format and options
5. Click "Export Training Data"

### 5. Customize Prompts

1. Go to "Prompt Configuration" tab
2. Select a template to edit
3. Modify the Jinja2 template
4. Click "Preview" to test
5. Click "Save" to persist changes

## Configuration

### Model Configuration (model_config.yaml)

```yaml
vllm_local:
  display_name: "vLLM Local"
  api_base: "http://localhost:8000/v1"
  api_key: ""
  default_model: "MAI-UI-8B"
```

### Prompt Templates (prompt_templates.yaml)

```yaml
default:
  name: "Default Prompt"
  description: "Description"
  template: |
    Your Jinja2 template here...
    {% if tools %}{{ tools }}{% endif %}
  variables:
    - name: "tools"
      description: "MCP tools"
```

## Data Formats

### Output Formats

- **SFT (Prompt-Response)**: For supervised fine-tuning
- **RL (Full Trajectory)**: For reinforcement learning
- **OpenAI Messages**: Standard chat completion format

### Image Formats

- **Base64**: Inline encoded images
- **Path**: File path references
- **Skip**: Exclude images

## Troubleshooting

### ADB Connection Issues

```bash
# Restart ADB server
adb kill-server && adb start-server

# Check connected devices
adb devices
```

### Model Connection Issues

1. Verify API base URL is correct
2. Check if model server is running
3. Test with curl: `curl http://localhost:8000/v1/models`

## License

MIT License
