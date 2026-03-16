# rOCDbot Demo Operator Notes

- Launch command: `python3 scripts/run_demo.py --mode release --seed 7`
- Backup command: `python3 scripts/run_demo.py --mode cache-only --seed 7`
- Canonical story beat: detect a rotated tabletop object, explain the disorder, correct it, then show the yaw-error delta.
- Use `judge_script.md` and `judge_story.gif` from the release bundle for the 60-second judge walkthrough.
- Live sequence timing: 5s wrong scene, 10s critique overlay, 25s correction, 10s before/after freeze frame, 10s buffer.
- If Nebius is slow or unavailable, use the packaged cache-only release artifacts and continue the explanation from the manifest.