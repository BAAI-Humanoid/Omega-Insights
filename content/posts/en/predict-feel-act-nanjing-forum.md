> This article is adapted from my talk at the Nanjing forum on November 15, 2026. It draws on the results reported in the Omega-EVA and DECO papers, introduces our ongoing work on SEET, and discusses research directions in physical interaction and data feedback loops. These projects are at different stages of validation; a more complete closed loop connecting them remains a research objective.

In the [previous article]({{BASE}}/en/insights/embodied-intelligence-physical-loop/), we discussed a research priority: as general-purpose models become more capable, how should embodied AI teams invest in physical execution, system coordination, and data feedback? In this talk, I wanted to take that question further: **what do we want robots to learn from physical interaction, and how can we tell whether they have learned it?**

My starting point is a concrete task: a robot picks up a basket, moves to a shelf, retrieves an item, and returns to put the basket down. Each action seems straightforward in isolation. Yet the state left by one step determines whether the next can proceed. We need to study the relationship between actions, their consequences, and the feedback that actually arrives.

Predict, Feel, and Act offer three perspectives on this problem: anticipating the consequences of actions, understanding contact during interaction, and turning expectations and feedback into behavior that keeps a task moving.

## 1. From action sequences to an evolving task state

A slightly misplaced grasp on the basket may not cause an immediate failure, but it can affect the subsequent motion. A hand reaching beside an object may appear to be in position without actually grasping it. Arriving at a shelf does not necessarily put the robot in a suitable stance for bimanual manipulation. In each case, completing a local action leaves a further question: can the overall task continue?

The difficulty of a long-horizon task therefore cannot be measured only by its number of actions or its duration. More fundamentally, the robot must continually maintain its task state: what is being held, which constraints have been established, which objects remain accessible, and whether the prerequisites for the next step still hold. A small contact error can propagate through the task sequence.

This leads to three connected questions. **Predict** concerns what happens before execution: how will the world change if this action chunk is executed? **Feel** concerns the interaction itself: did the expected contact occur, is the grasp secure, and is motion obstructed? **Act** concerns what comes next: when reality differs from the prediction, how should the robot adjust while preserving its original task objective?

We study these questions at different levels. Omega-EVA uses the predicted consequences of candidate actions in action generation. DECO brings measured tactile feedback into a bimanual policy. SEET explores learning contact representations from vision and interaction context. All three concern physical interaction, but their inputs, outputs, and stages of validation need to be explained separately.

<figure class="figure">
<a href="{{BASE}}/assets/predict-feel-act-loop-en.svg" aria-label="View the full Predict, Feel, Act research framework"><img src="{{BASE}}/assets/predict-feel-act-loop-en.svg" alt="Research framework: predict the consequences of candidate actions, understand actual contact, adjust behavior through feedback, and return interaction experience to data collection and training. Omega-EVA, SEET, and DECO address different research questions." loading="lazy" width="1050" height="690"></a>
<figcaption>Figure 1 · A conceptual research framework redrawn from the talk. Arrows show the information relationships we aim to establish; they do not imply that Omega-EVA, SEET, and DECO have already been integrated into a single system.</figcaption>
</figure>

## 2. Predict: letting a policy inspect its own proposed action

For a robot, a world model must answer a specific question: given the current state and a candidate action, what will that action cause? In the same scene, closing the fingers a little earlier or later, or choosing a different grasp position, may change the outcome. Predicting how a scene typically develops is not enough to help a policy choose among these alternatives.

Omega-EVA takes its name from Envision, Verify, and Act. A policy first proposes an action chunk from the current observation and task. An action-conditioned world model predicts the future latent state associated with that proposal. An action refiner then jointly reads the current state, predicted future, and proposed action to produce the final action sequence.[^eva-paper]

The information flow can be written as:

```text
candidate action = policy(current observation, task)
predicted consequence = world model(current observation, candidate action)
final action = refiner(current state, predicted consequence, candidate action)
```

Each input plays a different role. The current state describes the starting point, the candidate action describes the intended behavior, and the predicted consequence describes the changes that behavior may produce. The refiner connects these three pieces of information and uses the anticipated outcome to revise the action.

Here, Verify means learned consequence feedback and action refinement. It is not a formal proof of correctness, and it does not guarantee that the world model's prediction is accurate. After executing part of an action chunk, the robot still needs a new observation before its next decision. Prediction before execution and observation after execution are complementary parts of the loop.

