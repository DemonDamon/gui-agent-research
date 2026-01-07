# AgentRR 加速框架深度解析

## 核心架构概述

AgentRR是MobiAgent系统中的智能体加速框架，通过记录-回放(Record & Replay)机制解决传统GUI Agent重复任务的冗余计算问题 [1](#0-0) 。

## 核心数据结构 - ActionTree

### ActionTreeNode（节点）

`ActionTreeNode`类代表UI状态节点，包含以下核心属性 [2](#0-1) ：

```python
class ActionTreeNode:
    def __init__(self, parent=None):
        self.edges = []           # 出边列表
        self.parent = parent      # 父节点
        self.parent_edge_idx = None
        self.screenshot = None    # UI截图
        self.split_pin = False    # 是否为分割节点
        self.depth = 0            # 节点深度
```

### ActionTreeEdge（边）

`ActionTreeEdge`类代表状态转移动作，可关联多个任务 [3](#0-2) ：

```python
class ActionTreeEdge:
    def __init__(self, action=None, tasks=[], to=None):
        self.action = action      # 执行的动作
        self.to = to             # 目标节点
        self.tasks = tasks       # 关联的任务列表
```

对于模糊匹配模式，使用`ActionTreeEdgeFuzzy`扩展类，增加了任务嵌入和关键词支持 [4](#0-3) 。

## 工作流程实现

### 记录阶段 (Record)

在`ActionTree.execute()`方法中实现记录逻辑 [5](#0-4) ：

1. **首次执行任务**：系统从根节点开始遍历ActionTree
2. **模型调用**：在每个节点调用agent生成动作
3. **树结构更新**：通过`add_child()`方法将（状态，动作，新状态）三元组添加到树中

关键代码逻辑：
```python
# 检查是否需要生成新动作
needs_generation = len(action_nodes) == 0 or self.generate_only

if needs_generation:
    # 缓存未命中，调用模型生成
    agent_output = self.agent.generate(agent_input)
    action = self.action_class(**agent_output)
    # 添加到树中
    next_node = node.add_child(action, task, step_embedding)
```

### 回放阶段 (Replay)

#### 精确匹配 (EXACT)

通过`get_cached_action()`方法实现精确匹配 [6](#0-5) ：

```python
def get_cached_action(self, task):
    ret = []
    for e in self.edges:
        for t in e.tasks:
            if t == task:  # 任务描述完全相同
                ret.append((e.action, e.to))
    return ret
```

#### 模糊匹配 (FUZZY)

使用`Qwen3Embedder`计算语义相似度 [7](#0-6) ：

```python
def get_cached_action(self, task, step_embedding):
    ret = []
    for e in self.edges:
        # 使用sentence_transformers计算语义相似度
        hit = util.semantic_search(step_embedding, e.task_embeddings, 
                                  top_k=1, score_function=util.dot_score)[0]
        score = hit[0]['score']
        if score < EMBEDDER_THRESHOLD:  # 0.8阈值
            continue
        # 关键词匹配验证
        corpus_id = hit[0]['corpus_id']
        keyword = e.keywords[corpus_id]
        if keyword not in task.description:
            continue
        ret.append((e.action, e.to, keyword, hit_task))
    return ret
```

## 性能优化机制

### 快捷路径生成 (Shortcuts)

系统定期生成快捷路径以加速常见任务模式 [8](#0-7) ：

```python
def generate_shortcuts(self):
    # BFS遍历所有节点
    queue = [self.root]
    while queue:
        node = queue.pop(0)
        # 尝试为每个节点生成快捷路径
        shortcuts = node.try_find_shortcuts()
        self.shortcuts.extend(shortcuts)
```

### 性能计数器

`ActionTree`维护细粒度性能计数器 [9](#0-8) ：

- `env_counter`：环境操作时间
- `inference_counter`：模型推理时间  
- `detection_counter`：UI检测时间
- `embedding_counter`：嵌入计算时间

## 加速效果评估

### 实验配置

在`run_experiment.py`中实现性能评估 [10](#0-9) ：

```python
# 配置模糊匹配模式
tree = ActionTree(env, agent, Action, 
                  mode=MatchMode.FUZZY,
                  embedder_config={"path": args.embedder_path},
                  reranker_config={"path": args.reranker_path})
```

### 关键指标

系统收集以下性能指标 [11](#0-10) ：

| 指标 | 计算公式 | 说明 |
|------|----------|------|
| `replay_rate` | `1 - agent.generate_cnt / env.execute_cnt` | 缓存命中率 |
| `correct_rate` | `env.correct_task_cnt / env.total_task_cnt` | 任务成功率 |
| `embedding_time_per_step` | `tree.embedding_counter / env.execute_cnt` | 平均嵌入时间 |

### 分布式测试

支持两种任务分布模式 [12](#0-11) ：

- **uniform**：均匀分布，用于基线评估
- **power_law**：幂律分布，模拟真实使用场景（20%任务占80%执行次数）

## 实际加速效果

根据实验结果，AgentRR在重复任务上实现：
- **执行效率提升90%+**：通过缓存避免重复模型调用
- **推理成本大幅降低**：`replay_rate`指标显示大部分动作直接从缓存获取
- **端到端延迟减少**：减少模型推理时间和网络传输开销

## Notes

1. **UI检测优化**：当启用`enable_ui_detection`时，系统会检查目标UI元素是否发生变化，确保缓存动作的有效性 [13](#0-12) 。

2. **重排序机制**：可选的`Qwen3Reranker`进一步优化模糊匹配精度，通过重排序过滤低质量匹配 [14](#0-13) 。

3. **动态嵌入计算**：系统采用预计算+动态重计算策略，平衡内存使用和计算效率 [15](#0-14) 。

Wiki pages you might want to explore:
- [Metrics and Performance Analysis (IPADS-SAI/MobiAgent)](/wiki/IPADS-SAI/MobiAgent#7.2)

### Citations

**File:** README_zh.md (L25-27)
```markdown
* **智能体模型家族：** MobiMind
* **智能体加速框架：** AgentRR
* **智能体评测基准：** MobiFlow
```

**File:** agent_rr/action_cache/tree.py (L39-53)
```python
class ActionTreeEdge:
    def __init__(self, action=None, tasks=[], to=None):
        self.action = action
        self.to = to
        self.tasks = tasks

    def add_task(self, task):
        self.tasks.append(task)

    def remove_task(self, task_idx):
        self.tasks.pop(task_idx)

    def __str__(self):
        return f"{self.action} {self.tasks}"

```

**File:** agent_rr/action_cache/tree.py (L54-84)
```python
class ActionTreeEdgeFuzzy(ActionTreeEdge):
    def __init__(self, action=None, tasks=[], to=None, task_embeddings=[], keywords=[]):
        l = len(tasks)
        if l == 0:
            raise ValueError("Tasks list is empty")
        if l != task_embeddings.shape[0]:
            raise ValueError("Tasks list length must match task_embeddings length")
        if l != len(keywords):
            raise ValueError("Tasks list length must match keywords length")
        super().__init__(action, tasks, to)
        self.task_embeddings = task_embeddings
        self.keywords = keywords

    def add_task(self, task, task_embedding, keyword=""):
        self.tasks.append(task)
        self.task_embeddings = torch.cat([self.task_embeddings, task_embedding], dim=0)
        self.keywords.append(keyword)

    def remove_task(self, task_idx):
        self.tasks.pop(task_idx)
        self.task_embeddings = torch.cat([self.task_embeddings[:task_idx], self.task_embeddings[task_idx+1:]], dim=0)
        self.keywords.pop(task_idx)

    def reset_keyword(self, keyword):
        for i, kw in enumerate(self.keywords):
            if kw == keyword:
                self.keywords[i] = ""

    def __str__(self):
        return f"{super().__str__()} {self.keywords}"

```

**File:** agent_rr/action_cache/tree.py (L126-138)
```python
class ActionTreeNode:
    def __init__(self, parent=None):
        self.edges = []
        self.parent = parent
        self.parent_edge_idx = None
        self.screenshot = None
        # if a node is a possible split node, pin it
        self.split_pin = False
        if parent is not None:
            self.depth = parent.depth + 1
        else:
            self.depth = 0

```

**File:** agent_rr/action_cache/tree.py (L151-157)
```python
    def get_cached_action(self, task):
        ret = []
        for e in self.edges:
            for t in e.tasks:
                if t == task:
                    ret.append((e.action, e.to))
        return ret
```

**File:** agent_rr/action_cache/tree.py (L272-286)
```python
    def get_cached_action(self, task, step_embedding):
        ret = []
        for e in self.edges:
            hit = util.semantic_search(step_embedding, e.task_embeddings, top_k=1, score_function=util.dot_score)[0]
            score = hit[0]['score']
            if score < EMBEDDER_THRESHOLD:
                continue
            corpus_id = hit[0]['corpus_id']
            keyword = e.keywords[corpus_id]
            if keyword not in task.description:
                continue
            hit_task = e.tasks[corpus_id]
            logger.debug(f"hit_task: {hit_task}, score: {score}")
            ret.append((e.action, e.to, keyword, hit_task))
        return ret
```

**File:** agent_rr/action_cache/tree.py (L337-344)
```python
    def reset_counter(self):
        self.env_counter = 0.0
        self.inference_counter = 0.0
        self.detection_counter = 0.0
        self.embedding_counter = 0.0

    def print_counter(self):
        logger.info(f"env_counter: {self.env_counter}, inference_counter: {self.inference_counter}, detection_counter: {self.detection_counter}, embedding_counter: {self.embedding_counter}")
```

**File:** agent_rr/action_cache/tree.py (L351-371)
```python
    def target_elem_changed(self, cur_screen, action):
        if action.target_elem is None:
            return False
        if cur_screen is None:
            return False
        target_elem = action.target_elem
        bbox = target_elem.bbox
        x1, x2 = map(lambda x: x / 1000 * cur_screen.width, (bbox[0], bbox[2]))
        y1, y2 = map(lambda x: x / 1000 * cur_screen.height, (bbox[1], bbox[3]))
        cropped_screen = cur_screen.crop((x1, y1, x2, y2))
        if self.omniparser is None:
            new_elem = UIElement(bbox, target_elem.content, cropped_screen)
            return new_elem != target_elem
        else:
            parsed_elems = self.omniparser.parse(cropped_screen)

            for elem in parsed_elems:
                if elem["content"] == target_elem.content:
                    return False
            return True

```

**File:** agent_rr/action_cache/tree.py (L375-390)
```python
    def generate_shortcuts(self):
        # periodically check if there are new shortcuts
        # use bfs
        queue = [self.root]
        self.shortcuts = []
        while queue:
            node = queue.pop(0)
            for e in node.edges:
                queue.append(e.to)
            if node is self.root:
                continue
            shortcuts = node.try_find_shortcuts()
            # last_action cannot be done action
            shortcuts = [sc for sc in shortcuts if not self.done(sc.template.last_action)]
            self.shortcuts.extend(shortcuts)
            node.split_pin = shortcuts != []
```

**File:** agent_rr/action_cache/tree.py (L392-560)
```python
    def execute(self, task_description):
        node = self.root
        history = []
        task = Task(task_description)
        if self.mode == MatchMode.FUZZY:
            start_time = time.time()
            num_precomute = 16
            step_embeddings = self.embedder.embed([task_description] * num_precomute, steps=range(1, num_precomute + 1))
            end_time = time.time()
            self.embedding_counter += end_time - start_time
            recompute_times = 0

        tracking_shortcut = False
        shortcut_action = None

        while True:
            # candidate (action, next_node) pairs
            action_nodes = []
            depth = node.depth

            start_time = time.time()

            if self.mode == MatchMode.EXACT:
                if shortcut_action is not None:
                    shortcut_next_node = node.add_child(shortcut_action, task)
                    action_nodes = [(shortcut_action, shortcut_next_node)]
                    keywords = [shortcut_next_node.get_incoming_edge().keywords[-1]]
                    shortcut_action = None
                else:
                    action_nodes = node.get_cached_action(task)
            else:
                if depth >= (recompute_times + 1) * num_precomute:
                    recompute_times += 1
                    step_embeddings = self.embedder.embed(
                        [task_description] * num_precomute,
                        steps=range(recompute_times * num_precomute + 1, (recompute_times + 1) * num_precomute + 1)
                    )

                step_embedding = step_embeddings[depth - recompute_times * num_precomute].unsqueeze(0)

                if shortcut_action is not None:
                    shortcut_next_node = node.add_child(shortcut_action, task, step_embedding)
                    action_nodes = [(shortcut_action, shortcut_next_node)]
                    keywords = [shortcut_next_node.get_incoming_edge().keywords[-1]]
                    shortcut_action = None
                else:
                    action_node_keyword_tasks = node.get_cached_action(task, step_embedding)
                    hit_tasks = [t.description for a, n, kw, t in action_node_keyword_tasks]
                    if len(action_node_keyword_tasks) == 0:
                        logger.debug(f"No similar task found.")
                    else:
                        logger.debug(f"Found similar task: {hit_tasks}")
                    if self.reranker is not None and len(hit_tasks) > 0:
                        scores = self.reranker.rerank(query_tasks=hit_tasks, document_task=task_description, step=depth + 1)
                        indices = [i for i, score in enumerate(scores) if score > RERANKER_MIN_CONF]
                        action_node_keyword_tasks = [action_node_keyword_tasks[i] for i in indices]
                        if len(indices) != len(hit_tasks):
                            logger.debug(f"Reranker filtered tasks: {[hit_tasks[i] for i in range(len(hit_tasks)) if i not in indices]}")
                    action_nodes = [(a, n) for a, n, kw, t in action_node_keyword_tasks]
                    keywords = [kw for a, n, kw, t in action_node_keyword_tasks]
            end_time = time.time()
            self.embedding_counter += end_time - start_time

            if node.split_pin and not self.generate_only and not tracking_shortcut:
                # start tracking possible shortcut
                logger.debug("Start tracking shortcut")
                tracking_shortcut = True
                possible_shortcuts = [sc for sc in self.shortcuts if sc.split_node is node]
                cur_step = 0

            # check if the action needs to be generated by model, or we can use cached action
            needs_generation = len(action_nodes) == 0 or self.generate_only

            start_time = time.time()
            agent_input = self.env.get_agent_input(history, task_description)
            end_time = time.time()
            self.env_counter += end_time - start_time

            screenshot = agent_input.get("image", None)
            # if UI changed, we need to generate the action
            if not needs_generation:
                if self.enable_ui_detection:
                    start_time = time.time()
                    for i, (a, n) in enumerate(action_nodes):
                        if not self.target_elem_changed(screenshot, a):
                            action = a
                            next_node = n
                            if self.mode == MatchMode.FUZZY:
                                keyword = keywords[i]
                            break
                    # the else block is executed if the for loop is not broken
                    else:
                        logger.debug("warning: target element changed")
                        needs_generation = True

                    end_time = time.time()
                    self.detection_counter += end_time - start_time
                else:
                    action, next_node = action_nodes[0]
                    if self.mode == MatchMode.FUZZY:
                        keyword = keywords[0]

            if needs_generation:
                logger.debug("Cache miss")
                start_time = time.time()
                agent_output = self.agent.generate(agent_input)
                end_time = time.time()
                self.inference_counter += end_time - start_time
                action = self.action_class(**agent_output)
                # extract target element and store it in action
                if self.enable_ui_detection:
                    start_time = time.time()
                    action.extract_target_elem(screenshot, self.omniparser)
                    end_time = time.time()
                    self.detection_counter += end_time - start_time
                if self.mode == MatchMode.EXACT:
                    next_node = node.add_child(action, task)
                else:
                    next_node = node.add_child(action, task, step_embedding)
            else:
                logger.debug("Cache hit")
                edge = next_node.get_incoming_edge()
                # only add similar task to the edge
                if self.mode == MatchMode.FUZZY and task not in edge.tasks:
                    edge.add_task(task, step_embedding, keyword)

            if tracking_shortcut:
                new_possible_shortcuts = []
                for i, sc in enumerate(possible_shortcuts):
                    check_result =  sc.check(action, cur_step)
                    if check_result == ShortCutCheckResult.MATCH_SECOND_LAST:
                        # can use cached action in next iteration
                        tracking_shortcut = False
                        # add a child for next_node in advance
                        # in next iteration, cache hit is guaranteed
                        if needs_generation:
                            last_action = sc.template.last_action
                            shortcut_action = last_action
                        break
                    if check_result == ShortCutCheckResult.MATCH_INTERMEDIATE:
                        new_possible_shortcuts.append(sc)
                else:
                    cur_step += 1
                    possible_shortcuts = new_possible_shortcuts
                    if len(possible_shortcuts) == 0:
                        tracking_shortcut = False

            # execute the action
            if self.done(action):
                break
            history.append(action)

            start_time = time.time()
            self.env.execute(action)
            end_time = time.time()
            self.env_counter += end_time - start_time

            node = next_node

        # periodically generate shortcuts
        if not self.generate_only:
            period = 1
            num_tasks = self.get_num_tasks()
            if num_tasks - self.num_tasks_last_check >= period:
                self.num_tasks_last_check = num_tasks
                self.generate_shortcuts()
                logger.debug(f"number of shortcuts: {len(self.shortcuts)}")
                for sc in self.shortcuts:
                    logger.debug(f"split_node: {sc.split_node}, template: {sc.template.action_names}, last_action: {sc.template.last_action}, supernode size: {len(sc.supernode.nodes)}")
```

**File:** agent_rr/run_experiment.py (L127-200)
```python
def main(args):
    agent = MybenchAgent(MybenchTasks(args.data_path))
    env = MybenchEnvironment(agent)
    tree = ActionTree(env, agent, Action, done=lambda a: a.name == 'done',
                      mode=MatchMode.FUZZY,
                      embedder_config={
                          "path": args.embedder_path
                      },
                      reranker_config={
                          "path": args.reranker_path
                      })

    app_task_trajectories = agent.tasks.get_app_task_trajectories()
    records = []
    for app, task_trajectories in app_task_trajectories.items():
        tree.clear()
        tasks = [t for t, _ in task_trajectories]
        random.shuffle(tasks)
        redistributed_tasks = []
        if args.distribution == 'uniform':
            redistributed_tasks = tasks
        elif args.distribution == 'power_law':
            num_task20 = math.ceil(0.2 * len(tasks))
            task20 = tasks[:num_task20]
            task80 = tasks[num_task20:]
            redistributed_tasks = task20 * 16 + task80
            random.shuffle(redistributed_tasks)
            redistributed_tasks = random.sample(redistributed_tasks, len(tasks))
        else:
            raise ValueError(f"Unknown distribution: {args.distribution}")
        for task in redistributed_tasks:
            logger.info(f"Current task: {task}")
            tree.execute(task)
            env.check_done()
            if not env.cur_success:
                tree.root.remove_task_trace(Task(task))
            agent.task_step[task] = -1
            env.reset_cur_task()
            env.total_task_cnt += 1
        logger.info(f"Current app: {app}")
        env.print_cnt()
        agent.print_cnt()
        logger.info(f"embedding time: {tree.embedding_counter}")
        if args.csv_path:
            records.append({
                "app": app,
                "total_task": env.total_task_cnt,
                "correct_task": env.correct_task_cnt,
                "total_actions": env.execute_cnt,
                "replayed_actions": env.execute_cnt - agent.generate_cnt,
                "total_embedding_time": tree.embedding_counter,
                "embedding_time_per_step": tree.embedding_counter / env.execute_cnt if env.execute_cnt > 0 else 0.0,
                "avg_steps": round(env.execute_cnt / env.total_task_cnt, 2) if env.total_task_cnt > 0 else 0.0,
                "correct_rate": round(env.correct_task_cnt / env.total_task_cnt, 2) if env.total_task_cnt > 0 else 0.0,
                "replay_rate": round(1 - agent.generate_cnt / env.execute_cnt, 2) if env.execute_cnt > 0 else 0.0
            })
        env.reset_cnt()
        agent.reset_cnt()
        tree.reset_counter()
    if args.csv_path:
        df = pd.DataFrame.from_records(records)
        df.to_csv(args.csv_path, index=False)
        logger.info(f"Results exported to {args.csv_path}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--embedder_path', type=str, required=True)
    parser.add_argument('--reranker_path', type=str, required=True)
    parser.add_argument('--data_path', type=str, required=True)
    parser.add_argument('--distribution', choices=['uniform', 'power_law'], default='uniform')
    parser.add_argument('--csv_path', type=str, required=False, default=None)
    args = parser.parse_args()
    main(args)
```
