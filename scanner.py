import os
import subprocess
from google import genai
import requests

# التحقق من وجود الرابط المستهدف
target_url = os.getenv("TARGET_URL")
if not target_url:
    print("[-] Error: TARGET_URL is not set.")
    exit(1)

print(f"[*] Starting advanced security scan on: {target_url}")

# تشغيل أداة Nuclei
print("[*] Running Nuclei Scanner...")
nuclei_output = ""
try:
    nuclei_cmd = f"nuclei -u {target_url} -silent"
    nuclei_output = subprocess.check_output(nuclei_cmd, shell=True, text=True, timeout=300)
except Exception as e:
    nuclei_output = f"Nuclei completed or encountered: {str(e)}"

# تشغيل أداة Nikto
print("[*] Running Nikto Web Scanner...")
nikto_output = ""
try:
    nikto_cmd = f"nikto -h {target_url} -Tuning 123b -nointeractive"
    nikto_output = subprocess.check_output(nikto_cmd, shell=True, text=True, timeout=300)
except Exception as e:
    nikto_output = f"Nikto completed or encountered: {str(e)}"

# دمج النتائج
raw_data = f"=== NUCLEI RESULTS ===\n{nuclei_output}\n\n=== NIKTO RESULTS ===\n{nikto_output}"

# تحليل النتائج باستخدام Gemini AI
print("[*] Sending tool outputs to AI for deep analysis and vulnerability correlation...")
api_key = os.getenv("AI_API_KEY")
client = genai.Client(api_key=api_key)

prompt = f"""
قم بتحليل نتائج الفحص الأمني التالية للموقع {target_url} واكتب تقريراً احترافياً بالثغرات والحلول المقترحة:

{raw_data}
"""

try:
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=prompt,
    )
    report = response.text
except Exception as e:
    report = f"Failed to generate AI report: {str(e)}"

print(report)

# رفع التقرير كـ Issue في GitHub
github_token = os.getenv("GITHUB_TOKEN")
repository = os.getenv("REPOSITORY")
issue_number = os.getenv("ISSUE_NUMBER")

if github_token and repository:
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    }
    
    issue_data = {
        "title": f"🔒 AI Security Scan Report for {target_url}",
        "body": report
    }
    
    # إذا تم تشغيل السكربت عبر Issue، قم بالتعليق عليه، وإلا أنشئ Issue جديد
    if issue_number and issue_number != "None":
        comment_url = f"https://api.github.com/repos/{repository}/issues/{issue_number}/comments"
        requests.post(comment_url, json={"body": report}, headers=headers)
        print("[+] Report posted as a comment on the issue.")
    else:
        issues_url = f"https://api.github.com/repos/{repository}/issues"
        requests.post(issues_url, json=issue_data, headers=headers)
        print("[+] New security report issue created successfully.")
