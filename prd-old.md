# rOCDbot PRD

Version: 1.0  
Date: 2026-03-15  
Team: Hackathon core team  
Status: Build-ready

## 1. Executive Summary

`rOCDbot` is an agentic humanoid robotics project built around a simple but memorable behavior:

The robot notices environmental disorder that a detail-oriented human would notice, explains what is wrong, and physically fixes it.

For the hackathon, the product is a simulation-first system built on Unitree G1 + Isaac Lab + Nebius Token Factory:

- A scene is observed in Isaac.
- An LLM acts as an `Order Critic` that scores what looks wrong and proposes a correction.
- A G1 manipulation policy executes the correction.
- The system logs before/after state, rationale, and improvement metrics.
- If time allows, the team refines the correction policy with imitation learning first and RL second.

The core demo is not "general house cleaning." The core demo is:

1. A G1 sees an object on a table at the wrong angle or wrong placement.
2. rOCDbot identifies the violation.
3. rOCDbot plans a correction.
4. G1 walks to the object, picks it up, rotates/repositions it, and leaves the scene more orderly.

This project satisfies both hackathon statements because it combines:

- Open LLM reasoning and agentic planning.
- Robotics perception and action.
- Policy training and tuning in simulation.
- A credible path from semantic judgment to improved robot behavior.

## 2. Product Vision

Build a robot that enforces order in the physical world the way software linting enforces order in code.

Long term, the product is not just a tidying robot. It is a reusable `order-restoration layer` that can sit on top of existing robot stacks in hospitality, retail, inspection, facilities, and home robotics.

Examples:

- Hospitality: straighten chairs, reset table settings, align items at closing time.
- Retail: face products, align promotional displays, correct shelf drift.
- Facilities: restore standard room layouts and detect deviations.
- Industrial: compare current state to known-good layout and fix small placement errors.

## 3. Problem

Robots are usually trained to finish explicit tasks:

- pick this object
- carry this bin
- navigate to this point

They are much worse at noticing and fixing subtle disorder:

- one object is rotated 20 degrees off axis
- one item is slightly off grid
- one chair breaks the symmetry of a room
- a fork is on the wrong side of a plate

Humans notice these things instantly because they carry implicit priors about order, symmetry, etiquette, and layout consistency. Robots generally do not.

This creates a gap:

- vision systems can detect objects
- robot policies can move objects
- but there is no strong semantic layer deciding what is "out of place" in a human sense

rOCDbot fills that gap.

## 4. Product Thesis

The strongest thesis behind this project is:

LLMs already encode a large amount of human common sense about what orderly environments should look like. That semantic knowledge can be turned into:

- disorder detection
- correction planning
- synthetic labels
- reward shaping
- training data for robot behavior

In other words:

- LLMs decide what should be fixed.
- Robot policies learn how to fix it.

This split is important. We will not use the LLM as a motor controller. We will use it as a semantic critic and planner.

## 5. Hackathon Positioning

### Statement 1: Edge Inference & Agents

rOCDbot is an agentic pipeline, not a chatbot with tool calls.

It does all of the following:

- reasons over scene context
- optionally retrieves order rules or etiquette rules
- plans next corrective steps
- triggers physical action in simulation
- logs outcomes and improvement

Agent loop:

`scene -> order critic -> corrective planner -> robot skill -> evaluation`

This directly matches "reason over context, retrieve knowledge, plan next steps, and take actions."

### Statement 2: Robotics Optimization, Training, & Tuning

rOCDbot also satisfies the robotics statement:

- perceive environment
- reason about what is happening
- take meaningful physical actions
- train and refine a policy in simulation
- convert visual and language context into action

Our training stance is practical:

- `Must-have`: imitation learning / behavior cloning for correction behavior.
- `Stretch`: RL fine-tuning for precision and robustness.

This is the correct hackathon tradeoff. The official Isaac G1 locomanipulation environment is already wired for behavior cloning. We should use that advantage instead of trying to train a full humanoid from scratch.

## 6. Judging Strategy

### Impact Potential (20%)

We will frame rOCDbot as a general `physical quality-control layer` for robots:

- detect subtle physical drift
- restore known-good layouts
- learn preferences over time

The market story is stronger than "neat freak robot." It is:

`robots that maintain standards, not just complete tasks`

### Live Demo (45%)