This also shapes how we evaluate a world model. A plausible predicted future is one criterion. The more direct question is whether that future informs action selection and helps the robot complete its task.

## 3. A future representation can support action without becoming a video

Omega-EVA predicts action consequences in latent feature space. Online decisions use the future representation directly, without first generating a complete video and then extracting information from it again. Decoded future images serve mainly as diagnostics, helping us inspect what the model preserves and what its predictions miss.[^eva-paper]

Training has three stages. The first learns action-conditioned latent dynamics. The second learns an action policy from dynamics-aware visual representations, together with prediction objectives. The third feeds the policy's candidate action back into the world model and learns to produce a refined action from the proposal and its predicted consequence. Prediction and control are thus connected through a specific action proposal.

This is a computational choice. We want the future representation to retain information that supports decisions; reconstructing pixels from it serves a different purpose. Working in latent space does not automatically produce a better policy. Execution-based evaluation remains the deciding test.

The paper reports the following results for the proposal policy and the complete EVA pipeline. The three rows use different evaluation protocols and should be interpreted separately.[^eva-paper]

| Evaluation setting | Proposal policy | Complete EVA | Gain |
| --- | ---: | ---: | ---: |
| LIBERO | 97.9% | 98.6% | 0.7 percentage points |
| LIBERO-PLUS: zero-shot transfer from LIBERO | 71.3% | 72.2% | 0.9 percentage points |
| LIBERO-PLUS: trained on the benchmark's data | 81.2% | 83.4% | 2.2 percentage points |

The paper also evaluates bimanual tasks in RoboTwin 2.0. The overall comparisons presented here support the value of the complete consequence-feedback and refinement pipeline, but these aggregate results alone cannot isolate each module's contribution. An aggregate improvement also does not imply improvement under every perturbation or on every task.

Our next questions are when prediction helps most and when prediction errors can instead hurt execution. If a model has mainly seen the world after successful actions, its understanding of mistakes, deviations, and opportunities for recovery may be incomplete. Modeling failure states and enabling recovery therefore remain directions that require further validation.

## 4. Feel: bringing measured contact into a bimanual policy

Beyond predicting visual consequences, the robot must understand another layer of physical state. A hand near a handle and a hand holding it securely are different states. An object that has not moved may still be untouched, or it may already be in contact but constrained. Occlusion makes these distinctions harder to infer from images.

DECO studies multimodal policies for bimanual dexterous manipulation. Vision describes the scene, proprioception describes the robot itself, and measured touch provides direct evidence of contact. These signals have different characteristics, so they can enter the policy through different mechanisms.[^deco-paper]

DECO stands for Decoupled Multimodal Diffusion Transformer. Visual and action tokens undergo separate projections before interacting through joint self-attention. Proprioceptive state conditions the model through AdaLN, while touch enters through a dedicated cross-attention pathway. This design gives each modality an explicit route into action generation.

Training follows two stages: first learn a visually guided manipulation policy, then introduce contact information through a lightweight tactile adapter. The second stage builds on the visual manipulation capabilities already learned while updating only a small fraction of the parameters.

Across the pooled execution trials in the paper's four real-robot task categories, successes increase from **289/400 to 330/400**. The overall success rate therefore rises from **72.25% to 82.50%**, a gain of **10.25 percentage points**. Tactile adaptation updates **7.97M of 91.02M** parameters, approximately **8.8%**. The success rate pools all execution trials; it is not an unweighted average of the four task-level percentages.[^deco-paper]

Under the evaluated tasks and conditions, these results show that a relatively small parameter update can turn contact information into better manipulation performance. They also suggest a useful question when a policy fails: alongside collecting more action demonstrations, we should examine whether the policy receives enough physical feedback and can use it effectively.

DECO has addressed bimanual dexterous manipulation from the outset. Both hands sustain a shared physical process, and the constraints created by one hand change the actions available to the other. The value of contact information should be understood within this coordination.

## 5. SEET: learning contact knowledge in visual representations

Measured touch is valuable, but robots differ in their hands, sensors, and contact layouts. When the embodiment changes, must all contact knowledge be learned again? This question motivates our ongoing work on SEET.

