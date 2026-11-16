> This article develops the themes of our embodied AI discussion on September 24, 2026. Reference links were checked on November 16, 2026. It covers the model versions selected for that discussion, rather than presenting a list of the latest releases. Experimental results are attributed to their sources. The architectural choices and research priorities proposed here are our judgments, not reports of experiments already completed by our team.

Embodied AI is entering a phase in which we need to reconsider how work is divided. General-purpose multimodal models are becoming more capable, making more visual understanding, task decomposition, and tool use available through existing models. Yet robot execution in the real world remains fragile: objects slip, contact states change, views become occluded, and a task can fail at its final step.

This raises a practical question: **if general-purpose models can take on more high-level cognition, what should an embodied AI team's core assets be?**

Our view is to treat general cognition as an improving, replaceable source of capability, and concentrate research on reliable physical interaction, coordination across system layers, and the data infrastructure that can continuously improve both. A layered architecture lets us benefit from advances in different technologies while retaining control over the outcome of a complete task.

This view contains two hypotheses that need testing. First, general-purpose models will reduce the room for differentiation of some specialized embodied reasoning models. Second, physical execution and data feedback still contain many problems that must be solved close to real tasks. Neither hypothesis is established by the attention surrounding a model release; both require experiments.

## 1. Be precise about what it means to replace an “embodied brain”

The official GPT-6 Astra announcement describes advances in general reasoning, software tasks, and computer use. These advances give robotics teams access to stronger cognitive tools. They do not directly establish that robot contact control, action generalization, or real-world reliability have been solved.[^gpt6]

For an embodied AI team with limited resources, the issue is how readily its investment could be superseded. If we use scarce robot data and compute to retrain scene question answering, common-sense understanding, and general planning, an upgrade to an external foundation model may cover a substantial share of those gains. This risk is particularly relevant to high-level semantic capabilities.

However, claiming that “a specialized System 2 will never have a role” goes too far. Robots have their own states, tool protocols, task constraints, and histories. We need to test whether a general-purpose model can interpret this information consistently, recognize progress and failure within a useful latency budget, and operate at an acceptable cost. Domain adaptation may still help, but it should target measured gaps, rather than follow an assumption that we must own a proprietary brain.

Nor should we assume that the physical world is beyond the reach of large-scale learning. As the examples below show, pretraining on human behavior, reinforcement learning in simulation, and self-play are expanding the range of physical capabilities that can be learned. **Difficulty does not create a permanent barrier to competition. What is worth building is the ability to identify bottlenecks, collect useful data, and verify real improvements more quickly.**

## 2. Why layers: task semantics, action generation, and body feedback operate on different timescales

We borrow Figure's System 0/1/2 terminology as a framework for discussion, not as a universal classification of every company's architecture. Figure's network partition has a specific implementation; the table below is a functional abstraction for our own system design.

| Layer | Main question | Useful outputs | Constraints we care about |
| --- | --- | --- | --- |
| System 2: task cognition | What should be done, what comes next, and when should the plan change? | Subgoals, skill calls, constraints, and acceptance criteria | Semantic correctness, progress assessment, cost, and latency |
| System 1: perception-action policy | How can this subgoal be achieved from the current state? | Timestamped action chunks, local progress, and failure information | Feedback correction, memory, contact adaptation, and action continuity |
| System 0: body execution | How should actions be executed under the current dynamics and contacts? | Joint or actuator commands | Real-time response, balance, tracking error, and constraint satisfaction |

Layering does not require a separate large model for each layer, nor does it rule out joint training. It first defines interfaces and responsibilities. A higher layer may run more slowly, but it must not block body stabilization. A lower layer may run continuously, but it must accept cancellation, pauses, and goal updates. Every layer must report its state and uncertainty back to the system.

This composability is what we want to preserve. If a general-purpose model becomes the best System 2, we should integrate it. If an end-to-end policy performs better on a particular task, several layers can be encapsulated within one skill. The architecture should serve complete-task performance, rather than protect a fixed set of module names.

