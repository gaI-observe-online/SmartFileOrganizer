"""AI prompts for file organization."""

ORGANIZATION_SYSTEM_PROMPT = """You are an intelligent file organization assistant. Your task is to analyze files and suggest optimal organization strategies.

You should consider:
1. File type and content
2. Detected document type (invoice, contract, resume, etc.)
3. Entities mentioned (companies, people, dates)
4. Context clues from filename and content
5. Time-based organization preferences

Provide specific, actionable organization suggestions following these categories:
- Level 1 (Type): Documents, Images, Code, Finance, Videos, Audio, Archives
- Level 2 (Context): Work, Personal, Projects, Clients
- Level 3 (Time): Year-based or full date
- Level 4 (Smart): Project name, client name, or topic

Be concise and practical. Focus on creating a logical, easy-to-navigate structure."""

ORGANIZATION_USER_PROMPT = """Analyze the following files and suggest organization:

Files to organize:
{file_list}

Current date: {current_date}

For each file, suggest:
1. Destination folder structure (e.g., Documents/Work/2024/ProjectX)
2. Brief reasoning for the organization choice
3. Confidence level (0-100)

Respond in JSON format:
{{
  "suggestions": [
    {{
      "file": "filename",
      "destination": "Category/Context/Time/Smart",
      "reasoning": "brief explanation",
      "confidence": 85
    }}
  ],
  "overall_confidence": 90
}}"""

CONTEXT_DETECTION_PROMPT = """Analyze this file and determine its context:

Filename: {filename}
Content preview: {content}
Metadata: {metadata}

Determine:
1. Is this work-related or personal?
2. Does it belong to a specific project or client?
3. What is the main topic or subject?

Respond in JSON:
{{
  "context": "Work|Personal|Projects|Clients",
  "project_name": "name or null",
  "client_name": "name or null",
  "topic": "main topic",
  "confidence": 85
}}"""

ENTITY_EXTRACTION_PROMPT = """Extract key entities from this content:

Content: {content}

Extract:
1. Company names
2. Person names
3. Dates
4. Topics/keywords

Respond in JSON:
{{
  "companies": ["company1", "company2"],
  "people": ["person1", "person2"],
  "dates": ["2024-12-31"],
  "topics": ["topic1", "topic2"]
}}"""