The live demo is the most important criterion. Therefore:

- the primary demo is simulation-first
- it must be deterministic
- the scene reset must be fast
- the "before vs after" must be visually obvious

The initial scene must be clearly wrong to a human eye. The final scene must be clearly correct.

### Creativity and Originality (35%)

The creative angle is not only "robot tidies things."

The creative angle is:

- LLM as an order critic
- LLM-generated synthetic correction labels
- a humanoid that reasons about subtle disorder, not just explicit commands

This is more novel than a standard pick-and-place demo.

## 7. Official SDK Reality Check

This section is here to keep the team honest.

### Unitree SDK / ROS2

From the official Unitree SDK2 Python and ROS2 repos:

- `unitree_sdk2_python` requires Python 3.8+, CycloneDDS 0.10.2, NumPy, and OpenCV.
- The SDK includes G1-specific examples for low-level control, arm control, locomotion, and audio.
- `unitree_ros2` includes G1 low-level examples and state access through ROS2 topics.

Important implication:

- Real G1 integration is possible, but it is not the place to burn hackathon time unless the hardware slot is guaranteed and safety review is complete.
- The primary delivery path must be Isaac Lab simulation, with real G1 as optional supervised follow-up.

### Isaac Lab

From the official Isaac Lab repo:

- `Isaac-PickPlace-Locomanipulation-G1-Abs-v0` is a registered environment.
- The environment uses a Unitree G1 29-DOF robot.
- The scene already includes a packing table and an object.
- The lower body uses a pretrained locomotion policy.
- The upper body uses IK-driven control.
- The task is already connected to a `robomimic` BC config.

Important implication:

- We should not build a new humanoid stack from zero.
- We should modify this environment into an order-correction task.
- We should exploit the existing imitation-learning path first.

### Nebius Token Factory

From the official quickstart, docs, and cookbook:

- Token Factory exposes an OpenAI-compatible API.
- It supports open models and agent integrations.
- Nebius also provides fine-tuning and post-training workflows.

Important implication:

- We can plug the LLM layer in quickly.
- We can keep the agent code simple.
- If time allows, we can distill or fine-tune a smaller order-classification model later, but this is not required for the demo.

## 8. Product Scope

### In Scope for the Hackathon

- G1 in Isaac Lab
- single-scene or small multi-object order-restoration demo
- structured scene -> LLM reasoning -> corrective plan -> robot action
- imitation-learning baseline for correction behavior
- optional RL refinement for final placement precision
- demo video and live run

### Out of Scope

- full-home autonomy
- raw camera frame sent to LLM every frame
- training full humanoid locomotion from scratch
- unsupervised real-robot deployment
- broad multi-room semantic mapping
- production-grade table etiquette across many object classes

### Scope Levels

#### Must Have

- One custom G1 environment where an object starts misaligned.
- One end-to-end loop where the robot fixes it.
- One LLM rationale showing why the scene is wrong.

#### Should Have

- Multiple sampled disorder states.
- Generated demonstrations + BC policy.
- Multiple corrections in a single scene.

#### Could Have

- Fork/plate semantic placement.
- Chair symmetry detection.
- RL refinement for final pose precision.
- Real G1 replay or supervised bridge.

## 9. Core User Experience

The user experience for judges should look like this:

1. The scene appears visibly wrong.
2. The system explains what is wrong in one sentence.
3. The robot walks to the object and corrects it.
4. An overlay shows a quantitative improvement:
   - yaw error reduced
   - position error reduced
   - order score increased

Example narration:

`rOCDbot sees that the object is rotated 28 degrees off the table axis. It decides the scene violates the alignment rule, then executes a corrective pick-rotate-place action to restore order.`

## 10. MVP Demo Definition

### Base Demo

Starting point:

- `Isaac-PickPlace-Locomanipulation-G1-Abs-v0`

Modified task:

- object begins with wrong yaw and optionally small position offset
- target state is aligned with table axes and target placement zone

Robot behavior:

- detect disorder
- generate plan
- locomote to object
- grasp
- rotate/reposition
- place
- retract or stabilize

### Why this demo is right

It is:

- visually obvious
- grounded in the official G1 environment
- technically feasible
- strong enough to sell the bigger vision

### Stretch Demo

If time allows:

