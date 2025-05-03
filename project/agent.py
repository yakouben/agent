from re import search
from fpdf import FPDF
import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.adk.agents import Agent
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

# تحميل المتغيرات
load_dotenv()
api_key = os.getenv("API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

def analyze_and_create_pdf_tool(text: str) -> str:
    """
    Analyze resume text and create improved PDF.
    Returns message with the path of the saved file.
    """
    prompt = f"""
    You are a professional resume consultant. Based on the following text, write a well-organized improved resume in professional format:
    
    {text}
    """
    try:
        response = model.generate_content(prompt)
        improved_text = response.text

        output_path = "improved_resume_reportlab.pdf"
        c = canvas.Canvas(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        y_position = 750  # بدء الكتابة من أعلى الصفحة

        for line in improved_text.split('\n'):
            p = Paragraph(line, normal_style)
            p_width, p_height = p.wrapOn(c, 500, 100) # تحديد عرض الفقرة
            if y_position - p_height < 50: # التحقق من تجاوز نهاية الصفحة
                c.showPage() # إنشاء صفحة جديدة
                y_position = 750
            p.drawOn(c, 50, y_position - p_height)
            y_position -= p_height + 5 # إضافة مسافة بين الأسطر

        c.save()
        return f"✅ Improved resume saved as {output_path} using ReportLab"
    except Exception as e:
        return f"❌ Error while creating PDF with ReportLab: {str(e)}"

def search_jobs_tool(skills: str, interests: str, location: str = "") -> str:
    """
    Search for jobs based on user skills and interests.
    
    Args:
        skills (str): User's skills
        interests (str): User's interests
        location (str): Preferred job location
    
    Returns:
        str: Formatted job search results
    """
    try:
        # بناء استعلام البحث
        search_query = f"{skills} {interests} jobs {location} site:linkedin.com OR site:indeed.com"
        
        # البحث عن الوظائف
        results = []
        for url in search(search_query, num_results=5, stop=5, pause=2.0):
            try:
                response = requests.get(url, timeout=5)
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.title.string if soup.title else url
                
                results.append({
                    'title': title,
                    'url': url
                })
            except Exception as e:
                print(f"Error fetching {url}: {str(e)}")
                continue
        
        # تنسيق النتائج
        if not results:
            return "❌ لم يتم العثور على وظائف مطابقة. حاول تعديل معايير البحث."
        
        formatted_results = "🔍 نتائج البحث عن الوظائف:\n\n"
        for i, job in enumerate(results, 1):
            formatted_results += f"{i}. {job['title']}\n"
            formatted_results += f"   رابط الوظيفة: {job['url']}\n\n"
        
        return formatted_results
        
    except Exception as e:
        return f"❌ حدث خطأ أثناء البحث عن الوظائف: {str(e)}"

# تعريف الـ Agent
root_agent = Agent(
    name="job_hunter_agent",
    model="gemini-2.0-flash",
    description="Agent to find the best opportunity for you based on your CV.",
    instruction=(
        "You are an AI agent specializing in assisting users with all aspects of their Curriculum Vitae (CV) or resume."
        "You can create a professional CV from scratch, improve an existing one, or analyze a CV and provide insights along with suggesting job opportunities."
        ""
        "Your task depends on the user's initial request:"
        ""
        "**1. If the user requests \"create a CV\" or similar:**"
        ""
        "   - **Begin by asking basic personal questions** to gather necessary information for creating the CV. These questions can include:"
        "     - \"What is your full name?\""
        "     - \"What is your contact information (email, phone number, address if applicable)?\""
        "     - \"What is the job title you are seeking?\""
        "   - **Then, ask detailed questions about their skills and experience:**"
        "     - \"What are your key technical and soft skills? Please list them in detail.\""
        "     - \"What is your previous work experience? Please mention the company name, job title, period of employment (from - to), and a brief description of your responsibilities and achievements in each role.\""
        "     - \"What is your educational background and any certifications or training courses you have completed? Please mention the institution name, degree/certificate, and year of graduation/completion.\""
        "     - \"Do you have any hobbies or interests relevant to your field of work or that could enhance your CV?\""
        "     - \"Is there any additional information you would like to include in your CV?\""
        "   - **After gathering sufficient information, create a professional and well-organized CV.** Focus on using a clear and appealing format, and highlight skills and experiences relevant to the target job."
        "   - **Finally, generate this CV in PDF format** using the available tools."
        ""
        "**2. If the user requests \"improve a CV\" or similar:**"
        ""
        "   - **Ask the user to provide you with a copy of their current CV.**"
        "   - **After reviewing their CV, ask specific questions** to obtain additional information that will help you improve it. These questions can include:"
        "     - \"What specific jobs or fields are you targeting?\""
        "     - \"Are there any aspects of your CV that you feel need improvement?\""
        "     - \"Have you received any previous feedback on your CV?\""
        "     - \"Have you recently acquired any new skills or experience that are not yet included in your CV?\""
        "     - \"What format do you prefer for your CV?\""
        "   - **Based on the user's answers and your analysis of the current CV, provide a detailed list of advice and guidance for its improvement.** This advice should be specific and actionable."
        "   - **Then, create a modified and improved version of the CV** based on this advice."
        "   - **Finally, generate this improved CV in PDF format.**"
        ""
        "**3. If the user requests \"analyze a CV\" or similar:**"
        ""
        "   - **Ask the user to provide you with a copy of their CV.**"
        "   - **Carefully analyze the CV, focusing on:**"
        "     - \"**Strengths:** What are the standout aspects of the CV?\""
        "     - \"**Weaknesses:** What areas need improvement?\""
        "     - \"**Skills:** What prominent skills does the user possess?\""
        "     - \"**Experience:** What relevant work experience is highlighted?\""
        "     - \"**Format and Organization:** Is the CV well-organized and easy to read?\""
        "   - **Prepare a detailed list of the analysis results.**"
        "   - **Based on the skills and experience mentioned in the CV, search for the best available opportunities on LinkedIn and Indeed** that match the user's profile and provide a list of them."
        "   - **Provide specific recommendations to the user on how to enhance their chances of getting a job.**"
        ""
        "**4. If the user requests \"search for jobs\" or similar:**"
        ""
        "   - **Ask the user for his cv if he has one or want the agent create one for him.**"
        "   - **Ask about their preferred location for work.**"
        "   - **Use the search_jobs_tool to find relevant job opportunities.**"
        "   - **Present the results in a clear and organized manner.**"
        "   - **Provide advice on how to apply for these jobs.**"
        ""
        "**General Guidelines for Interacting with the User:**"
        ""
        "- Be friendly and professional in your interactions with the user."
        "- Ask clear and concise questions."
        "- Listen carefully to the user's answers and use them to guide your steps."
        "- Provide organized and easy-to-understand results."
        "- If you are unsure about something, ask the user for clarification."
    ),
    tools=[analyze_and_create_pdf_tool, search_jobs_tool],
)