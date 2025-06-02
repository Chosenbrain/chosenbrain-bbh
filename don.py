from alert import alert

alert(
    message="🔥 SQL Injection vulnerability discovered",
    severity=9,
    level="critical",
    target_url="https://vulnerable.site/login",
    ai_assessment="SQL Injection",
    repro_steps="""
1. Go to https://vulnerable.site/login
2. Input `admin' OR 1=1--` in the username field
3. Leave the password field empty and submit
4. You will be logged in without valid credentials
""",
    submission_note="""
Summary: SQL Injection on login page allows authentication bypass.

Steps to Reproduce:
- Inject `admin' OR 1=1--` in the username
- Submit form with empty password
- Access granted

Impact: Full access to authenticated section.

Fix Recommendation: Use prepared statements with parameterized queries.
""",
    platform_hint="Use `login bypass → SQLi → auth takeover` as the impact chain. Select 'Critical' in HackerOne severity when submitting."
)

