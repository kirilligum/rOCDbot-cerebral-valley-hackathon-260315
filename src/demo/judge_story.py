"""Judge-facing prompt, response, log, and storyboard generation."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageOps


def build_judge_conversation(demo_run: dict[str, Any], *, before_image: str, after_image: str) -> list[dict[str, Any]]:
    scene = demo_run["scene_state"]
    critic = demo_run["critic"]
    metrics = demo_run["metrics"]

    critique_prompt = (
        "I am a person with OCD. What looks out of place in this scene? "
        "Use the image and the structured scene summary. Focus on what would look visually wrong to someone who wants the table to feel ordered."
    )
    critique_response = (
        f"The object `{scene['object_id']}` is the main disorder. It is rotated {metrics['yaw_before_deg']:.1f} deg away from the table axis, "
        "so it does not look parallel to the surface and appears visually off."
    )

    action_prompt = (
        "What are the instructions for the robot to put the object back in place so that it satisfies a person with OCD? "
        "Return short, concrete robot instructions."
    )
    action_response = (
        f"Robot plan: {' -> '.join(critic['plan'])}. "
        f"Target: rotate `{critic['target_object']}` back to {scene['target_yaw_deg']:.1f} deg and place it centered on the target position."
    )

    completed = metrics["yaw_after_deg"] <= 5.0 and metrics["position_error_after_cm"] <= 2.0
    next_action = "No further action required." if completed else "Repeat grasp, rotate slightly toward the table axis, and settle again."
    evaluation_prompt = (
        "Evaluate how successful the action was. If the task is not completed, give a new action so that the object is in place."
    )
    evaluation_response = (
        f"Result: yaw error improved from {metrics['yaw_before_deg']:.1f} deg to {metrics['yaw_after_deg']:.1f} deg and "
        f"position error is {metrics['position_error_after_cm']:.1f} cm. "
        f"{'Task complete.' if completed else 'Task incomplete.'} {next_action}"
    )

    return [
        {
            "stage": "scene_critique",
            "image_path": before_image,
            "user_prompt": critique_prompt,
            "assistant_response": critique_response,
        },
        {
            "stage": "robot_instruction",
            "image_path": before_image,
            "user_prompt": action_prompt,
            "assistant_response": action_response,
        },
        {
            "stage": "post_action_evaluation",
            "image_path": after_image,
            "user_prompt": evaluation_prompt,
            "assistant_response": evaluation_response,
            "decision_source": critic["source"],
            "fallback_used": demo_run["fallback_used"],
        },
    ]


def write_judge_story_package(
    root: str | Path,
    *,
    demo_run: dict[str, Any],
    before_image: str | Path,
    after_image: str | Path,
) -> dict[str, str]:
    package_root = Path(root)
    package_root.mkdir(parents=True, exist_ok=True)

    before_path = Path(before_image)
    after_path = Path(after_image)
    conversation = build_judge_conversation(
        demo_run,
        before_image=str(before_path),
        after_image=str(after_path),
    )
    conversation_path = package_root / "judge_conversation.json"
    script_path = package_root / "judge_script.md"
    log_path = package_root / "judge_agent_log.jsonl"
    storyboard_path = package_root / "judge_story.gif"

    conversation_path.write_text(json.dumps(conversation, indent=2), encoding="utf-8")
    script_path.write_text(_build_judge_script(conversation, demo_run), encoding="utf-8")
    log_path.write_text(_build_agent_log(conversation, demo_run), encoding="utf-8")
    _write_storyboard_gif(storyboard_path, conversation, before_path, after_path, demo_run)

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
    entries = [
        {
            "step": 1,
            "event": "scene_captured",
            "image_path": conversation[0]["image_path"],
            "scene_object": demo_run["scene_state"]["object_id"],
            "yaw_before_deg": demo_run["metrics"]["yaw_before_deg"],
        },
        {
            "step": 2,
            "event": "order_critique_generated",
            "decision_source": demo_run["critic"]["source"],
            "fallback_used": demo_run["fallback_used"],
            "reason": demo_run["critic"]["reason"],
        },
        {
            "step": 3,
            "event": "robot_plan_selected",
            "plan": demo_run["critic"]["plan"],
            "execution_latency_ms": demo_run["execution"]["execution_latency_ms"],
        },
        {
            "step": 4,
            "event": "post_action_evaluated",
            "image_path": conversation[2]["image_path"],
            "yaw_after_deg": demo_run["metrics"]["yaw_after_deg"],
            "position_error_after_cm": demo_run["metrics"]["position_error_after_cm"],
            "run_status": demo_run["metrics"]["run_status"],
        },
    ]
    return "\n".join(json.dumps(entry) for entry in entries) + "\n"


def _write_storyboard_gif(
    output_path: Path,
    conversation: list[dict[str, Any]],
    before_path: Path,
    after_path: Path,
    demo_run: dict[str, Any],
) -> None:
    frames = [
        _render_card(
            title="Step 1: What Looks Out Of Place?",
            prompt=conversation[0]["user_prompt"],
            response=conversation[0]["assistant_response"],
            image_path=before_path,
            footer=f"Source: {demo_run['critic']['source']} | Fallback: {demo_run['fallback_used']}",
        ),
        _render_card(
            title="Step 2: What Should The Robot Do?",
            prompt=conversation[1]["user_prompt"],
            response=conversation[1]["assistant_response"],
            image_path=before_path,
            footer="Robot action prompt and primitive plan",
        ),
        _render_card(
            title="Step 3: Did The Action Succeed?",
            prompt=conversation[2]["user_prompt"],
            response=conversation[2]["assistant_response"],
            image_path=after_path,
            footer=f"Yaw after: {demo_run['metrics']['yaw_after_deg']:.1f} deg | Position error: {demo_run['metrics']['position_error_after_cm']:.1f} cm",
        ),
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=[1800, 1800, 2200],
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
