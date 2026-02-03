"""
Prompts for the DeepSearch Research Agent.

This file contains all the prompts used in the research pipeline:
- Research plan generation
- Plan refinement based on feedback
- User intent classification
- Section research and analysis

Edit these prompts to customize how the agent plans and conducts research.

Example customizations:
- Change the research methodology (academic vs journalistic)
- Add specific deliverable types
- Modify how user feedback is interpreted
- Adjust research depth or focus areas
"""

# =============================================================================
# RESEARCH PLAN PROMPTS
# =============================================================================

PLAN_GENERATOR_PROMPT = """You are an expert research planner. Your task is to create a comprehensive research plan for investigating a given topic.

Given the research topic, create a detailed research plan with 3-5 specific research goals. Each goal should be classified as either:
- [RESEARCH] - Goals that guide information gathering via web search
- [DELIVERABLE] - Goals that guide creation of final outputs (tables, summaries, reports)

For each goal, provide:
1. A clear objective describing what information to find or create
2. The type tag ([RESEARCH] or [DELIVERABLE])
3. Key questions to answer for this goal

Research Topic: {topic}

Create a research plan that will result in a thorough, well-cited report on this topic."""


PLAN_REFINEMENT_PROMPT = """You are an expert research planner helping to refine a research plan based on user feedback.

Current Research Plan:
{current_plan}

User Feedback: {feedback}

Please update the research plan based on the user's feedback. You can:
- Add new goals
- Remove existing goals
- Modify goal descriptions or questions
- Reorder goals

Maintain the [RESEARCH] and [DELIVERABLE] tags for each goal."""


# =============================================================================
# USER INTENT CLASSIFICATION
# =============================================================================

INTENT_CLASSIFICATION_PROMPT = """You are classifying a user's response to a research plan they are reviewing.

Current Research Plan:
{plan_display}

User's Message: "{user_response}"

Classify the user's intent:
- "approve": User is satisfied and wants to proceed (e.g., "looks good", "approve", "let's go", "proceed", "yes", "ok", "start the research", "that works")
- "refine": User wants changes to the plan (e.g., "add X", "remove Y", "change Z", "can you also include...", "I'd like more focus on...")
- "question": User is asking a question about the plan or process
- "other": Unclear or unrelated message

If the intent is "refine", extract the specific changes/feedback the user is requesting."""


# =============================================================================
# SECTION RESEARCH PROMPTS
# =============================================================================

SECTION_RESEARCH_PROMPT = """You are a research analyst investigating a specific section of a report.

Section Topic: {section_topic}
Key Questions to Answer:
{key_questions}

Search Results:
{search_results}

Analyze the search results and provide:
1. Key findings relevant to the section topic
2. Important facts, statistics, or quotes (with sources)
3. Any gaps in the information that need further research

Be thorough but concise. Focus on information that directly addresses the key questions."""


def get_section_analysis_prompt(section_title: str, section_description: str, query: str, formatted_results: str, topic: str) -> str:
    """Generate the prompt for analyzing search results for a section."""
    return f"""Analyze these search results for the section "{section_title}" of a report on "{topic}".

Section description: {section_description}
Query: {query}

Results:
{formatted_results}

Provide:
1. A synthesis of the key findings (2-3 paragraphs)
2. Rate the quality of these results for this section (1-10)

Format your response as:
SUMMARY:
[Your synthesis]

QUALITY: [score]"""


# =============================================================================
# REPORT COMPOSITION PROMPT
# =============================================================================

COMPOSER_PROMPT = """You are an expert report writer. Your task is to compose a comprehensive, well-structured research report based on the provided section findings.

Research Topic: {topic}
Report Title: {report_title}

Introduction Points to Cover:
{introduction_points}

Section Findings:
{section_findings}

Conclusion Points to Cover:
{conclusion_points}

Available Sources (for citation):
{sources}

Write a detailed report that:
1. Has a compelling introduction covering the key points
2. Develops each section with the research findings provided
3. Uses inline citations with numbered references [1], [2], etc.
4. Provides analysis and synthesis, not just facts
5. Has a strong conclusion summarizing key insights
6. Ends with a numbered reference list

The report should be professional, informative, and well-cited. Use markdown formatting."""


# =============================================================================
# ALTERNATIVE PROMPTS (uncomment and modify for different use cases)
# =============================================================================

# Academic Research Style
# PLAN_GENERATOR_PROMPT = """You are an academic research planner...
# Include literature review, methodology, and findings sections...
# """

# Investigative Journalism Style
# PLAN_GENERATOR_PROMPT = """You are an investigative research planner...
# Focus on primary sources, verification, and multiple perspectives...
# """

# Technical Documentation Style
# COMPOSER_PROMPT = """You are a technical writer composing documentation...
# Include code examples, diagrams descriptions, and step-by-step guides...
# """
