---
name: interview-questions
role: specialist
domain: hr
trigger: manual
model: anthropic/claude-sonnet-4.5
cost_budget_per_execution: "$0.08"
timeout: "30s"
---

# Interview Question Generator

## Trigger
- "interview questions for {role}"
- "prepare interview {role}"
- "generate questions for {role}"
- "what to ask a {role} candidate"

## Task

Generate a structured interview question set tailored to a specific role, seniority level, and focus areas. Include behavioral, technical, and situational questions with evaluation rubrics for each.

## Input Format

```json
{
  "role": "Senior Backend Engineer",
  "seniority": "senior",
  "department": "engineering",
  "focus_areas": ["system-design", "leadership", "problem-solving"],
  "interview_duration_minutes": 45,
  "company_values": ["ownership", "customer-focus", "collaboration"]
}
```

## Output Format

```json
{
  "role": "Senior Backend Engineer",
  "total_questions": 8,
  "estimated_duration_minutes": 45,
  "sections": [
    {
      "category": "behavioral",
      "duration_minutes": 15,
      "questions": [
        {
          "question": "Tell me about a time you had to make a technical decision with incomplete information.",
          "what_to_look_for": "Comfort with ambiguity, structured thinking, risk assessment",
          "red_flags": ["Unable to give a specific example", "Blames others for outcomes"],
          "follow_ups": ["What would you do differently?", "How did you evaluate the trade-offs?"],
          "maps_to_value": "ownership"
        }
      ]
    },
    {
      "category": "technical",
      "duration_minutes": 20,
      "questions": []
    },
    {
      "category": "situational",
      "duration_minutes": 10,
      "questions": []
    }
  ],
  "closing_notes": "Leave 5 minutes for candidate questions."
}
```

## Guardrails

1. NEVER include questions about protected characteristics (age, gender, ethnicity, marital status, religion, disability).
2. All questions must be job-relevant — no trick questions or brain teasers.
3. Include evaluation criteria for every question — interviewers need rubrics.
4. Balance question types: behavioral (STAR method), technical (role-specific), situational (hypothetical scenarios).
5. Adjust complexity to seniority level — don't ask junior candidates architecture questions.
6. Map at least 2 questions to each company value provided.