## 3. Figure: beyond layered control, pretraining data becomes a focus of competition

### From Helix to Helix 02

Helix, introduced in 2025, combined slower semantic reasoning with fast upper-body control. System 2 produced semantic representations, which System 1 combined with current perception to generate continuous actions. This offered a way for semantic generalization and low-latency control to work together without requiring a single inference process to handle every timescale.[^helix]

There is an important technical boundary here: the S2-to-S1 interface in Helix consists of jointly trained continuous latent variables, and gradients can cross that interface. Integrating an external model such as GPT is therefore more involved than changing an API endpoint. It requires representation alignment, adaptation training, or a redefinition of the skill interface. The `SkillSpec` proposed later in this article is a design suggestion for composing systems; it operates at a different level from Figure's native latent interface.[^helix]

Helix 02 extended control to the whole body and added System 0. Figure reports that S1 produces whole-body joint targets at 200 Hz, while S0 runs at 1 kHz. S0 has approximately 10 million parameters, uses more than 1,000 hours of retargeted human motion, and is trained in more than 200,000 parallel simulation environments. These frequencies were disclosed for Helix 02 and should not be attributed to Helix 2.5 without supporting disclosure.[^helix02]

For us, the lesson is that the body execution layer is more than a passive command relay. If the higher layer must specify balance, posture, and contact compensation in detail on every occasion, the planning problem quickly becomes more complex. Learning these capabilities as a reusable body prior can simplify how higher layers describe behavior. The prior's operating range, failure modes, and hardware constraints must also be part of the interface.

### Helix 2.5: what “zero-shot generalization across 30 homes” means

A key change in Helix 2.5 is pretraining from random initialization on Index human behavior data, followed by separate adaptation of the same base model to three behaviors: tidying living rooms, folding towels, and making beds. Figure tested in 30 unseen homes, and the official article reports an increase from 9% to 56% in a controlled pretraining ablation. Here, zero-shot refers to the environments and objects; the tasks were still adapted using data collected at other locations.[^helix25]

The most useful aspect of this experiment is its attempt to separate the contribution of foundation pretraining from that of task-data coverage. For our purposes, a similar experiment is more informative than another successful demonstration video: holding the task training set and evaluation set fixed while changing only the pretraining source can reveal what the base model actually contributes.

Figure also reports how action prediction error changes as pretraining data increases, with model size and downstream training held fixed. This is evidence of data scaling under particular conditions. It does not establish that arbitrary increases in compute will produce proportional gains in real-world success. Prediction error, task success, and commercial usability still need to be measured separately.[^helix25]

### Index: scaling data also means managing its distribution

Index expands behavioral coverage by collecting human videos, with a processing pipeline that includes filtering, fraud review, deduplication, rebalancing, and hierarchical descriptions. This differs from teleoperation that directly records robot actions, and it is not another name for the original UMI approach.[^index]

The question we care about is whether a data platform can identify what the next batch of data is missing. If new videos merely repeat existing situations, a larger dataset may not produce greater capability. Collection should be guided jointly by task coverage, failure distributions, and training gains. For a small team, selecting valuable data for a specific problem is usually more actionable than pursuing a total number of hours that is difficult to interpret.

## 4. PI and Gemini: high-level cognition, conditional control, and action capabilities continue to evolve together

### The PI series: from generalist action models to steerable behavior distributions

π₀ combined pretrained vision-language capabilities with continuous action generation, using Flow Matching to learn action distributions. π₀.₅ pushed further toward heterogeneous data and generalization in unseen environments. Their progression suggests that inheriting vision-language knowledge is only a starting point; how robot experience enters the model matters just as much.[^pi0][^pi05]

The RECAP approach in π*₀.₆ brought demonstrations, corrections, and autonomous execution experience together, emphasizing the transition from being able to complete a task to improving reliability and throughput. It turns deployment experience back into training signals, rather than leaving failures solely to human review after a demonstration.[^pistar06]

