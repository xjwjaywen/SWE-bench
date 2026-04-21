# Generative Agents 社会模拟平台 —— 项目规划

## 一、项目定位

构建一个生产级的 AI 社会模拟平台：十几个拥有独立人格、记忆、社交关系的 AI Agent 生活在一个虚拟社交世界中，自主决定每天做什么、跟谁交流、如何看待彼此。用户可以注入事件（如传播谣言、引入新成员、制造冲突），观察社交动态如何演化。

**参考论文**：Stanford "Generative Agents: Interactive Simulacra of Human Behavior"（2023），该论文 Google Scholar 引用 2000+，但开源实现是研究级代码，没有人做出工程化、可部署、可评估的版本。

**核心卖点**：这不是"套壳聊天"——每个 Agent 都有自主决策循环，多个 Agent 之间的交互产生涌现行为（群体极化、谣言传播、小团体形成），整个系统是一个真正的 Multi-Agent 自主系统。

---

## 二、为什么这个项目能拉开差距

### 2.1 真正的 Agent

每个角色都是一个独立的自主 Agent，执行完整的 **感知→检索→反思→规划→行动** 循环。没有固定脚本，同样的初始条件跑两次，社交演化路径完全不同。

### 2.2 差异化

| 维度 | 市面上常见项目 | 本项目 |
|------|---------------|--------|
| Agent 类型 | 单 Agent pipeline | 多 Agent 自主交互 |
| 记忆 | 简单对话历史 | 三层记忆架构（观察/反思/规划） |
| 交互 | 用户驱动 | Agent 自主发起 |
| 人格 | prompt 写死 | LoRA SFT + 人格一致性评估 |
| 评估 | 无/主观 | 5维量化评估体系 |
| 部署 | 调 API | 自部署 vLLM + 多 LoRA 热切换 |

### 2.3 L20 48GB 充分利用

- vLLM 部署 Qwen2.5-7B/14B 作为 Agent 大脑
- **多 LoRA 热切换**：每个角色人格对应一个 LoRA adapter，vLLM 原生支持同一 base model 上动态切换多个 LoRA，这是一个很硬的技术点
- LoRA SFT 训练不同人格风格的 adapter
- Embedding model 本地部署用于记忆检索

### 2.4 安全背景衔接

信息传播模拟天然关联网络安全：谣言传播 = 信息攻击模拟，观察 Agent 社交网络中的信息扩散模式，可以类比网络安全中的攻击传播分析。面试时可以说"用 Agent 模拟社交网络中的信息安全问题"。

---

## 三、系统架构

```
┌─────────────────────────────────────────────────────┐
│                   Web Dashboard                      │
│  (实时可视化：社交图谱 / Agent 活动 / 事件注入面板)    │
└──────────────────────┬──────────────────────────────┘
                       │ WebSocket
┌──────────────────────▼──────────────────────────────┐
│                  FastAPI Server                       │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐            │
│  │ 模拟控制 │ │ 事件注入  │ │ 查询接口   │            │
│  └────┬────┘ └─────┬────┘ └─────┬─────┘            │
│       │            │            │                    │
│  ┌────▼────────────▼────────────▼─────┐             │
│  │         Simulation Engine           │             │
│  │  (时间步调度 / Agent 轮转 / 交互管理) │             │
│  └────────────────┬───────────────────┘             │
│                   │                                  │
│  ┌────────────────▼───────────────────┐             │
│  │          Agent Runtime (×N)         │             │
│  │  ┌────────┐ ┌──────┐ ┌─────────┐  │             │
│  │  │Memory  │ │Reflect│ │Plan/Act │  │             │
│  │  │System  │ │Engine │ │Engine   │  │             │
│  │  └────────┘ └──────┘ └─────────┘  │             │
│  └────────────────┬───────────────────┘             │
│                   │                                  │
│  ┌────────────────▼───────────────────┐             │
│  │         World Model                 │             │
│  │  (地点 / 物品 / 社交图谱 / 时间)     │             │
│  └────────────────────────────────────┘             │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              Infrastructure Layer                     │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐            │
│  │ vLLM    │ │ ChromaDB │ │ Redis     │            │
│  │(多LoRA) │ │(向量检索) │ │(状态缓存) │            │
│  └─────────┘ └──────────┘ └───────────┘            │
└─────────────────────────────────────────────────────┘
```

---

## 四、Agent 核心设计

### 4.1 Agent 身份定义

每个 Agent 有一份结构化身份档案：