- two or three tabletop objects
- one object is the outlier
- rOCDbot identifies the outlier and corrects the scene

Best stretch:

- one simple semantic table-setting rule, such as cup above plate or fork left of plate

## 11. Product Requirements

### Functional Requirements

#### FR-1: Disorder Detection

The system must identify whether the scene violates a predefined or learned order rule.

Examples:

- object yaw off axis
- object position off target grid
- object on wrong side of another object

#### FR-2: Structured Scene Representation

The system must convert simulation state into a scene representation that the LLM can reason over.

Minimum fields:

- object ids
- object poses
- table reference frame
- target layout
- robot base pose
- graspable object metadata

#### FR-3: Order Critic

The LLM must:

- identify what is wrong
- explain why it is wrong
- propose a corrective action sequence
- optionally assign a severity score

#### FR-4: Corrective Planner

The planner must turn the LLM output into executable skills.

Minimum action sequence:

- navigate to target
- pre-grasp
- grasp
- rotate/reposition
- place

#### FR-5: Policy Execution

The G1 policy/controller must execute the correction in Isaac.

#### FR-6: Before/After Metrics

The system must compute and display:

- yaw error
- position error
- success/failure
- latency

#### FR-7: Training Loop

The system must support collecting demonstrations and training a correction policy.

#### FR-8: Safety / Human Override

For any real-robot extension:

- operator approval required
- supervised execution only
- no autonomous unsupervised motion around people

### Non-Functional Requirements

- Planning latency target: under 2 seconds
- Demo episode target: under 45 seconds
- Reset target: under 30 seconds
- Demo success target: at least 70 percent on prepared scenes
- Explanation quality target: one short, human-readable sentence

## 12. Architecture

## High-Level Architecture

```text
Isaac Scene / Simulator State
    ->
Scene Normalizer
    ->
Order Critic (Nebius LLM)
    ->
Corrective Planner
    ->
G1 Skill Executor
    ->
Before/After Evaluator
    ->
Dataset + Training Loop
```

### Component 1: Scene Normalizer

Purpose:

- convert simulator state into compact JSON

Example:

```json
{
  "table_axis_deg": 0,
  "objects": [
    {
      "id": "object_1",
      "class": "wheel",
      "yaw_deg": 28,
      "target_yaw_deg": 0,
      "pos_error_cm": 4.2
    }
  ],
  "robot": {
    "distance_to_object_m": 1.3
  }
}
```

### Component 2: Order Critic

Purpose:

- judge whether the scene looks wrong
- explain the violation
- produce a correction plan

Expected output schema:

```json
{
  "is_disordered": true,
  "severity": 0.88,
  "violations": [
    {
      "object_id": "object_1",
      "type": "rotation_misalignment",
      "explanation": "The wheel is rotated away from the table axis."
    }
  ],
  "plan": [
    "navigate_to_object",
    "grasp_object",
    "rotate_to_target_yaw",
    "place_on_target"
  ]
}
```

### Component 3: Corrective Planner

Purpose:

- map semantic plan to robot skills
- validate whether the plan is safe and supported

### Component 4: G1 Skill Executor

Purpose:

- use Isaac G1 locomanipulation environment for execution

### Component 5: Improvement Loop

Purpose:

- collect successful and failed rollouts
- generate additional data
- improve policy quality

## 13. Technical Design Decisions

### Decision 1: Simulation-first, real robot optional

Reason:

- hardware access is limited
- safety review may limit what is allowed
- judges reward working demos more than aspirational hardware claims

### Decision 2: Structured state to LLM, not raw video to LLM

Reason:

- faster
- cheaper
- more reliable
- easier to debug

If we use camera input later, it should produce a scene graph first.

### Decision 3: BC first, RL second

Reason:

- the official G1 environment already supports a BC path
- BC gets a decent policy quickly
- RL refinement is valuable, but not a day-one blocker

### Decision 4: LLM is semantic critic, not low-level controller

Reason:

- LLMs are good at judging order and generating task context
- they are not good at direct motor control

### Decision 5: Use simulator truth for MVP perception

Reason:

- removes brittle perception failure from the critical path
- still demonstrates the full reasoning and action loop

If time allows, we can add a vision-based pose estimator as a stretch.

## 14. Training Plan

## Phase A: Demonstration Collection

Use Isaac Lab Mimic and record a small set of successful demonstrations for the alignment task.

