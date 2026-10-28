#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# 검증된 고성능/경량 모델만 배치 (불필요한 400/429 유발 모델 제거)
DEFAULT_FALLBACK_CHAIN = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.6-flash",
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

# --- 2. Rate-Limit Safe Fallback Caller ---
def call_gemini_with_fallback(contents):
    env_model = os.environ.get("GEMINI_MODEL", "").strip()
    model_chain = [env_model] + [m for m in DEFAULT_FALLBACK_CHAIN if m != env_model] if env_model else DEFAULT_FALLBACK_CHAIN

    payload = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "tools": [{"functionDeclarations": TOOL_DECLARATIONS}]
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    while True:
        for model_name in model_chain:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
            try:
                print(f"  [*] Calling model: {model_name} (timeout=90s)...")
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=90) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="ignore")
                if e.code == 429:
                    print(f"  [!] {model_name} HTTP 429 (분당 호출 한도). 15초 쿨다운 대기 후 다음 모델 시도...")
                    time.sleep(15)
                else:
                    print(f"  [!] {model_name} HTTP {e.code} 오류 -> 3초 후 다음 예비 모델로 전환합니다.")
                    time.sleep(3)
            except Exception as e:
                print(f"  [!] {model_name} 타임아웃/예외 ({e}) -> 3초 후 다음 예비 모델로 전환합니다.")
                time.sleep(3)

        print("[-] 모든 모델이 일시적 한도 초과 상태입니다. 분당 쿼터 리셋을 위해 30초 대기합니다...")
        time.sleep(30)

# --- 3. ReAct Loop Runner ---
def main():
    max_steps = int(os.environ.get("ANTIGRAVITY_MAX_STEPS", "20"))
    task_prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "Check docs/PROGRESS.md and execute pending tasks autonomously using your tools."
    )

    print("=" * 68)
    print(f"[Antigravity CLI] Rate-Limit Safe Engine | Workspace: {os.getcwd()}")
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
            # 스텝 간 분당 호출(RPM) 보호를 위한 3초 호흡
            time.sleep(3)
        else:
            print("\n[+] Antigravity CLI 루프가 모든 작업을 마치고 정상 종료되었습니다.")
            break

if __name__ == "__main__":
    main()