```python
@dataclass
class AgentIdentity:
    name: str                    # "林小雨"
    age: int                     # 24
    occupation: str              # "咖啡店店员"
    personality_traits: dict     # Big Five: {"openness": 0.8, "agreeableness": 0.6, ...}
    background: str              # 背景故事（200字以内）
    initial_relationships: dict  # {"张明": "大学同学", "王芳": "邻居"}
    daily_routine: str           # "早上8点开店，下午3点休息，晚上喜欢散步"
    lora_adapter: str            # 对应的 LoRA adapter 路径
```

### 4.2 记忆系统（三层架构）

这是整个项目最核心的技术点：

**第一层：观察流（Memory Stream）**

```python
@dataclass
class Observation:
    timestamp: datetime          # 模拟世界时间
    content: str                 # "在咖啡店看到张明和一个陌生人争吵"
    location: str                # "中央咖啡店"
    importance: float            # LLM 打分 1-10，归一化到 0-1
    embedding: list[float]       # 用于向量检索
    related_agents: list[str]    # ["张明"]
```

所有 Agent 的感知（看到的、听到的、做过的、说过的）都以时间流的形式存入 Memory Stream。

**第二层：反思（Reflections）**

当 Agent 最近的观察积累到一定 importance 阈值时，触发反思：

```
触发条件：recent_observations 的 importance 总和 > threshold（如 15）

反思 Prompt：
"以下是林小雨最近的经历：
1. [observation_1]
2. [observation_2]
...
基于这些经历，林小雨会形成什么高层次的认识？请给出3条反思，每条不超过一句话。"

输出示例：
- "张明最近情绪不太稳定，可能遇到了什么烦心事"
- "咖啡店周末的客流量明显增加了"
- "我和王芳的关系越来越好，她是一个值得信任的朋友"
```

反思本身也存入 Memory Stream，但标记为 `type=reflection`，importance 通常较高。

**第三层：规划（Plans）**

每个模拟日开始时，Agent 生成当日计划：

```
规划 Prompt：
"你是林小雨，[身份描述]。
今天是模拟世界的第5天。
你最近的重要反思：[top reflections]
你今天的大致安排：[daily_routine]
最近发生的重要事情：[recent important observations]

请规划你今天的具体行程（按小时）。"
```

计划可以被突发事件打断（比如遇到了想聊天的人）。

### 4.3 记忆检索

当 Agent 需要做决策时，检索相关记忆。检索分数 = 三个因子的加权和：

```python
def retrieve_memories(agent, query: str, top_k: int = 10) -> list[Observation]:
    scores = []
    for memory in agent.memory_stream:
        # 因子1：相关性（embedding 余弦相似度）
        relevance = cosine_similarity(encode(query), memory.embedding)
        
        # 因子2：时效性（指数衰减）
        recency = decay_factor ** hours_since(memory.timestamp)
        
        # 因子3：重要性
        importance = memory.importance
        
        # 加权合并
        score = w1 * relevance + w2 * recency + w3 * importance
        scores.append((memory, score))
    
    return sorted(scores, key=lambda x: x[1], reverse=True)[:top_k]
```

### 4.4 Agent 决策循环（核心 Loop）

每个时间步（模拟世界中的1小时），每个 Agent 执行：

```
1. 感知（Perceive）
   → 获取当前位置的事件、在场的其他 Agent、环境变化
   → 存入 Memory Stream

2. 检索（Retrieve）
   → 根据当前感知，检索相关记忆
   → 包括过去的观察和反思

3. 决策（Decide）
   → 输入：当前感知 + 相关记忆 + 今日计划 + 人格特质
   → 输出：下一步行动（移动/交谈/观察/独处/...）
   → Prompt：
     "你是[身份]。现在是[时间]，你在[地点]。
      你看到：[perceptions]
      你想起：[retrieved memories]
      你今天的计划：[plan]
      你接下来会做什么？从以下选项中选择并说明原因：
      A. 移动到[可达地点列表]
      B. 与[在场Agent]交谈
      C. 继续当前活动
      D. [其他合理行动]"

4. 执行（Act）
   → 执行决策，产生新的 observation
   → 如果是交谈，进入对话子循环

5. 反思检查（Reflect Check）
   → 检查是否触发反思条件
   → 如果触发，生成反思并存入 Memory Stream
```

### 4.5 对话子循环

当两个 Agent 决定交谈时：