Preferred path:

- 5 to 10 clean demos
- short, smooth trajectories
- minimal pauses

### Output

- `dataset_align_seed.hdf5`

## Phase B: Data Generation

Use Isaac Lab Mimic to generate many more demonstrations from the seed set.

Goal:

- turn a small number of manual corrections into a much larger dataset

### Output

- `dataset_align_generated.hdf5`

## Phase C: Behavior Cloning Baseline

Train a `robomimic` BC policy on the generated dataset.

Why:

- fastest path to working correction behavior on the official G1 stack

### Output

- BC checkpoint
- rollout videos
- success metrics

## Phase D: RL Refinement

If time allows, fine-tune the final correction stage with RL.

Recommended scope:

- do not train locomotion
- keep lower-body locomotion frozen
- refine upper-body correction and final placement precision

### Suggested RL state

- object yaw error
- object position error
- eef pose
- hand joint state
- object-relative features

### Suggested RL action

- delta end-effector pose
- gripper action
- optional short placement refinement command

### Suggested reward

```text
reward =
  alignment_improvement
+ placement_improvement
+ success_bonus
- drop_penalty
- collision_penalty
- time_penalty
```

### Suggested algorithm

- PPO if reusing existing Isaac-friendly continuous control tooling
- only if environment adaptation is small

If RL is too heavy, stop after BC and keep RL as a clearly stated next step.

## 15. LLM Data Strategy

This is one of the most original parts of the project.

### Role of the LLM

The LLM should generate:

- scene-level order judgments
- violation explanations
- synthetic correction labels
- severity scores

### Example synthetic sample

Input:

```json
{
  "object": "fork",
  "plate_relation": "right_of",
  "target_rule": "fork should be left_of plate"
}
```

Output:

```json
{
  "is_disordered": true,
  "violation_type": "semantic_placement_error",
  "recommended_fix": "move fork to left side of plate"
}
```

### Why this matters

This lets the team claim a bigger story:

- the LLM is not only planning actions
- it is helping produce structured supervision for robot behavior

That is a strong answer to the robotics track.

## 16. Roadmap for the Hackathon

## Track A: Must-win demo path

### Milestone A1: Run official environment

Success criteria:

- G1 environment launches
- baseline pick-place behavior reproducible

### Milestone A2: Create custom alignment environment

Changes:

- randomize object yaw
- define target placement pose
- expose error metrics

Success criteria:

- reset produces clearly misaligned scenes
- success metric reflects order restoration

### Milestone A3: Add Order Critic

Success criteria:

- structured prompt in place
- LLM returns valid JSON
- plan is deterministic on prepared scenes

### Milestone A4: End-to-end demo

Success criteria:

- single-command demo run
- before/after metrics shown
- video capture ready

## Track B: Learning story

### Milestone B1: Record demos

Success criteria:

- 5 to 10 successful demonstrations

### Milestone B2: Generate larger dataset

Success criteria:

- synthetic or Mimic-generated dataset available

### Milestone B3: Train BC baseline

Success criteria:

- at least one checkpoint with acceptable success

### Milestone B4: Optional RL refinement

Success criteria:

- measurable improvement in final yaw/placement precision

## Track C: Stretch value

### Milestone C1: Semantic rulebook

Examples:

- fork left of plate
- cup above plate
- objects in row share orientation

### Milestone C2: Multi-object disorder ranking

Success criteria:

- robot chooses the worst offender first

## 17. Team Workstreams

### Workstream 1: Simulation and Controls

Owner:

- robotics / Isaac engineer

Responsibilities:

- environment fork
- reset logic
- success metrics
- execution pipeline

### Workstream 2: Agent and Data

Owner:

- LLM / backend engineer

Responsibilities:

- scene schema
- Nebius integration
- order critic prompts
- logging and evaluation
- synthetic dataset generation

### Workstream 3: Training and Demo Ops

Owner:

- ML engineer

Responsibilities:

- demo recording
- Mimic generation
- BC training
- checkpoint selection
- demo script and video capture

## 18. Proposed Repo Structure