A particularly relevant mechanism in π₀.₇ is its use of language, visual subgoals, quality and speed metadata, and control modes to disambiguate behavior in heterogeneous data. Its high-level policy can produce subtasks, a lightweight world model can produce goal images, and the action expert executes using observations and memory.[^pi07]

As a schematic modeling view, we can write an action policy as `p(A | O, H, G, M)`: `A` is a future action chunk, `O` the current observation, `H` the history, `G` the subgoal, and `M` conditions such as speed, quality, and control mode. This is not a reproduction of the original model's formula. It illustrates a data principle: before mixing datasets, determine which differences should be explicit conditions and which should be handled by invariant capabilities learned by the model.

This has direct implications for data design. The same label, “pick up the cup,” may cover different grasping methods, speed requirements, degrees of failure, and control spaces. If these differences are not recorded, the training objective will mix behaviors that are individually reasonable but conditioned on different circumstances. We should treat the data schema as part of the model interface: conditions omitted during collection are often difficult to reconstruct during training.

### Gemini Robotics: foundation model teams are also building action and deployment layers

Gemini Robotics 1.5 already included coordination between embodied reasoning and action models in its approach. For Robotics 2, the version considered here, the official description distinguishes task reasoning in ER 2, whole-body VLA capabilities in Robotics 2, and local execution and adaptation in On-Device 2.[^gemini15][^gemini2]

This carries two implications for us. Making high-level reasoning replaceable is consistent with the growing availability of capabilities from external providers. At the same time, foundation model teams are also working on bodies, end effectors, and local deployment. We cannot assume that they will remain confined to System 2.

“We work on System 1” is therefore insufficient as a strategy. The more specific question is: for which tasks, sensors, contact conditions, and deployment constraints can we achieve more reliable outcomes with less data and time? Answering it requires a measurable task scope and a process for continuously comparing our results with external models.

## 5. Robot-free collection and physical prompting: data interfaces are changing how models are used

“Robot-free data” generally means that collecting the data does not require operating a robot. It does not mean that the resulting data is automatically compatible with any robot. Viewpoints, coordinate frames, action representations, latency, reachability, and contact information all determine whether a demonstration can become an executable policy.

The original UMI collects demonstrations with a handheld gripper and emphasizes relative trajectory representations, inference-latency matching, and robot kinematic constraints. Its contribution includes designing the collection hardware and the policy interface together.[^umi] From this perspective, data quality is about more than clear images or correct labels: it also depends on retaining the information that deployment actually needs.

### Generalist: from pretraining to physical prompting

Generalist's GEN-0 emphasizes pretraining scaling with physical interaction data, while GEN-1 advances toward task mastery through post-training on small amounts of robot data.[^gen0][^gen1] These stages address two different questions: whether foundational capabilities can scale, and whether they can be adapted to practical tasks at low cost.

GEN-1.5 attempts to shorten adaptation further by placing demonstrations containing sensor and action information directly into a 30-second context. Across 10 simple, short tasks, it reports an average success rate of 59% with a single demonstration and no gradient updates, with a standard deviation of 10%. With five minutes of data and 10 gradient updates, the reported rate is 83%, with a standard deviation of 9%. The official 100 Hz figure describes action trajectories; it should not be interpreted as 100 complete network forward passes per second.[^gen15]

We are interested in this approach because it may change how skills are delivered. If demonstrations become inputs, teams must manage more than model weights: they also need demonstration libraries, retrieval conditions, context budgets, and demonstration quality. Evaluation must distinguish between reusing an existing skill in an unseen environment and acquiring a previously unlearned behavioral rule from context. These capabilities differ in both value and difficulty.

### Reward AI: designing collection devices and control interfaces together

OM-1 uses Omnibody Hand and One Data Interface to organize human demonstrations, combining vision, touch, proximity, pose, and force signals. The company states that the policy needs neither teleoperation nor robot training data, but its control layer still uses reinforcement learning in simulation and runs high-frequency feedback independently. It shares UMI's direction of reducing dependence on robot-based collection, while using different devices and action interfaces.[^om1]