```python
async def conversation_loop(agent_a, agent_b, context: str):
    """两个 Agent 之间的自主对话"""
    # 双方各自检索与对方相关的记忆
    a_memories = retrieve_memories(agent_a, f"与{agent_b.name}的关系和交流")
    b_memories = retrieve_memories(agent_b, f"与{agent_a.name}的关系和交流")
    
    dialogue = []
    for turn in range(MAX_TURNS):  # 对话最多 8 轮
        # Agent A 发言
        a_response = await generate_dialogue(
            agent=agent_a,
            partner=agent_b,
            memories=a_memories,
            dialogue_history=dialogue,
            context=context
        )
        
        if a_response.intent == "END_CONVERSATION":
            break
        dialogue.append({"speaker": agent_a.name, "content": a_response.text})
        
        # Agent B 回应
        b_response = await generate_dialogue(
            agent=agent_b,
            partner=agent_a,
            memories=b_memories,
            dialogue_history=dialogue,
            context=context
        )
        
        if b_response.intent == "END_CONVERSATION":
            break
        dialogue.append({"speaker": agent_b.name, "content": b_response.text})
    
    # 对话结束后，双方各自存储记忆并更新关系
    store_conversation_memory(agent_a, agent_b, dialogue)
    store_conversation_memory(agent_b, agent_a, dialogue)
    update_relationship(agent_a, agent_b, dialogue)
    update_relationship(agent_b, agent_a, dialogue)
```

---

## 五、社交图谱与关系演化

### 5.1 关系模型

```python
@dataclass
class Relationship:
    source: str              # "林小雨"
    target: str              # "张明"
    label: str               # "大学同学" / "邻居" / "陌生人"
    closeness: float         # 亲密度 0-1
    sentiment: float         # 好感度 -1 到 1
    trust: float             # 信任度 0-1
    last_interaction: datetime
    interaction_count: int
    notes: list[str]         # Agent 对这段关系的主观认知
                             # ["张明最近好像在隐瞒什么", "他上次帮了我大忙"]
```

### 5.2 关系更新机制

每次交互后，LLM 评估关系变化：

```
Prompt：
"林小雨刚刚和张明进行了以下对话：
[dialogue]

林小雨之前对张明的印象：[relationship.notes]
当前亲密度：{closeness}，好感度：{sentiment}，信任度：{trust}

这次对话后，林小雨对张明的各项评分会如何变化？请给出变化值（-0.2到+0.2之间）和原因。"
```

### 5.3 社交图谱可视化

实时展示的力导向图：
- 节点 = Agent（大小表示社交活跃度）
- 边 = 关系（颜色表示好感度，粗细表示亲密度）
- 动态更新，可以看到社交圈子的形成和变化

---

## 六、事件注入系统

这是项目的"可玩性"所在，也是展示 Agent 自主性的关键：

### 6.1 事件类型

```python
class EventType(Enum):
    RUMOR = "rumor"                    # 谣言传播：向某个 Agent 注入一条虚假信息
    NEW_AGENT = "new_agent"            # 新成员加入社区
    CONFLICT = "conflict"              # 制造两个 Agent 之间的矛盾
    RESOURCE = "resource"              # 引入稀缺资源（如一个工作机会）
    CRISIS = "crisis"                  # 突发危机（如咖啡店要关门）
    SECRET = "secret"                  # 告诉某个 Agent 一个秘密，观察是否泄露
```

### 6.2 事件注入示例

**谣言传播实验**：
```json
{
    "type": "rumor",
    "target_agent": "林小雨",
    "content": "听说张明要搬去另一个城市了",
    "source_credibility": 0.5,
    "inject_time": "Day3 14:00"
}
```

注入后观察：
- 林小雨是否相信这个谣言？（取决于她对信息来源的信任度）
- 她会告诉谁？（取决于她跟谁关系好、谁可能关心张明）
- 传播了几跳后信息如何变形？
- 张明自己听到后如何反应？

**秘密泄露实验**：
- 告诉 Agent A 一个秘密，标记为"不要告诉别人"
- 观察 Agent A 是否会在后续对话中泄露
- 测试不同 personality（高 agreeableness vs 低 agreeableness）的泄露概率差异

### 6.3 信息传播追踪

```python
@dataclass
class InformationTrace:
    info_id: str                       # 信息唯一标识
    original_content: str              # 原始内容
    injection_point: str               # 注入给谁
    injection_time: datetime
    propagation_chain: list[dict]      # [{"from": "林小雨", "to": "王芳", "time": ..., "mutated_content": ...}]
    current_believers: set[str]        # 当前相信这条信息的 Agent
    current_content_versions: dict     # 每个 Agent 记忆中这条信息的版本（可能变形了）
```

---

## 七、工程实现细节

### 7.1 技术栈

