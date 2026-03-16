"""Judge-facing prompt, response, log, and trace generation."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageOps

from src.demo.metrics import compute_metrics


STEP_COMPLETE_YAW_THRESHOLD = 5.0
STEP_COMPLETE_POS_THRESHOLD_CM = 0.2


def build_judge_conversation(
    demo_run: dict[str, Any],
    *,
    before_image: str,
    after_image: str,
    step_images: list[str] | None = None,
) -> list[dict[str, Any]]:
    scene = demo_run["scene_state"]
    critic = demo_run["critic"]

    step_payloads = _load_step_payloads(demo_run)
    step_image_paths = [str(item["image_path"]) for item in step_payloads]
    if step_images:
        for path in step_images:
            path_str = str(path)
            if path_str not in step_image_paths:
                step_image_paths.append(path_str)
    if not step_payloads:
        if not step_image_paths:
            step_image_paths = [str(before_image)]
        if after_image and str(after_image) not in step_image_paths:
            step_image_paths.append(str(after_image))

    scene_steps = _extract_step_states(demo_run)
    if len(scene_steps) < len(step_image_paths):
        scene_steps = _pad_scene_states(scene_steps, scene, len(step_image_paths))
    elif len(scene_steps) > len(step_image_paths):
        scene_steps = scene_steps[: len(step_image_paths)]

    critique_prompt = (
        "I am a person with OCD. What looks out of place in this scene? "
        "Use the image and the structured scene summary. Focus on what would look visually wrong to someone who wants the table to feel ordered."
    )
    critique_response = (
        f"The object `{scene['object_id']}` is the main disorder. It is rotated {scene['yaw_before_deg']:.1f} deg "
        "from the table axis and shifted from the aligned corner."
    )

    turns: list[dict[str, Any]] = [
        {
            "stage": "scene_critique",
            "step": 0,
            "image_path": str(before_image),
            "user_prompt": critique_prompt,
            "assistant_response": critique_response,
        }
    ]

    for step_index, step_state in enumerate(scene_steps, start=1):
        prior_image = str(before_image) if step_index == 1 else str(step_image_paths[step_index - 2])
        post_image = str(step_image_paths[step_index - 1])

        turns.append(
            {
                "stage": f"robot_instruction_step_{step_index}",
                "step": step_index,
                "image_path": prior_image,
                "user_prompt": (
                    f"Step {step_index}: What are the robot instructions to improve OCD-style order for this scene? "
                    "Return short concrete actions."
                ),
                "assistant_response": (
                    f"Step {step_index} action set: {' -> '.join(critic['plan'])}. "
                    f"Goal: rotate `{critic['target_object']}` back to {scene['target_yaw_deg']:.1f} deg and "
                    "place it at the target corner."
                ),
            }
        )

        step_metrics = _compute_step_metrics(scene, step_state)
        complete = _is_step_complete(step_metrics)
        turns.append(
            {
                "stage": f"post_action_evaluation_step_{step_index}",
                "step": step_index,
                "image_path": post_image,
                "user_prompt": (
                    f"Evaluate step {step_index}. If incomplete, propose one follow-up correction action."
                ),
                "assistant_response": (
                    f"Result: yaw is now {step_metrics['yaw_after_deg']:.1f} deg and position error is "
                    f"{step_metrics['position_error_after_cm']:.1f} cm. "
                    f"{'Task complete.' if complete else 'Task incomplete.'} "
                    f"{'No further action required.' if complete else 'Refine placement and settle again.'}"
                ),
                "decision_source": critic["source"],
                "fallback_used": demo_run["fallback_used"],
                "step_complete": complete,
                "step_metrics": {
                    "yaw_after_deg": step_metrics["yaw_after_deg"],
                    "position_error_after_cm": step_metrics["position_error_after_cm"],
                },
            }
        )

    return turns


def write_judge_story_package(
    root: str | Path,
    *,
    demo_run: dict[str, Any],
    before_image: str | Path,
    after_image: str | Path,
    step_images: list[str] | None = None,
) -> dict[str, str]:
    package_root = Path(root)
    package_root.mkdir(parents=True, exist_ok=True)

    before_path = Path(before_image)
    after_path = Path(after_image)
    step_list = [str(item["image_path"]) for item in _load_step_payloads(demo_run)]
    if step_images:
        for path in step_images:
            path_str = str(path)
            if path_str not in step_list:
                step_list.append(path_str)

    conversation = build_judge_conversation(
        demo_run,
        before_image=str(before_path),
        after_image=str(after_path),
        step_images=step_list,
    )
    conversation_path = package_root / "judge_conversation.json"
    script_path = package_root / "judge_script.md"
    log_path = package_root / "judge_agent_log.jsonl"
    storyboard_path = package_root / "judge_story.gif"

    conversation_path.write_text(json.dumps(conversation, indent=2), encoding="utf-8")
    script_path.write_text(_build_judge_script(conversation, demo_run), encoding="utf-8")
    log_path.write_text(_build_agent_log(conversation, demo_run), encoding="utf-8")
    _write_storyboard_gif(storyboard_path, conversation, demo_run)

    return {
        "judge_conversation": str(conversation_path),
        "judge_script": str(script_path),
        "judge_log": str(log_path),
        "judge_story_gif": str(storyboard_path),
    }


def _build_judge_script(conversation: list[dict[str, Any]], demo_run: dict[str, Any]) -> str:
    lines = [
        "# Judge Demo Script",
        "",
        f"- Run ID: `{demo_run['run_id']}`",
        f"- Decision source: `{demo_run['critic']['source']}`",
        f"- Fallback used: `{demo_run['fallback_used']}`",
        "",
    ]
    for turn in conversation:
        lines.extend(
            [
                f"## {turn['stage'].replace('_', ' ').title()}",
                "",
                f"- Image: `{turn['image_path']}`",
                f"- Prompt: {turn['user_prompt']}",
                f"- Response: {turn['assistant_response']}",
                "",
            ]
        )
    return "\n".join(lines)


def _build_agent_log(conversation: list[dict[str, Any]], demo_run: dict[str, Any]) -> str:
    scene = demo_run["scene_state"]
    critic = demo_run["critic"]
    entries: list[dict[str, Any]] = [
        {
            "step": 1,
            "event": "scene_captured",
            "image_path": conversation[0]["image_path"],
            "scene_object": scene["object_id"],
            "yaw_before_deg": scene["yaw_before_deg"],
        },
        {
            "step": 2,
            "event": "order_critique_generated",
            "decision_source": critic["source"],
            "fallback_used": demo_run["fallback_used"],
            "reason": critic["reason"],
        },
        {
            "step": 3,
            "event": "robot_plan_selected",
            "plan": critic["plan"],
            "execution_latency_ms": demo_run["execution"]["execution_latency_ms"],
        },
    ]

    for turn in conversation:
        if turn["stage"].startswith("robot_instruction_step_"):
            entries.append(
                {
                    "event": "robot_instruction_generated",
                    "step": turn["step"] + 3,
                    "image_path": turn["image_path"],
                    "stage": turn["stage"],
                    "instructions": turn["assistant_response"],
                }
            )
        if turn["stage"].startswith("post_action_evaluation_step_"):
            entries.append(
                {
                    "event": "post_action_evaluated",
                    "step": turn["step"] + 3,
                    "image_path": turn["image_path"],
                    "yaw_after_deg": turn["step_metrics"]["yaw_after_deg"],
                    "position_error_after_cm": turn["step_metrics"]["position_error_after_cm"],
                    "step_complete": turn["step_complete"],
                }
            )
    return "\n".join(json.dumps(entry) for entry in entries) + "\n"


def _write_storyboard_gif(output_path: Path, conversation: list[dict[str, Any]], demo_run: dict[str, Any]) -> None:
    frames = []
    for index, turn in enumerate(conversation, start=1):
        image_path = Path(turn["image_path"])
        if not image_path.exists():
            continue
        frames.append(
            _render_card(
                title=f"Turn {index}: {turn['stage'].replace('_', ' ').title()}",
                prompt=turn["user_prompt"],
                response=turn["assistant_response"],
                image_path=image_path,
                footer=f"Run: {demo_run['run_id']} | Source: {demo_run['critic']['source']} | Fallback: {demo_run['fallback_used']}",
            )
        )
    if not frames:
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=[1800] * len(frames),
        loop=0,
    )


def _render_card(*, title: str, prompt: str, response: str, image_path: Path, footer: str) -> Image.Image:
    canvas = Image.new("RGB", (1280, 720), "#f3eee4")
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle((40, 40, 1240, 680), radius=24, fill="#fffaf1", outline="#c9b48f", width=3)
    draw.text((80, 70), title, fill="#1f1f1f")

    image = Image.open(image_path).convert("RGB")
    image = ImageOps.contain(image, (480, 480))
    canvas.paste(image, (80, 150))

    prompt_block = "Prompt\n" + textwrap.fill(prompt, width=42)
    response_block = "Response\n" + textwrap.fill(response, width=42)
    draw.multiline_text((620, 150), prompt_block, fill="#2e2a23", spacing=8)
    draw.multiline_text((620, 370), response_block, fill="#2e2a23", spacing=8)
    draw.text((80, 640), footer, fill="#6b5c45")
    return canvas


def _load_step_payloads(demo_run: dict[str, Any]) -> list[dict[str, Any]]:
    steps = [
        step
        for step in demo_run.get("correction_steps", [])
        if isinstance(step, dict) and "scene_state" in step and "image_path" in step
    ]
    return sorted(steps, key=lambda item: int(item.get("step", 0)))


def _extract_step_states(demo_run: dict[str, Any]) -> list[dict[str, Any]]:
    return [step["scene_state"] for step in _load_step_payloads(demo_run) if isinstance(step.get("scene_state"), dict)]


def _pad_scene_states(step_states: list[dict[str, Any]], source: dict[str, Any], target_len: int) -> list[dict[str, Any]]:
    if not step_states:
        return [source] * target_len
    while len(step_states) < target_len:
        step_states.append(step_states[-1])
    return step_states


def _compute_step_metrics(initial_scene: dict[str, Any], step_scene: dict[str, Any]) -> dict[str, Any]:
    return compute_metrics(
        initial_scene,
        step_scene,
        critic_latency_ms=0,
        execution_latency_ms=0,
    )


def _is_step_complete(step_metrics: dict[str, float]) -> bool:
    return (
        step_metrics["yaw_after_deg"] <= STEP_COMPLETE_YAW_THRESHOLD
        and step_metrics["position_error_after_cm"] <= STEP_COMPLETE_POS_THRESHOLD_CM
    )