SEET combines SEE and Tactile. We call it a World Tactile Model, with an initial focus on **tactile estimation and contact representation learning**: using context such as multiview images, current proprioceptive state, and the previous frame's action to estimate current contact locations, probabilities, and forces. The previous action provides interaction context. Estimating current contact is a different task from predicting future contact conditioned on a future candidate action.

DECO and SEET therefore form a connected line of inquiry. DECO asks how a policy can use measured touch. SEET asks whether tactile supervision during training can teach contact knowledge to a visual model and eventually support reuse across different hardware configurations.

The architecture uses FLUX.2 Klein 4B as its visual generative backbone, with LoRA adaptation and tactile supervision to learn the relationship between visual observations and contact.[^flux2-klein] Work such as DreamZero, Fast-WAM, and LingBot-VA provides inspiration for connecting visual and physical interaction variables through a generative backbone. SEET focuses this idea on contact estimation, without directly reproducing their action-modeling designs.[^dreamzero][^fast-wam][^lingbot-va]

The shared backbone supports two outputs. One generates contact-marker images so that a person can inspect where the model believes contact occurs. The other reads contact probabilities and forces directly from finger-query features for each queried part, providing a numerical interface for downstream use.

The computational relationship matters: **the numerical branch produces its readout in a single forward pass. It does not wait for the contact-marker image to be generated, and it does not infer forces from that generated image.** A shared backbone allows the tasks to learn together. Visualization supports diagnosis, while the numerical interface supports subsequent computation and policy use.

<figure class="figure">
<a href="{{BASE}}/assets/seet-readouts-en.svg" aria-label="View the SEET dual-readout concept diagram"><img src="{{BASE}}/assets/seet-readouts-en.svg" alt="SEET architecture concept: multiview images, current state, and the previous frame's action enter a shared visual backbone. Separate branches generate contact-marker images and read contact probabilities and forces directly from finger queries. The numerical readout does not depend on image generation." loading="lazy" width="1050" height="740"></a>
<figcaption>Figure 2 · SEET's readout relationships, redrawn from the talk. A single forward pass refers to the numerical branch for contact probability and force. SEET remains ongoing research; the diagram describes the design, not a completed closed-loop validation with a downstream policy.</figcaption>
</figure>

The Allegro, Sharpa, and gripper examples in the talk show intermediate outputs for contact localization and force readout. These are simulation or dataset examples, and the Allegro demonstration includes training-set clips. They are not real-robot tactile measurements and do not establish zero-shot transfer to unseen embodiments. Showing outputs on several embodiments and demonstrating reliable cross-embodiment gains under an independent held-out protocol require different evidence.

Visual estimation also has limits. An image generally does not uniquely determine force; occlusion, object properties, and contact geometry all affect the inference. We need further evaluation of errors on unseen objects and embodiments, the amount of adaptation data required, and the practical gains when these estimates are connected to a downstream policy. Those experiments must determine whether contact knowledge can be reused.

## 6. Act: sustaining a complete task with local capabilities

Seen through the same research question, EVA supplies expectations about action consequences, SEET explores reusable representations of contact and force, and DECO studies how multimodal physical feedback enters a manipulation policy. Their shared concern is how a robot understands what it is doing to the world and how the world responds.

We aim to establish a sequence of information flow: form an expectation before acting, obtain feedback during interaction, and choose the next behavior based on the actual state. Building this coordination still requires decisions about which representations to share, which feedback to process separately, and how to balance computation with control requirements. System-level experiments must turn the conceptual connection into evidence.

The second half of the talk included a pharmacy-cart research demonstration with S1 and X Hand. Navigation, positioning in front of a shelf, and pick-and-place operations must remain coordinated throughout the task. At the end of each step, are the robot and objects in a state that supports the next one? This provides a platform for studying long-horizon interaction.

The demonstration and the opening basket task are two separate examples. Neither establishes a complete joint deployment of EVA, SEET, and DECO. A single demonstration shows a possible capability; reliability across repeated runs, performance under environmental changes, and adjustment after deviations require systematic evaluation.

In mobile manipulation, a contact error may only become apparent during movement, and a positioning error may only become apparent when the arm reaches out. When feedback arrives, and when the policy can revise its actions, directly affects whether the task can continue. This is why we want to test local models within longer task sequences.

## 7. Data must preserve the relationship between actions and the world