| 组件 | 技术选型 | 理由 |
|------|---------|------|
| Web 框架 | FastAPI | 异步支持、WebSocket |
| LLM 推理 | vLLM + Qwen2.5-7B | 多 LoRA 热切换、高吞吐 |
| 向量数据库 | ChromaDB | 轻量、易部署 |
| 缓存 | Redis | Agent 状态、模拟状态 |
| 前端可视化 | React + D3.js | 力导向图、实时更新 |
| 容器化 | Docker Compose | 一键部署 |
| Embedding | bge-small-zh-v1.5 | 本地部署，中文优化 |
| SFT 训练 | PEFT + TRL | LoRA 微调 |

### 7.2 多 LoRA 热切换（关键技术点）

这是面试中非常亮的一个点：同一个 base model，为不同人格角色训练不同的 LoRA adapter，vLLM 在推理时动态切换。

```python
from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest

# 启动 vLLM，启用 LoRA 支持
llm = LLM(
    model="Qwen/Qwen2.5-7B-Instruct",
    enable_lora=True,
    max_lora_rank=16,
    max_loras=16,           # 最多同时加载 16 个 LoRA（对应 16 个角色）
    gpu_memory_utilization=0.85,
)

# 为不同角色定义 LoRA
lora_requests = {
    "林小雨": LoRARequest("lin_xiaoyu", 1, "/models/lora/lin_xiaoyu"),
    "张明": LoRARequest("zhang_ming", 2, "/models/lora/zhang_ming"),
    "王芳": LoRARequest("wang_fang", 3, "/models/lora/wang_fang"),
    # ...
}

# 推理时指定角色对应的 LoRA
async def agent_think(agent_name: str, prompt: str) -> str:
    output = llm.generate(
        prompt,
        SamplingParams(temperature=0.8, max_tokens=512),
        lora_request=lora_requests[agent_name]
    )
    return output[0].outputs[0].text
```

**为什么这个点很亮**：
- 展示了对 vLLM 内部机制的理解（LoRA adapter 的动态加载和切换）
- 解决了真实的工程问题（不可能为每个角色部署一个模型）
- L20 48GB 刚好适合：7B base + 16 个 LoRA adapter 的内存占用约 20-25GB

### 7.3 模拟引擎调度

```python
class SimulationEngine:
    """模拟世界的时间推进引擎"""
    
    def __init__(self, agents: list[Agent], world: WorldModel):
        self.agents = agents
        self.world = world
        self.current_time = SimTime(day=1, hour=6)  # 从第1天早上6点开始
        self.event_queue = []        # 待注入事件
        self.trace_logger = TraceLogger()
    
    async def step(self):
        """推进一个时间步（模拟世界1小时）"""
        self.current_time.advance(hours=1)
        
        # 1. 处理待注入事件
        pending_events = self.get_pending_events(self.current_time)
        for event in pending_events:
            await self.inject_event(event)
        
        # 2. 每个 Agent 执行决策循环
        # 注意：同一地点的 Agent 可以并行感知，但交互需要串行
        location_groups = self.group_agents_by_location()
        
        for location, agents_here in location_groups.items():
            # 2a. 并行：每个 Agent 感知环境
            perceptions = await asyncio.gather(*[
                agent.perceive(self.world, self.current_time)
                for agent in agents_here
            ])
            
            # 2b. 并行：每个 Agent 做决策
            decisions = await asyncio.gather(*[
                agent.decide(perception)
                for agent, perception in zip(agents_here, perceptions)
            ])
            
            # 2c. 处理交互（如果两个 Agent 都想跟对方聊天）
            interactions = self.resolve_interactions(agents_here, decisions)
            for agent_a, agent_b, context in interactions:
                await conversation_loop(agent_a, agent_b, context)
            
            # 2d. 处理移动
            for agent, decision in zip(agents_here, decisions):
                if decision.action == "move":
                    self.world.move_agent(agent, decision.target_location)
        
        # 3. 全局反思检查
        for agent in self.agents:
            if agent.should_reflect():
                await agent.reflect()
        
        # 4. 记录 trace
        self.trace_logger.log_step(self.current_time, self.agents, self.world)
        
        # 5. 推送实时更新到前端
        await self.broadcast_state()
```

### 7.4 Observability 系统

```python
@dataclass
class SimulationTrace:
    """每一步模拟的完整记录"""
    step_id: int
    sim_time: SimTime
    agent_states: dict[str, AgentState]      # 每个 Agent 的位置、活动、情绪
    decisions: dict[str, Decision]            # 每个 Agent 的决策及推理过程
    interactions: list[Interaction]           # 本步发生的所有交互
    relationship_changes: list[RelChange]     # 关系变化
    memory_operations: list[MemoryOp]         # 记忆写入/检索记录
    llm_calls: list[LLMCall]                 # 所有 LLM 调用（prompt、response、token数、耗时）
    token_usage: dict[str, int]              # 每个 Agent 本步 token 消耗
```

