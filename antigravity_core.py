#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# 우선순위 폴백 모델 체인: Antigravity 전용 모델 -> 3.7 Flash -> 3.5 Flash -> 4 Argon -> 3.8 Flash
DEFAULT_FALLBACK_CHAIN = [
    "antigravity-preview-latest",
    "antigravity-preview-09-2026",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-4-argon",
    "gemini-3.8-flash"
]

if not API_KEY:
    print("[-] Error: GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    sys.exit(1)

# --- 1. Native Tools ---
def tool_read_file(path: str) -> str:
    if not os.path.exists(path):
        return f"Error: File '{path}' not found."
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"

def tool_write_file(path: str, content: str) -> str:
    try:
        if os.path.dirname(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Success: Wrote {len(content)} bytes to '{path}'."
    except Exception as e:
        return f"Error: {e}"

def tool_run_shell(command: str) -> str:
    try:
        res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        return f"ExitCode: {res.returncode}\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    except Exception as e:
        return f"Error: {e}"

TOOLS_MAP = {
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "run_shell": tool_run_shell
}

TOOL_DECLARATIONS = [
    {
        "name": "read_file",
        "description": "Reads the content of a file at the given relative path.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"path": {"type": "STRING"}},
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Writes content to a file at the given relative path.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING"},
                "content": {"type": "STRING"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "run_shell",
        "description": "Executes a shell command and returns exit code and output.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"command": {"type": "STRING"}},
            "required": ["command"]
        }
    }
]

SYSTEM_INSTRUCTION = """You are the Antigravity CLI Autonomous Agent.
Strictly follow this execution loop:
1. Call `read_file` on `docs/PROGRESS.md` to find the first uncompleted task (`- [ ]`).
2. If all tasks are `- [x]`, stop calling tools and output a final completion summary.
3. Read relevant specs (`docs/SRS.md`, `docs/SDS.md`) or target files as needed.
4. Execute the task using `write_file` or `run_shell`.
5. Verify your work. Then update `docs/PROGRESS.md` by changing that task from `- [ ]` to `- [x]`.
6. If `./sync_push.sh` exists, execute it via `run_shell` after marking a task complete.
"""

# --- 2. Multi-Model Fallback API Caller ---
def call_gemini_with_fallback(contents):
    env_model = os.environ.get("GEMINI_MODEL", "").strip()
    model_chain = [env_model] + [m for m in DEFAULT_FALLBACK_CHAIN if m != env_model] if env_model else DEFAULT_FALLBACK_CHAIN

    payload = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "tools": [{"functionDeclarations": TOOL_DECLARATIONS}],
        "generationConfig": {"temperature": 0.1}
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    for model_name in model_chain:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
        try:
            print(f"  [*] Calling model: {model_name} (timeout=25s)...")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=25) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            print(f"  [!] {model_name} HTTP {e.code} 응답 지연/오류 -> 즉시 다음 예비 모델로 전환합니다.")
        except Exception as e:
            print(f"  [!] {model_name} 응답 타임아웃/예외 ({e}) -> 즉시 다음 예비 모델로 전환합니다.")

    print("[-] 모든 폴백 모델 호출에 실패했습니다. 10초 후 재시도합니다.")
    time.sleep(10)
    return call_gemini_with_fallback(contents)

# --- 3. ReAct Loop Runner ---
def main():
    max_steps = int(os.environ.get("ANTIGRAVITY_MAX_STEPS", "15"))
    task_prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "Check docs/PROGRESS.md and execute pending tasks autonomously using your tools."
    )

    print("=" * 68)
    print(f"[Antigravity CLI] Multi-Model Engine | Workspace: {os.getcwd()}")
    print("=" * 68)

    contents = [{"role": "user", "parts": [{"text": task_prompt}]}]

    for step in range(1, max_steps + 1):
        print(f"\n[Step {step}/{max_steps}] Thinking...")
        res = call_gemini_with_fallback(contents)

        candidates = res.get("candidates", [])
        if not candidates:
            print("[-] 응답 후보가 없습니다. 종료합니다.")
            break

        parts = candidates[0].get("content", {}).get("parts", [])
        contents.append({"role": "model", "parts": parts})

        tool_responses = []
        for part in parts:
            if "text" in part and part["text"].strip():
                print(f"  [Thought] {part['text'].strip()}")

            if "functionCall" in part:
                fn = part["functionCall"]
                name = fn["name"]
                args = fn.get("args", {})
                print(f"  [Action]  -> {name}({json.dumps(args, ensure_ascii=False)})")

                func = TOOLS_MAP.get(name)
                result = func(**args) if func else f"Error: Unknown tool '{name}'"
                preview = (result[:120].replace("\n", " ") + "...") if len(result) > 120 else result.replace("\n", " ")
                print(f"  [Observe] <- {preview}")

                tool_responses.append({
                    "functionResponse": {
                        "name": name,
                        "response": {"result": result}
                    }
                })

        if tool_responses:
            contents.append({"role": "user", "parts": tool_responses})
        else:
            print("\n[+] Antigravity CLI 루프가 모든 작업을 마치고 정상 종료되었습니다.")
            break

if __name__ == "__main__":
    main()
