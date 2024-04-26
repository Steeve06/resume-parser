import re
import io
import spacy
from spacy.matcher import Matcher
import pandas as pd
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
nlp = spacy.load('en_core_web_sm')

nlp = spacy.load('en_core_web_sm')
STOPWORDS = set(nlp.Defaults.stop_words)


#extract text from resume
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            resource_manager = PDFResourceManager()
            fake_file_handle = io.StringIO()
            converter = TextConverter(resource_manager, fake_file_handle, codec='utf-8', laparams=LAParams())
            page_interpreter = PDFPageInterpreter(resource_manager, converter)
            page_interpreter.process_page(page)
            text = fake_file_handle.getvalue()
            yield text
            converter.close()
            fake_file_handle.close()

#extract name
def extract_names(resume_text):
     # Initialize matcher with a vocab
    matcher = Matcher(nlp.vocab)
    nlp_text = nlp(resume_text)
    pattern = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]
    matcher.add('NAME', [pattern])  # Add the name pattern to the Matcher object
    matches = matcher(nlp_text)
    for match_id, start, end in matches:
        span = nlp_text[start:end]
        return span.text

#extract phone number
def extract_mobile_number(text):
    phone = re.findall(
        re.compile(
            r'(?:(?:\+?([1-9]|[0-9][0-9]|[0-9][0-9][0-9])\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([0-9][1-9]|[0-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'),
        text)
    if phone:
        number = ''.join(phone[0])
        if len(number) > 10:
            return '+' + number
        else:
            return number
    return None

#extract email
def extract_email(email):
    email = re.findall("([^@|\s]+@[^@]+\.[^@|\s]+)", email)
    if email:
        try:
            return email[0].split()[0].strip(';')
        except IndexError:
            return None

#extract skills
def extract_skills(resume_text):
    nlp_text = nlp(resume_text)
    tokens = [token.text for token in nlp_text if not token.is_stop]
    data = pd.read_csv("skills.csv")
    skills = list(data.columns.values)
    skillset = []
    for token in tokens:
        if token.lower() in skills:
            skillset.append(token)
    for token in nlp_text.noun_chunks:
        token = token.text.lower().strip()
        if token in skills:
            skillset.append(token)
    return [i.capitalize() for i in set([i.lower() for i in skillset])]


# Extracting education
def extract_education(resume_text):
    education_info = []
    education_section = re.search(r'EDUCATION(.*?)SKILLS', resume_text, re.DOTALL)
    if education_section:
        education_text = education_section.group(1)
        education_lines = re.split(r'\n(?=\S)', education_text)
        for line in education_lines:
            line = line.strip()
            if line:
                education_info.append(line)
    return education_info

#extract work experience
def extract_experience(resume_text):
    # Define patterns to match experience section
    pattern = re.compile(r'(?i)(?:work|professional)\s+experience')
    matches = re.finditer(pattern, resume_text)
    start_idx = None
    end_idx = None
    for match in matches:
        start_idx = match.start()
        break
    if start_idx is None:
        return None  # If experience section not found
    # Search for the next section to determine the end of experience section
    next_sections = ['projects', 'education']
    for section in next_sections:
        end_idx = resume_text.lower().find(section)
        if end_idx != -1:
            break
    if end_idx == -1:
        end_idx = None  # If end of experience section not found, take till end of document
    experience_text = resume_text[start_idx:end_idx]
    return experience_text


# Extracting projects
def extract_projects(resume_text):
    projects_info = []
    projects_section = re.search(r'PROJECTS(.*?)$', resume_text, re.DOTALL)
    if projects_section:
        projects_text = projects_section.group(1)
        projects_lines = re.split(r'\n(?=\S)', projects_text)
        for line in projects_lines:
            line = line.strip()
            if line:
                projects_info.append(line)
    return projects_info


if __name__ == '__main__':
    file_path = 'resume.pdf'
    text = ''
    for page in extract_text_from_pdf(file_path):
        text += ' ' + page

    names = extract_names(text)
    phone_number = extract_mobile_number(text)
    email = extract_email(text)
    education_info = extract_education(text)
    experience_info = extract_experience(text)
    projects_info = extract_projects(text)
    skills_info = extract_skills(text)

    if names:
        print('\nName:', names)
    if phone_number:
        print('\nPhone Number:', phone_number)
    if email:
        print('\nEmail:', email)
    if education_info:
        print('\nEducation:')
        for item in education_info:
            print(item)
    if experience_info:
        print('\nExperience:')
        print(experience_info)
    if projects_info:
        print('\nProjects:')
        for item in projects_info:
            print(item)
    if skills_info:
        print('\nSkills:')
        for item in skills_info:
            print(item)