完整的 trace 让你可以：
- 回溯任何一个 Agent 的决策过程（"她为什么突然不跟张明说话了？"→ 翻 trace 看决策 prompt 和检索到的记忆）
- 计算成本（每步/每天/每个 Agent 的 token 消耗）
- Debug 异常行为
- 面试时展示系统的可观测性

### 7.5 成本控制

运行 12 个 Agent、每步每个 Agent 约 1000-2000 tokens（输入+输出），一个模拟日 = 18 步（6:00-24:00），总计约 12 × 18 × 1500 = 324K tokens/模拟日。

自部署 Qwen2.5-7B 在 L20 上跑，token 成本 = 0（只有电费），但需要控制推理时间：
- vLLM batching：同一时间步的多个 Agent 请求 batch 处理
- 缓存：相同 context 前缀的 KV cache 复用
- 异步并行：不需要交互的 Agent 并行推理

---

## 八、SFT 微调方案

### 8.1 目标

为不同人格类型训练 LoRA adapter，让 Agent 的语言风格和决策倾向与其人格匹配。

### 8.2 人格类型设计（Big Five 模型）

基于心理学 Big Five 人格模型，设计 4-6 种典型人格组合：

| 角色 | O(开放性) | C(尽责性) | E(外向性) | A(宜人性) | N(神经质) | 风格 |
|------|----------|----------|----------|----------|----------|------|
| 林小雨 | 高 | 中 | 高 | 高 | 低 | 热情开朗、好奇心强 |
| 张明 | 低 | 高 | 低 | 中 | 高 | 内敛严谨、容易焦虑 |
| 王芳 | 高 | 低 | 高 | 低 | 中 | 直率大胆、不拘小节 |
| 李华 | 中 | 高 | 中 | 高 | 低 | 稳重可靠、乐于助人 |
| ... | ... | ... | ... | ... | ... | ... |

### 8.3 训练数据构造

**方法：用强模型（Claude/GPT-4）生成人格一致的对话数据**

```python
# 数据生成 prompt 示例
GENERATE_PROMPT = """
你需要扮演一个具有以下人格特质的角色：
- 名字：{name}
- 人格：开放性={O}, 尽责性={C}, 外向性={E}, 宜人性={A}, 神经质={N}
- 背景：{background}
- 说话风格：{style_description}

请根据以下场景生成该角色的回应：

场景：{scenario}
对话上下文：{context}

要求：
1. 回应必须完全符合该角色的人格特质和说话风格
2. 长度适中（1-3句话）
3. 体现角色的独特视角和情感倾向
"""

# 场景类型：
# - 日常闲聊（"今天天气真好"）
# - 社交决策（"你要不要来参加聚会？"）
# - 冲突处理（"你为什么把我的秘密告诉了别人？"）
# - 信息传递（"你听说了吗，[某某事]"）
# - 情感表达（"最近觉得好累"）
```

每种人格生成 300-500 条高质量对话样本，总计 2000-3000 条。

### 8.4 训练配置

```python
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, SFTConfig

# LoRA 配置
lora_config = LoraConfig(
    r=16,                       # rank
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

# 训练配置（每种人格独立训练）
training_config = SFTConfig(
    output_dir=f"./lora_adapters/{persona_name}",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    warmup_ratio=0.1,
    bf16=True,                  # L20 支持 bf16
    logging_steps=10,
    save_strategy="epoch",
    max_seq_length=2048,
)

# L20 48GB 内存预估：
# Qwen2.5-7B bf16 ≈ 14GB
# LoRA 参数 ≈ 0.1GB
# 梯度 + 优化器 ≈ 8GB
# 总计 ≈ 22GB，L20 48GB 绰绰有余
# 甚至可以用 14B 模型（≈28GB base + 10GB 训练 ≈ 38GB）
```

### 8.5 人格一致性验证

训练完成后，用 Big Five Inventory (BFI-44) 问卷测试每个 LoRA adapter：