When the objective is to learn an action sequence, successful demonstrations provide direct supervision. When the objective expands to predicting consequences, understanding contact, and studying recovery, retaining only successful segments discards potentially valuable information.

An unsuccessful grasp still records a relationship between an action and changes in an object. An obstructed motion also records contact conditions and deviations in state. The key is to assign appropriate learning objectives to these data: successful demonstrations can supervise action learning, while failure trajectories can support dynamics modeling, deviation detection, and recovery research. Learning from failures does not require a policy to imitate failed actions.

Alignment is especially important for tactile learning. Vision, proprioception, actions, and tactile signals must refer to consistent times and contact regions. The model needs to know whether an image corresponds to the moment before contact, the establishment of contact, or force already being applied. Otherwise, collecting more data may simply add more ambiguous supervision.

Data infrastructure therefore needs to connect robot integration, collection, alignment and quality checks, training, evaluation, and the return of deployment experience into the next iteration. Deviations observed on a real robot should become actionable requirements: which contact transitions are missing, which failure conditions remain uncovered, and which interfaces need adaptation after a change of embodiment?

The goal is to accumulate reusable interaction knowledge. Alongside hours of data, we should measure the additional states, failure boundaries, and embodiment differences the data cover, and whether that information produces capability gains under a consistent evaluation protocol.

## 8. What would count as real progress?

I would define progress along this research direction through three concrete questions.

First, **can we collect less new data when the object, workstation, or task requirement changes?** This measures adaptation cost. If a model has learned reusable dynamics and contact knowledge, a new task should have an opportunity to benefit from it. Evaluation should record how much data is needed to reach a target level of performance, alongside the best final result.

Second, **can we reduce human takeovers after contact deviations or execution errors?** This measures the ability to continue acting and recover. We need to distinguish detecting a deviation, selecting an adjustment, and successfully recovering, while accounting for resets and human intervention over the complete task.

Third, **how much capability is retained when the robot embodiment or dexterous hand changes?** This measures the scope of transfer. We want physical knowledge to be shared, but joint limits, execution constraints, and sensor interfaces remain embodiment-dependent. Direct-transfer performance and the gains from a limited adaptation dataset should be measured separately.

These questions also connect this article to the [research priorities discussed in the previous one]({{BASE}}/en/insights/embodied-intelligence-physical-loop/). A focus on physical interaction should address measurable capability gaps. A data feedback loop should demonstrate that new experience helps close those gaps. Common task protocols, independent held-out conditions, and repeatable execution provide the basis for judging whether the investment works.

For me, Predict, Feel, and Act ultimately point toward the same goal: a robot that can anticipate the consequences of its actions, understand the contact that actually occurs, and keep a task moving when conditions change. These concrete questions guide our work from learning actions toward learning physical interaction.

## References

The methods and quantitative results for EVA and DECO are cited to the original papers. SEET's design and intermediate demonstrations are based on this forum talk. References to generative models and world action models provide research context; they are not evidence for SEET's experimental performance. External source links were checked on November 16, 2026.

[^eva-paper]: [ω-EVA: Envision, Verify, and Act with Latent Interactive World Models](https://arxiv.org/abs/2606.09457). 2026. This article compares the proposal policy with the complete EVA pipeline and does not attribute the aggregate gain to a single module.
[^deco-paper]: [DECO: Decoupled Multimodal Diffusion Transformer for Bimanual Dexterous Manipulation with a Plugin Tactile Adapter](https://proceedings.mlr.press/v306/li26fs.html). ICML, 2026. Success rates pool execution trials across four real-robot task categories.
[^flux2-klein]: Black Forest Labs. [FLUX.2 [klein]: Towards Interactive Visual Intelligence](https://bfl.ai/blog/flux2-klein-towards-interactive-visual-intelligence). 2026-01-15. Cited here only as the source of the visual generative backbone.
[^dreamzero]: [World Action Models are Zero-shot Policies](https://arxiv.org/abs/2602.15922) (DreamZero). 2026.
[^fast-wam]: [Fast-WAM: Do World Action Models Need Test-time Future Imagination?](https://arxiv.org/abs/2603.16666). 2026.
[^lingbot-va]: [Causal World Modeling for Robot Control](https://arxiv.org/abs/2601.21998) (LingBot-VA). 2026.
