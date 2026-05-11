#!/usr/bin/env python3
import argparse
import json
import os
import random
import sys
import time
from urllib import parse, request

BASE_URL = os.environ.get("COMFYUI_URL", "http://localhost:8188")
DEFAULT_WORKFLOW = os.path.join(os.path.dirname(__file__), "..", "references", "face_portrait_workflow.json")


def check_comfyui():
    req = request.Request(f"{BASE_URL}/system_stats", method="GET")
    with request.urlopen(req, timeout=5) as resp:
        return resp.read()


def load_workflow(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def submit(workflow):
    payload = json.dumps({"prompt": workflow}).encode("utf-8")
    req = request.Request(
        f"{BASE_URL}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_history():
    req = request.Request(f"{BASE_URL}/history", method="GET")
    with request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def wait_for_prompt(prompt_id, timeout=600, poll=2):
    start = time.time()
    while time.time() - start < timeout:
        try:
            history = get_history()
            if prompt_id in history:
                return history[prompt_id]
        except Exception:
            pass
        time.sleep(poll)
    raise TimeoutError(f"Timed out waiting for {prompt_id}")


def download_view(image_info, save_as):
    params = parse.urlencode(
        {
            "filename": image_info.get("filename"),
            "subfolder": image_info.get("subfolder", ""),
            "type": image_info.get("type", "output"),
        }
    )
    url = f"{BASE_URL}/view?{params}"
    req = request.Request(url, method="GET")
    with request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    with open(save_as, "wb") as f:
        f.write(data)
    return save_as


def find_images(history_entry):
    outputs = history_entry.get("outputs", {})
    images = []
    for node_out in outputs.values():
        for img in node_out.get("images", []):
            images.append(img)
    return images


def main():
    parser = argparse.ArgumentParser(description="Generate a face portrait through ComfyUI only")
    parser.add_argument("--workflow", default=DEFAULT_WORKFLOW, help="Path to workflow JSON")
    parser.add_argument("--prompt", help="Override prompt text")
    parser.add_argument("--seed", type=int, help="Override seed")
    parser.add_argument("--timeout", type=int, default=600, help="Wait timeout in seconds")
    parser.add_argument("--save-as", help="Download the first generated image to this path")
    args = parser.parse_args()

    try:
        check_comfyui()
    except Exception as e:
        print(f"ERROR: ComfyUI is not reachable at {BASE_URL}: {e}", file=sys.stderr)
        return 1

    try:
        workflow = load_workflow(args.workflow)
    except Exception as e:
        print(f"ERROR: cannot load workflow: {e}", file=sys.stderr)
        return 1

    if args.prompt:
        workflow["6"]["inputs"]["text"] = args.prompt

    seed = args.seed if args.seed is not None else random.randint(1, 2_147_483_647)
    workflow["9"]["inputs"]["seed"] = seed
    print(f"SEED {seed}")

    try:
        resp = submit(workflow)
    except Exception as e:
        print(f"ERROR: submit failed: {e}", file=sys.stderr)
        return 1

    prompt_id = resp.get("prompt_id")
    if not prompt_id:
        print(f"ERROR: no prompt_id returned: {resp}", file=sys.stderr)
        return 1

    print(f"SUBMITTED {prompt_id}")
    try:
        history = wait_for_prompt(prompt_id, timeout=args.timeout)
    except Exception as e:
        print(f"ERROR: wait failed: {e}", file=sys.stderr)
        return 1

    images = find_images(history)
    if not images:
        print("DONE no images found")
        return 0

    print("DONE")
    for img in images:
        print(f"IMAGE {img.get('filename')} {img.get('subfolder', '')} {img.get('type', 'output')}")

    if args.save_as:
        saved = download_view(images[0], args.save_as)
        print(f"SAVED {saved}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
