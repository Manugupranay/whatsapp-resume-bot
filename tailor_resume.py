import anthropic
import json
from resume_data import MASTER_RESUME

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env


def tailor_resume(job_description: str) -> dict:
    """
    Sends the JD + master resume to Claude.
    Returns a tailored resume dict ready for DOCX generation.
    """

    system_prompt = """You are an expert resume writer specializing in AI/ML engineering roles.
You will receive a candidate's master resume and a job description.
Your job is to produce a tailored version of the resume that maximizes the candidate's match to the JD.

Rules:
- NEVER invent experience, skills, or qualifications not in the master resume
- Rewrite the professional summary to directly mirror the JD's language and priorities
- Reorder skills sections to put the most JD-relevant skills first
- For each job, select and reorder the 6-8 most relevant bullets (drop less relevant ones)
- Slightly rephrase bullets to use the JD's terminology where truthful
- Keep all dates, company names, titles, education, and certifications exactly as provided
- Return ONLY valid JSON, no markdown, no explanation

Return this exact JSON structure:
{
  "summary": "rewritten summary paragraph",
  "skills": {
    "Category Name": "skill list string",
    ...keep same categories but reorder them by JD relevance...
  },
  "experience": [
    {
      "company": "...",
      "location": "...",
      "title": "...",
      "dates": "...",
      "bullets": ["bullet 1", "bullet 2", ...]
    }
  ],
  "keywords_matched": ["keyword1", "keyword2", ...]
}"""

    user_message = f"""JOB DESCRIPTION:
{job_description}

MASTER RESUME:
{json.dumps(MASTER_RESUME, indent=2)}

Tailor this resume for the job description above. Return only JSON."""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": user_message}],
        system=system_prompt,
    )

    raw = message.content[0].text.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    tailored = json.loads(raw)

    # Preserve static fields from master resume
    tailored["name"] = MASTER_RESUME["name"]
    tailored["email"] = MASTER_RESUME["email"]
    tailored["phone"] = MASTER_RESUME["phone"]
    tailored["certifications"] = MASTER_RESUME["certifications"]
    tailored["education"] = MASTER_RESUME["education"]

    return tailored
