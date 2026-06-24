import json
import re
from collections import Counter
from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()

SKILL_KEYWORDS = {
    "python",
    "fastapi",
    "sql",
    "postgresql",
    "redis",
    "celery",
    "docker",
    "kubernetes",
    "machine learning",
    "deep learning",
    "nlp",
    "llm",
    "rag",
    "pytorch",
    "tensorflow",
    "pandas",
    "numpy",
    "scikit-learn",
    "javascript",
    "typescript",
    "react",
    "vue",
    "git",
    "linux",
    "api",
    "data analysis",
}


def _find_skills(text: str) -> set[str]:
    lowered = text.lower()
    return {skill for skill in SKILL_KEYWORDS if skill in lowered}


def _top_terms(text: str, limit: int = 12) -> list[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z+#.-]{2,}", text.lower())
    stopwords = {"and", "the", "with", "for", "you", "are", "our", "will", "from", "this", "that", "have"}
    counts = Counter(word for word in words if word not in stopwords)
    return [word for word, _ in counts.most_common(limit)]


def fallback_analysis(resume_text: str, jd_text: str) -> dict[str, Any]:
    resume_skills = _find_skills(resume_text)
    jd_skills = _find_skills(jd_text)
    matched = resume_skills & jd_skills
    gaps = sorted(jd_skills - resume_skills)

    if jd_skills:
        score = int(round((len(matched) / len(jd_skills)) * 100))
    else:
        jd_terms = set(_top_terms(jd_text))
        resume_terms = set(_top_terms(resume_text, 40))
        score = int(round((len(jd_terms & resume_terms) / max(len(jd_terms), 1)) * 100))

    score = max(15, min(95, score))
    terms = ", ".join(sorted(matched)[:8]) or "岗位关键词"
    return {
        "score": score,
        "summary": f"候选人与岗位有 {score}% 的初步匹配度，当前简历中已体现 {terms}。建议继续强化与 JD 直接对应的项目证据。",
        "skill_gaps": gaps[:8] or ["补充更多与岗位要求直接对应的工具、项目指标和业务场景"],
        "resume_suggestions": [
            "把最相关的项目经历放到简历前半部分，并在每条经历中写清任务、技术栈和量化结果。",
            "针对 JD 中重复出现的关键词调整技能区和项目描述，避免只罗列工具名。",
            "增加 1-2 条能证明实习岗位核心能力的成果指标，例如性能提升、准确率、用户量或自动化节省时间。",
        ],
        "raw_response": {"mode": "fallback", "matched_skills": sorted(matched), "resume_skills": sorted(resume_skills)},
    }


async def analyze_with_llm(resume_text: str, jd_text: str) -> dict[str, Any]:
    if not settings.llm_api_key:
        return fallback_analysis(resume_text, jd_text)

    prompt = f"""
你是一个面向 AI 实习岗位的招聘匹配分析助手。请基于候选人简历和岗位 JD 输出严格 JSON：
{{
  "score": 0-100 的整数,
  "summary": "两到三句话概括匹配度",
  "skill_gaps": ["缺口1", "缺口2"],
  "resume_suggestions": ["建议1", "建议2", "建议3"]
}}

简历：
{resume_text[:12000]}

岗位 JD：
{jd_text[:8000]}
""".strip()

    headers = {"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"}
    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": "You return valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(settings.llm_base_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    return {
        "score": int(parsed.get("score", 0)),
        "summary": str(parsed.get("summary", "")),
        "skill_gaps": list(parsed.get("skill_gaps", [])),
        "resume_suggestions": list(parsed.get("resume_suggestions", [])),
        "raw_response": data,
    }
