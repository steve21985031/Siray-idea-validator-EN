import os
import sys
import json
import urllib.request
import urllib.error
import re
from datetime import datetime
from pathlib import Path

# Import demo data
import demo_input

# Color constants
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Siray API Config
DEFAULT_MODELS = {
    "evaluator": "deepseek/deepseek-v3.2",
    "ideation": "anthropic/claude-opus-4.5-thinking"
}

def load_environment():
    """Step 1: Environment Check & Guidance (Native implementation)"""
    env_path = Path(__file__).parent.parent / ".env"
    api_key = None
    
    # Try reading existing .env
    if env_path.exists():
        try:
            with open(env_path, "r") as f:
                for line in f:
                    if line.strip().startswith("SIRAY_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except Exception:
            pass

    # If no key, enter guidance
    if not api_key:
        print(f"\n{RED}{BOLD}💡 Siray API Configuration Guide{RESET}")
        print(f"{YELLOW}It seems you haven't configured your API keys yet.")
        print(f"Please visit {BOLD}https://www.siray.ai/{RESET}{YELLOW} login and get your API Key.")
        
        while True:
            key = input(f"\n{GREEN}Please paste your API Key here (sk-...): {RESET}").strip()
            if key.startswith("sk-") and len(key) > 20:
                with open(env_path, "w") as f:
                    f.write(f"SIRAY_API_KEY={key}\n")
                api_key = key
                print(f"{GREEN}✅ Configuration saved to {env_path}{RESET}")
                break
            else:
                print(f"{RED}❌ Invalid format, must start with sk-{RESET}")
    
    return api_key

def call_siray(api_key, model, messages, max_tokens=2048):
    """Generic Siray API call function"""
    url = "https://api.siray.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers)
        
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.load(response)
            return result['choices'][0]['message']['content']
            
    except urllib.error.HTTPError as e:
        error_content = e.read().decode()
        print(f"{RED}API HTTP Error {e.code}: {error_content}{RESET}")
        return None
    except Exception as e:
        print(f"{RED}API Call Failed: {e}{RESET}")
        return None

def step2_evaluate(api_key, content):
    """Step 2: DeepSeek Commercial Radar Scoring"""
    print(f"\n{CYAN}📡 Connecting to DeepSeek V3.2 for commercial radar scan...{RESET}")
    
    system_prompt = """
    You are a harsh, cold, and extremely professional Comic-Drama producer. 
    Score the user's script idea based on the following dimensions (0-100):
    1. Market Fit (40%): Does it align with current viral trends? Is it a hit or just self-indulgent?
    2. Visual Spectacle (30%): Does it have stunning visuals suitable for AI generation?
    3. Concept Novelty (30%): Is it a cliché or a micro-innovation?
    
    Strictly output JSON format, no chatter:
    {
        "scores": {"market": int, "visual": int, "novelty": int},
        "total_score": int,
        "verdict": "S/A/B/C",
        "critique": "A sharp, harsh critique under 200 words, striking the pain points",
        "needs_refinement": true/false
    }
    """
    
    response = call_siray(api_key, DEFAULT_MODELS["evaluator"], [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Script Sample:\n{content}"}
    ])
    
    try:
        json_str = re.search(r'\{.*\}', response, re.DOTALL).group()
        result = json.loads(json_str)
        return result
    except:
        print(f"{RED}Failed to parse evaluation result. Raw response:\n{response}{RESET}")
        return None

def step3_ideation(api_key, content, critique):
    """Step 3: Claude Creative Fission"""
    print(f"\n{CYAN}✨ Launching Claude Opus 4.5 Thinking for Creative Fission...{RESET}")
    
    system_prompt = """
    You are a top Creative Architect. The previous script was brutally rejected by the producer.
    Use T1-T5 tactics (Setting Displacement, Scale Multiplier, Visual-First etc.) to "reconstruct" this into a viral hit.
    
    Producer's Critique: {critique}
    
    Please provide 2 specific fission plans:
    Option A (T2/T5 Epic Narrative): Focus on visual spectacle.
    Option B (T1/T3 Twist Narrative): Focus on human nature and micro-innovation.
    
    Output in Markdown format, including: [Tactic Analysis], [One-sentence High Concept], [Golden 3-Second Hook].
    """
    
    response = call_siray(api_key, DEFAULT_MODELS["ideation"], [
        {"role": "system", "content": system_prompt.format(critique=critique)},
        {"role": "user", "content": f"Original Script:\n{content}"}
    ])
    
    return response

def generate_html_card(output_dir, filename_stem, content, eval_result, ideation_result):
    """Generate high-aesthetic HTML report card"""
    safe_ideation = json.dumps(ideation_result)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Siray Business Evaluation Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        :root {{ --bg: #0f172a; --card: #1e293b; --text: #f1f5f9; --accent: #6366f1; --accent-dim: rgba(99, 102, 241, 0.1); --danger: #ef4444; --success: #10b981; --border: rgba(255,255,255,0.1); }}
        body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); padding: 40px; display: flex; justify-content: center; }}
        .container {{ width: 900px; background: var(--card); border-radius: 20px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); overflow: hidden; border: 1px solid var(--border); }}
        .header {{ background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 30px; display: flex; justify-content: space-between; align-items: center; }}
        .header h1 {{ margin: 0; font-size: 24px; font-weight: 800; }}
        .score-badge {{ background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 99px; font-weight: 800; font-size: 20px; }}
        .content {{ padding: 30px; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
        .metric {{ background: rgba(255,255,255,0.05); padding: 15px; border-radius: 12px; text-align: center; border: 1px solid var(--border); }}
        .metric-label {{ font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }}
        .metric-value {{ font-size: 24px; font-weight: 700; color: var(--accent); }}
        .section-title {{ font-size: 13px; color: #94a3b8; text-transform: uppercase; margin: 40px 0 20px; border-bottom: 1px solid var(--border); padding-bottom: 10px; display: flex; align-items: center; gap: 8px; }}
        .section-title::before {{ content: ''; display: block; width: 4px; height: 16px; background: var(--accent); border-radius: 2px; }}
        .critique-box {{ background: rgba(239, 68, 68, 0.1); border-left: 4px solid var(--danger); padding: 20px; border-radius: 8px; color: #fca5a5; font-style: italic; margin-bottom: 30px; line-height: 1.6; font-size: 15px; }}
        .markdown-body {{ line-height: 1.7; color: #cbd5e1; }}
        .markdown-body h3 {{ color: #fff; margin-top: 30px; margin-bottom: 15px; font-size: 18px; border-left: 3px solid var(--accent); padding-left: 12px; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid var(--border); background: rgba(0,0,0,0.2); margin-top: 40px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🕵️ Business Evaluation Report</h1>
                <div style="font-size: 11px; opacity: 0.8; margin-top: 5px;">Powered by Siray Multi-Model Engine</div>
            </div>
            <div class="score-badge">{eval_result['total_score']} / 100 ({eval_result['verdict']})</div>
        </div>
        <div class="content">
            <div class="section-title">DeepSeek Commercial Radar</div>
            <div class="grid">
                <div class="metric">
                    <div class="metric-label">Market Fit</div>
                    <div class="metric-value">{eval_result['scores'].get('market', 0)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Visual Potential</div>
                    <div class="metric-value">{eval_result['scores'].get('visual', 0)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Concept Novelty</div>
                    <div class="metric-value">{eval_result['scores'].get('novelty', 0)}</div>
                </div> 
            </div>
            <div class="section-title">Producer's Brutal Critique</div>
            <div class="critique-box">"{eval_result['critique']}"</div>
            <div class="section-title">Claude Innovation Strategy</div>
            <div id="ideation-render" class="markdown-body"></div>
        </div>
        <div class="footer">Generated by Siray Idea-Validator • {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
    </div>
    <script>
        const rawMarkdown = {safe_ideation};
        document.getElementById('ideation-render').innerHTML = marked.parse(rawMarkdown);
    </script>
</body>
</html>"""
    
    html_path = output_dir / f"{filename_stem}.html"
    with open(html_path, "w") as f:
        f.write(html_content)
    print(f"{GREEN}🖼️ HTML Card generated: {html_path}{RESET}")

def generate_report(content, eval_result, ideation_result):
    """Step 4: Generate report files (MD + HTML)"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    slug = "Demo_Case"
    output_dir = Path(__file__).parent.parent / "output" / slug
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename_stem = f"Report_{timestamp}"
    md_path = output_dir / f"{filename_stem}.md"
    
    markdown = f"""# 🕵️ Siray Business Evaluation Report

**Project**: Demo Case
**Time**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Models**: DeepSeek V3.2 (Evaluator) + Claude Opus 4.5 (Ideation)

---

## 📊 Step 2: Commercial Radar Scoring (DeepSeek)

* **Total Score**: {eval_result['total_score']} / 100 ({eval_result['verdict']})
* **Market Fit**: {eval_result['scores'].get('market', 'N/A')}
* **Visual Spectacle**: {eval_result['scores'].get('visual', 'N/A')}
* **Novelty**: {eval_result['scores'].get('novelty', 'N/A')}

### Producer's Verdict
> {eval_result['critique']}

---

## ✨ Step 3: Creative Fission (Claude)

{ideation_result}

---
*Powered by Siray Comic Suite*
"""
    
    with open(md_path, "w") as f:
        f.write(markdown)
    print(f"\n{GREEN}📄 Markdown Report generated: {md_path}{RESET}")
    generate_html_card(output_dir, filename_stem, content, eval_result, ideation_result)

def main():
    api_key = load_environment()
    content = demo_input.SCENARIO
    print(f"{BOLD}Input Script Fragment:{RESET}\n{content.strip()}\n")
    eval_result = step2_evaluate(api_key, content)
    if not eval_result: return
    print(f"\n{BOLD}DeepSeek Score:{RESET} {eval_result['total_score']} ({eval_result['verdict']})")
    print(f"Critique: {eval_result['critique']}")
    if eval_result.get('needs_refinement', True) or eval_result['total_score'] < 85:
        ideation_result = step3_ideation(api_key, content, eval_result['critique'])
        generate_report(content, eval_result, ideation_result)
    else:
        print(f"\n{GREEN}🎉 Congratulations! This is an S-Tier perfect script, no fission required.{RESET}")

if __name__ == "__main__":
    main()