This example reinforces our view that models, data, and control are difficult to optimize in complete isolation. Recording more precise contact information may be more useful than switching to a larger visual encoder, but that information yields benefits only if the model can use it and the execution layer can respond. The research question should progress from “can we add another sensor?” to “for which failures does this sensor provide demonstrably useful new information?”

## 6. Skild, Atlas, and RSI: improvement requires feedback loops at different levels

### Skild S1: using task demonstrations as conditions

Skild S1 is a product name, not a direct equivalent of Figure's System 1. Its public approach emphasizes in-context learning conditioned on video demonstrations, with reports of execution on unseen tasks and tasks lasting up to roughly ten minutes. Whereas Generalist describes the natural emergence of this capability, Skild explicitly trains for understanding tasks from demonstrations. The tasks, data, and evaluations differ, so the two cannot be ranked on a common scale from these reports.[^skilds1]

We should instead learn from the problem being posed: how is a new skill specified? Video prompts can preserve details that language may struggle to describe fully. They can also contain irrelevant movements, viewpoint differences, and features of the demonstrator's body. A system must identify which information defines the goal and which merely reflects one way of achieving it.

### Physical Self-Play: improving a policy within an environment

Skild's Physical Self-Play uses the objective of scoring goals, with policies competing against recent versions in simulation. It reports real-world transfer after a cumulative 140 years of simulated experience. This shows how self-play can generate curricula and experience for dynamic interaction. The clear rewards and repeatable simulation available in soccer do not automatically provide the conditions needed for scalable learning in open-ended household tasks.[^selfplay]

For our own work, the priority is to identify tasks with trustworthy rewards, manageable reset costs, and sufficiently faithful simulation. Once these conditions are defined, additional training compute has a clear role. Otherwise, training may simply optimize the wrong objective more efficiently.

### Atlas: beyond the action model, engineering interfaces determine whether learning can continue

The Atlas policy described by Boston Dynamics and TRI uses a Diffusion Transformer and Flow Matching. Images arrive at 30 Hz; the model predicts 48 action steps, covering approximately 1.6 seconds, and typically executes 24 of them before running inference again. These quantities are distinct from the network's forward-pass frequency and the low-level servo frequency. The work also emphasizes shared interfaces between simulation and real robots, along with demonstration review and feedback.[^atlas]

This example reminds us that system progress can come from straightforward but difficult engineering: ensuring that teleoperation and autonomous policies use consistent action semantics, making simulation and real-world records comparable, and tracking the samples used in every training run. These capabilities improve the credibility of all subsequent model experiments and deserve investment as research infrastructure.

### RSI and research agents: improving the experimental process

Simate's public framework connects the Sinfra platform, Sipai models, and the RoboScientist research process. At the time of our check, its website still described the RoboDojo evaluation as in progress. We therefore treat it as a direction to watch in automated research and do not adopt rankings from media reports that lack sufficient verification.[^simate]

Two levels should be distinguished here. Self-play improves a policy within an environment; research agents propose experiments, run code, and compare results to improve the research process. For the latter to become a credible mechanism for recursive improvement, it needs at least controlled variables, data versions, experimental lineage, independent evaluation, and failure records. Automatically generating more experiments is different from consistently producing useful knowledge.

### Comparing the questions behind the approaches

| Approach | Notable changes in the public work | Implications for our work |
| --- | --- | --- |
| Figure / Index | Layered whole-body control; human-video pretraining and transfer to new homes | Design control interfaces and data distributions together |
| PI | Conditional action generation; policy improvement from deployment experience | Preserve modes, quality information, and failures in the data |
| Gemini Robotics | Parallel advances in reasoning, whole-body actions, and on-device execution | Large teams are also building action layers; keep comparing against external capabilities |
| Generalist / Reward | Collection without robots; physical prompting and unified interfaces | Reduce collection costs while preserving executable action information |
| Skild | Demonstration-conditioned learning and simulated self-play | Specifying a skill and improving a policy are different problems |
| Atlas | Action chunking, shared interfaces, and data review | Reliable infrastructure increases the value of every model experiment |
| Simate / research agents | Connecting data, models, and experimental workflows | Automation depends on reproducible, independent evaluation |