```text
/sim
  /isaaclab_ext
    rocdbot_align_env.py
    rocdbot_align_mimic_env.py

/agent
  order_critic.py
  planner.py
  schemas.py
  prompts/

/training
  collect_demos.md
  train_bc.sh
  train_refine_rl.sh
  evaluate_policy.sh

/scripts
  run_demo.py
  run_order_critic_eval.py
  export_demo_video.sh

/datasets
  .gitkeep

/docs
  architecture.md

/prd.md
```

## 19. Metrics

### Demo Metrics

- disorder detection accuracy on prepared scenes
- plan validity rate
- end-to-end correction success rate
- average correction latency
- yaw error reduction
- position error reduction

### Target Demo Thresholds

- detection accuracy: at least 90 percent on demo scenes
- plan validity: at least 95 percent on demo scenes
- correction success: at least 70 percent
- yaw error after correction: less than 5 degrees
- position error after correction: less than 3 cm

## 20. Risks and Mitigations

### Risk: Full G1 learning is too heavy

Mitigation:

- freeze locomotion
- use BC first
- use RL only for placement refinement

### Risk: LLM output is inconsistent

Mitigation:

- use strict JSON schema
- use prepared scene types
- add deterministic post-validation

### Risk: Demo becomes a generic pick-and-place

Mitigation:

- always show the semantic judgment
- display why the object is wrong
- display before/after order score

### Risk: Real robot access is limited or denied

Mitigation:

- do not depend on hardware for the main judging demo
- keep hardware bridge optional

### Risk: Perception complexity explodes

Mitigation:

- use simulator truth first
- add camera perception only if the core loop is already stable

### Risk: The project name reads as a joke

Mitigation:

- keep the internal codename `rOCDbot`
- in judge-facing copy emphasize `order restoration`, `environmental consistency`, and `physical quality control`

## 21. Definition of Done

The project is done for hackathon purposes when all of the following are true:

- a custom G1 alignment scene exists in Isaac Lab
- the system detects a disorder state and explains it
- the system executes a correction end-to-end
- a stable live demo can be run in one command
- the repo contains instructions for setup and running the demo
- a one-minute demo video is recorded

## 22. Developer Instructions

### Setup Priorities

1. Get Isaac Lab running locally or on a GPU machine.
2. Verify the official G1 locomanipulation environment launches.
3. Add Nebius API access with a minimal prompt test.
4. Fork the environment into a custom alignment task.
5. Only after that, start data collection and training.

### Do Not Do First

- do not start with real-robot networking
- do not start with camera perception
- do not start with RL from scratch
- do not build a multi-room demo before the single-object demo works

### Recommended Order of Work

1. Launch official env.
2. Modify reset and success logic.
3. Add scene-to-JSON exporter.
4. Add LLM order critic.
5. Add demo script.
6. Collect demonstrations.
7. Train BC policy.
8. Add RL refinement only if the above is stable.

## 23. Submission Narrative

Use this as the baseline one-sentence pitch:

`rOCDbot is an agentic humanoid robot that detects subtle environmental disorder, explains what is wrong, and restores order using LLM reasoning plus learned robot correction policies.`

Use this as the stronger technical version:

`We built a G1-based order-restoration system where a Nebius-powered LLM acts as a semantic order critic, Isaac Lab provides the embodied environment, and imitation learning plus RL refine the robot's physical correction behavior.`

## 24. References

Official references used to ground this PRD:

- Unitree G1 developer portal: https://support.unitree.com/home/en/G1_developer
- Unitree SDK2 Python: https://github.com/unitreerobotics/unitree_sdk2_python
- Unitree ROS2: https://github.com/unitreerobotics/unitree_ros2
- Isaac Lab environments overview: https://github.com/isaac-sim/IsaacLab/blob/main/docs/source/overview/environments.rst
- Isaac Lab G1 locomanipulation environment registration: https://github.com/isaac-sim/IsaacLab/blob/main/source/isaaclab_tasks/isaaclab_tasks/manager_based/locomanipulation/pick_place/__init__.py
- Isaac Lab teleoperation and imitation learning: https://github.com/isaac-sim/IsaacLab/blob/main/docs/source/overview/imitation-learning/teleop_imitation.rst
- Nebius Token Factory quickstart: https://docs.tokenfactory.nebius.com/quickstart
- Nebius Token Factory fine-tuning docs: https://docs.tokenfactory.nebius.com/guides/fine-tuning/overview
- Nebius Token Factory cookbook: https://github.com/nebius/token-factory-cookbook

