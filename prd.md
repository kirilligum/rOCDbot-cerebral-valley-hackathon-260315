PROJECT REQUIREMENTS DOCUMENT (PRD)

Project Name: rOCDbot
Expanded Name: Robotic Order Correction Demo Bot
Hackathon: Nebius.Build SF
Team: TBD
Version: 2.0

---

1. PROJECT OVERVIEW

---

rOCDbot is a humanoid robotics system that detects environmental disorder
(such as misaligned objects) and autonomously corrects it using reasoning,
planning, and physical manipulation.

The system demonstrates an agentic robotics pipeline combining:

- Vision perception
- LLM reasoning
- Robot control
- Reinforcement learning optimization

Example behavior:

Initial state:
cube rotated 30° on table

Robot process:
detect misalignment
plan correction
grasp object
rotate object
place object aligned

Final state:
cube aligned with table axis

The project demonstrates a robot that maintains order in its environment.

---

2. PROBLEM STATEMENT

---

Robots today are good at executing predefined tasks but poor at detecting
and correcting small environmental irregularities.

Humans instantly notice when:

- chairs are misaligned
- objects are slightly rotated
- items are placed incorrectly

Robots typically do not.

The goal of this project is to build a robot that can:

1. perceive the environment
2. detect disorder
3. reason about the correct state
4. physically fix the issue

---

3. SOLUTION SUMMARY

---

rOCDbot implements an agentic robotics pipeline that:

1. observes the environment
2. identifies misalignment
3. plans a correction
4. executes a manipulation task
5. improves the manipulation policy using reinforcement learning

The system operates in simulation using:

- NVIDIA Isaac Sim
- Isaac Lab environments
- Unitree G1 humanoid robot

Primary environment:

    Isaac-PickPlace-Locomanipulation-G1-Abs-v0

---

4. SYSTEM ARCHITECTURE

---

High-Level Pipeline

    Camera / Simulation
        ↓
    Object Detection / Pose Estimation
        ↓
    Scene Representation (structured state)
        ↓
    LLM Reasoning (Nebius Token Factory)
        ↓
    Action Planner
        ↓
    Robot Controller
        ↓
    Reinforcement Learning Optimization

---

5. CORE COMPONENTS

---

5.1 Perception System

Input:
simulator camera feed

Output:
structured scene state

Example scene state:

    object: cube
    position: (x,y,z)
    rotation: 25 degrees
    table_axis: 0 degrees

---

5.2 Scene Representation

Convert perception into structured format:

Example:

    cube_rotation = 25°
    target_rotation = 0°
    rotation_error = 25°

This representation is passed to the reasoning system.

---

5.3 Agentic Reasoning (Nebius Token Factory)

The reasoning layer determines whether the scene violates
environmental order rules.

Example prompt:

    Scene:
    cube rotation = 25°

    Rule:
    objects should align with table axis

    What action should be taken?

Expected response:

    Pick the cube, rotate it until aligned with the table axis,
    and place it back.

The LLM functions as the high-level decision agent.

---

5.4 Action Planning

The planner converts LLM decisions into robot commands.

Example plan:

    walk_to_object
    grasp_object
    rotate_object
    place_object

---

5.5 Robot Execution

Robot performs actions using:

    locomotion
    arm manipulation
    gripper control

Commands execute in Isaac Sim using the G1 robot model.

---

5.6 Reinforcement Learning Optimization

RL improves the precision and efficiency of manipulation tasks.

Training occurs in simulation.

State:

    object pose
    robot pose
    target pose

Actions:

    joint movements
    gripper control
    placement pose

Reward example:

    reward = - |rotation_error|

Success condition:

    object_rotation_error < threshold

RL improves:

    grasp accuracy
    object rotation precision
    task completion speed

---

6. DEMO SCENARIO

---

Environment:

    table
    cube
    robot

Initial state:

    cube rotated 30°

Robot process:

    scan scene
    detect disorder
    walk to cube
    grasp cube
    rotate cube
    place cube aligned

Final state:

    cube rotation ≈ 0°

---

7. MAPPING TO HACKATHON STATEMENTS

---

STATEMENT 1
Edge Inference & Agents

Requirement:
Build agentic pipelines that reason over context and take actions.

Implementation in rOCDbot:

    vision perception
    → scene interpretation
    → LLM reasoning
    → action planning
    → robot execution

The robot operates as an autonomous agent capable of
contextual reasoning and physical action.

---

STATEMENT 2
Robotics Optimization, Training & Tuning

Requirement:
Use RL and simulation to improve robot behavior.

Implementation in rOCDbot:

    Isaac Sim environment
    → RL policy training
    → improved manipulation behavior

The robot converts:

    visual input → action plan → physical action

RL optimizes the manipulation policy.

---

8. JUDGING CRITERIA ALIGNMENT

---

Impact Potential (20%)

Potential applications:

    warehouse organization
    hotel room reset robots
    restaurant table setup
    autonomous cleaning robots
    office environment maintenance

The concept enables robots that maintain order in human environments.

---

Live Demo (45%)

Demo structure:

    misaligned cube
    → robot detects disorder
    → robot fixes alignment

Before/after visual transformation.

Clear and easy for judges to understand.

---

Creativity & Originality (35%)

Unique aspect:

    robots enforcing environmental order

Instead of executing predefined tasks, the robot:

    evaluates the environment
    decides what is wrong
    fixes it autonomously

---

9. SUCCESS METRICS

---

alignment accuracy

    rotation error < 5°

task success rate

    >90%

demo runtime

    <10 seconds

---

10. DELIVERABLES

---

Hackathon deliverables:

- working simulation demo
- GitHub repository
- 1 minute demo video
- architecture diagram

---

11. FUTURE EXTENSIONS

---

multi-object organization

    robot aligns multiple objects

symmetry detection

    robot detects disorder automatically

user preference learning

    robot adapts to human organization preferences

real robot deployment

    transfer policy from simulation to real Unitree G1