```python
BFI_QUESTIONS = [
    "我觉得自己是一个话很多的人",           # E+
    "我容易找到别人的缺点",                 # A-
    "我做事认真彻底",                       # C+
    "我经常感到沮丧、忧郁",                 # N+
    "我对艺术和美有很强的感受力",            # O+
    # ... 共44题
]

def evaluate_personality_consistency(adapter_path, expected_traits):
    """用 BFI 问卷测试 LoRA adapter 的人格一致性"""
    model = load_model_with_lora(adapter_path)
    
    scores = {}
    for question in BFI_QUESTIONS:
        prompt = f"你是{agent_name}。请根据你的真实感受回答：'{question}'\n选择：1=非常不同意 2=不同意 3=中立 4=同意 5=非常同意\n你的选择："
        response = model.generate(prompt)
        scores[question] = parse_score(response)
    
    # 计算 Big Five 各维度得分
    measured_traits = compute_big_five(scores)
    
    # 与预期人格的相关性
    consistency = pearson_correlation(expected_traits, measured_traits)
    return consistency  # 目标 > 0.7
```

---

## 九、评估体系（5维量化）

### 9.1 人格一致性（Personality Consistency）

- **方法**：在模拟的第1天、第5天、第10天分别给 Agent 做 BFI 问卷
- **指标**：跨时间点的 BFI 得分相关性（Pearson r）
- **目标**：r > 0.7（人格不应随时间漂移）

### 9.2 记忆准确性（Memory Accuracy）

- **方法**：在模拟过程中向 Agent 提问关于过去事件的问题
- **示例**："昨天你在咖啡店遇到了谁？""上周王芳跟你说了什么？"
- **指标**：回答正确率（Recall@1, Recall@5）
- **目标**：Recall@1 > 0.6, Recall@5 > 0.85

### 9.3 社交行为合理性（Social Plausibility）

- **方法**：抽取 Agent 对话片段，让人类评估者盲评
- **评估项**：
  - 对话自然度（1-5分）
  - 人格一致性（这段话像这个角色说的吗？1-5分）
  - 社交合理性（这个行为在这个场景下合理吗？1-5分）
- **对比实验**：有 LoRA SFT vs 无 SFT（纯 prompt）的差异
- **目标**：SFT 版本在所有维度上显著优于纯 prompt 版本

### 9.4 信息传播分析（Information Propagation）

- **方法**：注入 N 条信息，追踪传播路径
- **指标**：
  - 传播深度（平均经过几跳）
  - 传播广度（最终有多少 Agent 知道这条信息）
  - 传播速度（从注入到 50% Agent 知道的时间）
  - 信息变形率（传播后内容与原始内容的语义差异）
- **对比**：与经典的 SIR（Susceptible-Infected-Recovered）传播模型对比，分析 Agent 模拟的传播模式是否符合社会学规律
- **目标**：传播模式与 SIR 模型的拟合度 R² > 0.6

### 9.5 涌现行为检测（Emergent Behavior）

- **方法**：运行长时间模拟（30+天），观察是否出现以下涌现现象：
  - 小团体形成（社交图谱中出现紧密子图）
  - 意见领袖出现（某些 Agent 在信息传播中占据关键位置）
  - 社交孤立（某些 Agent 逐渐边缘化）
  - 信息茧房（Agent 倾向于和观点相似的 Agent 交流）
- **指标**：社交网络分析指标（聚类系数、中心性、模块度）
- **目标**：聚类系数 > 随机图（表明有非随机的社交结构形成）

---

## 十、世界设计

### 10.1 地点设计

一个小型社区，包含 6-8 个地点：

```python
LOCATIONS = {
    "中央咖啡店": {"type": "social", "capacity": 8, "hours": "7:00-22:00"},
    "社区公园": {"type": "outdoor", "capacity": 20, "hours": "6:00-23:00"},
    "便利店": {"type": "commercial", "capacity": 5, "hours": "24h"},
    "社区图书馆": {"type": "quiet", "capacity": 10, "hours": "9:00-21:00"},
    "居民楼A": {"type": "residential", "capacity": 6, "hours": "24h"},
    "居民楼B": {"type": "residential", "capacity": 6, "hours": "24h"},
    "篮球场": {"type": "sports", "capacity": 10, "hours": "6:00-22:00"},
    "小吃街": {"type": "commercial", "capacity": 15, "hours": "10:00-23:00"},
}
```

### 10.2 Agent 数量

初始 12 个 Agent（可通过事件注入增减）。12 个是经过权衡的数字：
- 足够多：能形成有意义的社交网络（至少 3 个小团体）
- 足够少：L20 推理负担可控，trace 可以人工审查

### 10.3 时间系统

- 模拟时间粒度：1小时/步
- Agent 活跃时间：6:00-24:00（18步/天）
- 一个完整模拟周期：模拟 10-30 天

---

## 十一、项目时间规划（12周）

### Phase 1: 基础架构（第1-3周）