This table compares research questions and approaches, not the strength of the companies. The experimental conditions and limits of the evidence are discussed alongside the references above.

## 7. Three interdependent parts we should build

The companies above follow different paths, but they suggest a common lesson for us: complete-task outcomes depend on coordination between cognition, actions, the body, and data. The architecture below is our implementation proposal, not a reconstruction of any company's internal system.

<figure class="figure">
<a href="{{BASE}}/assets/architecture-en.svg" aria-label="View the full layered architecture diagram"><img src="{{BASE}}/assets/architecture-en.svg" alt="Proposed architecture: a replaceable System 2 coordinates System 1 and System 0 through an agent runtime, while physical interaction records feed a data and evaluation loop." loading="lazy" width="1050" height="620"></a>
<figcaption>Figure 1 · Our proposed system architecture. The modules represent functional responsibilities, rather than reproducing Figure's native latent interface. Select the image to view it at full size.</figcaption>
</figure>

### 7.1 Make System 2 replaceable and establish clear execution contracts

Task state and execution contracts should be central to the agent framework. Every skill request from a higher layer should describe, at a minimum, the goal, applicability conditions, constraints, stopping criteria, and acceptance checks. A skill's result must distinguish success, a locally recoverable failure, a failure that requires replanning, and a state that requires human intervention.

For example, “put the cup in the cabinet” cannot be represented by a single model call alone. During execution, the system must keep assessing whether the cup is still in the hand, whether the cabinet door is reachable, and whether the object has been placed securely. If grasping fails, should it retry in place, change the pose, or ask the higher layer to select another target? These states determine how the system makes and preserves progress.

We propose organizing the runtime around four message types:

| Message | Core fields | Purpose |
| --- | --- | --- |
| `SkillSpec` | Goal, constraints, preconditions, acceptance criteria, timeout | Let different high-level models invoke the same skill |
| `Observation` | Sampling time, coordinate frame, state, confidence information | Let reasoning account for when an observation is valid |
| `ActionChunk` | Start time, action space, trajectory, validity period | Give policies and controllers a consistent interpretation of time |
| `Outcome` | Progress, failure type, evidence, recovery suggestions | Let task planning and data feedback work from the same facts |

This is a proposed interface design. A real implementation also needs cancellation and preemption, action queues, timeout handling, version compatibility, and state recovery. Establishing stable contracts early reduces the likelihood that replacing one model will require rewriting the whole system.

### 7.2 Focus System 0/1 research on weaknesses in execution with feedback

Priorities worth investigating include state estimation before and after contact, memory under occlusion, transitions between action chunks, failure recovery, and adaptation to changes in the robot body. All of these directly affect whether a complete task can continue to make progress.

Action chunking is particularly easy to misinterpret: producing a densely sampled trajectory does not mean that the system can correct it from perception at the same frequency. PI's Real-Time Chunking addresses the conflict between inference latency and action continuity by generating the next chunk asynchronously and handling the prefix of actions already committed for execution.[^rtc] We therefore need to record more than average model inference time. We also need observation age, queue length, end-to-end latency percentiles, and discontinuities when new actions enter execution.

At System 0, the balance between learned and conventional control should also be determined through task evaluation. A learned policy can provide a motion prior while deterministic constraint handling and state estimation remain in place. The key is to define each component's responsibilities and operating range, then test their combined performance under disturbances, changing contacts, and changing loads.

### 7.3 Design data infrastructure alongside model research

The data loop should cover raw records, processed outputs, training snapshots, and real-world evaluation. For every trajectory, we need to know the robot embodiment, sensor and calibration versions, control space, human takeovers, and final success criteria. Model differences become interpretable only when these conditions can be reproduced.

Next, turn failures into collection requirements. A task failure can initially be classified as a misunderstanding of the goal, an error in identifying the target, a reachability problem, a contact failure, an action discontinuity, a recovery failure, or an incorrect acceptance decision. Classification is not the endpoint: it should guide whether to collect more data, change the representation, modify control, or fix the hardware.

