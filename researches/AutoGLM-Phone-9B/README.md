# AutoGLM: A Deep Dive into the Autonomous GUI Agent

## 1. Introduction

AutoGLM is a series of foundation agents developed by Zhipu AI, built upon the ChatGLM family of models. It is designed for the autonomous control of digital devices through Graphical User Interfaces (GUIs), with a particular focus on web and mobile environments. The initial paper introducing AutoGLM was submitted on October 28, 2024. The core of AutoGLM's innovation lies in its ability to understand and interact with GUIs in a human-like manner, bridging the gap between the vast knowledge of foundation models and the dynamic, real-world decision-making required for seamless device control.

## 2. Research Paper

The foundational research for AutoGLM is detailed in the paper **"AutoGLM: Autonomous Foundation Agents for GUIs"** [1]. The paper is available on arXiv and provides a comprehensive overview of the model's architecture, training methodology, and performance.

> We present AutoGLM, a new series in the ChatGLM family, designed to serve as foundation agents for autonomous control of digital devices through Graphical User Interfaces (GUIs). While foundation models excel at acquiring human knowledge, they often struggle with decision-making in dynamic real-world environments, limiting their progress toward artificial general intelligence. This limitation underscores the importance of developing foundation agents capable of learning through autonomous environmental interactions by reinforcing existing models. Focusing on Web Browser and Phone as representative GUI scenarios, we have developed AutoGLM as a practical foundation agent system for real-world GUI interactions. Our approach integrates a comprehensive suite of techniques and infrastructures to create deployable agent systems suitable for user delivery. Through this development, we have derived two key insights: First, the design of an appropriate "intermediate interface" for GUI control is crucial, enabling the separation of planning and grounding behaviors, which require distinct optimization for flexibility and accuracy respectively. Second, we have developed a novel progressive training framework that enables self-evolving online curriculum reinforcement learning for AutoGLM. Our evaluations demonstrate AutoGLM's effectiveness across multiple domains. For web browsing, AutoGLM achieves a 55.2% success rate on VAB-WebArena-Lite (improving to 59.1% with a second attempt) and 96.2% on OpenTable evaluation tasks. In Android device control, AutoGLM attains a 36.2% success rate on AndroidLab (VAB-Mobile) and 89.7% on common tasks in popular Chinese APPs.

## 3. Open Source

AutoGLM is an open-source project with its code available on GitHub under the Apache-2.0 license. The repository, **"Open-AutoGLM"** [2], has garnered significant attention from the developer community, with over 20,000 stars.

| | |
| :--- | :--- |
| **GitHub URL** | https://github.com/zai-org/Open-AutoGLM |
| **GitHub Stars** | 20.7k |
| **License** | Apache-2.0 |

## 4. Technical Details

### 4.1. Architecture

AutoGLM employs a sophisticated **planner-grounder architecture**. This design separates the high-level task of planning from the low-level task of grounding, which involves identifying and interacting with specific UI elements. This separation allows for the independent optimization of each component, leading to greater flexibility and accuracy. The model is part of the ChatGLM family and the publicly released version, AutoGLM-Phone-9B, has 9 billion parameters.

### 4.2. Training

The training of AutoGLM addresses the critical challenge of data scarcity in decision-making tasks. The researchers employed a multi-faceted approach:

*   **Behavior Cloning (BC):** The model is trained on high-quality expert trajectories to learn from human demonstrations.
*   **Self-Evolving Online Curriculum Reinforcement Learning (RL):** This innovative framework allows the model to learn and improve through its own interactions with the environment, progressively tackling more complex tasks.
*   **Weakly-Supervised Data:** The model also leverages existing online data with weak decision-making signals to augment its training.

## 5. Performance

AutoGLM has demonstrated impressive performance across a range of benchmarks, outperforming other leading models.

| Benchmark | Task | AutoGLM Success Rate | GPT-4o Success Rate | Claude-3.5-Sonnet Success Rate |
| :--- | :--- | :--- | :--- | :--- |
| VAB-WebArena-Lite | Web Browsing | 55.2% (59.1% with 2nd attempt) | 18.2% | - |
| OpenTable | Web Browsing | 96.2% | 62.6% | - |
| AndroidLab (VAB-Mobile) | Android Control | 36.2% | 31.2% | 29.0% |
| Common Chinese APPs | Android Control | 89.7% (human evaluation) | - | - |

## 6. Platforms and Applications

AutoGLM is designed to operate across multiple platforms:

*   **Web:** A browser plugin called "Qingyan" is available for Chrome and Edge.
*   **Android:** A dedicated application leverages the AccessibilityService for device control and is currently available for invited internal testing.

## 7. Conclusion

AutoGLM represents a significant advancement in the field of GUI agents. Its innovative architecture, robust training methodology, and impressive performance make it a powerful tool for automating tasks on digital devices. While challenges such as data scarcity and error recovery remain, AutoGLM's practical applications and open-source nature pave the way for a future where humans and AI can collaborate more seamlessly in the digital world.

## References

[1] Liu, X., et al. (2024). *AutoGLM: Autonomous Foundation Agents for GUIs*. arXiv. https://arxiv.org/abs/2411.00820

[2] zai-org. (2024). *Open-AutoGLM*. GitHub. https://github.com/zai-org/Open-AutoGLM