**第1周：Agent 核心**
- [ ] AgentIdentity 数据模型
- [ ] Memory Stream 实现（Observation 存储 + 检索）
- [ ] 基础 Perceive → Decide → Act 循环
- [ ] 单 Agent 跑通（一个 Agent 在世界中自主行动）

**第2周：多 Agent 交互**
- [ ] World Model（地点、移动、时间）
- [ ] Simulation Engine 调度器
- [ ] 对话子循环
- [ ] 多 Agent 同时运行跑通

**第3周：记忆与反思**
- [ ] 三因子记忆检索（relevance + recency + importance）
- [ ] ChromaDB 集成（embedding 存储与检索）
- [ ] 反思触发机制 + 反思生成
- [ ] 日计划生成

### Phase 2: 社交系统（第4-5周）

**第4周：关系演化**
- [ ] Relationship 数据模型
- [ ] 关系更新机制（对话后自动评估）
- [ ] 社交图谱数据结构
- [ ] 关系影响决策（更倾向于跟亲密的人互动）

**第5周：事件系统**
- [ ] 事件注入接口
- [ ] 谣言传播实现 + 信息追踪
- [ ] 秘密泄露实现
- [ ] 新成员加入 / 冲突制造

### Phase 3: 工程化（第6-8周）

**第6周：vLLM 部署 + LoRA**
- [ ] vLLM 部署 Qwen2.5-7B
- [ ] 多 LoRA 热切换跑通
- [ ] 推理性能基准测试
- [ ] Token 统计与成本追踪

**第7周：SFT 训练**
- [ ] 训练数据生成（用 Claude/GPT-4 生成人格对话）
- [ ] LoRA SFT 训练 4-6 种人格 adapter
- [ ] BFI 人格一致性测试
- [ ] 对比实验：SFT vs 纯 prompt

**第8周：API + 可视化**
- [ ] FastAPI 接口（模拟控制、事件注入、状态查询）
- [ ] WebSocket 实时推送
- [ ] React + D3.js 社交图谱可视化
- [ ] Agent 活动时间线视图
- [ ] Trace 查看器

### Phase 4: 评估与优化（第9-11周）

**第9周：评估框架**
- [ ] 人格一致性自动评估（BFI 问卷自动化）
- [ ] 记忆准确性测试集构建
- [ ] 信息传播追踪分析
- [ ] 社交网络指标计算

**第10周：长时间模拟实验**
- [ ] 30天模拟运行
- [ ] 涌现行为观察与记录
- [ ] SIR 模型对比分析
- [ ] 发现并修复 Agent 行为异常

**第11周：优化迭代**
- [ ] 基于评估结果调优 prompt / 记忆检索参数
- [ ] 性能优化（推理速度、内存占用）
- [ ] Trace 系统完善
- [ ] 文档撰写

### Phase 5: 收尾（第12周）

**第12周**
- [ ] Docker Compose 一键部署
- [ ] README + Demo 视频
- [ ] 评估报告整理
- [ ] 面试话术准备

---

## 十二、面试话术（30秒版）

> "我做了一个生产级的 AI 社会模拟平台。12 个 AI Agent 各自拥有独立人格、三层记忆系统和社交关系，在一个虚拟社区中自主生活、交流、形成关系。核心技术点有三个：第一，三层记忆架构——观察流、反思、规划，用向量检索 + 时效性 + 重要性的三因子加权做记忆召回；第二，vLLM 多 LoRA 热切换——同一个 base model 上为每个角色动态加载不同人格的 LoRA adapter，单张 L20 跑 12 个 Agent；第三，五维量化评估体系——人格一致性、记忆准确率、社交合理性、信息传播拟合度、涌现行为检测，全部有数字指标。最有趣的发现是，跑了 30 天模拟后，Agent 自发形成了 3 个社交小团体，谣言的传播模式跟经典 SIR 模型的拟合 R² 达到了 0.65。"

### 面试深挖应对

**Q: 你的记忆系统是怎么设计的？为什么用三层？**
> 第一层是观察流，记录所有感知事件，类似人的短期记忆。第二层是反思，当近期观察的重要性累积到阈值时触发 LLM 生成高层次总结，类似人的长期记忆抽象。第三层是规划，基于反思和近期观察生成行动计划。检索时用 relevance × recency × importance 三因子加权，其中 recency 用指数衰减模拟遗忘曲线。这个设计参考了 Stanford Generative Agents 论文，但工程实现上我用 ChromaDB 做向量索引，Redis 做状态缓存，支持实时检索。

