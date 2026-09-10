import os
import sys
import subprocess
import json
from openai import OpenAI

TARGET_URL = os.environ.get("TARGET_URL")
AI_API_KEY = os.environ.get("AI_API_KEY")

client = OpenAI(api_key=AI_API_KEY)

def run_security_tools(url):
    print(f"[*] Starting advanced security scan on: {url}")
    scan_results = ""

    # 1. تشغيل أداة Nuclei
    print("[*] Running Nuclei Scanner...")
    try:
        nuclei_cmd = ["nuclei", "-u", url, "-jsonl", "-silent", "-severity", "low,medium,high,critical"]
        result = subprocess.run(nuclei_cmd, capture_output=True, text=True, timeout=180)
        if result.stdout:
            scan_results += "=== NUCLEI VULNERABILITY SCAN RESULTS ===\n"
            scan_results += result.stdout[:15000] + "\n\n"
    except Exception as e:
        scan_results += f"Nuclei scan error or timeout: {str(e)}\n"

    # 2. تشغيل أداة Nikto
    print("[*] Running Nikto Web Scanner...")
    try:
        nikto_cmd = ["nikto", "-h", url, "-Tuning", "1234789b", "-maxtime", "60"]
        result = subprocess.run(nikto_cmd, capture_output=True, text=True, timeout=90)
        if result.stdout:
            scan_results += "=== NIKTO WEB SERVER SCAN RESULTS ===\n"
            scan_results += result.stdout[:5000] + "\n"
    except Exception as e:
        scan_results += f"Nikto scan error or timeout: {str(e)}\n"

    if not scan_results.strip():
        scan_results = "No vulnerabilities detected by standard tools or target blocked the scanner."

    return scan_results

def analyze_with_ai(raw_scan_data, url):
    print("[*] Sending tool outputs to AI for deep analysis and vulnerability correlation...")

    prompt = f"""
    You are an elite Senior Penetration Tester and Application Security Expert.
    I have run automated security scanners (Nuclei and Nikto) against the target: {url}.

    Here is the raw output from the scanners:
    {raw_scan_data}

    Your tasks:
    1. Analyze the raw findings, eliminate false positives, and correlate them with famous vulnerability categories (such as OWASP Top 10, common CVEs, misconfigurations, or exposed sensitive files).
    2. Structure the findings clearly by severity (Critical, High, Medium, Low).
    3. For each real vulnerability found, explain the risk and provide a concrete, professional remediation/fix recommendation.
    4. If no severe vulnerabilities are found, highlight the security posture and potential hardening steps.

    Provide a professional Markdown security report.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    if not TARGET_URL:
        print("[-] Error: TARGET_URL is not set.")
        sys.exit(1)

    raw_data = run_security_tools(TARGET_URL)
    final_report = analyze_with_ai(raw_data, TARGET_URL)

    with open("security_report.md", "w", encoding="utf-8") as f:
        f.write(final_report)
    print("[+] Advanced AI Security Report generated successfully!")
