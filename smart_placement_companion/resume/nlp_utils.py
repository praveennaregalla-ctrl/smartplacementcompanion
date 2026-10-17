import pdfplumber
import re

try:
    import spacy
except Exception:
    spacy = None

# Load spaCy model if available.
if spacy is not None:
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        nlp = None
else:
    nlp = None

# Predefined skills list (Hybrid approach: Keyword matching)
TECHNICAL_SKILLS = [
    'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'swift', 'kotlin',
    'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'cassandra', 'oracle',
    'django', 'flask', 'fastapi', 'spring', 'node.js', 'react', 'angular', 'vue',
    'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'terraform', 'jenkins', 'git',
    'machine learning', 'data science', 'deep learning', 'nlp', 'computer vision',
    'html', 'css', 'bootstrap', 'tailwind', 'rest api', 'graphql',
    'dsa', 'data structures', 'algorithms', 'operating systems', 'dbms', 'computer networks'
]

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF using pdfplumber"""
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error extracting PDF: {e}")
    return text

def analyze_resume_logic(extracted_text, required_skills_list=None):
    """
    Main analysis logic:
    1. Normalize text
    2. Match against predefined skills or company required skills
    3. Calculate score with bonus
    4. Provide suggestions
    """
    text = extracted_text.lower()
    
    # Use predefined skills if no required skills provided
    skills_to_check = required_skills_list if required_skills_list else TECHNICAL_SKILLS
    
    matched = []
    for skill in skills_to_check:
        # Use regex to match whole words/phrases
        if re.search(r'\b' + re.escape(skill) + r'\b', text):
            matched.append(skill)
    
    missing = [s for s in skills_to_check if s not in matched]
    
    # Scoring
    total = len(skills_to_check)
    if total > 0:
        base_score = (len(matched) / total) * 100
    else:
        base_score = 0
        
    # Bonus for projects/experience
    bonus = 0
    if "project" in text or "experience" in text or "internship" in text:
        bonus = 10
        
    final_score = min(100, round(base_score + bonus))
    
    # Suggestions
    suggestions = []
    if bonus == 0:
        suggestions.append("Add a 'Projects' or 'Experience' section to highlight your practical work.")
    
    if len(missing) > 0:
        suggestions.append(f"Consider learning or highlighting these missing skills: {', '.join(missing[:5])}.")
        
    if final_score < 70:
        suggestions.append("Your resume score is below 70. Try to include more keywords relevant to the job description.")
    else:
        suggestions.append("Great job! Your resume has a strong match with core industry skills.")

    # spaCy enhancement (Optional extraction of entities like Organizations/Names)
    entities = []
    if nlp:
        doc = nlp(extracted_text[:10000]) # Limit text for performance
        for ent in doc.ents:
            if ent.label_ in ["ORG", "GPE", "PRODUCT"]:
                entities.append(ent.text)

    grammar_score = _calculate_grammar_score(text)
    section_list = _detect_resume_sections(extracted_text)
    ats_score = _calculate_ats_score(base_score, grammar_score, section_list)

    # Add section-specific suggestion if no major sections found
    if len(section_list) < 3:
        suggestions.append(
            'Include clear resume sections such as Education, Experience, Skills, and Projects to improve ATS readability.'
        )

    return {
        'score': final_score,
        'ats_score': ats_score,
        'grammar_score': grammar_score,
        'matched': matched,
        'missing': missing,
        'resume_sections': section_list,
        'suggestions': suggestions,
        'entities': list(set(entities))
    }


def _calculate_grammar_score(text):
    """Estimate grammar quality with simple heuristics."""
    normalized = re.sub(r'\s+', ' ', text.strip())
    sentences = re.split(r'(?<=[.!?])\s+', normalized)
    if not sentences or normalized == '':
        return 0

    issues = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if not sentence[0].isupper():
            issues += 1
        if sentence[-1] not in '.!?':
            issues += 1
        if re.search(r'\b(\w+)\s+\1\b', sentence, flags=re.IGNORECASE):
            issues += 2

    punctuation_density = normalized.count('.') + normalized.count('?') + normalized.count('!')
    if punctuation_density < max(1, len(sentences) / 2):
        issues += 1

    score = max(0, 100 - min(70, issues * 7))
    return score


def _detect_resume_sections(text):
    """Detect common resume sections by heading keywords."""
    sections = []
    section_keywords = [
        'summary', 'objective', 'education', 'experience', 'work experience', 'projects',
        'skills', 'certifications', 'achievements', 'internship', 'leadership', 'hobbies',
        'publications', 'profile', 'technical skills'
    ]

    # Look for keywords at the beginning of lines
    for line in re.split(r'\r?\n', text.lower()):
        clean_line = line.strip(': ').strip()
        if not clean_line:
            continue
        for keyword in section_keywords:
            if clean_line == keyword or clean_line.startswith(keyword + ':') or clean_line.startswith(keyword + ' -'):
                if keyword not in sections:
                    sections.append(keyword.title())

    # Fall back to a basic section if no headings detected
    if not sections and len(text) > 0:
        sections = ['Resume Content']

    return sections


def _calculate_ats_score(base_score, grammar_score, section_list):
    """Estimate ATS compatibility by combining skill match, grammar, and section structure."""
    skill_component = base_score
    grammar_component = grammar_score * 0.2
    section_component = min(100, len(section_list) * 25)
    ats = round((skill_component * 0.55) + grammar_component + (section_component * 0.25))
    return min(100, max(0, ats))