We should also avoid a common mistake: responding to system failure by collecting more successful demonstrations of the same kind. If latency or calibration is the main bottleneck, more demonstrations may not help. The data platform should locate the problem in a component we can intervene on, and preserve evidence from before and after the intervention.

<figure class="figure">
<a href="{{BASE}}/assets/data-loop-en.svg" aria-label="View the full data feedback loop diagram"><img src="{{BASE}}/assets/data-loop-en.svg" alt="The data loop begins with tasks and failure diagnosis, proceeds through targeted collection, versioned data, training ablations, and independent real-world evaluation, then feeds back into the next round of tasks." loading="lazy" width="1050" height="610"></a>
<figcaption>Figure 2 · Our proposed data and research process. Independent held-out evaluation determines whether to accept an improvement; failure diagnosis guides the next round of collection. Select the image to view it at full size.</figcaption>
</figure>

## 8. Let experiments determine where resources go

We suggest starting with reproducible comparisons, rather than deciding in advance which “large model” we must train. The first set of experiments holds System 0/1, the task set, and tool interfaces fixed, and changes only the higher layer: a general-purpose multimodal model, a specialized embodied reasoning model, a general-purpose model with domain adaptation, and a reference condition with human-provided subgoals.

These comparisons can distinguish high-level reasoning bottlenecks from execution bottlenecks. If even human-provided subgoals fail to improve completion rates substantially, further System 2 optimization may not be the most effective current investment. If a general-purpose model already meets the target under the same interface, specialized training budgets should move toward unresolved problems.

The second set of experiments holds the model architecture and task-training budget fixed while comparing data sources and processing choices: ordinary successful demonstrations, targeted collection for failures, trajectories containing recovery, and data with additional contact information. New data should be evaluated on independent objects, scenes, or task combinations, rather than reporting only improvements within the training distribution.

The third set tests coordination across the system. Does asynchronous action chunking reduce pauses? Does local recovery reduce high-level replanning? Does progress assessment prevent repeated actions? These capabilities must be evaluated through complete tasks, not represented solely by single-step prediction accuracy.

We suggest reporting a common set of metrics: complete-task success, autonomous recovery success, human takeovers per hundred tasks, labor costs including resets, effective throughput, end-to-end latency, and the amount of data needed to reach the target quality. Generalization tests should separately identify unseen objects, environments, embodiments, and skills, rather than compressing different levels of difficulty into one number.

A practical 90-day schedule would use the first 30 days to establish a fixed task set, baselines, logging, and held-out evaluation. Days 31–60 would focus data collection and improvements in contact handling and recovery on the dominant failure modes. Days 61–90 would complete at least two reproducible data–model iterations and the System 2 replacement comparison. Research agents can assist with experiments throughout, but every conclusion must pass the same independent evaluation.

These plans should also allow our judgments to be overturned. If an external System 1 already meets requirements at a lower cost, integration should take priority. If substantial additional data produces no gains, we should revisit representations, distributions, and optimization. If sensors or mechanisms are the main bottleneck, hardware investment should change accordingly. One value of the architecture is to make these changes inexpensive.

The capability we want to build is the ability to turn stronger general-purpose models into more reliable physical task execution, while making every real interaction useful evidence for the next improvement. System 0/1, agent coordination, and data infrastructure should be developed as a joint design problem.

## References

The references below prioritize official releases, original papers, and project pages. Company demonstrations and internal evaluations are not equivalent to independent replication across institutions. Success rates from different task settings are not used to rank models directly.