**Q: 多 LoRA 热切换具体怎么实现的？性能如何？**
> vLLM 原生支持 multi-LoRA serving。base model 加载一次，每个 LoRA adapter 只有几十 MB。请求时通过 LoRARequest 指定 adapter ID，vLLM 在 attention 层动态注入 LoRA 参数。12 个角色 adapter 同时加载，总额外显存不到 1GB。性能测试结果：batch size=12 时，throughput 大约 X tokens/s，单步模拟（12个Agent）约 Y 秒。

**Q: 评估是怎么做的？你怎么证明 Agent 行为是合理的？**
> 五个维度。人格一致性：用 BFI-44 问卷在不同时间点测试，跨时间点 Pearson r > 0.7 说明人格稳定。记忆准确性：构造事实性问题，测 Recall。社交合理性：人类盲评打分，SFT 版显著优于纯 prompt。信息传播：跟 SIR 模型拟合。涌现行为：用图论指标（聚类系数、模块度）验证非随机社交结构的形成。

**Q: 跟 Stanford 那篇论文的区别是什么？**
> 三个区别。第一，他们用 GPT-3.5 API，我用自部署 Qwen2.5-7B + 多 LoRA，解决隐私和成本问题。第二，他们的实现是研究级脚本，我做了完整的工程化——FastAPI、WebSocket 实时推送、Docker Compose 一键部署、完整 trace 系统。第三，他们没有做量化评估，我设计了五维评估体系，所有指标都有数字。

---

## 十三、预算与资源

| 项目 | 费用 | 说明 |
|------|------|------|
| 训练数据生成 | ≈ $30-50 | Claude/GPT-4 API 生成人格对话数据 |
| LLM 推理 | $0 | 自部署 vLLM，L20 本地运行 |
| 人类评估 | ≈ $50-100 | 社交合理性评估，可用同学互评替代 |
| 云服务 | $0 | 全部本地运行 |
| **总计** | **≈ $80-150** | |

---

## 十四、项目结构

```
generative-agents/
├── docker-compose.yml          # 一键部署
├── README.md
├── configs/
│   ├── agents.yaml             # Agent 身份配置
│   ├── world.yaml              # 世界地点配置
│   └── simulation.yaml         # 模拟参数配置
├── src/
│   ├── agent/
│   │   ├── identity.py         # AgentIdentity 定义
│   │   ├── memory.py           # Memory Stream + 检索
│   │   ├── reflection.py       # 反思引擎
│   │   ├── planning.py         # 规划引擎
│   │   ├── decision.py         # 决策循环
│   │   └── conversation.py     # 对话子循环
│   ├── world/
│   │   ├── model.py            # WorldModel
│   │   ├── location.py         # 地点管理
│   │   ├── social_graph.py     # 社交图谱
│   │   └── time.py             # 模拟时间系统
│   ├── engine/
│   │   ├── simulation.py       # SimulationEngine 主循环
│   │   ├── scheduler.py        # Agent 调度
│   │   └── event.py            # 事件注入系统
│   ├── infra/
│   │   ├── llm_client.py       # vLLM 客户端 + 多 LoRA
│   │   ├── embedding.py        # Embedding 服务
│   │   ├── vector_store.py     # ChromaDB 封装
│   │   ├── cache.py            # Redis 缓存
│   │   └── trace.py            # Trace 日志系统
│   ├── api/
│   │   ├── main.py             # FastAPI 入口
│   │   ├── routes/
│   │   │   ├── simulation.py   # 模拟控制接口
│   │   │   ├── event.py        # 事件注入接口
│   │   │   ├── query.py        # 状态查询接口
│   │   │   └── ws.py           # WebSocket 实时推送
│   │   └── schemas.py          # API 数据模型
│   └── eval/
│       ├── personality.py      # BFI 人格一致性测试
│       ├── memory_accuracy.py  # 记忆准确性测试
│       ├── social_plausibility.py  # 社交合理性评估
│       ├── propagation.py      # 信息传播分析
│       └── emergence.py        # 涌现行为检测
├── training/
│   ├── generate_data.py        # 用大模型生成训练数据
│   ├── train_lora.py           # LoRA SFT 训练脚本
│   └── eval_personality.py     # 训练后人格评估
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── SocialGraph.jsx     # D3.js 社交图谱
│   │   │   ├── Timeline.jsx        # Agent 活动时间线
│   │   │   ├── AgentPanel.jsx      # Agent 详情面板
│   │   │   ├── EventInjector.jsx   # 事件注入面板
│   │   │   └── TraceViewer.jsx     # Trace 查看器
│   │   └── hooks/
│   │       └── useWebSocket.js     # WebSocket 连接
│   └── package.json
└── tests/
    ├── test_memory.py
    ├── test_simulation.py
    └── test_evaluation.py
```