[^gpt6]: OpenAI. [GPT-6 Astra: A new generation of intelligence](https://openai.com/index/gpt-6-astra/). 2026. We cite the direction of its general capabilities, without extrapolating its reported metrics to real-world robot performance.
[^helix]: Figure. [Helix: A Vision-Language-Action Model for Generalist Humanoid Control](https://www.figure.ai/news/helix). 2025-02-20.
[^helix02]: Figure. [Introducing Helix 02: Full-Body Autonomy](https://www.figure.ai/news/helix-02). 2026-01-27.
[^helix25]: Figure. [Helix 2.5: Zero-Shot 30-Home Generalization](https://www.figure.ai/news/helix-2-5-zero-shot-30-home-generalization). 2026-09-17. We use the 9% and 56% figures disclosed in the official article, without treating the company's experiment as a common industry benchmark.
[^index]: Figure. [Introducing Index: Building The World’s Largest and Most Diverse Physical Dataset](https://www.figure.ai/news/introducing-index). 2026-08-25.
[^pi0]: Physical Intelligence. [π₀: Our First Generalist Policy](https://www.pi.website/blog/pi0). 2024-10-31.
[^pi05]: Physical Intelligence. [π₀.₅: A VLA with Open-World Generalization](https://www.pi.website/blog/pi05). 2025-04-22.
[^pistar06]: Physical Intelligence. [π*₀.₆: A VLA that Learns from Experience](https://www.pi.website/blog/pistar06). 2025-11-17.
[^pi07]: Physical Intelligence. [π₀.₇: A Steerable Model with Emergent Capabilities](https://www.pi.website/blog/pi07). 2026-04-16.
[^gemini15]: Google DeepMind. [Gemini Robotics 1.5 brings AI agents into the physical world](https://deepmind.google/blog/gemini-robotics-15-brings-ai-agents-into-the-physical-world/). 2025-09-25.
[^gemini2]: Google DeepMind. [Gemini Robotics 2 brings whole body intelligence to robots](https://deepmind.google/blog/gemini-robotics-2-brings-whole-body-intelligence-to-robots/). 2026-07-30. We use the fixed release article; the continuously updated model overview does not define the boundaries of a historical version.
[^umi]: Chi, C., Xu, Z., Pan, C., et al. [Universal Manipulation Interface: In-The-Wild Robot Teaching Without In-The-Wild Robots](https://umi-gripper.github.io/). Robotics: Science and Systems, 2024.
[^gen0]: Generalist. [GEN-0: Embodied Foundation Models That Scale with Physical Interaction](https://generalistai.com/blog/gen-0). 2025-11-04.
[^gen1]: Generalist. [GEN-1: Scaling Embodied Foundation Models to Mastery](https://generalistai.com/blog/gen-1). 2026-04-02.
[^gen15]: Generalist. [GEN-1.5: Embodied Foundation Models are One-Shot Learners](https://generalistai.com/blog/gen-1.5). 2026-08-19. Standard deviations are reported as given by the company; they are not confidence intervals.
[^om1]: Reward AI Team. [OM-1: Frontier Robot Intelligence, Learned Firsthand from Humans](https://www.rewardai.com/blog/OM-1/). September 2026, as specified in the website's Citation section.
[^skilds1]: Skild AI. [Introducing S1: In-Context Learning for Robotics](https://www.skild.ai/blogs/s1). August 2026; the month is cross-checked against “last month” in the subsequent Self-Play article.
[^selfplay]: Skild AI. [Physical Self-Play](https://www.skild.ai/blogs/physical-self-play). 2026-09-23.
[^atlas]: Boston Dynamics / Toyota Research Institute. [Large Behavior Models and Atlas Find New Footing](https://bostondynamics.com/blog/large-behavior-models-atlas-find-new-footing/). Accessed 2026-11-16.
[^simate]: Simate. [Intelligence, in motion — Platform, Model, Scientist](https://mate-robot.cn/home/). Accessed 2026-11-16. The [36Kr report](https://eu.36kr.com/en/p/3996798461628297) supplied for the original discussion informed the topic selection; the technical descriptions and evaluation status here follow verifiable official information.
[^rtc]: Black, K., Galliker, M. Y., & Levine, S. [Real-Time Execution of Action Chunking Flow Policies](https://www.pi.website/download/real_time_chunking.pdf). NeurIPS, 2025.
