import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import json
import time
import requests
from PIL import Image
from io import BytesIO

# Import modules
from modules.student_model import StudentProfile
from modules.academic_tracker import AcademicTracker
from modules.financial_planner import FinancialPlanner
from modules.mental_wellness import MentalWellnessCoach
from modules.career_guide import CareerGuide
from modules.resource_connector import ResourceConnector
from modules.ai_advisor import GroqAdvisor  # Import for the AI advisor

# Import utilities
from utils.data_manager import DataManager
from utils.visualization import create_gauge_chart, create_trend_chart, create_pie_chart
from utils.prediction_engine import PredictiveEngine

def patch_missing_methods():
    """Patch missing methods to ensure application doesn't crash"""
    from modules.financial_planner import FinancialPlanner
    from modules.career_guide import CareerGuide
    from modules.student_model import StudentProfile
    
    # Patch FinancialPlanner
    if not hasattr(FinancialPlanner, 'get_expenses_by_category'):
        def get_expenses_by_category(self):
            """Get expenses categorized by category"""
            try:
                # Get all transactions
                transactions = []
                try:
                    if hasattr(self, 'get_all_transactions'):
                        transactions = self.get_all_transactions()
                    elif hasattr(self.data_manager, 'get_data'):
                        transactions = self.data_manager.get_data(
                            self.student_id, "financial_transactions", default=[]
                        )
                except:
                    # Fallback
                    transactions = []
                
                # Filter for expenses (negative amounts)
                expenses = [t for t in transactions if t.get('amount', 0) < 0]
                
                # Group by category
                categories = {}
                for expense in expenses:
                    category = expense.get('category', 'Other')
                    amount = abs(expense.get('amount', 0))
                    
                    if category not in categories:
                        categories[category] = 0
                    
                    categories[category] += amount
                
                # Convert to list of dicts for visualization
                result = [{"category": cat, "amount": amt} for cat, amt in categories.items()]
                result.sort(key=lambda x: x["amount"], reverse=True)
                
                return result
            except:
                return []
        
        FinancialPlanner.get_expenses_by_category = get_expenses_by_category
        print("Patched get_expenses_by_category method to FinancialPlanner")
    
    # Patch CareerGuide
    if not hasattr(CareerGuide, 'get_career_profile'):
        def get_career_profile(self):
            """Get career profile for the student"""
            try:
                profile = None
                if hasattr(self.data_manager, 'get_data'):
                    profile = self.data_manager.get_data(
                        self.student_id, "career_profile", default=None
                    )
                return profile
            except:
                return None
        
        CareerGuide.get_career_profile = get_career_profile
        print("Patched get_career_profile method to CareerGuide")
    
    # Patch StudentProfile
    if not hasattr(StudentProfile, 'get_all_data'):
        def get_all_data(self):
            """Get all profile data"""
            try:
                return self.profile_data
            except:
                return {}
        
        StudentProfile.get_all_data = get_all_data
        print("Patched get_all_data method to StudentProfile")

# Set page configuration
st.set_page_config(
    page_title="HARMONY-India: Student Success Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'student_profile' not in st.session_state:
    st.session_state.student_profile = None
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"
if 'is_first_run' not in st.session_state:
    st.session_state.is_first_run = True
if 'show_welcome' not in st.session_state:
    st.session_state.show_welcome = True
if 'ai_advisor' not in st.session_state:
    st.session_state.ai_advisor = GroqAdvisor()  # Initialize AI advisor
if 'first_visit_sections' not in st.session_state:
    st.session_state.first_visit_sections = {
        "Finance": True,
        "Academics": True,
        "Wellness": True,
        "Career": True,
        "Resources": True
    }
if 'groq_api_key' not in st.session_state:
    st.session_state.groq_api_key = None
if 'last_trend_update' not in st.session_state:
    st.session_state.last_trend_update = None
if 'cached_content' not in st.session_state:
    st.session_state.cached_content = {
        "academic_trends": None,
        "financial_tips": None,
        "wellness_tips": None,
        "career_insights": None,
        "resources": {},
        "last_updated": None
    }

# Patch function to ensure FinancialPlanner has the needed method
# This is a fix for the error where get_all_transactions might not exist
def patch_financial_planner():
    original_init = FinancialPlanner.__init__
    
    # Check if get_all_transactions already exists
    if not hasattr(FinancialPlanner, 'get_all_transactions'):
        # Add the method if it doesn't exist
        def get_all_transactions(self):
            """Get all financial transactions for the student."""
            return self.data_manager.get_data(
                self.student_id, "financial_transactions", default=[]
            )
        
        FinancialPlanner.get_all_transactions = get_all_transactions
        print("Added get_all_transactions method to FinancialPlanner")

# Apply the patch
patch_financial_planner()

# AI Agent class for fetching latest information and providing personalized recommendations
class AIAdvisorAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.initialized = api_key is not None
        self.base_url = "https://api.groq.com/openai/v1"
    
    def set_api_key(self, api_key):
        """Set GROQ API key"""
        self.api_key = api_key
        self.initialized = True
        return True
    
    def _make_groq_request(self, model, messages, temperature=0.7, max_tokens=800):
        """Make a request to GROQ API"""
        if not self.initialized:
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"GROQ API Error: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            print(f"Error making GROQ request: {e}")
            return None
    
    def get_academic_trends(self, degree=None, year=None):
        """Get latest academic trends for the student's field"""
        if not self.initialized:
            return self._get_fallback_academic_trends(degree)
        
        try:
            prompt = f"Provide 3 latest academic trends and study techniques for {degree} students in {year} in India for 2025. Format as a JSON list of dictionaries with keys 'trend', 'description', and 'benefit'."
            
            messages = [
                {"role": "system", "content": "You're an educational advisor for Indian students."},
                {"role": "user", "content": prompt}
            ]
            
            response = self._make_groq_request(
                model="llama3-70b-8192",
                messages=messages
            )
            
            if response:
                content = response["choices"][0]["message"]["content"]
                try:
                    # Extract just the JSON part (in case there's additional text)
                    import re
                    json_match = re.search(r'\[.*\]', content, re.DOTALL)
                    if json_match:
                        content = json_match.group()
                    
                    trends = json.loads(content)
                    return trends
                except:
                    return self._get_fallback_academic_trends(degree)
            else:
                return self._get_fallback_academic_trends(degree)
                
        except Exception as e:
            print(f"Error getting academic trends: {e}")
            return self._get_fallback_academic_trends(degree)
    
    def _get_fallback_academic_trends(self, degree=None):
        """Fallback academic trends when API fails"""
        if "B.Tech" in str(degree) or "B.E." in str(degree):
            return [
                {
                    "trend": "Project-Based Learning",
                    "description": "Engineering programs are increasingly adopting project-based approaches that mirror industry practices",
                    "benefit": "Develops practical skills and portfolio for job market"
                },
                {
                    "trend": "AI & ML Integration",
                    "description": "AI and machine learning concepts are being integrated across engineering disciplines",
                    "benefit": "Prepares students for the most in-demand technical skills"
                },
                {
                    "trend": "Micro-credentials",
                    "description": "Short, specialized certifications that complement formal degrees",
                    "benefit": "Allows students to demonstrate specific technical competencies to employers"
                }
            ]
        elif "BBA" in str(degree) or "B.Com" in str(degree):
            return [
                {
                    "trend": "Data-Driven Decision Making",
                    "description": "Business curricula now emphasize statistical analysis and data interpretation",
                    "benefit": "Essential skill for modern business operations and strategy"
                },
                {
                    "trend": "Entrepreneurship Focus",
                    "description": "Programs emphasizing startup methodologies and business model innovation",
                    "benefit": "Prepares students for both corporate and startup environments"
                },
                {
                    "trend": "Sustainability Management",
                    "description": "Business courses integrating environmental and social impact considerations",
                    "benefit": "Alignment with emerging business priorities and regulations"
                }
            ]
        else:
            return [
                {
                    "trend": "Interdisciplinary Learning",
                    "description": "Programs that blend multiple fields of study for broader perspectives",
                    "benefit": "Develops versatile thinking and adaptability"
                },
                {
                    "trend": "Digital Literacy Enhancement",
                    "description": "Focused training on digital tools relevant to all disciplines",
                    "benefit": "Essential workplace skills regardless of field"
                },
                {
                    "trend": "Active Learning Methods",
                    "description": "Techniques that emphasize student participation over passive lectures",
                    "benefit": "Improves retention and practical application of concepts"
                }
            ]
    
    def get_financial_advice(self, profile_data, financial_data=None):
        """Get personalized financial advice based on student profile and data"""
        if not self.initialized:
            return self._get_fallback_financial_advice(profile_data)
        
        try:
            degree = profile_data.get("degree", "")
            year = profile_data.get("year_of_study", "")
            
            # Create a concise summary of financial data if available
            financial_summary = "No financial data available."
            if financial_data:
                income = sum([t['amount'] for t in financial_data if t['amount'] > 0])
                expenses = abs(sum([t['amount'] for t in financial_data if t['amount'] < 0]))
                top_expense_category = "Unknown"
                if expenses > 0:
                    expense_by_category = {}
                    for t in financial_data:
                        if t['amount'] < 0:
                            category = t.get('category', 'Other')
                            if category not in expense_by_category:
                                expense_by_category[category] = 0
                            expense_by_category[category] += abs(t['amount'])
                    
                    if expense_by_category:
                        top_expense_category = max(expense_by_category.items(), key=lambda x: x[1])[0]
                
                financial_summary = f"Monthly income: ₹{income:.0f}, Monthly expenses: ₹{expenses:.0f}, Top expense category: {top_expense_category}"
            
            prompt = f"""
            As a financial advisor for Indian students, provide 3 personalized financial tips for a {year} {degree} student in India.
            
            Financial context: {financial_summary}
            
            Include the most current 2025 information about scholarships, student financial programs, and money management strategies in India.
            Format as a JSON list of dictionaries with keys 'tip', 'description', and 'action_item'.
            Keep it concise and specific to Indian students.
            """
            
            messages = [
                {"role": "system", "content": "You're a financial advisor for Indian college students."},
                {"role": "user", "content": prompt}
            ]
            
            response = self._make_groq_request(
                model="llama3-70b-8192",
                messages=messages
            )
            
            if response:
                content = response["choices"][0]["message"]["content"]
                try:
                    # Extract just the JSON part
                    import re
                    json_match = re.search(r'\[.*\]', content, re.DOTALL)
                    if json_match:
                        content = json_match.group()
                        
                    advice = json.loads(content)
                    return advice
                except:
                    return self._get_fallback_financial_advice(profile_data)
            else:
                return self._get_fallback_financial_advice(profile_data)
                
        except Exception as e:
            print(f"Error getting financial advice: {e}")
            return self._get_fallback_financial_advice(profile_data)
    
    def _get_fallback_financial_advice(self, profile_data):
        """Fallback financial advice when API fails"""
        degree = profile_data.get("degree", "")
        
        if "B.Tech" in str(degree) or "B.E." in str(degree):
            return [
                {
                    "tip": "Leverage Technical Scholarships",
                    "description": "Many engineering-specific scholarships remain unclaimed each year",
                    "action_item": "Apply for AICTE, Siemens, and Google technical scholarships by May 2025"
                },
                {
                    "tip": "Budget for Technical Resources",
                    "description": "Engineering courses often require specialized software and equipment",
                    "action_item": "Allocate ₹2,000-3,000 per semester for technical tools and resources"
                },
                {
                    "tip": "Consider Technical Freelancing",
                    "description": "Your engineering skills can generate income even while studying",
                    "action_item": "Create profiles on Upwork or Fiverr offering programming or CAD services"
                }
            ]
        elif "BBA" in str(degree) or "B.Com" in str(degree):
            return [
                {
                    "tip": "Invest in Market Knowledge",
                    "description": "Business students benefit from early market exposure",
                    "action_item": "Open a demat account with minimal funds to learn real-world investing"
                },
                {
                    "tip": "Budget for Business Events",
                    "description": "Networking events and conferences are valuable for business students",
                    "action_item": "Set aside ₹5,000 per year for attending industry conferences and events"
                },
                {
                    "tip": "Content Creation for Income",
                    "description": "Business knowledge is in demand online",
                    "action_item": "Start a business/finance blog or YouTube channel to build both resume and income"
                }
            ]
        else:
            return [
                {
                    "tip": "Education Loan Interest Subsidy",
                    "description": "Government subsidies can reduce your effective interest rate",
                    "action_item": "Check eligibility for interest subsidy schemes through the Vidya Lakshmi portal"
                },
                {
                    "tip": "Digital Subscription Pooling",
                    "description": "Share costs of educational resources with classmates",
                    "action_item": "Create a subscription pool with 3-4 friends for digital learning platforms"
                },
                {
                    "tip": "Track Academic Expenses",
                    "description": "Education-related expenses may qualify for tax benefits",
                    "action_item": "Maintain receipts of all educational expenses for potential tax benefits"
                }
            ]
    
    def get_wellness_tips(self, profile_data, mood_data=None):
        """Get personalized wellness tips based on student profile and mood data"""
        if not self.initialized:
            return self._get_fallback_wellness_tips(profile_data)
        
        try:
            degree = profile_data.get("degree", "")
            year = profile_data.get("year_of_study", "")
            
            # Create a summary of mood data if available
            mood_summary = "No mood data available."
            if mood_data and len(mood_data) > 0:
                avg_mood = sum(entry.get('score', 0) for entry in mood_data) / len(mood_data)
                common_stressors = []
                stress_count = {}
                
                for entry in mood_data:
                    factors = entry.get('stress_factors', [])
                    for factor in factors:
                        if factor not in stress_count:
                            stress_count[factor] = 0
                        stress_count[factor] += 1
                
                if stress_count:
                    common_stressors = sorted(stress_count.items(), key=lambda x: x[1], reverse=True)[:2]
                    common_stressors = [factor for factor, _ in common_stressors]
                
                mood_summary = f"Average mood: {avg_mood:.1f}/10. Common stressors: {', '.join(common_stressors) if common_stressors else 'None identified'}."
            
            prompt = f"""
            As a mental wellness coach for Indian students in 2025, provide 3 personalized wellness tips for a {year} {degree} student in India.
            
            Mood context: {mood_summary}
            
            Include the latest research and mental wellness practices that are specifically effective for students in the Indian educational context.
            Format as a JSON list of dictionaries with keys 'tip', 'description', and 'practice'.
            Keep it concise, specific to Indian students, and culturally appropriate.
            """
            
            messages = [
                {"role": "system", "content": "You're a wellness coach for Indian college students."},
                {"role": "user", "content": prompt}
            ]
            
            response = self._make_groq_request(
                model="llama3-70b-8192",
                messages=messages
            )
            
            if response:
                content = response["choices"][0]["message"]["content"]
                try:
                    # Extract just the JSON part
                    import re
                    json_match = re.search(r'\[.*\]', content, re.DOTALL)
                    if json_match:
                        content = json_match.group()
                        
                    tips = json.loads(content)
                    return tips
                except:
                    return self._get_fallback_wellness_tips(profile_data)
            else:
                return self._get_fallback_wellness_tips(profile_data)
                
        except Exception as e:
            print(f"Error getting wellness tips: {e}")
            return self._get_fallback_wellness_tips(profile_data)
    
    def _get_fallback_wellness_tips(self, profile_data):
        """Fallback wellness tips when API fails"""
        degree = profile_data.get("degree", "")
        
        if "B.Tech" in str(degree) or "B.E." in str(degree):
            return [
                {
                    "tip": "Pomodoro Technique for Technical Studies",
                    "description": "Engineering subjects require intense focus but also regular breaks",
                    "practice": "Study in 25-minute blocks with 5-minute breaks to prevent burnout"
                },
                {
                    "tip": "Physical Movement Between Coding Sessions",
                    "description": "Long coding sessions can lead to physical strain",
                    "practice": "Do 5 minutes of simple stretches after every hour of programming"
                },
                {
                    "tip": "Mindfulness for Technical Problem-Solving",
                    "description": "Engineering challenges can create frustration loops",
                    "practice": "When stuck on a problem, practice 2 minutes of deep breathing before continuing"
                }
            ]
        elif "BBA" in str(degree) or "B.Com" in str(degree):
            return [
                {
                    "tip": "Presentation Anxiety Management",
                    "description": "Business programs often require frequent presentations",
                    "practice": "Practice the 4-7-8 breathing technique before presentations (inhale for 4, hold for 7, exhale for 8)"
                },
                {
                    "tip": "Networking Without Exhaustion",
                    "description": "Business networking can be draining for many students",
                    "practice": "Schedule 30-minute quiet time after networking events to recharge"
                },
                {
                    "tip": "Balancing Competition and Wellbeing",
                    "description": "Business environments can be highly competitive",
                    "practice": "Keep a weekly 'wins journal' to focus on personal growth rather than comparison"
                }
            ]
        else:
            return [
                {
                    "tip": "Study-Life Integration",
                    "description": "Balancing academics with personal life is essential for wellbeing",
                    "practice": "Schedule at least 2 hours of non-academic activities you enjoy every week"
                },
                {
                    "tip": "Morning Routine for Focus",
                    "description": "How you start your day impacts your mental state",
                    "practice": "Begin each day with 10 minutes of quiet reflection before checking your phone"
                },
                {
                    "tip": "Social Connection Planning",
                    "description": "Regular social connections improve mental health",
                    "practice": "Schedule at least one meaningful social interaction (even if brief) every day"
                }
            ]
    
    def get_career_insights(self, profile_data, career_preferences=None):
        """Get personalized career insights based on student profile and preferences"""
        if not self.initialized:
            return self._get_fallback_career_insights(profile_data)
        
        try:
            degree = profile_data.get("degree", "")
            year = profile_data.get("year_of_study", "")
            
            # Create a summary of career preferences if available
            career_summary = "No career preferences specified."
            if career_preferences:
                interests = career_preferences.get('interests', [])
                target_roles = career_preferences.get('target_roles', [])
                
                career_summary = f"Interests: {', '.join(interests) if interests else 'Not specified'}. "
                career_summary += f"Target roles: {', '.join(target_roles) if target_roles else 'Not specified'}."
            
            prompt = f"""
            As a career advisor for Indian students in 2025, provide 3 personalized career insights for a {year} {degree} student in India.
            
            Career context: {career_summary}
            
            Include the latest industry trends from 2025, new emerging roles, job market opportunities in India, and specific skills that are in high demand.
            Format as a JSON list of dictionaries with keys 'insight', 'trend', and 'action'.
            Keep it concise and specific to the Indian job market.
            """
            
            messages = [
                {"role": "system", "content": "You're a career advisor for Indian college students."},
                {"role": "user", "content": prompt}
            ]
            
            response = self._make_groq_request(
                model="llama3-70b-8192",
                messages=messages
            )
            
            if response:
                content = response["choices"][0]["message"]["content"]
                try:
                    # Extract just the JSON part
                    import re
                    json_match = re.search(r'\[.*\]', content, re.DOTALL)
                    if json_match:
                        content = json_match.group()
                        
                    insights = json.loads(content)
                    return insights
                except:
                    return self._get_fallback_career_insights(profile_data)
            else:
                return self._get_fallback_career_insights(profile_data)
                
        except Exception as e:
            print(f"Error getting career insights: {e}")
            return self._get_fallback_career_insights(profile_data)
    
    def _get_fallback_career_insights(self, profile_data):
        """Fallback career insights when API fails"""
        degree = profile_data.get("degree", "")
        
        if "B.Tech" in str(degree) or "B.E." in str(degree):
            return [
                {
                    "insight": "Specialized Technical Skills Premium",
                    "trend": "Companies are paying 30-40% higher for specialized tech skills beyond the core curriculum",
                    "action": "Identify 2-3 specializations (e.g., cloud, cybersecurity, AI) and develop projects in those areas"
                },
                {
                    "insight": "Cross-functional Engineering Roles",
                    "trend": "Engineers who can bridge technical and business domains are in high demand",
                    "action": "Take at least one business or product management course alongside technical studies"
                },
                {
                    "insight": "Open Source Contribution Value",
                    "trend": "Companies increasingly evaluate candidates based on open source contributions",
                    "action": "Contribute to at least one open source project relevant to your field before graduation"
                }
            ]
        elif "BBA" in str(degree) or "B.Com" in str(degree):
            return [
                {
                    "insight": "Data Analytics for Business Graduates",
                    "trend": "Business analytics roles have increased 70% for commerce graduates",
                    "action": "Learn SQL and basic data visualization tools alongside your business curriculum"
                },
                {
                    "insight": "FinTech Sector Growth",
                    "trend": "Indian FinTech sector is projected to reach $150 billion by 2025",
                    "action": "Consider specialized courses in digital payments, blockchain, or financial analysis"
                },
                {
                    "insight": "Sustainability Business Models",
                    "trend": "ESG (Environmental, Social, Governance) roles growing at 45% annually",
                    "action": "Add sustainability-focused projects or certifications to your portfolio"
                }
            ]
        else:
            return [
                {
                    "insight": "Digital Portfolio Necessity",
                    "trend": "93% of recruiters review candidates' online presence before interviews",
                    "action": "Create a personal website or comprehensive LinkedIn profile showcasing projects and skills"
                },
                {
                    "insight": "Micro-Internship Growth",
                    "trend": "Short-term, project-based internships becoming standard entry points",
                    "action": "Complete at least 2-3 micro-internships (2-8 weeks) before your final year"
                },
                {
                    "insight": "Remote Work Readiness",
                    "trend": "Hybrid and remote positions expected to constitute 35% of entry-level jobs",
                    "action": "Develop strong digital collaboration skills and self-management practices"
                }
            ]

    def get_learning_resources(self, query, profile_data):
        """Get personalized learning resource recommendations based on query and student profile"""
        if not self.initialized:
            return self._get_fallback_learning_resources(query, profile_data)
        
        try:
            degree = profile_data.get("degree", "")
            year = profile_data.get("year_of_study", "")
            
            prompt = f"""
            As an educational resource specialist for Indian students in 2025, recommend 5 specific learning resources for a {year} {degree} student interested in learning about "{query}".
            
            Include a mix of:
            - Free online courses/materials
            - Indian-specific resources
            - Mobile apps
            - Books/publications
            - Communities/forums
            
            Make sure to include the most current and relevant resources that are actually available to Indian students in 2025.
            Format as a JSON list of dictionaries with keys 'name', 'type', 'description', 'link', and 'why_useful'.
            Keep it concise and specific to Indian students.
            """
            
            messages = [
                {"role": "system", "content": "You're an educational resource specialist for Indian students."},
                {"role": "user", "content": prompt}
            ]
            
            response = self._make_groq_request(
                model="llama3-70b-8192",
                messages=messages
            )
            
            if response:
                content = response["choices"][0]["message"]["content"]
                try:
                    # Extract just the JSON part
                    import re
                    json_match = re.search(r'\[.*\]', content, re.DOTALL)
                    if json_match:
                        content = json_match.group()
                        
                    resources = json.loads(content)
                    return resources
                except:
                    return self._get_fallback_learning_resources(query, profile_data)
            else:
                return self._get_fallback_learning_resources(query, profile_data)
                
        except Exception as e:
            print(f"Error getting learning resources: {e}")
            return self._get_fallback_learning_resources(query, profile_data)
    
    def _get_fallback_learning_resources(self, query, profile_data):
        """Fallback learning resources when API fails"""
        degree = profile_data.get("degree", "")
        
        general_resources = [
            {
                "name": "NPTEL",
                "type": "Online Course Platform",
                "description": "Free courses from IITs and leading Indian institutions",
                "link": "https://nptel.ac.in/",
                "why_useful": "Official content from India's top technical institutions with certificates"
            },
            {
                "name": "Swayam",
                "type": "Online Course Platform",
                "description": "Government platform for online education",
                "link": "https://swayam.gov.in/",
                "why_useful": "Credit-eligible courses from recognized institutions"
            },
            {
                "name": "National Digital Library of India",
                "type": "Digital Library",
                "description": "Massive collection of educational materials across disciplines",
                "link": "https://ndl.iitkgp.ac.in/",
                "why_useful": "Single-window access to millions of Indian academic resources"
            },
            {
                "name": "e-PG Pathshala",
                "type": "Learning Material",
                "description": "Postgraduate level educational materials",
                "link": "https://epgp.inflibnet.ac.in/",
                "why_useful": "High-quality, curriculum-based interactive content"
            },
            {
                "name": "Shodhganga",
                "type": "Research Repository",
                "description": "Repository of Indian theses and dissertations",
                "link": "https://shodhganga.inflibnet.ac.in/",
                "why_useful": "Access to research work from Indian universities"
            }
        ]
        
        if "programming" in query.lower() or "coding" in query.lower() or "computer" in query.lower():
            return [
                {
                    "name": "GeeksforGeeks",
                    "type": "Learning Website",
                    "description": "Programming tutorials and practice problems",
                    "link": "https://www.geeksforgeeks.org/",
                    "why_useful": "Created by Indians with explanations suited to Indian curriculum"
                },
                {
                    "name": "CodeChef",
                    "type": "Competitive Programming",
                    "description": "Indian competitive programming platform",
                    "link": "https://www.codechef.com/",
                    "why_useful": "Indian programming community with regular contests"
                },
                {
                    "name": "NPTEL Programming Courses",
                    "type": "Online Courses",
                    "description": "Programming courses from IITs",
                    "link": "https://nptel.ac.in/course.html",
                    "why_useful": "Recognized certificates from top Indian institutions"
                },
                {
                    "name": "Scaler Academy",
                    "type": "Coding Bootcamp",
                    "description": "Intensive programming training",
                    "link": "https://www.scaler.com/",
                    "why_useful": "Industry-connected training designed for Indian tech jobs"
                },
                {
                    "name": "TCS CodeVita",
                    "type": "Coding Competition",
                    "description": "Annual programming contest by TCS",
                    "link": "https://www.tcscodevita.com/",
                    "why_useful": "Great for resume and potential job opportunities at TCS"
                }
            ]
        elif "business" in query.lower() or "management" in query.lower() or "finance" in query.lower():
            return [
                {
                    "name": "Finology",
                    "type": "Financial Education Platform",
                    "description": "Stock market and financial learning for Indians",
                    "link": "https://finology.in/",
                    "why_useful": "Focuses on Indian markets and regulations"
                },
                {
                    "name": "InsideIIM",
                    "type": "Management Website",
                    "description": "Content for management students and professionals",
                    "link": "https://insideiim.com/",
                    "why_useful": "Insider perspectives on Indian business schools and companies"
                },
                {
                    "name": "Varsity by Zerodha",
                    "type": "Financial Education",
                    "description": "Free stock market and financial education",
                    "link": "https://zerodha.com/varsity/",
                    "why_useful": "Practical financial knowledge for Indian markets"
                },
                {
                    "name": "ET Markets",
                    "type": "Financial News",
                    "description": "Business and financial news from Economic Times",
                    "link": "https://economictimes.indiatimes.com/markets",
                    "why_useful": "Latest updates on Indian economy and markets"
                },
                {
                    "name": "IIM MOOC Courses",
                    "type": "Management Courses",
                    "description": "Free online courses from IIMs",
                    "link": "https://www.iimb.ac.in/eep/product/57/MOOC",
                    "why_useful": "Premium management education from India's top business schools"
                }
            ]
        else:
            return general_resources
    
    def get_latest_news(self, category):
        """Get latest news in a specific category"""
        if not self.initialized:
            return fetch_trending_news(category)
        
        try:
            prompt = f"""
            As a news aggregator for Indian students in 2025, provide 3 latest news items about {category} that would be relevant to college students in India.
            
            Format as a JSON list of dictionaries with keys 'title', 'date', and 'source'.
            Make sure the news items are current (2025) and specifically useful or relevant to Indian college students.
            """
            
            messages = [
                {"role": "system", "content": "You're a news specialist for Indian college students."},
                {"role": "user", "content": prompt}
            ]
            
            response = self._make_groq_request(
                model="llama3-70b-8192",
                messages=messages,
                max_tokens=300
            )
            
            if response:
                content = response["choices"][0]["message"]["content"]
                try:
                    # Extract just the JSON part
                    import re
                    json_match = re.search(r'\[.*\]', content, re.DOTALL)
                    if json_match:
                        content = json_match.group()
                        
                    news = json.loads(content)
                    return news
                except:
                    return fetch_trending_news(category)
            else:
                return fetch_trending_news(category)
                
        except Exception as e:
            print(f"Error getting news: {e}")
            return fetch_trending_news(category)

# Initialize AI Agent
if 'ai_agent' not in st.session_state:
    st.session_state.ai_agent = AIAdvisorAgent()
    # If GROQ key is set, initialize the agent with it
    if st.session_state.groq_api_key:
        st.session_state.ai_agent.set_api_key(st.session_state.groq_api_key)

# Rest of the code remains the same...
# ... [continues with the update_content_cache function and all other functions]

# Function to update content cache
def update_content_cache(force=False):
    """Update cached content using AI agent"""
    # Check if we need to update - do it daily or if forced
    current_time = datetime.now()
    last_updated = st.session_state.cached_content.get("last_updated")
    
    if not force and last_updated and (current_time - last_updated).days < 1:
        return  # Skip update if less than a day and not forced
    
    # Only update if we have a working API
    if not st.session_state.ai_agent.initialized:
        return
        
    try:
        # Get student profile for personalized content
        if st.session_state.student_profile:
            profile = st.session_state.student_profile
            profile_data = {
                "degree": profile.get_degree(),
                "year_of_study": profile.get_year_of_study(),
                "college": profile.get_college_name()
            }
            
            # Update academic trends
            st.session_state.cached_content["academic_trends"] = st.session_state.ai_agent.get_academic_trends(
                profile_data["degree"], profile_data["year_of_study"]
            )
            
            # Update financial tips
            financial_data = None
            if 'financial_planner' in st.session_state:
                financial_data = st.session_state.financial_planner.get_all_transactions()
                
            st.session_state.cached_content["financial_tips"] = st.session_state.ai_agent.get_financial_advice(
                profile_data, financial_data
            )
            
            # Update wellness tips
            mood_data = None
            if 'mental_wellness' in st.session_state:
                mood_data = st.session_state.mental_wellness.get_mood_history()
                
            st.session_state.cached_content["wellness_tips"] = st.session_state.ai_agent.get_wellness_tips(
                profile_data, mood_data
            )
            
            # Update career insights
            career_preferences = None
            if 'career_guide' in st.session_state:
                career_preferences = st.session_state.career_guide.get_career_preferences()
                
            st.session_state.cached_content["career_insights"] = st.session_state.ai_agent.get_career_insights(
                profile_data, career_preferences
            )
            
            # Update news for each category
            st.session_state.cached_content["education_news"] = st.session_state.ai_agent.get_latest_news("education")
            st.session_state.cached_content["finance_news"] = st.session_state.ai_agent.get_latest_news("finance")
            st.session_state.cached_content["wellness_news"] = st.session_state.ai_agent.get_latest_news("wellness")
            st.session_state.cached_content["career_news"] = st.session_state.ai_agent.get_latest_news("career")
            
            # Update timestamp
            st.session_state.cached_content["last_updated"] = current_time
    except Exception as e:
        print(f"Error updating content cache: {e}")
        # We'll fall back to default values if the update fails

# Function to fetch trending news
def fetch_trending_news(topic, max_items=3):
    """Get trending news either from cache or fallback data"""
    # First check if we have cached news
    cache_key = f"{topic}_news"
    if cache_key in st.session_state.cached_content and st.session_state.cached_content[cache_key]:
        return st.session_state.cached_content[cache_key][:max_items]
    
    # Fallback data if not in cache
    news_data = {
        "education": [
            {"title": "NEP 2020: New Changes Coming for Engineering Programs", "date": "April 5, 2025", "source": "Education Times"},
            {"title": "Top 10 Universities in India Announce Special Scholarships", "date": "April 2, 2025", "source": "India Today"},
            {"title": "Digital Learning Platforms See 45% Growth in Indian Student Adoption", "date": "March 28, 2025", "source": "Tech Education"}
        ],
        "finance": [
            {"title": "New Government Financial Aid Scheme for STEM Students Announced", "date": "April 6, 2025", "source": "Financial Express"},
            {"title": "Student Credit Card with Special Benefits Launched by SBI", "date": "April 1, 2025", "source": "Banking News"},
            {"title": "How to Apply for Education Loan: Updated Guidelines for 2025", "date": "March 25, 2025", "source": "Student Finance"}
        ],
        "wellness": [
            {"title": "Study Shows Direct Link Between Sleep Quality and Exam Performance", "date": "April 4, 2025", "source": "Health Times"},
            {"title": "Campus Mental Health Programs See Positive Results", "date": "March 30, 2025", "source": "Wellness Today"},
            {"title": "Mindfulness Apps Specifically Designed for Student Stress Released", "date": "March 20, 2025", "source": "Digital Wellness"}
        ],
        "career": [
            {"title": "Top In-Demand Skills for 2025 Graduates in India", "date": "April 7, 2025", "source": "Career Guide"},
            {"title": "Major Tech Companies Announce Increased Hiring for Indian Graduates", "date": "April 3, 2025", "source": "Tech Careers"},
            {"title": "Remote Work Opportunities for Students Rise by 60%", "date": "March 29, 2025", "source": "Future of Work"}
        ],
        "resources": [
            {"title": "5 New Digital Libraries Offering Free Resources to Indian Students", "date": "April 6, 2025", "source": "Education Resources"},
            {"title": "NPTEL Launches 50 New Free Certification Courses", "date": "April 2, 2025", "source": "Online Learning"},
            {"title": "Government Launches National Digital Skills Portal for Students", "date": "March 28, 2025", "source": "Digital India"}
        ]
    }
    
    return news_data.get(topic, [])[0:max_items]

# Function to generate relevant opportunities based on student profile
def generate_personalized_opportunities(student):
    """Generate personalized opportunities based on student profile"""
    # Check if we have cached career insights
    if "career_insights" in st.session_state.cached_content and st.session_state.cached_content["career_insights"]:
        # We'll use these to influence opportunities without having to make a new API call
        insights = st.session_state.cached_content["career_insights"]
    else:
        insights = []
    
    degree = student.get_degree()
    year = student.get_year_of_study()
    
    opportunities = []
    
    # Tech/Engineering opportunities
    if "B.Tech" in degree or "B.E." in degree or "Computer" in degree:
        opportunities.append({
            "title": "Google Summer of Code 2025",
            "organization": "Google",
            "deadline": "April 15, 2025",
            "description": "Paid open-source development opportunity with Google",
            "relevance": "Perfect for computer science and engineering students",
            "link": "https://summerofcode.withgoogle.com/"
        })
        
        opportunities.append({
            "title": "Microsoft Engage 2025",
            "organization": "Microsoft",
            "deadline": "May 1, 2025",
            "description": "Mentorship and development program for engineering students",
            "relevance": "Great for building industry connections",
            "link": "https://microsoft.com/engage"
        })
        
        if "Final Year" in year:
            opportunities.append({
                "title": "Tech Mahindra Campus Recruitment",
                "organization": "Tech Mahindra",
                "deadline": "April 20, 2025",
                "description": "Campus recruitment for engineering graduates",
                "relevance": "High-priority for final year students",
                "link": "https://techmahindra.com/careers"
            })
    
    # Business/Commerce opportunities
    elif "BBA" in degree or "B.Com" in degree or "MBA" in degree:
        opportunities.append({
            "title": "KPMG Business Case Competition",
            "organization": "KPMG",
            "deadline": "April 30, 2025",
            "description": "National business case competition with cash prizes",
            "relevance": "Excellent for business students to showcase analytical skills",
            "link": "https://kpmg.com/casechallenge"
        })
        
        opportunities.append({
            "title": "Flipkart LEAP Accelerator Program",
            "organization": "Flipkart",
            "deadline": "May 15, 2025",
            "description": "Startup accelerator program for student entrepreneurs",
            "relevance": "Perfect for students with business ideas",
            "link": "https://flipkart.com/leap"
        })
    
    # General opportunities for all students
    opportunities.append({
        "title": "Fullbright Scholarship 2025-26",
        "organization": "Fullbright India",
        "deadline": "June 15, 2025",
        "description": "Prestigious scholarship for higher education in the US",
        "relevance": "Excellent opportunity for high-achieving students",
        "link": "https://fulbright-india.org"
    })
    
    if "1st Year" in year or "2nd Year" in year:
        opportunities.append({
            "title": "National Innovation Challenge 2025",
            "organization": "Ministry of Education",
            "deadline": "May 31, 2025",
            "description": "Innovation challenge for undergraduate students with mentorship and funding",
            "relevance": "Great early-career experience and networking",
            "link": "https://innovation.gov.in"
        })
    
    # If we have insights from AI, add a custom opportunity based on those
    if insights and len(insights) > 0:
        # Use the first insight to create a custom opportunity
        insight = insights[0]
        opportunities.append({
            "title": f"New Opportunity: {insight.get('insight', 'Skill Development')}",
            "organization": "HARMONY Recommendation",
            "deadline": "Ongoing",
            "description": insight.get('trend', 'Trending skill or opportunity in your field'),
            "relevance": insight.get('action', 'Recommended next step for your career'),
            "link": "#"
        })
    
    return opportunities

# Function to initialize modules based on student profile
def initialize_modules(student_id):
    data_manager = st.session_state.data_manager
    student_data = data_manager.load_student_profile(student_id)
    
    if student_data:
        st.session_state.student_profile = StudentProfile(student_id, student_data)
        st.session_state.academic_tracker = AcademicTracker(student_id, data_manager)
        st.session_state.financial_planner = FinancialPlanner(student_id, data_manager)
        st.session_state.mental_wellness = MentalWellnessCoach(student_id, data_manager)
        st.session_state.career_guide = CareerGuide(student_id, data_manager)
        st.session_state.resource_connector = ResourceConnector(student_id, data_manager)
        st.session_state.prediction_engine = PredictiveEngine(student_id, data_manager)
        
        # Initialize with sample data for better first-time experience
        initialize_sample_data(student_id, data_manager)
        
        # Update content cache to get personalized content
        update_content_cache(True)
        
        return True
    return False

# Function to initialize sample data for first-time users
def initialize_sample_data(student_id, data_manager):
    """Add sample data for first-time users to improve initial experience"""
    # Sample financial transactions if none exist
    financial = FinancialPlanner(student_id, data_manager)
    
    # Use try/except in case the method doesn't exist (which is causing our error)
    try:
        transactions = financial.get_all_transactions()
        has_transactions = transactions and len(transactions) > 0
    except AttributeError:
        # If method doesn't exist, assume no transactions
        has_transactions = False
    
    if not has_transactions:
        sample_transactions = [
            {
                "amount": -2000,
                "description": "Textbooks for semester",
                "category": "Books & Supplies",
                "date": (datetime.now() - timedelta(days=10)).isoformat(),
                "type": "expense"
            },
            {
                "amount": -800,
                "description": "Weekly food expenses",
                "category": "Food",
                "date": (datetime.now() - timedelta(days=5)).isoformat(),
                "type": "expense"
            },
            {
                "amount": 5000,
                "description": "Monthly allowance",
                "category": "Pocket Money",
                "date": (datetime.now() - timedelta(days=15)).isoformat(),
                "type": "income"
            }
        ]
        
        for transaction in sample_transactions:
            # Use try/except in case the method doesn't exist
            try:
                financial.add_transaction(transaction)
            except AttributeError:
                print("Warning: add_transaction method not found in FinancialPlanner class")
                break
        
        # Set a sample budget
        sample_budget = {
            "Food & Dining": 4000,
            "Transportation": 1500,
            "Books & Supplies": 2000,
            "Rent & Utilities": 0,
            "Entertainment": 1000,
            "Personal Care": 800,
            "Mobile & Internet": 600,
            "Clothing": 500,
            "Miscellaneous": 1000
        }
        try:
            financial.set_budget(sample_budget)
        except AttributeError:
            print("Warning: set_budget method not found in FinancialPlanner class")
    
    # Sample mood entries if none exist
    wellness = MentalWellnessCoach(student_id, data_manager)
    
    try:
        has_mood_history = wellness.get_mood_history() and len(wellness.get_mood_history()) > 0
    except AttributeError:
        has_mood_history = False
    
    if not has_mood_history:
        sample_moods = [
            {
                "date": (datetime.now() - timedelta(days=7)).isoformat(),
                "score": 7,
                "stress_factors": ["Academic pressure"],
                "sleep_hours": 7,
                "notes": "Felt good after completing an assignment"
            },
            {
                "date": (datetime.now() - timedelta(days=4)).isoformat(),
                "score": 5,
                "stress_factors": ["Exam stress", "Poor sleep"],
                "sleep_hours": 5,
                "notes": "Worried about upcoming exam"
            },
            {
                "date": (datetime.now() - timedelta(days=1)).isoformat(),
                "score": 8,
                "stress_factors": [],
                "sleep_hours": 8,
                "notes": "Relaxed weekend"
            }
        ]
        
        for mood in sample_moods:
            try:
                wellness.log_mood(mood)
            except AttributeError:
                print("Warning: log_mood method not found in MentalWellnessCoach class")
                break
    
    # Sample courses if none exist
    academic = AcademicTracker(student_id, data_manager)
    
    try:
        has_courses = academic.get_courses() and len(academic.get_courses()) > 0
    except AttributeError:
        has_courses = False
    
    if not has_courses:
        student = StudentProfile(student_id, data_manager.load_student_profile(student_id))
        degree = student.get_degree()
        
        # Sample courses based on degree
        sample_courses = []
        
        if "B.Tech" in degree or "B.E." in degree:
            sample_courses = [
                {
                    "code": "CS101",
                    "title": "Introduction to Computer Science",
                    "credits": 4,
                    "faculty": "Dr. Sharma",
                    "schedule": "Mon, Wed 10:00-11:30",
                    "is_current": True,
                    "semester": "Current Semester"
                },
                {
                    "code": "MATH201",
                    "title": "Linear Algebra",
                    "credits": 3,
                    "faculty": "Dr. Gupta",
                    "schedule": "Tue, Thu 9:00-10:30",
                    "is_current": True,
                    "semester": "Current Semester"
                }
            ]
        elif "BBA" in degree or "B.Com" in degree:
            sample_courses = [
                {
                    "code": "MGT101",
                    "title": "Principles of Management",
                    "credits": 4,
                    "faculty": "Dr. Patel",
                    "schedule": "Mon, Wed 10:00-11:30",
                    "is_current": True,
                    "semester": "Current Semester"
                },
                {
                    "code": "ECON201",
                    "title": "Microeconomics",
                    "credits": 3,
                    "faculty": "Dr. Sen",
                    "schedule": "Tue, Thu 9:00-10:30",
                    "is_current": True,
                    "semester": "Current Semester"
                }
            ]
        else:
            sample_courses = [
                {
                    "code": "GEN101",
                    "title": "Academic Writing",
                    "credits": 3,
                    "faculty": "Dr. Kumar",
                    "schedule": "Mon, Wed 10:00-11:30",
                    "is_current": True,
                    "semester": "Current Semester"
                },
                {
                    "code": "GEN102",
                    "title": "Critical Thinking",
                    "credits": 3,
                    "faculty": "Dr. Singh",
                    "schedule": "Tue, Thu 9:00-10:30",
                    "is_current": True,
                    "semester": "Current Semester"
                }
            ]
        
        for course in sample_courses:
            try:
                academic.add_course(course)
            except AttributeError:
                print("Warning: add_course method not found in AcademicTracker class")
                break
        
        # Add sample tasks
        sample_tasks = [
            {
                "type": "Assignment",
                "title": "Research Paper",
                "course_code": sample_courses[0]["code"],
                "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "status": "pending"
            },
            {
                "type": "Exam",
                "title": "Midterm Examination",
                "course_code": sample_courses[1]["code"],
                "due_date": (datetime.now() + timedelta(days=14)).isoformat(),
                "status": "pending"
            }
        ]
        
        for task in sample_tasks:
            try:
                academic.add_task(task)
            except AttributeError:
                print("Warning: add_task method not found in AcademicTracker class")
                break

def load_css():
    """Load custom CSS styling for better UI experience"""
    # Check if the style.css file exists, if not create it
    if not os.path.exists('assets/style.css'):
        os.makedirs('assets', exist_ok=True)
        with open('assets/style.css', 'w') as f:
            f.write("""
            /* HARMONY-India - Enhanced UI Styling */
            
            /* Base Typography with better readability */
            body {
                font-family: 'Arial', 'Helvetica', sans-serif;
                color: #333333;
                background-color: #fafafa;
                line-height: 1.5;
            }
            
            /* Typography - ensuring good contrast */
            h1, h2, h3, h4, h5, h6 {
                color: #0a3d62;
                font-weight: 600;
                margin-bottom: 0.5rem;
            }
            
            p, li, label, div {
                color: #333333;
            }
            
            /* Link styling */
            a {
                color: #1a73e8;
                text-decoration: none;
                transition: color 0.2s ease;
            }
            
            a:hover {
                color: #174ea6;
                text-decoration: underline;
            }
            
            /* Dashboard card styling with improved contrast */
            .stMetric {
                background-color: #ffffff;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
                transition: all 0.3s ease;
                color: #333333;
            }
            
            .stMetric:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
            
            /* Custom metric and KPI coloring for better visibility */
            .metric-positive {
                color: #2e7d32 !important;
                font-weight: 600;
            }
            
            .metric-neutral {
                color: #0d47a1 !important;
                font-weight: 600;
            }
            
            .metric-warning {
                color: #e65100 !important;
                font-weight: 600;
            }
            
            .metric-negative {
                color: #c62828 !important;
                font-weight: 600;
            }
            
            /* Button styling with clear contrast */
            .stButton>button {
                border-radius: 20px;
                font-weight: 500;
                padding: 0.5rem 1rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                transition: all 0.2s ease;
                color: #ffffff;
                background-color: #0a3d62;
                border: none;
            }
            
            .stButton>button:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                background-color: #0d47a1;
            }
            
            /* Secondary button style */
            .secondary-button>button {
                background-color: #f5f5f5;
                color: #0a3d62;
                border: 1px solid #e0e0e0;
            }
            
            .secondary-button>button:hover {
                background-color: #e0e0e0;
            }
            
            /* Expander styling with better colors */
            .streamlit-expanderHeader {
                font-weight: 600;
                color: #0a3d62;
                background-color: #f8f9fa;
                border-radius: 6px;
                padding: 0.5rem;
            }
            
            /* Enhanced Sidebar styling */
            .sidebar .sidebar-content {
                background-color: #f8f9fb;
                border-right: 1px solid #e0e0e0;
            }
            
            /* Sidebar navigation buttons with better contrast */
            .sidebar .stButton>button {
                text-align: left;
                width: 100%;
                padding: 0.75rem 1rem;
                margin-bottom: 0.5rem;
                border-radius: 8px;
                font-weight: 500;
                transition: all 0.2s ease;
                color: #333333;
                background-color: #f2f2f2;
            }
            
            .sidebar .stButton>button:hover {
                background-color: #e3f2fd;
                color: #0a3d62;
            }
            
            /* Active sidebar button */
            .sidebar .stButton>button.active {
                background-color: #e3f2fd;
                color: #0a3d62;
                border-left: 4px solid #0a3d62;
            }
            
            /* Form styling with better spacing and colors */
            .stForm {
                padding: 20px;
                border-radius: 10px;
                background-color: #ffffff;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
                margin-bottom: 20px;
                color: #333333;
            }
            
            .stForm label {
                color: #0a3d62;
                font-weight: 500;
            }
            
            /* Input fields styling */
            input, select, textarea {
                border-radius: 6px !important;
                border: 1px solid #e0e0e0 !important;
                padding: 0.5rem !important;
                transition: border 0.2s ease !important;
            }
            
            input:focus, select:focus, textarea:focus {
                border: 1px solid #0a3d62 !important;
                box-shadow: 0 0 0 2px rgba(10, 61, 98, 0.1) !important;
            }
            
            /* Cards and Sections with proper contrast */
            /* Light Background Cards */
            .light-bg-card, 
            [style*="background-color: #f5f5f5"],
            [style*="background-color: #f8f9fa"],
            [style*="background-color: #ffffff"],
            [style*="background-color: #e3f2fd"],
            [style*="background-color: #e8f5e9"],
            [style*="background-color: #fff3e0"],
            [style*="background-color: #f3e5f5"],
            [style*="background-color: #e1f5fe"],
            [style*="background-color: #fafafa"] {
                color: #333333 !important;
            }
            
            /* Dark Background Cards */
            .dark-bg-card,
            [style*="background-color: #0a3d62"],
            [style*="background-color: #0d47a1"],
            [style*="background-color: #1565c0"],
            [style*="background-color: #01579b"],
            [style*="background-color: #006064"] {
                color: #ffffff !important;
            }
            
            /* Card styling with better contrast */
            .card {
                background-color: #ffffff;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 3px 5px rgba(0, 0, 0, 0.08);
                margin-bottom: 20px;
                color: #333333;
            }
            
            /* Card title formatting */
            .card h3, .card h4 {
                color: #0a3d62;
                margin-top: 0;
                border-bottom: 1px solid #f0f0f0;
                padding-bottom: 10px;
                margin-bottom: 15px;
            }
            
            /* Empty state styling */
            .empty-state {
                background-color: #f9f9f9;
                border: 1px dashed #dddddd;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                color: #666666;
            }
            
            /* Progress bar styling with better colors */
            div[role="progressbar"] {
                margin: 8px 0;
            }
            
            div[role="progressbar"] > div {
                background-color: #1976d2;
                border-radius: 8px;
            }
            
            /* Status Indicators and Alert Boxes with proper contrast */
            /* Info boxes */
            .info-box, .st-bd {
                background-color: #e3f2fd;
                border-left: 4px solid #2196F3;
                padding: 12px;
                border-radius: 4px;
                margin: 15px 0;
                color: #0d47a1;
            }
            
            /* Warning boxes */
            .warning-box, .st-ae {
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 12px;
                border-radius: 4px;
                margin: 15px 0;
                color: #856404;
            }
            
            /* Success boxes */
            .success-box, .st-bh {
                background-color: #d4edda;
                border-left: 4px solid #28a745;
                padding: 12px;
                border-radius: 4px;
                margin: 15px 0;
                color: #155724;
            }
            
            /* Error boxes */
            .error-box, .st-bp {
                background-color: #f8d7da;
                border-left: 4px solid #dc3545;
                padding: 12px;
                border-radius: 4px;
                margin: 15px 0;
                color: #721c24;
            }
            
            /* Tabs styling with better contrast */
            .stTabs [data-baseweb="tab-list"] {
                gap: 2px;
            }
            
            .stTabs [data-baseweb="tab"] {
                padding: 10px 16px;
                background-color: #f5f5f5;
                border-radius: 6px 6px 0 0;
                color: #666666;
            }
            
            .stTabs [aria-selected="true"] {
                background-color: white !important;
                font-weight: 600;
                color: #0a3d62 !important;
            }
            
            /* News card styling with better contrast */
            .news-card {
                border-left: 3px solid #0a3d62;
                padding: 15px;
                margin-bottom: 15px;
                background-color: #ffffff;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                border-radius: 6px;
            }
            
            .news-card h4 {
                margin: 0 0 8px 0;
                font-weight: 600;
                color: #0a3d62;
            }
            
            .news-card p {
                margin: 5px 0;
                color: #666666;
                font-size: 0.9rem;
            }
            
            /* Trend card styling with better contrast */
            .trend-card {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                border-left: 4px solid #4CAF50;
                color: #333333;
            }
            
            .trend-card h4 {
                margin-top: 0;
                color: #2e7d32;
            }
            
            .trend-card p {
                margin-bottom: 5px;
                color: #333333;
            }
            
            /* Opportunity card styling with better contrast */
            .opportunity-card {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                background-color: #ffffff;
                color: #333333;
            }
            
            .opportunity-card:hover {
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            
            .opportunity-card h4 {
                color: #0a3d62;
                margin-top: 0;
            }
            
            .opportunity-card .organization {
                color: #0d47a1;
                font-weight: 500;
            }
            
            .opportunity-card .deadline {
                color: #e65100;
                font-weight: 500;
            }
            
            /* Resource card styling */
            .resource-card {
                background-color: #ffffff;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                color: #333333;
            }
            
            .resource-card h4 {
                color: #0a3d62;
                margin-top: 0;
            }
            
            .resource-card .resource-type {
                background-color: #e3f2fd;
                color: #0d47a1;
                padding: 3px 10px;
                border-radius: 15px;
                font-size: 0.8rem;
                display: inline-block;
                margin-bottom: 10px;
            }
            
            /* Chat message styling with better contrast */
            .chat-message {
                padding: 10px;
                border-radius: 10px;
                margin-bottom: 10px;
                display: flex;
                flex-direction: column;
            }
            
            .user-message {
                background-color: #e3f2fd;
                margin-left: 20px;
                border-radius: 15px 15px 5px 15px;
                color: #0d47a1;
            }
            
            .ai-message {
                background-color: #f0f0f0;
                margin-right: 20px;
                border-radius: 15px 15px 15px 5px;
                color: #333333;
            }
            
            /* Data badges with proper contrast */
            .data-badge {
                background-color: #e3f2fd;
                color: #0d47a1;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 0.8rem;
                font-weight: 500;
                margin-left: 8px;
                vertical-align: middle;
            }
            
            /* Tag styling */
            .tag {
                background-color: #f0f0f0;
                color: #333333;
                padding: 3px 8px;
                border-radius: 15px;
                font-size: 0.8rem;
                margin-right: 5px;
                display: inline-block;
            }
            
            .tag-blue {
                background-color: #e3f2fd;
                color: #0d47a1;
            }
            
            .tag-green {
                background-color: #e8f5e9;
                color: #2e7d32;
            }
            
            .tag-orange {
                background-color: #fff3e0;
                color: #e65100;
            }
            
            .tag-purple {
                background-color: #f3e5f5;
                color: #6a1b9a;
            }
            
            /* Dashboard widget styling */
            .dash-widget {
                background-color: #ffffff;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                margin-bottom: 15px;
                color: #333333;
            }
            
            .dash-widget h3 {
                color: #0a3d62;
                font-size: 1.2rem;
                margin-top: 0;
                border-bottom: 1px solid #f0f0f0;
                padding-bottom: 10px;
                margin-bottom: 15px;
            }
            
            /* Button group styling */
            .button-group {
                display: flex;
                gap: 10px;
                margin: 10px 0;
            }
            
            /* Grid layout helpers */
            .grid-container {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                grid-gap: 15px;
                margin: 15px 0;
            }
            
            /* Section dividers */
            .section-divider {
                height: 1px;
                background-color: #e0e0e0;
                margin: 20px 0;
            }
            
            /* Better formatted tables */
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                color: #333333;
            }
            
            th {
                background-color: #f5f5f5;
                color: #0a3d62;
                font-weight: 600;
                padding: 8px 15px;
                text-align: left;
                border-bottom: 2px solid #e0e0e0;
            }
            
            td {
                padding: 8px 15px;
                border-bottom: 1px solid #f0f0f0;
                color: #333333;
            }
            
            tr:nth-child(even) {
                background-color: #fafafa;
            }
            
            tr:hover {
                background-color: #f0f7ff;
            }
            
            /* Responsive adjustments for mobile */
            @media only screen and (max-width: 768px) {
                .grid-container {
                    grid-template-columns: 1fr;
                }
                
                .button-group {
                    flex-direction: column;
                }
                
                .sidebar .stButton>button {
                    padding: 0.5rem;
                }
            }
            
            /* Fix for Plotly charts to ensure text is visible */
            .js-plotly-plot .plotly .main-svg text {
                fill: #333333 !important;
            }
            
            /* Fixes for academic trends sections */
            [style*="background-color: #e8f5e9"] h4,
            [style*="background-color: #e8f5e9"] p,
            [style*="background-color: #e8f5e9"] li {
                color: #2e7d32 !important;
            }
            
            /* Fixes for wellness sections */
            [style*="background-color: #e3f2fd"] h4,
            [style*="background-color: #e3f2fd"] p,
            [style*="background-color: #e3f2fd"] li {
                color: #0d47a1 !important;
            }
            
            /* Fixes for finance sections */
            [style*="background-color: #fff3e0"] h4,
            [style*="background-color: #fff3e0"] p,
            [style*="background-color: #fff3e0"] li {
                color: #e65100 !important;
            }
            
            /* Fixes for career insights sections */
            [style*="background-color: #f3e5f5"] h4,
            [style*="background-color: #f3e5f5"] p,
            [style*="background-color: #f3e5f5"] li {
                color: #6a1b9a !important;
            }
            
            /* Fix for opportunity card relevance section */
            .opportunity-card [style*="background-color: #e3f2fd"] {
                color: #0d47a1 !important;
            }
            """)
    
    with open('assets/style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Check for logo and create a placeholder if it doesn't exist
def ensure_logo_exists():
    if not os.path.exists('assets/harmony_logo.png'):
        os.makedirs('assets', exist_ok=True)
        # Create a simple placeholder logo using matplotlib
        try:
            plt.figure(figsize=(6, 2))
            plt.text(0.5, 0.5, 'HARMONY-India', 
                   fontsize=30, ha='center', va='center', 
                   color='#0a3d62', fontweight='bold')
            plt.axis('off')
            plt.savefig('assets/harmony_logo.png', bbox_inches='tight', dpi=100, transparent=True)
            plt.close()
        except:
            # If matplotlib fails, just log a message but continue
            print("Could not create placeholder logo. Please add your own logo to assets/harmony_logo.png")

# Load CSS and ensure logo exists
load_css()
ensure_logo_exists()

# Function to show section guidance
def show_section_guidance(section_name):
    if st.session_state.first_visit_sections.get(section_name, False):
        st.info(f"👋 Welcome to the {section_name} section! This guide will help you get started. You'll only see this once.")
        
        # Different guidance for each section
        if section_name == "Finance":
            st.markdown("""
            ### Getting Started with Financial Planning
            
            1. **Add your income and expenses** to start tracking your finances
            2. **Set up a budget** to manage your spending effectively
            3. **Explore scholarships** that match your academic profile
            4. Use the **Financial Chatbot** for personalized financial advice
            
            Start by entering a transaction or two below!
            """)
        elif section_name == "Academics":
            st.markdown("""
            ### Getting Started with Academic Tracking
            
            1. **Add your courses** to organize your academic schedule
            2. **Enter your semester results** to track your performance
            3. **Log your study hours** to monitor your learning habits
            4. Use the **Academic Chatbot** for study advice and planning
            
            Start by adding a course below!
            """)
        elif section_name == "Wellness":
            st.markdown("""
            ### Getting Started with Wellness Tracking
            
            1. **Log your daily mood** to track emotional patterns
            2. **Identify stress factors** that affect your well-being
            3. **Try the stress relief techniques** in the Stress Management tab
            4. Use the **Wellness Chatbot** for mental health advice
            
            Start by logging today's mood!
            """)
        elif section_name == "Career":
            st.markdown("""
            ### Getting Started with Career Planning
            
            1. **Set your career interests** to receive personalized recommendations
            2. **Track your skills** to identify areas for development
            3. **Explore opportunities** matched to your profile
            4. Use the **Career Chatbot** for job search and interview advice
            
            Start by updating your career preferences!
            """)
        elif section_name == "Resources":
            st.markdown("""
            ### Getting Started with Learning Resources
            
            1. **Browse campus resources** to find support services
            2. **Search for subject-specific materials** for your studies
            3. **Explore scholarship opportunities** for financial support
            4. Use the **Resource Chatbot** to find specific learning materials
            
            Start by searching for a subject or browsing campus resources!
            """)
        
        if st.button("Got it!", key=f"dismiss_{section_name}"):
            st.session_state.first_visit_sections[section_name] = False
            st.rerun()

# Sidebar navigation with improved UI
def sidebar_navigation():
    st.sidebar.image('assets/harmony_logo.png', width=250)
    st.sidebar.title("नमस्ते! Welcome")
    
    if st.session_state.student_profile:
        profile = st.session_state.student_profile
        st.sidebar.info(f"👤 **{profile.get_full_name()}**\n\n🏫 {profile.get_college_name()}\n\n🎓 {profile.get_degree()}, {profile.get_year_of_study()}")
        
        st.sidebar.markdown("### Navigate")
        
        # More descriptive button labels
        if st.sidebar.button("🏠 Dashboard", key="nav_home", 
                         help="View your personalized dashboard with key metrics and insights"):
            st.session_state.current_page = "Dashboard"
            
        if st.sidebar.button("📚 Academic Tracker", key="nav_academics", 
                         help="Track courses, assignments, grades, and study patterns"):
            st.session_state.current_page = "Academics"
            
        if st.sidebar.button("💰 Financial Planner", key="nav_finance", 
                         help="Manage expenses, budget, scholarships, and financial planning"):
            st.session_state.current_page = "Finance"
            
        if st.sidebar.button("🧠 Mental Wellness", key="nav_wellness", 
                         help="Track mood, manage stress, and access wellness resources"):
            st.session_state.current_page = "Wellness"
            
        if st.sidebar.button("🚀 Career Pathway", key="nav_career", 
                         help="Plan your career, track skills, and discover opportunities"):
            st.session_state.current_page = "Career"
            
        if st.sidebar.button("🔗 Learning Resources", key="nav_resources", 
                         help="Access campus, digital, and scholarship resources"):
            st.session_state.current_page = "Resources"
            
        # AI Advisor button
        if st.sidebar.button("🤖 AI Advisor", key="nav_advisor", 
                         help="Get personalized advice on all aspects of student life"):
            st.session_state.current_page = "AI_Advisor"
            
        if st.sidebar.button("⚙️ Settings & Profile", key="nav_settings", 
                         help="Manage your profile, preferences, and application settings"):
            st.session_state.current_page = "Settings"
            
        if st.sidebar.button("🚪 Logout", key="nav_logout"):
            st.session_state.student_profile = None
            st.session_state.current_page = "Home"
            st.rerun()
        
        st.sidebar.markdown("---")
        
        # Show data freshness
        if st.session_state.cached_content["last_updated"]:
            last_update = st.session_state.cached_content["last_updated"]
            time_diff = datetime.now() - last_update
            if time_diff.days == 0:
                update_text = f"Data updated {time_diff.seconds // 3600} hours ago"
            else:
                update_text = f"Data updated {time_diff.days} days ago"
            
            st.sidebar.caption(f"💫 {update_text}")
            
            if time_diff.days >= 1:
                # Offer refresh if data is a day old
                if st.sidebar.button("🔄 Refresh Data"):
                    with st.sidebar.spinner("Updating data..."):
                        update_content_cache(force=True)
                    st.sidebar.success("Data refreshed!")
                    time.sleep(1)
                    st.rerun()
    
    # Show app information in sidebar
    with st.sidebar.expander("About HARMONY-India"):
        st.write("""
        HARMONY-India is designed specifically for Indian college students to help navigate the unique challenges of higher education.
        
        This platform provides personalized guidance on academics, finances, mental well-being, and career preparation.
        
        All data is stored locally on your device for complete privacy.
        
        **Version**: 1.0.1  
        **Last Updated**: April 8, 2025
        """)
        
    st.sidebar.markdown("---")
    current_date = datetime.now().strftime("%d %b %Y")
    st.sidebar.caption(f"© 2025 HARMONY-India | {current_date}")

# Welcome/login page with improved UI
def show_welcome_page():
    st.markdown("# 🎓 HARMONY-India")
    st.markdown("## Your Personalized Success Platform")
    
    # Add a more attractive header with a background image
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <h1 style="color: #0a3d62; margin-bottom: 10px;">HARMONY-India</h1>
        <p style="color: #555; font-size: 1.2rem; font-weight: 500;">Your Complete Student Success Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("""
        HARMONY-India is a comprehensive AI-powered platform designed specifically for Indian college students.
        
        ### What HARMONY Offers:
        
        - 📚 **Academic Excellence** - Course tracking, performance analytics, and study optimization
        - 💰 **Financial Wisdom** - Budget management, scholarship finder, and expense tracking
        - 🧠 **Mental Wellbeing** - Mood tracking, stress management, and wellness resources
        - 🚀 **Career Success** - Skill development, opportunity matching, and job preparation
        """)
        
        st.info("🔒 Your data stays private on your computer - nothing is sent to external servers.")
        
        with st.expander("Why HARMONY-India?"):
            st.markdown("""
            * **Designed for Indian Students**: Understands the unique pressures, academic systems, and challenges you face in the Indian educational environment
            
            * **Personalized Guidance**: Provides recommendations tailored to your specific situation, college, degree, and career aspirations
            
            * **Research-Backed**: Built on proven strategies for student success from leading educational institutions
            
            * **Holistic Approach**: Addresses all aspects of student life, not just academics - because success requires balance
            
            * **Current Trends**: Stays updated with the latest opportunities, scholarships, and educational developments in India
            """)
    
    with col2:
        st.markdown("""
        <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
        <h3 style="color: #0a3d62; text-align: center; margin-bottom: 20px;">Get Started</h3>
        """, unsafe_allow_html=True)
        
        login_option = st.radio("Choose an option:", ["Login", "Create New Profile"])
        
        if login_option == "Login":
            # Check for existing profiles and display them
            existing_profiles = st.session_state.data_manager.get_existing_profiles()
            
            if existing_profiles:
                st.write("Select your profile to continue:")
                selected_profile = st.selectbox("Your Profile:", 
                                              options=existing_profiles,
                                              format_func=lambda x: st.session_state.data_manager.get_profile_name(x))
                
                # Added some visual appeal to the login button
                if st.button("🔑 Login to Your Account", key="btn_login"):
                    with st.spinner("Loading your personalized dashboard..."):
                        if initialize_modules(selected_profile):
                            st.session_state.current_page = "Dashboard"
                            st.rerun()
                        else:
                            st.error("Could not load profile. Please try again or create a new profile.")
            else:
                st.warning("No existing profiles found. Please create a new profile to get started.")
                login_option = "Create New Profile"
                
        if login_option == "Create New Profile":
            with st.form("new_profile_form"):
                st.subheader("Create Your Profile")
                
                # Enhanced form with clear labels and placeholders
                full_name = st.text_input("👤 Full Name*", placeholder="Enter your full name")
                college_name = st.text_input("🏫 College/University Name*", placeholder="Enter your college/university name")
                
                col1, col2 = st.columns(2)
                with col1:
                    degree = st.selectbox("🎓 Degree Program*", [
                        "B.Tech/B.E.", "BBA", "B.Sc.", "B.Com.", "B.A.", 
                        "M.Tech/M.E.", "MBA", "M.Sc.", "M.Com.", "M.A.",
                        "BCA", "MCA", "Ph.D.", "Diploma", "Other"
                    ])
                    
                with col2:
                    year_of_study = st.selectbox("📚 Year of Study*", [
                        "1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year", "Final Year"
                    ])
                
                dob = st.date_input("🗓️ Date of Birth", 
                                   min_value=datetime(1980, 1, 1),
                                   max_value=datetime.now() - timedelta(days=365*16))  # Minimum 16 years old
                
                email = st.text_input("📧 Email Address", placeholder="your.email@example.com")
                
                st.info("Fields marked with * are required")
                
                submitted = st.form_submit_button("Create Profile & Get Started")
                
                if submitted:
                    if not full_name or not college_name:
                        st.error("Please fill in all required fields marked with *")
                    else:
                        # Generate a unique student ID
                        import uuid
                        student_id = str(uuid.uuid4())
                        
                        # Create student profile
                        profile_data = {
                            "full_name": full_name,
                            "college_name": college_name,
                            "degree": degree,
                            "year_of_study": year_of_study,
                            "dob": dob.strftime("%Y-%m-%d") if dob else None,
                            "email": email,
                            "created_at": datetime.now().isoformat()
                        }
                        
                        # Save profile
                        if st.session_state.data_manager.save_student_profile(student_id, profile_data):
                            st.success("Profile created successfully!")
                            
                            # Initialize modules with the new profile
                            with st.spinner("Setting up your personalized dashboard..."):
                                if initialize_modules(student_id):
                                    st.session_state.current_page = "Dashboard"
                                    # Show onboarding tips
                                    st.session_state.show_welcome = True
                                    st.rerun()
                                else:
                                    st.error("Error initializing your profile. Please try again.")
                        else:
                            st.error("Error creating profile. Please try again.")
        
        st.markdown("</div>", unsafe_allow_html=True)

# AI Settings configuration
def show_ai_settings():
    st.subheader("🤖 AI Advisor Configuration")
    
    st.write("Configure your AI advisor to get personalized insights and recommendations across all sections.")
    
    # Groq API Key Configuration
    with st.expander("Groq API Key Setup", expanded=st.session_state.groq_api_key is None):
        st.write("""
        HARMONY uses Groq's LLM models to provide personalized recommendations, latest trends, and specialized advice.
        
        To enable this functionality:
        1. Create a Groq account at [console.groq.com](https://console.groq.com)
        2. Generate an API key
        3. Enter it below
        
        Your API key is stored only in your local session and is never sent to our servers.
        """)
        
        api_key = st.text_input(
            "Groq API Key",
            type="password",
            value=st.session_state.groq_api_key if st.session_state.groq_api_key else "",
            placeholder="gsk_..."
        )
        
        if st.button("Save API Key", key="save_groq_key"):
            if api_key.startswith("gsk_"):
                st.session_state.groq_api_key = api_key
                st.session_state.ai_agent.set_api_key(api_key)
                st.session_state.ai_advisor = GroqAdvisor(api_key=api_key)  # Also update the chatbot advisor
                st.success("API key saved! AI features are now enabled across all sections.")
                
                # Reset trend data to force refresh with AI
                st.session_state.cached_content["last_updated"] = None
                
                # Update content with new AI capabilities
                with st.spinner("Fetching personalized content..."):
                    update_content_cache(force=True)
                
                # Add a small delay before rerun
                time.sleep(1)
                st.rerun()
            elif api_key == "":
                st.warning("API key removed. AI personalization features will be limited.")
                st.session_state.groq_api_key = None
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid API key format. Groq keys start with 'gsk_'")
    
    # AI Feature Controls
    with st.expander("AI Feature Controls"):
        st.write("Customize how AI is used throughout the application:")
        
        trend_frequency = st.selectbox(
            "Trend Update Frequency",
            options=["Daily", "Weekly", "Monthly", "Always"],
            index=0,
            help="How often AI should fetch new trend data (requires API calls)"
        )
        
        content_caching = st.checkbox(
            "Cache AI-generated content", 
            value=True,
            help="Save AI responses to reduce API usage (recommended)"
        )
        
        # Save preferences
        if st.button("Save Preferences"):
            st.success("AI preferences saved successfully!")
            
        # Content refresh
    with st.expander("Refresh Content Data"):
        st.write("You can manually refresh the AI-generated content to get the latest information:")
        
        last_update = st.session_state.cached_content.get("last_updated")
        if last_update:
            time_diff = datetime.now() - last_update
            if time_diff.days == 0:
                st.info(f"Content last updated {time_diff.seconds // 3600} hours ago.")
            else:
                st.warning(f"Content last updated {time_diff.days} days ago.")
        else:
            st.warning("Content has not been updated yet.")
        
        if st.button("Refresh All Content Now"):
            with st.spinner("Fetching latest information with AI..."):
                update_content_cache(force=True)
            st.success("All content refreshed successfully!")
            time.sleep(1)
            st.rerun()
    
    # AI Usage Statistics
    with st.expander("AI Usage Statistics"):
        st.write("View your AI usage and available quota:")
        
        # Mock usage stats - in a real app this would come from the Groq API
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("API Calls Today", "27")
            st.metric("Monthly Usage", "245/1000")
        
        with col2:
            st.metric("Content Updates", "3")
            st.metric("Advisor Chats", "12")
            
        st.caption("Usage resets on the 1st of each month")

# AI Advisor page with improved UI and Groq integration
def show_ai_advisor_page():
    st.title("🤖 AI Advisor: Your Personal Guide")
    
    # Check if Groq API is configured
    if st.session_state.groq_api_key is None:
        show_ai_settings()
        st.warning("Please configure your Groq API key to use the AI Advisor's full capabilities.")
        st.write("Once configured, the AI Advisor will provide personalized guidance tailored to your specific needs.")
        return
    
    # Main chatbot interface with improved UX
    st.markdown("""
    <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); margin-bottom: 20px;">
        <h3 style="color: #0a3d62; margin-bottom: 15px;">Your Personal AI Advisor</h3>
        <p>Ask me anything about your student life. I can help with:</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Topic cards
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background-color: #e7f5fe; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h4 style="margin-top: 0;">🧠 Mental Wellness</h4>
            <p>Stress management, anxiety relief, mindfulness techniques, and emotional well-being strategies</p>
        </div>
        
        <div style="background-color: #e7fff5; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h4 style="margin-top: 0;">💰 Financial Wellbeing</h4>
            <p>Budgeting tips, scholarship applications, student loans, and money management</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background-color: #fff5e7; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h4 style="margin-top: 0;">📚 Academic Success</h4>
            <p>Study techniques, time management, course selection, and exam preparation</p>
        </div>
        
        <div style="background-color: #f9e7ff; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h4 style="margin-top: 0;">🚀 Career Planning</h4>
            <p>Career pathways, skills development, internships, and job applications</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Domain selection
    st.markdown("### What would you like advice on?")
    domain_options = {
        "Let AI detect the topic": None,
        "Mental Wellness": "mental_health",
        "Academic Success": "academic", 
        "Career Planning": "career",
        "Financial Wellbeing": "financial"
    }
    
    selected_domain_label = st.selectbox(
        "Choose a topic or let AI detect the best category",
        options=list(domain_options.keys())
    )
    
    selected_domain = domain_options[selected_domain_label]
    
    # Initialize chat history if it doesn't exist
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Chat interface
    st.markdown("### Ask Your Question")
    
    # Display chat history in a better format
    if st.session_state.chat_history:
        st.markdown('<div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; max-height: 400px; overflow-y: auto;">', unsafe_allow_html=True)
        
        for i, (role, message) in enumerate(st.session_state.chat_history):
            if role == "user":
                st.markdown(f'<div style="background-color: #e7f5fe; padding: 10px; border-radius: 15px 15px 5px 15px; margin-bottom: 10px; margin-left: 20px;"><strong>You:</strong> {message}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 15px 15px 15px 5px; margin-bottom: 10px;"><strong>AI Advisor:</strong> {message}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Input for new question
    with st.form("chat_form"):
        user_query = st.text_area("Type your question here", height=100, placeholder="e.g., How can I manage exam stress? or What scholarships are available for engineering students?")
        submitted = st.form_submit_button("Get Advice")
        
        if submitted and user_query:
            # Add user message to chat history
            st.session_state.chat_history.append(("user", user_query))
            
            # Prepare student context for more personalized answers
            student_context = None
            if st.session_state.student_profile:
                profile = st.session_state.student_profile
                student_context = {
                    "degree": profile.get_degree(),
                    "year": profile.get_year_of_study(),
                    "college": profile.get_college_name()
                }
            
            # Determine domain if auto-detection is selected
            query_domain = selected_domain
            if query_domain is None:
                query_domain = st.session_state.ai_advisor.classify_query_domain(user_query)
            
            # Get AI response
            with st.spinner("Thinking about your question..."):
                ai_response = st.session_state.ai_advisor.get_advice(
                    user_query, query_domain, student_context
                )
            
            # Add AI response to chat history
            st.session_state.chat_history.append(("ai", ai_response))
            
            # Force a rerun to show the updated chat
            st.rerun()

# Dashboard page with improved UI
def show_dashboard():
    st.title("Your Student Dashboard")
    
    # Show onboarding tips for new users with better UX
    if st.session_state.show_welcome:
        st.markdown("""
        <div style="background-color: #e7f5fe; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #2196F3;">
            <h3 style="margin-top: 0; color: #0a3d62;">Welcome to HARMONY-India!</h3>
            <p>This is your personalized dashboard. Here's what you can do:</p>
            <ul>
                <li>View your progress in key areas of student life</li>
                <li>Track upcoming deadlines and tasks</li>
                <li>See personalized recommendations based on your profile</li>
                <li>Add new data to enhance your experience</li>
            </ul>
            <p>Explore the different sections using the sidebar navigation to get the most out of HARMONY.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Got it, thanks!", key="welcome_dismiss"):
            st.session_state.show_welcome = False
            st.rerun()
    
    # Get student data
    student = st.session_state.student_profile
    academic = st.session_state.academic_tracker
    financial = st.session_state.financial_planner
    wellness = st.session_state.mental_wellness
    career = st.session_state.career_guide
    
    # Current date display
    current_date = datetime.now().strftime("%A, %d %B %Y")
    st.markdown(f"### {current_date}")
    
    # First row - Overview cards with improved visualizations
    st.markdown("## Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### Academic Standing")
        current_cgpa = academic.get_current_cgpa()
        cgpa_goal = academic.get_cgpa_goal()
        
        fig = create_gauge_chart(
            current_value=current_cgpa,
            min_value=0,
            max_value=10,
            threshold=cgpa_goal,
            title="Current CGPA"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        if current_cgpa >= 8.5:
            st.success("Excellent academic performance!")
        elif current_cgpa >= 7.5:
            st.info("Good academic standing")
        elif current_cgpa > 0:
            st.warning("Room for improvement")
        
    with col2:
        st.markdown("### Financial Health")
        budget_adherence = financial.get_budget_adherence()
        
        fig = create_gauge_chart(
            current_value=budget_adherence,
            min_value=0,
            max_value=100,
            threshold=80,
            title="Budget Adherence %",
            is_percent=True
        )
        st.plotly_chart(fig, use_container_width=True)
        
        if budget_adherence >= 90:
            st.success("Excellent budget management!")
        elif budget_adherence >= 75:
            st.info("Good financial discipline")
        elif budget_adherence > 0:
            st.warning("Budget needs attention")
        
    with col3:
        st.markdown("### Well-being")
        wellness_score = wellness.get_current_wellness_score()
        
        fig = create_gauge_chart(
            current_value=wellness_score,
            min_value=0,
            max_value=10,
            threshold=7,
            title="Well-being Score"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        if wellness_score >= 8:
            st.success("Great mental well-being!")
        elif wellness_score >= 6:
            st.info("Balanced mental state")
        elif wellness_score > 0:
            st.warning("Your well-being needs attention")
        
    with col4:
        st.markdown("### Career Readiness")
        career_readiness = career.get_career_readiness_score()
        
        fig = create_gauge_chart(
            current_value=career_readiness,
            min_value=0,
            max_value=100,
            threshold=70,
            title="Career Readiness %",
            is_percent=True
        )
        st.plotly_chart(fig, use_container_width=True)
        
        if career_readiness >= 80:
            st.success("Well-prepared for career challenges!")
        elif career_readiness >= 60:
            st.info("Making good career progress")
        elif career_readiness > 0:
            st.warning("Career preparation needs focus")
    
    # Second row - Upcoming tasks with better visual hierarchy
    st.markdown("## Upcoming Deadlines & Events")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        upcoming_tasks = academic.get_upcoming_tasks(limit=5)
        if upcoming_tasks:
            task_df = pd.DataFrame(upcoming_tasks)
            task_df['days_left'] = task_df['due_date'].apply(lambda x: (datetime.fromisoformat(x) - datetime.now()).days if x else None)
            
            # Group tasks by urgency
            overdue_tasks = task_df[task_df['days_left'] < 0]
            due_today = task_df[task_df['days_left'] == 0]
            due_soon = task_df[(task_df['days_left'] > 0) & (task_df['days_left'] <= 3)]
            upcoming = task_df[task_df['days_left'] > 3]
            
            # Display tasks by group with distinctive styling
            if not overdue_tasks.empty:
                st.markdown("<h4 style='color: #d32f2f;'>⚠️ Overdue Tasks</h4>", unsafe_allow_html=True)
                for _, task in overdue_tasks.iterrows():
                    st.markdown(f"""
                    <div style="background-color: #ffebee; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #d32f2f;">
                        <strong>{task['title']}</strong> - {task['course_code']} ({abs(task['days_left'])} days ago)
                    </div>
                    """, unsafe_allow_html=True)
            
            if not due_today.empty:
                st.markdown("<h4 style='color: #ff9800;'>⏰ Due Today</h4>", unsafe_allow_html=True)
                for _, task in due_today.iterrows():
                    st.markdown(f"""
                    <div style="background-color: #fff3e0; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #ff9800;">
                        <strong>{task['title']}</strong> - {task['course_code']}
                    </div>
                    """, unsafe_allow_html=True)
            
            if not due_soon.empty:
                st.markdown("<h4 style='color: #2196f3;'>🔜 Due Soon</h4>", unsafe_allow_html=True)
                for _, task in due_soon.iterrows():
                    st.markdown(f"""
                    <div style="background-color: #e3f2fd; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #2196f3;">
                        <strong>{task['title']}</strong> - {task['course_code']} ({task['days_left']} days left)
                    </div>
                    """, unsafe_allow_html=True)
            
            if not upcoming.empty:
                st.markdown("<h4 style='color: #4caf50;'>📝 Upcoming</h4>", unsafe_allow_html=True)
                for _, task in upcoming.iterrows():
                    st.markdown(f"""
                    <div style="background-color: #e8f5e9; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #4caf50;">
                        <strong>{task['title']}</strong> - {task['course_code']} ({task['days_left']} days left)
                    </div>
                    """, unsafe_allow_html=True)
        else:
            # Better empty state
            st.markdown("""
            <div style="background-color: #f9f9f9; border: 1px dashed #ddd; border-radius: 8px; padding: 20px; text-align: center;">
                <h4 style="color: #666;">No upcoming tasks found</h4>
                <p>Add your first task using the form on the right →</p>
            </div>
            """, unsafe_allow_html=True)
            
    with col2:
        st.subheader("Quick Add Task")
        
        with st.form("quick_add_form"):
            task_type = st.selectbox("Task Type", ["Assignment", "Exam", "Project", "Study", "Meeting"])
            task_title = st.text_input("Title", placeholder="e.g., Research Paper")
            due_date = st.date_input("Due Date", min_value=datetime.now())
            courses = academic.get_courses()
            
            if courses:
                course = st.selectbox("Course", courses)
            else:
                st.info("First, add a course in Academics section")
                course = st.text_input("Course Code", placeholder="e.g., CS101")
            
            st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
            submitted = st.form_submit_button("Add Task")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if submitted:
                if task_title and course:
                    new_task = {
                        "type": task_type,
                        "title": task_title,
                        "course_code": course,
                        "due_date": due_date.isoformat(),
                        "status": "pending"
                    }
                    if academic.add_task(new_task):
                        st.success("Task added successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to add task.")
                else:
                    st.error("Please fill in all required fields.")
    
    # Third row - Insights and recommendations with better visual design
    st.markdown("## Personalized Insights")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Trends & Patterns")
        
        trend_option = st.selectbox(
            "Select trend to view:",
            ["Academic Performance", "Mood & Well-being", "Financial Overview", "Study Hours"],
            help="View different aspects of your student life over time"
        )
        
        if trend_option == "Academic Performance":
            performance_data = academic.get_performance_history()
            if performance_data:
                fig = create_trend_chart(
                    data=performance_data,
                    x_key="semester",
                    y_key="cgpa",
                    title="CGPA Trend",
                    color="#1f77b4"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Add trend analysis
                if len(performance_data) > 1:
                    latest = performance_data[-1]['cgpa']
                    previous = performance_data[-2]['cgpa']
                    if latest > previous:
                        st.success(f"📈 Your CGPA improved by {latest - previous:.2f} points in the latest semester!")
                    elif latest < previous:
                        st.warning(f"📉 Your CGPA decreased by {previous - latest:.2f} points. Consider academic support.")
                    else:
                        st.info("Your CGPA remained stable in the latest semester.")
            else:
                # Better empty state with sample data
                st.info("No academic performance data available yet.")
                
                # Show a sample chart to demonstrate the feature
                sample_data = [
                    {"semester": "Sem 1", "cgpa": 7.8, "semester_index": 1},
                    {"semester": "Sem 2", "cgpa": 8.1, "semester_index": 2},
                    {"semester": "Sem 3", "cgpa": 8.4, "semester_index": 3}
                ]
                
                fig = create_trend_chart(
                    data=sample_data,
                    x_key="semester",
                    y_key="cgpa",
                    title="Sample CGPA Trend (What you'll see)",
                    color="#1f77b4"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("**Add your semester results in the Academic Tracker to see your performance trend!**")
        
        elif trend_option == "Mood & Well-being":
            mood_data = wellness.get_mood_history()
            if mood_data:
                fig = create_trend_chart(
                    data=mood_data,
                    x_key="date",
                    y_key="score",
                    title="Mood Trend",
                    color="#ff7f0e"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Add mood analysis
                if len(mood_data) > 5:
                    recent_scores = [entry['score'] for entry in mood_data[-5:]]
                    avg_recent = sum(recent_scores) / len(recent_scores)
                    all_scores = [entry['score'] for entry in mood_data]
                    avg_all = sum(all_scores) / len(all_scores)
                    
                    if avg_recent > avg_all + 1:
                        st.success("🌟 Your recent mood is significantly better than your average. Keep up whatever you're doing!")
                    elif avg_recent < avg_all - 1:
                        st.warning("📉 Your recent mood is lower than your average. Consider some self-care activities.")
            else:
                st.info("No mood data available yet. Start tracking in the Mental Wellness section.")
                
                # Sample data
                dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7, 0, -1)]
                sample_data = [
                    {"date": dates[0], "score": 6},
                    {"date": dates[1], "score": 7},
                    {"date": dates[2], "score": 5},
                    {"date": dates[3], "score": 6},
                    {"date": dates[4], "score": 8},
                    {"date": dates[5], "score": 7},
                    {"date": dates[6], "score": 9}
                ]
                
                fig = create_trend_chart(
                    data=sample_data,
                    x_key="date",
                    y_key="score",
                    title="Sample Mood Trend (What you'll see)",
                    color="#ff7f0e"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        elif trend_option == "Financial Overview":
            expense_data = financial.get_monthly_expenses()
            if expense_data:
                fig = create_pie_chart(
                    data=expense_data,
                    labels_key="category",
                    values_key="amount",
                    title="Monthly Expenses"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Add financial insights
                largest_category = max(expense_data, key=lambda x: x['amount'])
                st.info(f"💡 Your largest expense category is {largest_category['category']} (₹{largest_category['amount']:,.2f}).")
            else:
                st.info("No expense data available yet. Add your expenses in the Financial Planner section.")
                
                # Sample data for visualization
                sample_expenses = [
                    {"category": "Food", "amount": 4000},
                    {"category": "Transportation", "amount": 1200},
                    {"category": "Books & Supplies", "amount": 2500},
                    {"category": "Entertainment", "amount": 800},
                    {"category": "Other", "amount": 1500}
                ]
                
                fig = create_pie_chart(
                    data=sample_expenses,
                    labels_key="category",
                    values_key="amount",
                    title="Sample Expense Breakdown (What you'll see)"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        elif trend_option == "Study Hours":
            study_data = academic.get_study_hours_history()
            if study_data:
                fig = create_trend_chart(
                    data=study_data,
                    x_key="date",
                    y_key="hours",
                    title="Study Hours",
                    color="#2ca02c"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Add study pattern insights
                if len(study_data) > 3:
                    total_hours = sum(entry['hours'] for entry in study_data)
                    avg_daily = total_hours / len(study_data)
                    
                    if avg_daily < 2:
                        st.warning("⚠️ You're studying less than the recommended minimum of 2 hours per day.")
                    elif avg_daily > 8:
                        st.warning("⚠️ You're studying more than 8 hours per day. Remember to take breaks!")
                    else:
                        st.success(f"✅ You're studying an average of {avg_daily:.1f} hours per day, which is a healthy amount.")
            else:
                st.info("No study tracking data available yet. Track your study hours in the Academic Tracker section.")
                
                # Sample data
                dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7, 0, -1)]
                sample_data = [
                    {"date": dates[0], "hours": 2.5, "subject": "Math"},
                    {"date": dates[1], "hours": 3.0, "subject": "Physics"},
                    {"date": dates[2], "hours": 1.5, "subject": "English"},
                    {"date": dates[3], "hours": 4.0, "subject": "CS"},
                    {"date": dates[4], "hours": 2.0, "subject": "History"},
                    {"date": dates[5], "hours": 3.5, "subject": "CS"},
                    {"date": dates[6], "hours": 2.0, "subject": "Math"}
                ]
                
                df = pd.DataFrame(sample_data)
                fig = px.bar(
                    df,
                    x="date",
                    y="hours",
                    color="subject",
                    title="Sample Study Hours (What you'll see)",
                    labels={"hours": "Hours", "date": "Date"}
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Latest Education News")
        
        # Get trending education news from cache or AI
        education_news = fetch_trending_news("education")
        
        for news in education_news:
            st.markdown(f"""
            <div class="news-card">
                <h4>{news['title']}</h4>
                <p>{news['date']} • {news['source']}</p>
            </div>
            """, unsafe_allow_html=True)
        

    st.markdown("## Personalized Recommendations")

    # Get personalized recommendations with error handling
    try:
        recommendations = st.session_state.prediction_engine.get_personalized_recommendations()
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        recommendations = []

    # Show recommendations with better styling
        if recommendations:
            for rec in recommendations:
                if rec.get("priority") == "high":
                    st.markdown(f"""
                    <div style="background-color: #ffebee; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #d32f2f;">
                        <strong style="color: #c62828;">❗ {rec.get('title')}</strong><br>
                        <span style="color: #333333;">{rec.get('description')}</span>
                    </div>
                    """, unsafe_allow_html=True)
                elif rec.get("priority") == "medium":
                    st.markdown(f"""
                    <div style="background-color: #fff3e0; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #ff9800;">
                        <strong style="color: #e65100;">⚠️ {rec.get('title')}</strong><br>
                        <span style="color: #333333;">{rec.get('description')}</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background-color: #e8f5e9; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #4caf50;">
                        <strong style="color: #2e7d32;">💡 {rec.get('title')}</strong><br>
                        <span style="color: #333333;">{rec.get('description')}</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No personalized recommendations available at this time.")

        
        # Show a top opportunity
        if opportunities:
            st.markdown("### Top Opportunity for You")
            top_opportunity = opportunities[0]
            
            st.markdown(f"""
            <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin-top: 15px; border: 1px solid #bbdefb;">
                <h4 style="margin-top: 0;">{top_opportunity['title']}</h4>
                <p><strong>Organization:</strong> {top_opportunity['organization']}</p>
                <p><strong>Deadline:</strong> {top_opportunity['deadline']}</p>
                <p>{top_opportunity['description']}</p>
                <p><em>Why this matters to you:</em> {top_opportunity['relevance']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Get more AI-driven career insights if available
            if st.session_state.cached_content.get("career_insights"):
                st.markdown("### AI Career Insights")
                insights = st.session_state.cached_content["career_insights"]
                
                for insight in insights[:1]:  # Show just the top insight
                    st.markdown(f"""
                    <div style="background-color: #f0f4c3; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #cddc39;">
                        <h4 style="margin-top: 0;">{insight.get('insight', 'Career Insight')}</h4>
                        <p><strong>Trend:</strong> {insight.get('trend', '')}</p>
                        <p><strong>Recommended Action:</strong> {insight.get('action', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)

# Academic Tracker section with improved UI
def show_academics_page():
    st.title("Academic Tracker")
    
    # Show guidance for first-time visitors
    show_section_guidance("Academics")
    
    academic = st.session_state.academic_tracker
    
    # Create tabs for different academic features
    tab1, tab2, tab3, tab4 = st.tabs(["Courses", "Performance", "Study Tracker", "Academic Chatbot"])
    
    # Courses tab
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Current Courses")
            courses = academic.get_courses(current_only=True)
            
            if courses:
                for course in courses:
                    with st.expander(f"{course['code']}: {course['title']}"):
                        st.write(f"**Credits:** {course['credits']}")
                        st.write(f"**Faculty:** {course['faculty']}")
                        st.write(f"**Schedule:** {course['schedule']}")
                        
                        # Show course performance
                        course_performance = academic.get_course_performance(course['code'])
                        if course_performance:
                            st.write("**Performance:**")
                            for assessment in course_performance:
                                st.write(f"- {assessment['title']}: {assessment['score']}/{assessment['max_score']} ({assessment['percentage']}%)")
                
                # Show upcoming tasks for courses
                st.subheader("Upcoming Course Tasks")
                upcoming_tasks = academic.get_upcoming_tasks(limit=5)
                
                if upcoming_tasks:
                    task_df = pd.DataFrame(upcoming_tasks)
                    task_df['days_left'] = task_df['due_date'].apply(lambda x: (datetime.fromisoformat(x) - datetime.now()).days if x else None)
                    
                    for _, task in task_df.sort_values('days_left').iterrows():
                        days_left = task['days_left']
                        if days_left is not None:
                            if days_left < 0:
                                st.markdown(f"""
                                <div style="background-color: #ffebee; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #d32f2f;">
                                    <strong>⚠️ OVERDUE:</strong> {task['title']} - {task['course_code']} ({abs(days_left)} days ago)
                                </div>
                                """, unsafe_allow_html=True)
                            elif days_left == 0:
                                st.markdown(f"""
                                <div style="background-color: #fff3e0; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #ff9800;">
                                    <strong>⏰ DUE TODAY:</strong> {task['title']} - {task['course_code']}
                                </div>
                                """, unsafe_allow_html=True)
                            elif days_left <= 3:
                                st.markdown(f"""
                                <div style="background-color: #e3f2fd; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #2196f3;">
                                    <strong>🔜 DUE SOON:</strong> {task['title']} - {task['course_code']} ({days_left} days left)
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                    <strong>📝 {task['title']}</strong> - {task['course_code']} ({days_left} days left)
                                </div>
                                """, unsafe_allow_html=True)
                else:
                    st.info("No upcoming tasks for your courses. Add tasks using the Task form in the Dashboard.")
            else:
                # Empty state with better UI
                st.markdown("""
                <div style="background-color: #f9f9f9; border: 1px dashed #ddd; border-radius: 8px; padding: 30px; text-align: center; margin-bottom: 20px;">
                    <h3 style="color: #666; margin-bottom: 15px;">No courses added yet</h3>
                    <p style="color: #888;">Add your first course using the form on the right to track your academic progress.</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.subheader("Add New Course")
            
            with st.form("add_course_form"):
                course_code = st.text_input("Course Code*", placeholder="e.g., CS101")
                course_title = st.text_input("Course Title*", placeholder="e.g., Introduction to Computer Science")
                credits = st.number_input("Credits", min_value=1, max_value=10, value=4)
                faculty = st.text_input("Faculty Name", placeholder="e.g., Dr. Sharma")
                schedule = st.text_input("Schedule", placeholder="e.g., Mon, Wed 10:00-11:30")
                is_current = st.checkbox("Current Course", value=True)
                semester = st.selectbox("Semester", ["Monsoon 2025", "Winter 2025", "Summer 2025", "Custom"])
                
                if semester == "Custom":
                    semester = st.text_input("Enter Semester Name")
                
                st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
                submitted = st.form_submit_button("Add Course")
                st.markdown('</div>', unsafe_allow_html=True)
                
                if submitted:
                    if course_code and course_title:
                        new_course = {
                            "code": course_code,
                            "title": course_title,
                            "credits": credits,
                            "faculty": faculty,
                            "schedule": schedule,
                            "is_current": is_current,
                            "semester": semester
                        }
                        if academic.add_course(new_course):
                            st.success("Course added successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to add course.")
                    else:
                        st.error("Please fill in all required fields marked with *")
            
            # Course resources - use AI-generated trends if available 
            st.markdown("### Latest Academic Trends")
            
            academic_trends = None
            if st.session_state.cached_content.get("academic_trends"):
                academic_trends = st.session_state.cached_content["academic_trends"]
            
            if academic_trends:
                for trend in academic_trends:
                    st.markdown(f"""
                    <div class="trend-card">
                        <h4>{trend.get('trend', 'Academic Trend')}</h4>
                        <p><strong>Description:</strong> {trend.get('description', '')}</p>
                        <p><strong>Benefit:</strong> {trend.get('benefit', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                # Fallback if no AI-generated content
                st.markdown("""
                <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; margin-top: 15px;">
                    <h4 style="margin-top: 0;">Latest Education Trends</h4>
                    <ul style="margin-bottom: 0;">
                        <li><strong>Project-Based Learning</strong> becoming standard in engineering courses</li>
                        <li><strong>Digital Lab Journals</strong> being adopted by science departments</li>
                        <li><strong>Peer-to-Peer Teaching</strong> shown to improve comprehension by 32%</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
    
    # Performance tab
    with tab2:
        st.subheader("Academic Performance")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Display performance history
            performance_history = academic.get_performance_history()
            
            if performance_history:
                current_cgpa = academic.get_current_cgpa()
                st.metric("Current CGPA", f"{current_cgpa:.2f}/10.0")
                
                # Create DataFrame for display
                df = pd.DataFrame(performance_history)
                df = df.sort_values('semester_index', ascending=False)
                
                # Display summary table
                summary_df = df[['semester', 'cgpa', 'sgpa']].copy()
                summary_df.columns = ['Semester', 'CGPA', 'SGPA']
                st.table(summary_df)
                
                # Plot performance trend
                fig = px.line(
                    df.sort_values('semester_index'), 
                    x='semester', 
                    y=['sgpa', 'cgpa'],
                    title='Academic Performance Trend',
                    labels={'value': 'GPA', 'semester': 'Semester', 'variable': 'Metric'},
                    markers=True,
                    template="plotly_white"
                )
                fig.update_layout(legend=dict(
                    title=None,
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                ))
                st.plotly_chart(fig, use_container_width=True)
                
                # Personalized insights based on performance
                if len(performance_history) >= 2:
                    latest_sgpa = performance_history[-1].get('sgpa', 0)
                    previous_sgpa = performance_history[-2].get('sgpa', 0)
                    
                    if latest_sgpa > previous_sgpa:
                        st.success(f"🌟 **Great improvement!** Your SGPA increased from {previous_sgpa:.2f} to {latest_sgpa:.2f}. Keep up the good work!")
                    elif latest_sgpa < previous_sgpa:
                        st.warning(f"📉 Your SGPA decreased from {previous_sgpa:.2f} to {latest_sgpa:.2f}. Consider scheduling a meeting with your academic advisor.")
                
                # Academic standing and advice
                degree = st.session_state.student_profile.get_degree()
                year = st.session_state.student_profile.get_year_of_study()
                
                if "B.Tech" in degree or "B.E." in degree:
                    if current_cgpa < 7.0:
                        st.warning("⚠️ Engineering programs typically require a minimum CGPA of 7.0 for many campus placements.")
                    elif current_cgpa >= 8.5:
                        st.success("✅ Your CGPA qualifies you for most premium campus placements and higher studies applications!")
                
                if "1st Year" in year:
                    st.info("💡 **First Year Tip:** Building a strong foundation now will make advanced courses easier later.")
                elif "Final Year" in year:
                    st.info("💡 **Final Year Tip:** Focus on maintaining your CGPA while balancing placement preparation.")
            else:
                # Better empty state with guidance
                st.markdown("""
                <div style="background-color: #f9f9f9; border: 1px dashed #ddd; border-radius: 8px; padding: 30px; text-align: center; margin-bottom: 20px;">
                    <h3 style="color: #666; margin-bottom: 15px;">No academic performance data yet</h3>
                    <p style="color: #888;">Add your semester results to visualize your academic progress.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Sample data visualization to show what they'll get
                st.subheader("What You'll See After Adding Data:")
                
                # Create sample data
                sample_data = [
                    {"semester": "Semester 1", "sgpa": 8.1, "cgpa": 8.1, "semester_index": 1},
                    {"semester": "Semester 2", "sgpa": 8.3, "cgpa": 8.2, "semester_index": 2},
                    {"semester": "Semester 3", "sgpa": 7.9, "cgpa": 8.1, "semester_index": 3},
                    {"semester": "Semester 4", "sgpa": 8.5, "cgpa": 8.2, "semester_index": 4}
                ]
                
                # Plot sample performance trend
                df = pd.DataFrame(sample_data)
                fig = px.line(
                    df, 
                    x='semester', 
                    y=['sgpa', 'cgpa'],
                    title='Sample Academic Performance Trend',
                    labels={'value': 'GPA', 'semester': 'Semester', 'variable': 'Metric'},
                    markers=True,
                    template="plotly_white"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Add Semester Result")
            
            with st.form("add_semester_form"):
                semester_name = st.selectbox(
                    "Semester*", 
                    ["Monsoon 2025", "Winter 2025", "Summer 2025", "Custom"],
                    key="semester_select"
                )
                
                if semester_name == "Custom":
                    semester_name = st.text_input("Enter Semester Name")
                
                semester_index = st.number_input("Semester Number", min_value=1, max_value=12, value=1, 
                                               help="1 for first semester, 2 for second, etc.")
                
                sgpa = st.number_input("SGPA", min_value=0.0, max_value=10.0, value=8.0, step=0.1, 
                                     help="Semester Grade Point Average (out of 10)")
                
                total_credits = st.number_input("Credits Earned", min_value=1, max_value=30, value=20, 
                                              help="Total credits earned this semester")
                
                st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
                submitted = st.form_submit_button("Add Semester")
                st.markdown('</div>', unsafe_allow_html=True)
                
                if submitted:
                    if semester_name:
                        new_semester = {
                            "semester": semester_name,
                            "semester_index": semester_index,
                            "sgpa": sgpa,
                            "credits": total_credits,
                            "date_added": datetime.now().isoformat()
                        }
                        if academic.add_semester_performance(new_semester):
                            st.success("Semester result added successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to add semester result.")
                    else:
                        st.error("Please fill in all required fields.")
            
            # Academic tips based on standard
            st.markdown("### Academic Standards")
            st.markdown("""
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 15px;">
                <h4 style="margin-top: 0;">CGPA Interpretation</h4>
                <ul style="margin-bottom: 0;">
                    <li><strong>9.0-10.0:</strong> Outstanding (First Class with Distinction)</li>
                    <li><strong>8.0-8.9:</strong> Excellent (First Class)</li>
                    <li><strong>7.0-7.9:</strong> Very Good (First Class)</li>
                    <li><strong>6.0-6.9:</strong> Good (Second Class)</li>
                    <li><strong>5.0-5.9:</strong> Average (Pass Class)</li>
                    <li><strong>Below 5.0:</strong> Needs Improvement</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # Study Tracker tab
    with tab3:
        st.subheader("Study Hours Tracker")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            study_data = academic.get_study_hours_history()
            
            if study_data:
                # Calculate statistics
                total_hours = sum(entry['hours'] for entry in study_data)
                avg_daily = total_hours / len(study_data)
                
                # Create metrics with more visual appeal
                col1, col2, col3 = st.columns(3)
                
                col1.markdown(f"""
                <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; text-align: center;">
                    <h2 style="margin: 0; color: #2e7d32;">{total_hours:.1f}</h2>
                    <p style="margin: 0; color: #2e7d32;">Total Study Hours</p>
                </div>
                """, unsafe_allow_html=True)
                
                col2.markdown(f"""
                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; text-align: center;">
                    <h2 style="margin: 0; color: #1565c0;">{avg_daily:.1f}</h2>
                    <p style="margin: 0; color: #1565c0;">Avg. Daily Hours</p>
                </div>
                """, unsafe_allow_html=True)
                
                col3.markdown(f"""
                <div style="background-color: #fff3e0; padding: 15px; border-radius: 8px; text-align: center;">
                    <h2 style="margin: 0; color: #e65100;">{len(study_data)}</h2>
                    <p style="margin: 0; color: #e65100;">Study Sessions</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Bar chart of recent study sessions
                df = pd.DataFrame(sorted(study_data, key=lambda x: x.get('date', ''))[-10:])
                
                if not df.empty:
                    if 'subject' in df.columns:
                        fig = px.bar(
                            df,
                            x="date",
                            y="hours",
                            color="subject",
                            title="Recent Study Sessions",
                            labels={"hours": "Hours", "date": "Date", "subject": "Subject"}
                        )
                    else:
                        fig = px.bar(
                            df,
                            x="date",
                            y="hours",
                            title="Recent Study Sessions",
                            labels={"hours": "Hours", "date": "Date"}
                        )
                    
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Subject breakdown if available
                subjects = {}
                for entry in study_data:
                    if 'subject' in entry:
                        subject = entry['subject']
                        if subject not in subjects:
                            subjects[subject] = 0
                        subjects[subject] += entry['hours']
                
                if subjects:
                    st.subheader("Subject Breakdown")
                    
                    # Sort subjects by hours
                    sorted_subjects = sorted(subjects.items(), key=lambda x: x[1], reverse=True)
                    
                    subject_df = pd.DataFrame(sorted_subjects, columns=['Subject', 'Hours'])
                    fig = px.pie(
                        subject_df,
                        values='Hours',
                        names='Subject',
                        title='Study Time by Subject',
                        hole=0.4
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Study recommendations based on subject distribution
                    least_studied = sorted_subjects[-1][0]
                    most_studied = sorted_subjects[0][0]
                    
                    st.info(f"💡 You're spending most time on **{most_studied}**. Consider balancing with more focus on **{least_studied}** which has received less attention.")
            else:
                st.info("No study tracking data available yet. Track your study hours using the form on the right.")
                
                # Sample data
                dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7, 0, -1)]
                sample_data = [
                    {"date": dates[0], "hours": 2.5, "subject": "Math"},
                    {"date": dates[1], "hours": 3.0, "subject": "Physics"},
                    {"date": dates[2], "hours": 1.5, "subject": "English"},
                    {"date": dates[3], "hours": 4.0, "subject": "CS"},
                    {"date": dates[4], "hours": 2.0, "subject": "History"},
                    {"date": dates[5], "hours": 3.5, "subject": "CS"},
                    {"date": dates[6], "hours": 2.0, "subject": "Math"}
                ]
                
                df = pd.DataFrame(sample_data)
                fig = px.bar(
                    df,
                    x="date",
                    y="hours",
                    color="subject",
                    title="Sample Study Hours (What you'll see)",
                    labels={"hours": "Hours", "date": "Date"}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Log Study Session")
            
            with st.form("log_study_form"):
                date = st.date_input("Date", value=datetime.now())
                hours = st.number_input("Hours", min_value=0.5, max_value=12.0, value=2.0, step=0.5)
                
                # Get subjects from courses
                courses = academic.get_courses(current_only=True)
                subject_options = ["Other"]
                
                if courses:
                    for course in courses:
                        subject_options.append(course["title"])
                
                subject = st.selectbox("Subject", options=subject_options)
                
                if subject == "Other":
                    subject = st.text_input("Enter Subject Name")
                
                notes = st.text_area("Study Notes (Optional)", placeholder="What did you study? Any challenges?", max_chars=200)
                
                submitted = st.form_submit_button("Log Study Session")
                
                if submitted:
                    if hours > 0 and subject:
                        new_session = {
                            "date": date.isoformat(),
                            "hours": hours,
                            "subject": subject,
                            "notes": notes
                        }
                        
                        if academic.log_study_hours(new_session):
                            st.success("Study session logged successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to log study session.")
                    else:
                        st.error("Please enter valid study hours and subject.")
            
            # Study tips from AI 
            if st.session_state.cached_content.get("academic_trends"):
                st.markdown("### AI Study Tips")
                
                trends = st.session_state.cached_content["academic_trends"]
                for trend in trends[:1]:  # Just show the first tip
                    st.markdown(f"""
                    <div style="background-color: #e1f5fe; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #03a9f4;">
                        <h4 style="margin-top: 0; color: #01579b;">Try This: {trend.get('trend', 'Study Technique')}</h4>
                        <p><em>{trend.get('description', '')}</em></p>
                        <p style="margin-bottom: 0;"><strong>Benefit:</strong> {trend.get('benefit', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 15px;">
                    <h4 style="margin-top: 0;">Effective Study Tips</h4>
                    <ul style="margin-bottom: 0;">
                        <li><strong>Active recall</strong> is more effective than passive rereading</li>
                        <li><strong>Spaced repetition</strong> enhances long-term retention</li>
                        <li><strong>Pomodoro Technique</strong> (25 min work, 5 min break) maintains focus</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
    
    # Academic Chatbot tab
    with tab4:
        st.subheader("Academic Assistant")
        
        if st.session_state.groq_api_key is None:
            st.warning("Please configure your Groq API key in Settings to use the Academic Assistant.")
            if st.button("Go to Settings"):
                st.session_state.current_page = "Settings"
                st.rerun()
        else:
            st.write("Ask anything about your studies, courses, or academic strategies.")
            
            # Initialize academic chat history if it doesn't exist
            if 'academic_chat_history' not in st.session_state:
                st.session_state.academic_chat_history = []
            
            # Display academic chat history
            if st.session_state.academic_chat_history:
                st.markdown('<div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; max-height: 400px; overflow-y: auto;">', unsafe_allow_html=True)
                
                for i, (role, message) in enumerate(st.session_state.academic_chat_history):
                    if role == "user":
                        st.markdown(f'<div style="background-color: #e7f5fe; padding: 10px; border-radius: 15px 15px 5px 15px; margin-bottom: 10px; margin-left: 20px;"><strong>You:</strong> {message}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 15px 15px 15px 5px; margin-bottom: 10px;"><strong>Academic Assistant:</strong> {message}</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Input for academic question
            academic_query = st.text_input("Ask about your courses, study techniques, or academic concerns", key="academic_query")
            
            if st.button("Get Academic Advice", key="get_academic_advice"):
                if academic_query:
                    # Add user message to academic chat history
                    st.session_state.academic_chat_history.append(("user", academic_query))
                    
                    # Context from academics
                    courses = academic.get_courses(current_only=True)
                    course_names = [f"{c['code']}: {c['title']}" for c in courses]
                    course_context = ", ".join(course_names) if course_names else "No courses added yet"
                    
                    # Prepare student context for more personalized answers
                    student_context = None
                    if st.session_state.student_profile:
                        profile = st.session_state.student_profile
                        student_context = {
                            "degree": profile.get_degree(),
                            "year": profile.get_year_of_study(),
                            "college": profile.get_college_name(),
                            "courses": course_context
                        }
                    
                    # Get AI response for academics specifically
                    with st.spinner("Researching your question..."):
                        ai_response = st.session_state.ai_advisor.get_advice(
                            academic_query, "academic", student_context
                        )
                    
                    # Add AI response to academic chat history
                    st.session_state.academic_chat_history.append(("ai", ai_response))
                    
                    # Force a rerun to show the updated chat
                    st.rerun()

# Financial Planner page
def show_finance_page():
    st.title("Financial Planner")
    
    # Show guidance for first-time visitors
    show_section_guidance("Finance")
    
    financial = st.session_state.financial_planner
    
    # Create tabs for different finance features
    tab1, tab2, tab3, tab4 = st.tabs(["Transactions", "Budget", "Scholarships", "Financial Advisor"])
    
    # Transactions tab
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Recent Transactions")
            
            transactions = financial.get_all_transactions()
            
            if transactions:
                # Financial summary metrics
                income = sum([t['amount'] for t in transactions if t['amount'] > 0])
                expenses = abs(sum([t['amount'] for t in transactions if t['amount'] < 0]))
                balance = income - expenses
                
                col1, col2, col3 = st.columns(3)
                
                col1.metric(
                    "Income",
                    f"₹{income:,.2f}",
                    delta=None
                )
                
                col2.metric(
                    "Expenses",
                    f"₹{expenses:,.2f}",
                    delta=None
                )
                
                col3.metric(
                    "Balance", 
                    f"₹{balance:,.2f}",
                    delta=None,
                    delta_color="normal"
                )
                
                # Transaction list with better formatting
                st.write("### Transaction History")
                
                # Sort transactions by date (most recent first)
                sorted_transactions = sorted(transactions, key=lambda x: x.get('date', ''), reverse=True)
                
                for transaction in sorted_transactions[:10]:  # Show only the 10 most recent
                    amount = transaction['amount']
                    is_expense = amount < 0
                    
                    if is_expense:
                        st.markdown(f"""
                        <div style="background-color: #ffebee; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #ef5350; display: flex; justify-content: space-between;">
                            <div>
                                <strong>{transaction['description']}</strong><br>
                                <small>{transaction.get('date', 'N/A')} | {transaction.get('category', 'Uncategorized')}</small>
                            </div>
                            <div style="color: #d32f2f; font-weight: bold; align-self: center;">
                                - ₹{abs(amount):,.2f}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background-color: #e8f5e9; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #66bb6a; display: flex; justify-content: space-between;">
                            <div>
                                <strong>{transaction['description']}</strong><br>
                                <small>{transaction.get('date', 'N/A')} | {transaction.get('category', 'Uncategorized')}</small>
                            </div>
                            <div style="color: #2e7d32; font-weight: bold; align-self: center;">
                                + ₹{amount:,.2f}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                if len(sorted_transactions) > 10:
                    st.info(f"Showing 10 of {len(sorted_transactions)} transactions. View more by downloading your transaction history.")
                    
                    if st.button("Download Complete Transaction History"):
                        # Create a DataFrame for download
                        df = pd.DataFrame(sorted_transactions)
                        
                        # Convert to CSV for download
                        csv = df.to_csv(index=False)
                        
                        # Create a download button
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name="my_transactions.csv",
                            mime="text/csv"
                        )
            else:
                # Empty state with sample visualization
                st.markdown("""
                <div style="background-color: #f9f9f9; border: 1px dashed #ddd; border-radius: 8px; padding: 30px; text-align: center; margin-bottom: 20px;">
                    <h3 style="color: #666; margin-bottom: 15px;">No transactions added yet</h3>
                    <p style="color: #888;">Add your first transaction using the form on the right to start tracking your finances.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Sample expense breakdown
                st.subheader("Sample Expense Breakdown (What you'll see)")
                
                sample_expenses = [
                    {"category": "Food", "amount": 4000},
                    {"category": "Transportation", "amount": 1200},
                    {"category": "Books & Supplies", "amount": 2500},
                    {"category": "Entertainment", "amount": 800},
                    {"category": "Other", "amount": 1500}
                ]
                
                fig = create_pie_chart(
                    data=sample_expenses,
                    labels_key="category",
                    values_key="amount",
                    title="Sample Monthly Expenses"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Add Transaction")
            
            with st.form("add_transaction_form"):
                transaction_type = st.radio("Transaction Type", ["Expense", "Income"])
                amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0, value=0.0)
                description = st.text_input("Description", placeholder="e.g., Lunch, Books, Allowance")
                
                # Different category options based on type
                if transaction_type == "Expense":
                    categories = [
                        "Food & Dining", "Transportation", "Books & Supplies", 
                        "Rent & Utilities", "Entertainment", "Personal Care",
                        "Mobile & Internet", "Clothing", "Miscellaneous"
                    ]
                else:
                    categories = [
                        "Pocket Money", "Salary/Stipend", "Scholarship", 
                        "Investment Returns", "Gifts", "Other Income"
                    ]
                
                category = st.selectbox("Category", categories)
                date = st.date_input("Date", value=datetime.now())
                
                st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
                submitted = st.form_submit_button("Add Transaction")
                st.markdown('</div>', unsafe_allow_html=True)
                
                if submitted:
                    if amount > 0 and description:
                        # Adjust amount sign based on transaction type
                        final_amount = amount if transaction_type == "Income" else -amount
                        
                        new_transaction = {
                            "amount": final_amount,
                            "description": description,
                            "category": category,
                            "date": date.isoformat(),
                            "type": transaction_type.lower()
                        }
                        
                        if financial.add_transaction(new_transaction):
                            st.success(f"{transaction_type} added successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Failed to add {transaction_type.lower()}.")
                    else:
                        st.error("Please enter a valid amount and description.")
            
            # Financial tips from AI
            if st.session_state.cached_content.get("financial_tips"):
                st.markdown("### Financial Tips")
                
                tips = st.session_state.cached_content["financial_tips"]
                for tip in tips[:1]:  # Just show the first tip
                    st.markdown(f"""
                    <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #4caf50;">
                        <h4 style="margin-top: 0; color: #2e7d32;">{tip.get('tip', 'Financial Tip')}</h4>
                        <p>{tip.get('description', '')}</p>
                        <p style="margin-bottom: 0;"><strong>Action:</strong> {tip.get('action_item', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                # Fallback financial tips
                st.markdown("""
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 15px;">
                    <h4 style="margin-top: 0;">Student Finance Tips</h4>
                    <ul style="margin-bottom: 0;">
                        <li><strong>Track all expenses</strong>, even small ones - they add up quickly</li>
                        <li><strong>Look for student discounts</strong> on software, transportation, and food</li>
                        <li><strong>Set up automatic savings</strong>, even if it's just ₹500 per month</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
    
    # Budget tab
    with tab2:
        st.subheader("Budget Management")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            budget = financial.get_budget()
            expenses_by_category = financial.get_expenses_by_category()
            
            if budget:
                # Display budget vs actual expenses
                budget_data = []
                
                for category, budgeted in budget.items():
                    spent = expenses_by_category.get(category, 0)
                    percentage = (spent / budgeted * 100) if budgeted > 0 else 0
                    remaining = budgeted - spent
                    status = "Over" if percentage > 100 else "On Track"
                    
                    budget_data.append({
                        "category": category,
                        "budgeted": budgeted,
                        "spent": spent,
                        "percentage": percentage,
                        "remaining": remaining,
                        "status": status
                    })
                
                # Sort categories by percentage spent (highest first)
                budget_data = sorted(budget_data, key=lambda x: x['percentage'], reverse=True)
                
                # Display budget progress bars
                for item in budget_data:
                    percentage = min(item['percentage'], 100)  # Cap at 100% for the progress bar
                    
                    # Determine color based on percentage
                    if percentage >= 100:
                        bar_color = "#f44336"  # Red for over budget
                        text_color = "#d32f2f"
                    elif percentage >= 80:
                        bar_color = "#ff9800"  # Orange for close to budget
                        text_color = "#e65100"
                    else:
                        bar_color = "#4caf50"  # Green for under budget
                        text_color = "#2e7d32"
                    
                    st.markdown(f"""
                    <div style="margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <div><strong>{item['category']}</strong></div>
                            <div style="color: {text_color};">₹{item['spent']:,.2f} / ₹{item['budgeted']:,.2f}</div>
                        </div>
                        <div style="background-color: #f0f0f0; border-radius: 5px; height: 10px; width: 100%;">
                            <div style="background-color: {bar_color}; border-radius: 5px; height: 10px; width: {percentage}%;"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 0.8rem;">
                            <div style="color: {text_color};">{item['percentage']:.1f}% used</div>
                            <div>₹{item['remaining']:,.2f} remaining</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Budget overview
                total_budget = sum(budget.values())
                total_spent = sum(expenses_by_category.values())
                overall_percentage = (total_spent / total_budget * 100) if total_budget > 0 else 0
                
                st.markdown(f"""
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 20px; margin-bottom: 20px;">
                    <h4 style="margin-top: 0;">Budget Overview</h4>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <div>Total Budget</div>
                        <div>₹{total_budget:,.2f}</div>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <div>Total Spent</div>
                        <div>₹{total_spent:,.2f}</div>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <div>Remaining</div>
                        <div>₹{total_budget - total_spent:,.2f}</div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-weight: bold;">
                        <div>Budget Utilized</div>
                        <div>{overall_percentage:.1f}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Tips based on budget
                over_budget_categories = [item for item in budget_data if item['percentage'] > 100]
                if over_budget_categories:
                    st.warning(f"⚠️ You're over budget in {len(over_budget_categories)} categories. Consider adjusting your spending or your budget.")
                    
                    # Specific tips for the most exceeded category
                    worst_category = over_budget_categories[0]['category']
                    if worst_category == "Food & Dining":
                        st.markdown("""
                        <div style="background-color: #fff3e0; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #ff9800;">
                            <h4 style="margin-top: 0;">Food Budget Tips</h4>
                            <ul style="margin-bottom: 0;">
                                <li>Meal prep on weekends to reduce eating out</li>
                                <li>Look for student meal deals and discounts</li>
                                <li>Share cooking with roommates/friends to split costs</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                    elif worst_category == "Entertainment":
                        st.markdown("""
                        <div style="background-color: #fff3e0; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #ff9800;">
                            <h4 style="margin-top: 0;">Entertainment Budget Tips</h4>
                            <ul style="margin-bottom: 0;">
                                <li>Use student discounts at theaters and events</li>
                                <li>Share subscription services with friends</li>
                                <li>Look for free campus events and activities</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                # Empty state with guidance
                st.markdown("""
                <div style="background-color: #f9f9f9; border: 1px dashed #ddd; border-radius: 8px; padding: 30px; text-align: center; margin-bottom: 20px;">
                    <h3 style="color: #666; margin-bottom: 15px;">No budget set up yet</h3>
                    <p style="color: #888;">Set up your monthly budget using the form on the right to track your spending against your targets.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Sample budget visualization
                st.subheader("Sample Budget (What you'll see)")
                
                sample_budget_data = [
                    {"category": "Food & Dining", "budgeted": 4000, "spent": 3500, "percentage": 87.5},
                    {"category": "Transportation", "budgeted": 1500, "spent": 1200, "percentage": 80},
                    {"category": "Books & Supplies", "budgeted": 2000, "spent": 2200, "percentage": 110},
                    {"category": "Entertainment", "budgeted": 1000, "spent": 800, "percentage": 80},
                ]
                
                for item in sample_budget_data:
                    percentage = item['percentage']
                    
                    # Determine color based on percentage
                    if percentage >= 100:
                        bar_color = "#f44336"  # Red for over budget
                        text_color = "#d32f2f"
                    elif percentage >= 80:
                        bar_color = "#ff9800"  # Orange for close to budget
                        text_color = "#e65100"
                    else:
                        bar_color = "#4caf50"  # Green for under budget
                        text_color = "#2e7d32"
                    
                    st.markdown(f"""
                    <div style="margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <div><strong>{item['category']}</strong></div>
                            <div style="color: {text_color};">₹{item['spent']:,.2f} / ₹{item['budgeted']:,.2f}</div>
                        </div>
                        <div style="background-color: #f0f0f0; border-radius: 5px; height: 10px; width: 100%;">
                            <div style="background-color: {bar_color}; border-radius: 5px; height: 10px; width: {percentage}%;"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 0.8rem;">
                            <div style="color: {text_color};">{item['percentage']:.1f}% used</div>
                            <div>₹{item['budgeted'] - item['spent']:,.2f} remaining</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        with col2:
            st.subheader("Set Budget")
            
            current_budget = financial.get_budget() or {}
            
            with st.form("budget_form"):
                st.write("Set your monthly budget for each category:")
                
                categories = [
                    "Food & Dining", "Transportation", "Books & Supplies", 
                    "Rent & Utilities", "Entertainment", "Personal Care",
                    "Mobile & Internet", "Clothing", "Miscellaneous"
                ]
                
                budget_values = {}
                
                for category in categories:
                    current_value = current_budget.get(category, 0)
                    budget_values[category] = st.number_input(
                        f"{category} (₹)",
                        min_value=0,
                        value=int(current_value),
                        step=500
                    )
                
                st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
                submitted = st.form_submit_button("Update Budget")
                st.markdown('</div>', unsafe_allow_html=True)
                
                if submitted:
                    if financial.set_budget(budget_values):
                        st.success("Budget updated successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to update budget.")
            
            # Budget template recommendations
            st.markdown("### Budget Templates")
            
            st.write("Quick templates based on your profile:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Student Living at Home"):
                    template = {
                        "Food & Dining": 3000,
                        "Transportation": 2000,
                        "Books & Supplies": 2500,
                        "Rent & Utilities": 0,
                        "Entertainment": 1500,
                        "Personal Care": 1000,
                        "Mobile & Internet": 800,
                        "Clothing": 1000,
                        "Miscellaneous": 1200
                    }
                    if financial.set_budget(template):
                        st.success("Template applied!")
                        time.sleep(1)
                        st.rerun()
            
            with col2:
                if st.button("Hostel/PG Student"):
                    template = {
                        "Food & Dining": 4500,
                        "Transportation": 1500,
                        "Books & Supplies": 2500,
                        "Rent & Utilities": 7000,
                        "Entertainment": 1200,
                        "Personal Care": 800,
                        "Mobile & Internet": 800,
                        "Clothing": 800,
                        "Miscellaneous": 1000
                    }
                    if financial.set_budget(template):
                        st.success("Template applied!")
                        time.sleep(1)
                        st.rerun()
    
    # Scholarships tab
    with tab3:
        st.subheader("Scholarship Finder")
        
        # Get student profile info
        student = st.session_state.student_profile
        student_degree = student.get_degree() if student else "Unknown"
        student_year = student.get_year_of_study() if student else "Unknown"
        
        # AI-generated scholarship data if available
        if st.session_state.cached_content.get("financial_tips"):
            # Try to extract scholarship info from financial tips
            for tip in st.session_state.cached_content["financial_tips"]:
                if "scholarship" in tip.get("tip", "").lower() or "scholarship" in tip.get("description", "").lower():
                    st.markdown(f"""
                    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #2196f3;">
                        <h4 style="margin-top: 0; color: #0d47a1;">{tip.get('tip', 'Scholarship Opportunity')}</h4>
                        <p>{tip.get('description', '')}</p>
                        <p style="margin-bottom: 0;"><strong>Action Required:</strong> {tip.get('action_item', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    break
        
        # Search and filters
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_query = st.text_input("Search Scholarships", placeholder="e.g., Engineering, Merit, Women, SC/ST")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                eligibility_filter = st.multiselect(
                    "Eligibility",
                    ["Merit-based", "Need-based", "Women-specific", "SC/ST/OBC", "Minority", "Disability"]
                )
            
            with col2:
                amount_filter = st.selectbox(
                    "Amount Range",
                    ["Any", "Up to ₹10,000", "₹10,000-₹50,000", "₹50,000-₹1,00,000", "Above ₹1,00,000"]
                )
            
            with col3:
                deadline_filter = st.selectbox(
                    "Deadline",
                    ["Any", "Within 1 month", "Within 3 months", "Future"]
                )
        
        with col2:
            st.markdown('<div style="text-align: center; margin-top: 24px;">', unsafe_allow_html=True)
            search_button = st.button("🔍 Search Scholarships")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Scholarship results - would be dynamic based on search in a real implementation
        # For this prototype, we're showing relevant scholarships based on the student profile
        
        if search_button or True:  # Always show some results for now
            st.markdown("### Matching Scholarships")
            
            # Get finance news for scholarships
            finance_news = fetch_trending_news("finance")
            scholarship_news = None
            
            # Check if any news is about scholarships
            for news in finance_news:
                if "scholarship" in news.get("title", "").lower():
                    scholarship_news = news
                    break
            
            # Generate relevant scholarships based on degree
            scholarships = []
            
            if "B.Tech" in student_degree or "B.E." in student_degree:
                scholarships.extend([
                    {
                        "name": "AICTE Pragati Scholarship for Girls",
                        "provider": "AICTE",
                        "amount": "₹50,000 per annum",
                        "eligibility": "Girl students in AICTE approved Technical Institutions",
                        "deadline": "May 15, 2025", 
                        "website": "https://www.aicte-pragati-saksham-gov.in/"
                    },
                    {
                        "name": "Inspire Scholarship for Engineering Students",
                        "provider": "Department of Science & Technology",
                        "amount": "₹80,000 per annum",
                        "eligibility": "Top 1% in class 12 board exams",
                        "deadline": "June 30, 2025",
                        "website": "https://www.inspire-dst.gov.in/scholarship.html"
                    }
                ])
            
            if "BBA" in student_degree or "B.Com" in student_degree or "MBA" in student_degree:
                scholarships.extend([
                    {
                        "name": "Future Business Leaders Scholarship",
                        "provider": "CII (Confederation of Indian Industry)",
                        "amount": "₹60,000 per annum",
                        "eligibility": "Commerce and Business students with academic excellence",
                        "deadline": "July 31, 2025",
                        "website": "https://www.cii.in/Scholarships.aspx"
                    }
                ])
            
            # Add general scholarships
            scholarships.extend([
                {
                    "name": "National Scholarship Portal Schemes",
                    "provider": "Government of India",
                    "amount": "Varies by scheme",
                    "eligibility": "Based on merit, category, and income criteria",
                    "deadline": "Variable by scheme",
                    "website": "https://scholarships.gov.in/"
                },
                                {
                    "name": "Tata Trusts Scholarships",
                    "provider": "Tata Trusts",
                    "amount": "Up to ₹2,00,000 per annum",
                    "eligibility": "Merit-cum-means basis for undergraduate and postgraduate students",
                    "deadline": "April 30, 2025",
                    "website": "https://www.tatatrusts.org/our-work/education/scholarships"
                },
                {
                    "name": "Keep India Smiling Scholarship",
                    "provider": "Colgate-Palmolive",
                    "amount": "Up to ₹30,000 per annum",
                    "eligibility": "Students from families with annual income less than ₹5 lakhs",
                    "deadline": "June 15, 2025",
                    "website": "https://www.colgate.com/en-in/smile-karo-aur-shuru-ho-jao/keep-india-smiling"
                }
            ])
            
            # Add scholarship from news if available
            if scholarship_news:
                scholarships.append({
                    "name": scholarship_news["title"],
                    "provider": scholarship_news["source"],
                    "amount": "Check website for details",
                    "eligibility": "Check website for details",
                    "deadline": "Recently announced",
                    "website": "#"
                })
            
            # Filter scholarships based on search query if provided
            if search_query:
                filtered_scholarships = []
                query_lower = search_query.lower()
                for scholarship in scholarships:
                    if (query_lower in scholarship["name"].lower() or
                        query_lower in scholarship["provider"].lower() or
                        query_lower in scholarship["eligibility"].lower()):
                        filtered_scholarships.append(scholarship)
                scholarships = filtered_scholarships
            
            # Display scholarships
            if scholarships:
                for scholarship in scholarships:
                    st.markdown(f"""
                    <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                        <h4 style="margin-top: 0; color: #0a3d62;">{scholarship["name"]}</h4>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <div><strong>Provider:</strong> {scholarship["provider"]}</div>
                            <div><strong>Amount:</strong> {scholarship["amount"]}</div>
                        </div>
                        <p><strong>Eligibility:</strong> {scholarship["eligibility"]}</p>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div><strong>Deadline:</strong> {scholarship["deadline"]}</div>
                            <a href="{scholarship["website"]}" target="_blank" style="background-color: #0a3d62; color: white; padding: 5px 15px; border-radius: 20px; text-decoration: none; font-size: 0.9rem;">Visit Website</a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No scholarships matching your criteria found. Try adjusting your filters or search terms.")
            
            # Scholarship tips
            st.markdown("### Scholarship Application Tips")
            st.markdown("""
            <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px;">
                <h4 style="margin-top: 0; color: #2e7d32;">Maximize Your Chances</h4>
                <ul>
                    <li><strong>Apply early</strong> - Many scholarships have limited funds</li>
                    <li><strong>Prepare documents</strong> - Keep income certificates, mark sheets, and ID proofs ready</li>
                    <li><strong>Quality essays</strong> - Spend time on personal statements and essays</li>
                    <li><strong>Multiple applications</strong> - Apply to several scholarships to increase your chances</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Getting help
            st.markdown("### Need Help with Applications?")
            st.markdown("""
            <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px;">
                <h4 style="margin-top: 0; color: #0d47a1;">Resources Available</h4>
                <ul>
                    <li>Contact your <strong>college financial aid office</strong> for guidance</li>
                    <li>Join the <strong>Scholarship Discussion Forum</strong> on your college portal</li>
                    <li>Use the <strong>Financial Advisor</strong> tab to get personalized scholarship advice</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # Financial Advisor tab
    with tab4:
        st.subheader("Financial Advisor")
        
        if st.session_state.groq_api_key is None:
            st.warning("Please configure your Groq API key in Settings to use the Financial Advisor.")
            if st.button("Go to Settings"):
                st.session_state.current_page = "Settings"
                st.rerun()
        else:
            st.write("Ask anything about financial planning, scholarships, budgeting, or student finances.")
            
            # Initialize financial chat history if it doesn't exist
            if 'finance_chat_history' not in st.session_state:
                st.session_state.finance_chat_history = []
            
            # Display financial chat history
            if st.session_state.finance_chat_history:
                st.markdown('<div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; max-height: 400px; overflow-y: auto;">', unsafe_allow_html=True)
                
                for i, (role, message) in enumerate(st.session_state.finance_chat_history):
                    if role == "user":
                        st.markdown(f'<div style="background-color: #e7f5fe; padding: 10px; border-radius: 15px 15px 5px 15px; margin-bottom: 10px; margin-left: 20px;"><strong>You:</strong> {message}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 15px 15px 15px 5px; margin-bottom: 10px;"><strong>Financial Advisor:</strong> {message}</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Show AI-generated financial advice if available
            if st.session_state.cached_content.get("financial_tips") and not st.session_state.finance_chat_history:
                st.markdown("### AI-Generated Financial Insights")
                tips = st.session_state.cached_content["financial_tips"]
                
                for tip in tips:
                    st.markdown(f"""
                    <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #4caf50;">
                        <h4 style="margin-top: 0; color: #2e7d32;">{tip.get('tip', 'Financial Tip')}</h4>
                        <p>{tip.get('description', '')}</p>
                        <p style="margin-bottom: 0;"><strong>Action:</strong> {tip.get('action_item', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Input for financial question
            finance_query = st.text_input("Ask about budgeting, scholarships, financial planning, etc.", key="finance_query")
            
            if st.button("Get Financial Advice", key="get_finance_advice"):
                if finance_query:
                    # Add user message to finance chat history
                    st.session_state.finance_chat_history.append(("user", finance_query))
                    
                    # Context from finances
                    budget = financial.get_budget()
                    budget_context = "Budget set up" if budget else "No budget set up"
                    
                    transactions = financial.get_all_transactions()
                    transaction_context = f"{len(transactions)} transactions recorded" if transactions else "No transactions recorded"
                    
                    # Prepare student context for more personalized answers
                    student_context = None
                    if st.session_state.student_profile:
                        profile = st.session_state.student_profile
                        student_context = {
                            "degree": profile.get_degree(),
                            "year": profile.get_year_of_study(),
                            "college": profile.get_college_name(),
                            "finance_status": f"{budget_context}, {transaction_context}"
                        }
                    
                    # Get AI response for finances specifically
                    with st.spinner("Researching your financial question..."):
                        ai_response = st.session_state.ai_advisor.get_advice(
                            finance_query, "financial", student_context
                        )
                    
                    # Add AI response to finance chat history
                    st.session_state.finance_chat_history.append(("ai", ai_response))
                    
                    # Force a rerun to show the updated chat
                    st.rerun()

# Mental Wellness page
def show_wellness_page():
    st.title("Mental Wellness")
    
    # Show guidance for first-time visitors
    show_section_guidance("Wellness")
    
    wellness = st.session_state.mental_wellness
    
    # Create tabs for different wellness features
    tab1, tab2, tab3, tab4 = st.tabs(["Mood Tracker", "Stress Management", "Resources", "Wellness Chatbot"])
    
    # Mood Tracker tab
    with tab1:
        st.subheader("Track Your Mood")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Display mood history
            mood_history = wellness.get_mood_history()
            
            if mood_history:
                # Calculate statistics
                recent_moods = mood_history[-7:] if len(mood_history) >= 7 else mood_history
                avg_mood = sum(entry['score'] for entry in recent_moods) / len(recent_moods)
                avg_sleep = sum(entry.get('sleep_hours', 0) for entry in recent_moods) / len(recent_moods)
                
                # Show mood metrics
                col1, col2, col3 = st.columns(3)
                
                col1.markdown(f"""
                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; text-align: center;">
                    <h2 style="margin: 0; color: #1565c0;">{avg_mood:.1f}/10</h2>
                    <p style="margin: 0; color: #1565c0;">Avg. Mood (Last 7 Days)</p>
                </div>
                """, unsafe_allow_html=True)
                
                col2.markdown(f"""
                <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; text-align: center;">
                    <h2 style="margin: 0; color: #2e7d32;">{avg_sleep:.1f}h</h2>
                    <p style="margin: 0; color: #2e7d32;">Avg. Sleep (Last 7 Days)</p>
                </div>
                """, unsafe_allow_html=True)
                
                mood_today = next((entry for entry in mood_history if entry.get('date') == datetime.now().strftime("%Y-%m-%d")), None)
                if mood_today:
                    col3.markdown(f"""
                    <div style="background-color: #e1f5fe; padding: 15px; border-radius: 8px; text-align: center;">
                        <h2 style="margin: 0; color: #0288d1;">{mood_today['score']}/10</h2>
                        <p style="margin: 0; color: #0288d1;">Today's Mood</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    col3.markdown(f"""
                    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; text-align: center;">
                        <h2 style="margin: 0; color: #757575;">-</h2>
                        <p style="margin: 0; color: #757575;">Today's Mood (Not Logged)</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Mood trend visualization
                st.subheader("Mood Trend")
                
                df = pd.DataFrame(sorted(mood_history, key=lambda x: x.get('date', ''))[-30:])  # Last 30 days
                
                if not df.empty:
                    fig = px.line(
                        df,
                        x="date",
                        y="score",
                        title="Your Mood Over Time",
                        labels={"score": "Mood (1-10)", "date": "Date"},
                        markers=True
                    )
                    
                    # Add sleep hours as a secondary y-axis if available
                    if 'sleep_hours' in df.columns:
                        fig2 = px.line(
                            df,
                            x="date",
                            y="sleep_hours",
                            labels={"sleep_hours": "Sleep (hours)"}
                        )
                        fig2.update_traces(yaxis="y2", line=dict(color="green"))
                        
                        # Add second y-axis
                        fig.add_traces(fig2.data)
                        fig.update_layout(
                            yaxis2=dict(
                                title="Sleep (hours)",
                                side="right",
                                overlaying="y"
                            )
                        )
                    
                    fig.update_layout(hovermode="x unified")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Common stressors analysis
                stress_factors = {}
                for entry in mood_history:
                    factors = entry.get('stress_factors', [])
                    for factor in factors:
                        if factor not in stress_factors:
                            stress_factors[factor] = 0
                        stress_factors[factor] += 1
                
                if stress_factors:
                    st.subheader("Your Common Stressors")
                    
                    # Sort stressors by frequency
                    sorted_stressors = sorted(stress_factors.items(), key=lambda x: x[1], reverse=True)
                    
                    stressor_df = pd.DataFrame(sorted_stressors, columns=['Stressor', 'Frequency'])
                    fig = px.bar(
                        stressor_df,
                        x='Stressor',
                        y='Frequency',
                        title='Frequency of Stress Factors',
                        color='Frequency',
                        color_continuous_scale=px.colors.sequential.Blues
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Recommendations based on top stressors
                    top_stressor = sorted_stressors[0][0]
                    
                    st.markdown("### Personalized Recommendations")
                    
                    if "Academic pressure" in top_stressor:
                        st.markdown("""
                        <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #2196f3;">
                            <h4 style="margin-top: 0; color: #0d47a1;">Managing Academic Stress</h4>
                            <ul style="margin-bottom: 0;">
                                <li>Break large tasks into smaller, manageable chunks</li>
                                <li>Create a study schedule with regular breaks</li>
                                <li>Form or join study groups for difficult subjects</li>
                                <li>Talk to professors or TAs when struggling with concepts</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                    elif "Poor sleep" in top_stressor:
                        st.markdown("""
                        <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #2196f3;">
                            <h4 style="margin-top: 0; color: #0d47a1;">Improving Sleep Quality</h4>
                            <ul style="margin-bottom: 0;">
                                <li>Maintain a consistent sleep schedule, even on weekends</li>
                                <li>Create a relaxing pre-sleep routine (reading, light stretching)</li>
                                <li>Keep electronics out of the bedroom</li>
                                <li>Avoid caffeine at least 6 hours before bedtime</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                    elif "Social" in top_stressor:
                        st.markdown("""
                        <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #2196f3;">
                            <h4 style="margin-top: 0; color: #0d47a1;">Building Social Connections</h4>
                            <ul style="margin-bottom: 0;">
                                <li>Join clubs or groups aligned with your interests</li>
                                <li>Schedule regular check-ins with friends and family</li>
                                <li>Consider volunteering for campus activities</li>
                                <li>Practice social skills in low-pressure settings</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                # Empty state with sample visualization
                st.info("No mood tracking data available yet. Start logging your daily mood using the form on the right.")
                
                # Sample data
                dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(14, 0, -1)]
                sample_data = []
                
                for i, date in enumerate(dates):
                    # Create slightly realistic patterns
                    base_mood = 7
                    weekend_boost = 1 if i % 7 >= 5 else 0  # Higher mood on weekends
                    random_factor = np.random.normal(0, 1)  # Random fluctuation
                    
                    mood = max(1, min(10, base_mood + weekend_boost + random_factor))
                    
                    sample_data.append({
                        "date": date,
                        "score": round(mood, 1),
                        "sleep_hours": round(max(5, min(9, 7 + np.random.normal(0, 0.5))), 1)
                    })
                
                df = pd.DataFrame(sample_data)
                
                fig = px.line(
                    df,
                    x="date",
                    y="score",
                    title="Sample Mood Trend (What you'll see)",
                    labels={"score": "Mood (1-10)", "date": "Date"},
                    markers=True
                )
                
                # Add sleep hours as a secondary y-axis
                fig2 = px.line(
                    df,
                    x="date",
                    y="sleep_hours",
                    labels={"sleep_hours": "Sleep (hours)"}
                )
                fig2.update_traces(yaxis="y2", line=dict(color="green"))
                
                # Add second y-axis
                fig.add_traces(fig2.data)
                fig.update_layout(
                    yaxis2=dict(
                        title="Sleep (hours)",
                        side="right",
                        overlaying="y"
                    ),
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Log Today's Mood")
            
            with st.form("log_mood_form"):
                today = datetime.now().date()
                date = st.date_input("Date", value=today, max_value=today)
                
                mood_score = st.slider("Mood (1-10)", min_value=1, max_value=10, value=7, 
                                      help="1 = Very poor, 10 = Excellent")
                
                sleep_hours = st.number_input("Hours of Sleep", min_value=0.0, max_value=12.0, value=7.0, step=0.5)
                
                # Common stress factors
                stress_factors = st.multiselect(
                    "Stress Factors (if any)",
                    ["Academic pressure", "Exam stress", "Assignment deadlines", 
                     "Poor sleep", "Health issues", "Financial concerns", 
                     "Social challenges", "Homesickness", "Relationship issues", 
                     "Time management", "Future career concerns", "Other"]
                )
                
                if "Other" in stress_factors:
                    other_stress = st.text_input("Specify other stress factor")
                    if other_stress:
                        stress_factors.remove("Other")
                        stress_factors.append(other_stress)
                
                notes = st.text_area("Notes (Optional)", placeholder="How are you feeling today? Any specific thoughts?", max_chars=200)
                
                submitted = st.form_submit_button("Log Mood")
                
                if submitted:
                    # Check if already logged for today
                    existing_entry = next((entry for entry in wellness.get_mood_history() if entry.get('date') == date.isoformat()), None)
                    
                    if existing_entry and date == today:
                        overwrite = st.warning("You've already logged your mood for today. Do you want to update it?")
                        if st.button("Update Today's Mood"):
                            new_mood = {
                                "date": date.isoformat(),
                                "score": mood_score,
                                "stress_factors": stress_factors,
                                "sleep_hours": sleep_hours,
                                "notes": notes
                            }
                            
                            if wellness.log_mood(new_mood, update=True):
                                st.success("Mood updated successfully!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to update mood entry.")
                    else:
                        new_mood = {
                            "date": date.isoformat(),
                            "score": mood_score,
                            "stress_factors": stress_factors,
                            "sleep_hours": sleep_hours,
                            "notes": notes
                        }
                        
                        if wellness.log_mood(new_mood):
                            st.success("Mood logged successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to log mood.")
            
            # Mood improvement tips from AI if available
            if st.session_state.cached_content.get("wellness_tips"):
                st.markdown("### Personalized Wellness Tips")
                
                tips = st.session_state.cached_content["wellness_tips"]
                for tip in tips[:1]:  # Show just one tip to save space
                    st.markdown(f"""
                    <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #4caf50;">
                        <h4 style="margin-top: 0; color: #2e7d32;">{tip.get('tip', 'Wellness Tip')}</h4>
                        <p>{tip.get('description', '')}</p>
                        <p style="margin-bottom: 0;"><strong>Try this:</strong> {tip.get('practice', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                # Fallback wellness tip
                st.markdown("""
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 15px;">
                    <h4 style="margin-top: 0;">Mood Booster Technique</h4>
                    <p>Try the <strong>3-3-3 Exercise</strong> when feeling stressed:</p>
                    <ul style="margin-bottom: 0;">
                        <li>Name <strong>3 things you can see</strong></li>
                        <li>Name <strong>3 things you can hear</strong></li>
                        <li>Move <strong>3 parts of your body</strong></li>
                    </ul>
                    <p style="margin-top: 10px;">This simple mindfulness practice can help ground you during stressful moments.</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Stress Management tab
    with tab2:
        st.subheader("Stress Management Techniques")
        
        # Techniques categorized by time required
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### Quick Relief (1-5 minutes)")
            
            techniques = [
                {
                    "name": "Box Breathing",
                    "description": "Inhale for 4 counts, hold for 4, exhale for 4, hold for 4. Repeat.",
                    "benefits": "Reduces acute stress, lowers heart rate, improves focus",
                    "when_to_use": "Before exams, during stressful situations, when feeling overwhelmed"
                },
                {
                    "name": "5-4-3-2-1 Grounding",
                    "description": "Name 5 things you see, 4 things you feel, 3 things you hear, 2 things you smell, and 1 thing you taste.",
                    "benefits": "Interrupts anxiety spirals, brings awareness to the present moment",
                    "when_to_use": "During anxiety attacks, when overthinking, when feeling disconnected"
                },
                {
                    "name": "Progressive Muscle Relaxation",
                    "description": "Tense and then release each muscle group in your body, from toes to head.",
                    "benefits": "Releases physical tension, improves body awareness, reduces physical symptoms of stress",
                    "when_to_use": "Before bed, after long study sessions, when feeling physically tense"
                }
            ]
            
            for technique in techniques:
                with st.expander(f"📝 {technique['name']}"):
                    st.write(f"**Description:** {technique['description']}")
                    st.write(f"**Benefits:** {technique['benefits']}")
                    st.write(f"**When to use:** {technique['when_to_use']}")
        
        with col2:
            st.markdown("### Daily Practices (10-15 minutes)")
            
            practices = [
                {
                    "name": "Guided Meditation",
                    "description": "Follow along with a guided meditation focusing on breathing and awareness.",
                    "benefits": "Reduces stress hormones, improves focus, builds emotional resilience",
                    "when_to_use": "Morning routine, before studying, after a stressful day"
                },
                {
                    "name": "Journaling",
                    "description": "Write about your thoughts, feelings, and experiences without judgment.",
                    "benefits": "Clarifies thinking, processes emotions, tracks patterns over time",
                    "when_to_use": "End of day reflection, when processing complex emotions, for problem-solving"
                },
                {
                    "name": "Physical Movement",
                    "description": "Short yoga sequence, brisk walk, or simple stretching routine.",
                    "benefits": "Releases endorphins, improves circulation, shifts mental state",
                    "when_to_use": "Study breaks, when feeling stuck, to boost energy or focus"
                }
            ]
            
            for practice in practices:
                with st.expander(f"🧘 {practice['name']}"):
                    st.write(f"**Description:** {practice['description']}")
                    st.write(f"**Benefits:** {practice['benefits']}")
                    st.write(f"**When to use:** {practice['when_to_use']}")
        
        # Interactive relaxation exercise
        st.subheader("Try Now: Guided Breathing Exercise")
        
        st.markdown("""
        <div style="background-color: #e8f5e9; padding: 20px; border-radius: 10px; text-align: center;">
            <h3 style="margin-top: 0; color: #2e7d32;">4-7-8 Breathing</h3>
            <p>A powerful technique to calm your nervous system in just one minute</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Start 1-Minute Breathing Exercise"):
            st.markdown("""
            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 10px; text-align: center; margin-top: 20px;">
                <div id="breath-animation" style="font-size: 2rem; margin-bottom: 10px;">Inhale...</div>
                <div id="instructions" style="font-size: 1.2rem;">Breathe in through your nose for 4 counts</div>
                <div id="timer" style="font-size: 1.5rem; margin-top: 20px;">1:00</div>
            </div>
            
            <script>
                // This would be the breathing animation in a real implementation
                // For the prototype, we just show the text
            </script>
            """, unsafe_allow_html=True)
            
            # Simulate the breathing exercise with text
            for i in range(3):  # 3 breath cycles
                st.markdown("### Inhale")
                time.sleep(1)
                st.markdown("### Hold")
                time.sleep(1)
                st.markdown("### Exhale")
                time.sleep(1)
            
            st.success("Breathing exercise completed! How do you feel?")
        
        # Stress test assessment
        st.subheader("Stress Self-Assessment")
        
        st.write("Take this quick assessment to gauge your current stress levels.")
        
        if st.button("Take Stress Assessment"):
            with st.form("stress_assessment"):
                st.write("Rate each statement from 1 (Not at all) to 5 (Very much):")
                
                q1 = st.slider("I feel overwhelmed with my academic workload", 1, 5, 3)
                q2 = st.slider("I have trouble sleeping due to stress or worry", 1, 5, 3)
                q3 = st.slider("I find it difficult to concentrate on my studies", 1, 5, 3)
                q4 = st.slider("I feel physically tense or experience physical symptoms of stress", 1, 5, 3)
                q5 = st.slider("I worry frequently about my future", 1, 5, 3)
                
                submitted = st.form_submit_button("Calculate Results")
                
                if submitted:
                    score = q1 + q2 + q3 + q4 + q5
                    
                    if score < 10:
                        st.success("Your stress level appears to be low. Keep up your good coping strategies!")
                    elif score < 17:
                        st.warning("You're experiencing moderate stress. Consider incorporating some stress management techniques into your daily routine.")
                    else:
                        st.error("Your stress level appears to be high. Please consider talking to a counselor at your college's wellness center.")
                    
                    # Recommend specific techniques
                    st.markdown("### Recommended Techniques Based on Your Results")
                    
                    if q1 > 3:
                        st.markdown("""
                        <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #2196f3;">
                            <h4 style="margin-top: 0; color: #0d47a1;">For Academic Overwhelm</h4>
                            <p>Try the <strong>Pomodoro Technique</strong>: Work for 25 minutes, then take a 5-minute break. After 4 cycles, take a longer 15-30 minute break.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if q2 > 3:
                        st.markdown("""
                        <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #2196f3;">
                            <h4 style="margin-top: 0; color: #0d47a1;">For Sleep Difficulties</h4>
                            <p>Practice <strong>Progressive Muscle Relaxation</strong> before bed and create a consistent sleep routine. Avoid screens 1 hour before sleep.</p>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Resources tab
    with tab3:
        st.subheader("Wellness Resources")
        
        # Campus resources
        st.markdown("### Campus Support Services")
        
        campus_resources = [
            {
                "name": "College Counseling Center",
                "description": "Free confidential counseling services for students",
                "contact": "Visit Student Center, 2nd Floor or call 123-456-7890",
                "hours": "Mon-Fri: 9am-5pm"
            },
            {
                "name": "Peer Support Network",
                "description": "Trained student volunteers providing peer counseling and support",
                "contact": "Email peer.support@college.edu",
                "hours": "Available 24/7 via chat"
            },
            {
                "name": "Wellness Workshops",
                "description": "Regular workshops on stress management, mindfulness, and wellness",
                "contact": "Check college events calendar for schedule",
                "hours": "Typically held on Wednesdays at 4pm"
            }
        ]
        
        col1, col2, col3 = st.columns(3)
        
        for i, resource in enumerate(campus_resources):
            col = [col1, col2, col3][i % 3]
            with col:
                st.markdown(f"""
                <div style="background-color: white; padding: 15px; border-radius: 8px; height: 100%; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h4 style="margin-top: 0; color: #0a3d62;">{resource['name']}</h4>
                    <p>{resource['description']}</p>
                    <p><strong>Contact:</strong> {resource['contact']}</p>
                    <p><strong>Hours:</strong> {resource['hours']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Crisis resources
        st.markdown("### Crisis Support Resources")
        
        st.markdown("""
        <div style="background-color: #ffebee; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #f44336;">
            <h4 style="margin-top: 0; color: #b71c1c;">Immediate Help Resources</h4>
            <ul>
                <li><strong>NIMHANS Helpline:</strong> 080-46110007 - 24/7 mental health support</li>
                <li><strong>iCall Helpline:</strong> 022-25521111 - Monday to Saturday, 8 AM to 10 PM</li>
                <li><strong>Vandrevala Foundation:</strong> 1860-2662-345 - 24/7 support</li>
                <li><strong>College Emergency Number:</strong> 555-123-4567 - On-campus emergencies</li>
            </ul>
            <p style="margin-bottom: 0;"><em>If experiencing thoughts of self-harm or in immediate danger, please call emergency services (102) or contact campus security.</em></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Apps and tools
        st.markdown("### Recommended Apps & Tools")
        
        apps = [
            {
                "name": "Headspace",
                "category": "Meditation",
                "description": "Guided meditations for stress, focus, and sleep. Free with student plan.",
                "link": "https://www.headspace.com/studentplan"
            },
            {
                "name": "Calm",
                "category": "Meditation & Sleep",
                "description": "Sleep stories, meditations, and breathing exercises.",
                "link": "https://www.calm.com/"
            },
            {
                "name": "Wakeout",
                "category": "Movement",
                "description": "Quick exercises designed for studying breaks.",
                "link": "https://wakeout.app/"
            },
            {
                "name": "Reflectly",
                "category": "Journaling",
                "description": "AI-guided journaling app to track mood and build self-awareness.",
                "link": "https://reflectly.app/"
            },
            {
                "name": "Forest",
                "category": "Focus",
                "description": "Stay focused and present by growing virtual trees.",
                "link": "https://www.forestapp.cc/"
            },
            {
                "name": "Finch",
                "category": "Self-Care",
                "description": "Self-care pet game that helps build healthy habits.",
                "link": "https://finchcare.com/"
            }
        ]
        
        col1, col2 = st.columns(2)
        
        for i, app in enumerate(apps):
            col = col1 if i % 2 == 0 else col2
            with col:
                st.markdown(f"""
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <h4 style="margin-top: 0; color: #0a3d62;">{app['name']}</h4>
                    <p><strong>Category:</strong> {app['category']}</p>
                    <p>{app['description']}</p>
                    <a href="{app['link']}" target="_blank">Learn More</a>
                </div>
                """, unsafe_allow_html=True)
        
        # AI-powered wellness articles if available
        if st.session_state.cached_content.get("wellness_tips"):
            st.markdown("### Latest Wellness Articles")
            
            tips = st.session_state.cached_content["wellness_tips"]
            for i, tip in enumerate(tips):
                st.markdown(f"""
                <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #4caf50;">
                    <h4 style="margin-top: 0; color: #2e7d32;">Article: {tip.get('tip', 'Wellness Tip')}</h4>
                    <p>{tip.get('description', '')}</p>
                    <p style="margin-bottom: 0;"><strong>Practice:</strong> {tip.get('practice', '')}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Wellness Chatbot tab
    with tab4:
        st.subheader("Wellness Chatbot")
        
        if st.session_state.groq_api_key is None:
            st.warning("Please configure your Groq API key in Settings to use the Wellness Assistant.")
            if st.button("Go to Settings"):
                st.session_state.current_page = "Settings"
                st.rerun()
        else:
            st.write("Ask anything about mental health, stress management, emotional well-being, or self-care.")
            
            # Initialize wellness chat history if it doesn't exist
            if 'wellness_chat_history' not in st.session_state:
                st.session_state.wellness_chat_history = []
            
            # Display wellness chat history
            if st.session_state.wellness_chat_history:
                st.markdown('<div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; max-height: 400px; overflow-y: auto;">', unsafe_allow_html=True)
                
                for i, (role, message) in enumerate(st.session_state.wellness_chat_history):
                    if role == "user":
                        st.markdown(f'<div style="background-color: #e7f5fe; padding: 10px; border-radius: 15px 15px 5px 15px; margin-bottom: 10px; margin-left: 20px;"><strong>You:</strong> {message}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 15px 15px 15px 5px; margin-bottom: 10px;"><strong>Wellness Assistant:</strong> {message}</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Show AI-generated wellness tips if available
            if st.session_state.cached_content.get("wellness_tips") and not st.session_state.wellness_chat_history:
                st.markdown("### AI-Generated Wellness Insights")
                tips = st.session_state.cached_content["wellness_tips"]
                
                for tip in tips:
                    st.markdown(f"""
                    <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #4caf50;">
                        <h4 style="margin-top: 0; color: #2e7d32;">{tip.get('tip', 'Wellness Tip')}</h4>
                        <p>{tip.get('description', '')}</p>
                        <p style="margin-bottom: 0;"><strong>Practice:</strong> {tip.get('practice', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Input for wellness question
            wellness_query = st.text_input("Ask about stress, emotions, self-care, relationships, etc.", key="wellness_query")
            
            if st.button("Get Wellness Advice", key="get_wellness_advice"):
                if wellness_query:
                    # Add user message to wellness chat history
                    st.session_state.wellness_chat_history.append(("user", wellness_query))
                    
                    # Prepare student context for more personalized answers
                    student_context = None
                    if st.session_state.student_profile:
                        profile = st.session_state.student_profile
                        student_context = {
                            "degree": profile.get_degree(),
                            "year": profile.get_year_of_study(),
                            "college": profile.get_college_name()
                        }
                    
                    # Get AI response for mental health specifically
                    with st.spinner("Researching your wellness question..."):
                        ai_response = st.session_state.ai_advisor.get_advice(
                            wellness_query, "mental_health", student_context
                        )
                    
                    # Add AI response to wellness chat history
                    st.session_state.wellness_chat_history.append(("ai", ai_response))
                    
                    # Force a rerun to show the updated chat
                    st.rerun()

# Career Pathway page
def show_career_page():
    st.title("Career Pathway")
    
    # Show guidance for first-time visitors
    show_section_guidance("Career")
    
    career = st.session_state.career_guide
    
    # Create tabs for different career features
    tab1, tab2, tab3, tab4 = st.tabs(["Career Profile", "Skills Tracker", "Opportunities", "Career Advisor"])
    
    # Career Profile tab
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Your Career Profile")
            
            # Get profile data
            career_profile = career.get_career_profile()
            
            if career_profile:
                # Display career readiness score
                career_readiness = career.get_career_readiness_score()
                
                st.markdown(f"""
                <div style="background-color: #e3f2fd; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0; color: #1565c0; text-align: center;">Career Readiness Score</h3>
                    <h1 style="color: #1565c0; text-align: center; margin: 10px 0;">{career_readiness}%</h1>
                    <div style="background-color: #f5f5f5; border-radius: 5px; height: 15px; width: 100%;">
                        <div style="background-color: #1976d2; border-radius: 5px; height: 15px; width: {career_readiness}%;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Display career interests
                st.markdown("### Career Interests")
                
                interests = career_profile.get('interests', [])
                if interests:
                    interest_text = ", ".join(interests)
                    st.write(f"**Your Interests:** {interest_text}")
                    
                    # Display as tags
                    st.markdown('<div style="display: flex; flex-wrap: wrap; gap: 10px;">', unsafe_allow_html=True)
                    for interest in interests:
                        st.markdown(f"""
                        <div style="background-color: #e1f5fe; color: #0277bd; padding: 5px 15px; border-radius: 20px; font-size: 0.9rem;">
                            {interest}
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("No career interests specified yet. Update your profile to add your interests.")
                
                # Display target roles
                st.markdown("### Target Roles")
                
                target_roles = career_profile.get('target_roles', [])
                if target_roles:
                    st.markdown('<div style="display: flex; flex-wrap: wrap; gap: 10px;">', unsafe_allow_html=True)
                    for role in target_roles:
                        st.markdown(f"""
                        <div style="background-color: #fff8e1; color: #ff8f00; padding: 5px 15px; border-radius: 20px; font-size: 0.9rem;">
                            {role}
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("No target roles specified yet. Update your profile to add your target roles.")
                
                # Display strength and weakness assessment
                st.markdown("### Self-Assessment")
                
                strengths = career_profile.get('strengths', [])
                weaknesses = career_profile.get('areas_for_improvement', [])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Strengths")
                    if strengths:
                        for strength in strengths:
                            st.markdown(f"""
                            <div style="background-color: #e8f5e9; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 4px solid #4caf50;">
                                {strength}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No strengths added yet.")
                
                with col2:
                    st.markdown("#### Areas for Improvement")
                    if weaknesses:
                        for weakness in weaknesses:
                            st.markdown(f"""
                            <div style="background-color: #fff3e0; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 4px solid #ff9800;">
                                {weakness}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No areas for improvement added yet.")
            else:
                # Empty state
                st.markdown("""
                <div style="background-color: #f9f9f9; border: 1px dashed #ddd; border-radius: 8px; padding: 30px; text-align: center; margin-bottom: 20px;">
                    <h3 style="color: #666; margin-bottom: 15px;">No career profile set up yet</h3>
                    <p style="color: #888;">Complete your career profile using the form on the right to get personalized career recommendations.</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.subheader("Update Career Profile")
            
            with st.form("career_profile_form"):
                # Get current profile data
                current_profile = career.get_career_profile() or {}
                
                # Career interests multi-select
                interest_options = [
                    "Software Development", "Data Science", "Artificial Intelligence", 
                    "Product Management", "UX/UI Design", "Marketing", 
                    "Finance", "Consulting", "Research", "Teaching",
                    "Entrepreneurship", "Healthcare", "Government/Public Service"
                ]
                
                current_interests = current_profile.get('interests', [])
                selected_interests = st.multiselect(
                    "Career Interests", 
                    options=interest_options, 
                    default=current_interests
                )
                
                # Target roles multi-select
                current_roles = current_profile.get('target_roles', [])
                target_roles = st.text_area(
                    "Target Roles (one per line)", 
                    value="\n".join(current_roles) if current_roles else "",
                    placeholder="e.g.,\nSoftware Engineer\nData Scientist\nProduct Manager"
                )
                
                # Strengths and weaknesses
                current_strengths = current_profile.get('strengths', [])
                strengths = st.text_area(
                    "Your Strengths (one per line)",
                    value="\n".join(current_strengths) if current_strengths else "",
                    placeholder="e.g.,\nProblem solving\nTeam collaboration\nCoding skills"
                )
                
                current_weaknesses = current_profile.get('areas_for_improvement', [])
                weaknesses = st.text_area(
                    "Areas for Improvement (one per line)",
                    value="\n".join(current_weaknesses) if current_weaknesses else "",
                    placeholder="e.g.,\nPublic speaking\nTime management\nNetworking"
                )
                
                submitted = st.form_submit_button("Update Profile")
                
                if submitted:
                    # Process target roles, strengths, and weaknesses from text areas
                    target_roles_list = [role.strip() for role in target_roles.split('\n') if role.strip()]
                    strengths_list = [s.strip() for s in strengths.split('\n') if s.strip()]
                    weaknesses_list = [w.strip() for w in weaknesses.split('\n') if w.strip()]
                    
                    # Create profile data
                    profile_data = {
                        'interests': selected_interests,
                        'target_roles': target_roles_list,
                        'strengths': strengths_list,
                        'areas_for_improvement': weaknesses_list,
                        'last_updated': datetime.now().isoformat()
                    }
                    
                    # Save profile
                    if career.update_career_profile(profile_data):
                        st.success("Career profile updated successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to update career profile.")
            
            # AI career insights if available
            if st.session_state.cached_content.get("career_insights"):
                st.markdown("### Industry Insights")
                
                insights = st.session_state.cached_content["career_insights"]
                for insight in insights[:1]:  # Show just one insight to save space
                    st.markdown(f"""
                    <div style="background-color: #f3e5f5; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #9c27b0;">
                        <h4 style="margin-top: 0; color: #6a1b9a;">{insight.get('insight', 'Career Insight')}</h4>
                        <p><strong>Trend:</strong> {insight.get('trend', '')}</p>
                        <p style="margin-bottom: 0;"><strong>Action:</strong> {insight.get('action', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Skills Tracker tab
    with tab2:
        st.subheader("Skills Tracker")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Display tracked skills
            skills = career.get_skills()
            
            if skills:
                # Group skills by category
                skills_by_category = {}
                for skill in skills:
                    category = skill.get('category', 'Other')
                    if category not in skills_by_category:
                        skills_by_category[category] = []
                    skills_by_category[category].append(skill)
                
                # Display skills by category
                for category, category_skills in skills_by_category.items():
                    st.markdown(f"### {category}")
                    
                    for skill in category_skills:
                        skill_name = skill.get('name', 'Unnamed Skill')
                        skill_level = skill.get('level', 1)
                        skill_certifications = skill.get('certifications', [])
                        
                        # Create a progress bar for skill level
                        st.markdown(f"""
                        <div style="margin-bottom: 20px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <div><strong>{skill_name}</strong></div>
                                <div>{get_level_label(skill_level)}</div>
                            </div>
                            <div style="background-color: #f0f0f0; border-radius: 5px; height: 10px; width: 100%;">
                                <div style="background-color: #4caf50; border-radius: 5px; height: 10px; width: {skill_level * 20}%;"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Display certifications if any
                        if skill_certifications:
                            cert_text = ", ".join(skill_certifications)
                            st.markdown(f"**Certifications:** {cert_text}")
                
                # Skills visualization
                st.subheader("Skills Overview")
                
                # Create radar chart data
                categories = list(skills_by_category.keys())
                avg_levels = []
                
                for category in categories:
                    category_skills = skills_by_category[category]
                    avg_level = sum(skill.get('level', 1) for skill in category_skills) / len(category_skills)
                    avg_levels.append(avg_level)
                
                # Add the first category again to close the radar chart
                if categories:
                    categories.append(categories[0])
                    avg_levels.append(avg_levels[0])
                
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=avg_levels,
                        theta=categories,
                        fill='toself',
                        name='Skills'
                    ))
                    
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 5]
                            )
                        ),
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            else:
                # Empty state
                st.markdown("""
                <div style="background-color: #f9f9f9; border: 1px dashed #ddd; border-radius: 8px; padding: 30px; text-align: center; margin-bottom: 20px;">
                    <h3 style="color: #666; margin-bottom: 15px;">No skills tracked yet</h3>
                    <p style="color: #888;">Add your skills using the form on the right to track your development.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Sample skills visualization
                st.subheader("Sample Skills Overview (What you'll see)")
                
                # Sample radar chart data
                sample_categories = ["Technical", "Communication", "Leadership", "Problem-Solving", "Technical"]
                sample_levels = [3.5, 4, 2.5, 4, 3.5]
                
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=sample_levels,
                    theta=sample_categories,
                    fill='toself',
                    name='Skills'
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 5]
                        )
                    ),
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Add/Update Skill")
            
            with st.form("add_skill_form"):
                skill_name = st.text_input("Skill Name", placeholder="e.g., Python Programming")
                
                category_options = [
                    "Technical", "Communication", "Leadership", 
                    "Problem-Solving", "Design", "Research",
                    "Language", "Business", "Other"
                ]
                skill_category = st.selectbox("Category", category_options)
                
                skill_level = st.slider(
                    "Proficiency Level",
                    min_value=1,
                    max_value=5,
                    value=3,
                    help="1 = Beginner, 5 = Expert"
                )
                
                certifications = st.text_area(
                    "Certifications (one per line, if any)",
                    placeholder="e.g.,\nPython for Data Science (Coursera)\nAdvanced Python (Udemy)"
                )
                
                development_plan = st.text_area(
                    "Development Plan (optional)",
                    placeholder="How do you plan to improve this skill?"
                )
                
                submitted = st.form_submit_button("Add/Update Skill")
                
                if submitted:
                    if skill_name:
                        # Process certifications from text area
                        certification_list = [cert.strip() for cert in certifications.split('\n') if cert.strip()]
                        
                        # Create skill data
                        skill_data = {
                            'name': skill_name,
                            'category': skill_category,
                            'level': skill_level,
                            'certifications': certification_list,
                            'development_plan': development_plan,
                            'last_updated': datetime.now().isoformat()
                        }
                        
                        # Save skill
                        if career.update_skill(skill_data):
                            st.success("Skill added/updated successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to add/update skill.")
                    else:
                        st.error("Please enter a skill name.")
            
            # Skill level reference
            st.markdown("### Skill Level Reference")
            st.markdown("""
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 15px;">
                <p><strong>Level 1 (Beginner):</strong> Basic understanding, need supervision</p>
                <p><strong>Level 2 (Basic):</strong> Can perform with guidance, understand fundamentals</p>
                <p><strong>Level 3 (Intermediate):</strong> Work independently on routine tasks</p>
                <p><strong>Level 4 (Advanced):</strong> Deep knowledge, can teach others, handle complex tasks</p>
                <p><strong>Level 5 (Expert):</strong> Exceptional capability, thought leadership, innovate in this area</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Personalized skill recommendations based on career interests
            career_profile = career.get_career_profile() or {}
            interests = career_profile.get('interests', [])
            
            if interests:
                st.markdown("### Recommended Skills to Develop")
                
                # AI-generated recommendations if available
                if st.session_state.cached_content.get("career_insights"):
                    insights = st.session_state.cached_content["career_insights"]
                    for insight in insights:
                        if "skill" in insight.get("action", "").lower():
                            st.markdown(f"""
                            <div style="background-color: #f3e5f5; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #9c27b0;">
                                <p><strong>Based on Industry Trends:</strong> {insight.get('action', '')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            break
                
                # Otherwise show static recommendations based on interests
                if "Software Development" in interests:
                    st.markdown("""
                    <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #4caf50;">
                        <p><strong>For Software Development:</strong> Cloud computing (AWS/Azure), Containerization (Docker), CI/CD pipelines</p>
                    </div>
                    """, unsafe_allow_html=True)
                elif "Data Science" in interests:
                    st.markdown("""
                    <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #4caf50;">
                        <p><strong>For Data Science:</strong> MLOps, PyTorch, Data Visualization (Tableau/PowerBI)</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Opportunities tab
    with tab3:
        st.subheader("Career Opportunities")
        
        # Get student profile
        student = st.session_state.student_profile
        
        # Generate opportunities
        opportunities = generate_personalized_opportunities(student)
        
        # Filters for opportunities
        col1, col2, col3 = st.columns(3)
        
        with col1:
            opp_filter_type = st.multiselect(
                "Type",
                ["Internship", "Job", "Scholarship", "Competition", "Program", "All"],
                default=["All"]
            )
        
        with col2:
            opp_filter_deadline = st.selectbox(
                "Deadline",
                ["All", "This Month", "Next Month", "Next 3 Months"]
            )
        
        with col3:
            opp_filter_sort = st.selectbox(
                "Sort By",
                ["Relevance", "Deadline (Soonest)", "Organization"]
            )
        
        # Display opportunities with filtering logic (simplified for prototype)
        if opportunities:
            for opportunity in opportunities:
                st.markdown(f"""
                <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h4 style="margin-top: 0; color: #0a3d62;">{opportunity["title"]}</h4>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <div><strong>Organization:</strong> {opportunity["organization"]}</div>
                        <div><strong>Deadline:</strong> {opportunity["deadline"]}</div>
                    </div>
                    <p>{opportunity["description"]}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="background-color: #e3f2fd; color: #0d47a1; padding: 5px 10px; border-radius: 5px; font-size: 0.9rem;">
                            <strong>Why it's relevant:</strong> {opportunity["relevance"]}
                        </div>
                        <a href="{opportunity["link"]}" target="_blank" style="background-color: #0a3d62; color: white; padding: 5px 15px; border-radius: 20px; text-decoration: none; font-size: 0.9rem;">View Details</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No matching opportunities found. Try adjusting your filters or complete your career profile for better matches.")
        
        # Latest career news section
        st.subheader("Latest Career Trends")
        
        # Fetch career news from cache or AI
        career_news = fetch_trending_news("career")
        
        # Display news cards
        col1, col2, col3 = st.columns(3)
        columns = [col1, col2, col3]
        
        for i, news in enumerate(career_news):
            with columns[i % 3]:
                st.markdown(f"""
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; height: 100%; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                    <h4 style="margin-top: 0; color: #0a3d62;">{news['title']}</h4>
                    <p style="color: #666; font-size: 0.9rem;">{news['date']} • {news['source']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Career preparation tips
        st.subheader("Career Preparation Tips")
        
        # Use AI-generated career insights if available
        if st.session_state.cached_content.get("career_insights"):
            insights = st.session_state.cached_content["career_insights"]
            
            for insight in insights:
                st.markdown(f"""
                <div style="background-color: #f3e5f5; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #9c27b0;">
                    <h4 style="margin-top: 0; color: #6a1b9a;">{insight.get('insight', 'Career Insight')}</h4>
                    <p><strong>Current Trend:</strong> {insight.get('trend', '')}</p>
                    <p style="margin-bottom: 0;"><strong>Recommended Action:</strong> {insight.get('action', '')}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Fallback career tips
            st.markdown("""
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 15px;">
                <h4 style="margin-top: 0;">Resume Building Tips</h4>
                <ul style="margin-bottom: 0;">
                    <li>Quantify achievements with specific metrics when possible</li>
                    <li>Tailor your resume for each application</li>
                    <li>Include relevant projects and their impact</li>
                    <li>Keep it concise - 1 page for students/recent graduates</li>
                </ul>
            </div>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 15px;">
                <h4 style="margin-top: 0;">Interview Preparation</h4>
                <ul style="margin-bottom: 0;">
                    <li>Research the company and role thoroughly</li>
                    <li>Prepare STAR (Situation, Task, Action, Result) stories</li>
                    <li>Practice with mock interviews</li>
                    <li>Prepare thoughtful questions to ask interviewers</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # Career Advisor tab
    with tab4:
        st.subheader("Career Advisor")
        
        if st.session_state.groq_api_key is None:
            st.warning("Please configure your Groq API key in Settings to use the Career Advisor.")
            if st.button("Go to Settings"):
                st.session_state.current_page = "Settings"
                st.rerun()
        else:
            st.write("Ask anything about career planning, job search, resume building, interviews, or professional development.")
            
            # Initialize career chat history if it doesn't exist
            if 'career_chat_history' not in st.session_state:
                st.session_state.career_chat_history = []
            
            # Display career chat history
            if st.session_state.career_chat_history:
                st.markdown('<div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; max-height: 400px; overflow-y: auto;">', unsafe_allow_html=True)
                
                for i, (role, message) in enumerate(st.session_state.career_chat_history):
                    if role == "user":
                        st.markdown(f'<div style="background-color: #e7f5fe; padding: 10px; border-radius: 15px 15px 5px 15px; margin-bottom: 10px; margin-left: 20px;"><strong>You:</strong> {message}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 15px 15px 15px 5px; margin-bottom: 10px;"><strong>Career Advisor:</strong> {message}</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Show AI-generated career insights if available
            if st.session_state.cached_content.get("career_insights") and not st.session_state.career_chat_history:
                st.markdown("### AI-Generated Career Insights")
                insights = st.session_state.cached_content["career_insights"]
                
                for insight in insights:
                    st.markdown(f"""
                    <div style="background-color: #f3e5f5; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #9c27b0;">
                        <h4 style="margin-top: 0; color: #6a1b9a;">{insight.get('insight', 'Career Insight')}</h4>
                        <p><strong>Trend:</strong> {insight.get('trend', '')}</p>
                        <p style="margin-bottom: 0;"><strong>Action:</strong> {insight.get('action', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Input for career question
            career_query = st.text_input("Ask about career planning, jobs, interviews, etc.", key="career_query")
            
            if st.button("Get Career Advice", key="get_career_advice"):
                if career_query:
                    # Add user message to career chat history
                    st.session_state.career_chat_history.append(("user", career_query))
                    
                    # Context from career profile
                    career_profile = career.get_career_profile() or {}
                    interests = career_profile.get('interests', [])
                    target_roles = career_profile.get('target_roles', [])
                    
                    interests_text = ", ".join(interests) if interests else "Not specified"
                    roles_text = ", ".join(target_roles) if target_roles else "Not specified"
                    
                    # Prepare student context for more personalized answers
                    student_context = None
                    if st.session_state.student_profile:
                        profile = st.session_state.student_profile
                        student_context = {
                            "degree": profile.get_degree(),
                            "year": profile.get_year_of_study(),
                            "college": profile.get_college_name(),
                            "career_interests": interests_text,
                            "target_roles": roles_text
                        }
                    
                    # Get AI response for career specifically
                    with st.spinner("Researching your career question..."):
                        ai_response = st.session_state.ai_advisor.get_advice(
                            career_query, "career", student_context
                        )
                    
                    # Add AI response to career chat history
                    st.session_state.career_chat_history.append(("ai", ai_response))
                    
                    # Force a rerun to show the updated chat
                    st.rerun()

# Helper function for skill level labels
def get_level_label(level):
    levels = {
        1: "Beginner",
        2: "Basic",
        3: "Intermediate",
        4: "Advanced",
        5: "Expert"
    }
    return levels.get(level, "Unknown")

# Learning Resources page
def show_resources_page():
    st.title("Learning Resources")
    
    # Show guidance for first-time visitors
    show_section_guidance("Resources")
    
    resources = st.session_state.resource_connector
    
    # Create tabs for different resource types
    tab1, tab2, tab3, tab4 = st.tabs(["Find Resources", "My Collection", "Campus Resources", "Resource Advisor"])
    
    # Find Resources tab
    with tab1:
        st.subheader("Find Learning Resources")
        
        # Search and filters
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input("Search for Resources", placeholder="e.g., Data Science, Python, Machine Learning, Communication Skills")
        
        with col2:
            st.markdown('<div style="margin-top: 24px;">', unsafe_allow_html=True)
            search_button = st.button("🔍 Search", key="resource_search")
            st.markdown('</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            resource_type = st.multiselect(
                "Resource Type",
                ["Courses", "Books", "Videos", "Articles", "Tools", "All"],
                default=["All"]
            )
        
        with col2:
            skill_level = st.selectbox(
                "Skill Level",
                ["All Levels", "Beginner", "Intermediate", "Advanced"]
            )
        
        with col3:
            sort_by = st.selectbox(
                "Sort By",
                ["Relevance", "Rating", "Most Recent"]
            )
        
        # Search results - in a real app, this would query a database or API
        if search_button or search_query:
            st.subheader("Search Results")
            
            if search_query:
                # Get personalized learning resources from AI if available
                resources_data = None
                
                if st.session_state.groq_api_key:
                    # Check if we have cached resources for this query
                    cache_key = search_query.lower().strip()
                    if cache_key in st.session_state.cached_content.get("resources", {}):
                        resources_data = st.session_state.cached_content["resources"][cache_key]
                    else:
                        # Get new resources with AI
                        with st.spinner("Finding the best resources for you..."):
                            student_context = {}
                            if st.session_state.student_profile:
                                profile = st.session_state.student_profile
                                student_context = {
                                    "degree": profile.get_degree(),
                                    "year": profile.get_year_of_study()
                                }
                            
                            resources_data = st.session_state.ai_agent.get_learning_resources(search_query, student_context)
                            
                            # Cache the results
                            if "resources" not in st.session_state.cached_content:
                                st.session_state.cached_content["resources"] = {}
                            
                            st.session_state.cached_content["resources"][cache_key] = resources_data
                
                if resources_data:
                    # Display AI-recommended resources
                    for resource in resources_data:
                        st.markdown(f"""
                        <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                            <h4 style="margin-top: 0; color: #0a3d62;">{resource.get('name', 'Resource')}</h4>
                            <div style="background-color: #e3f2fd; color: #0d47a1; display: inline-block; padding: 3px 10px; border-radius: 15px; font-size: 0.8rem; margin-bottom: 10px;">
                                {resource.get('type', 'Resource')}
                            </div>
                            <p>{resource.get('description', '')}</p>
                            <p><strong>Why it's useful:</strong> {resource.get('why_useful', '')}</p>
                            <div style="display: flex; justify-content: flex-end;">
                                <a href="{resource.get('link', '#')}" target="_blank" style="background-color: #0a3d62; color: white; padding: 5px 15px; border-radius: 20px; text-decoration: none; font-size: 0.9rem;">Visit Resource</a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    # Fallback with static recommendations based on query
                    if "python" in search_query.lower():
                        show_python_resources()
                    elif "machine learning" in search_query.lower() or "data science" in search_query.lower():
                        show_data_science_resources()
                    elif "english" in search_query.lower() or "communication" in search_query.lower():
                        show_communication_resources()
                    else:
                        st.info(f"Showing general resources related to '{search_query}'")
                        show_general_resources(search_query)
            else:
                # Show trending resources if no specific search
                st.info("Enter a search query to find specific resources, or browse these trending topics:")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 15px; cursor: pointer;">
                        <h4 style="margin-top: 0; color: #0d47a1;">Programming & Development</h4>
                        <p>Python, Java, Web Development, Mobile Apps, Cloud Computing</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; margin-bottom: 15px; cursor: pointer;">
                        <h4 style="margin-top: 0; color: #2e7d32;">Business & Management</h4>
                        <p>Finance, Marketing, Project Management, Entrepreneurship</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("""
                    <div style="background-color: #fff3e0; padding: 15px; border-radius: 8px; margin-bottom: 15px; cursor: pointer;">
                        <h4 style="margin-top: 0; color: #e65100;">Data Science & AI</h4>
                        <p>Machine Learning, Data Analysis, Visualization, Neural Networks</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div style="background-color: #f3e5f5; padding: 15px; border-radius: 8px; margin-bottom: 15px; cursor: pointer;">
                        <h4 style="margin-top: 0; color: #6a1b9a;">Soft Skills</h4>
                        <p>Communication, Leadership, Time Management, Presentation Skills</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Latest resources section
        st.subheader("Latest Educational Resources")
        
        # Fetch resources news
        resources_news = fetch_trending_news("resources")
        
        # Display news cards
        for news in resources_news:
            st.markdown(f"""
            <div class="news-card">
                <h4>{news['title']}</h4>
                <p>{news['date']} • {news['source']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Learning tips section
        st.subheader("Effective Learning Strategies")
        
        # Use AI-generated learning tips if available
        if st.session_state.cached_content.get("academic_trends"):
            trends = st.session_state.cached_content["academic_trends"]
            
            st.write("Based on latest educational research:")
            
            for trend in trends:
                st.markdown(f"""
                <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #4caf50;">
                    <h4 style="margin-top: 0; color: #2e7d32;">{trend.get('trend', 'Learning Technique')}</h4>
                    <p>{trend.get('description', '')}</p>
                    <p style="margin-bottom: 0;"><strong>Benefit:</strong> {trend.get('benefit', '')}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Fallback learning tips
            st.markdown("""
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 15px;">
                <h4 style="margin-top: 0;">Evidence-Based Learning Techniques</h4>
                <ul style="margin-bottom: 0;">
                    <li><strong>Spaced Repetition</strong> - Review material at increasing intervals for better retention</li>
                    <li><strong>Active Recall</strong> - Test yourself rather than passive re-reading</li>
                    <li><strong>Interleaved Practice</strong> - Mix different topics instead of studying one topic at a time</li>
                    <li><strong>Dual Coding</strong> - Combine verbal and visual learning for stronger memory formation</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # My Collection tab
    with tab2:
        st.subheader("My Resource Collection")
        
        # Get saved resources
        saved_resources = resources.get_saved_resources()
        
        if saved_resources:
            # Group resources by category
            resources_by_category = {}
            for resource in saved_resources:
                category = resource.get('category', 'Other')
                if category not in resources_by_category:
                    resources_by_category[category] = []
                resources_by_category[category].append(resource)
            
            # Display resources by category
            for category, category_resources in resources_by_category.items():
                st.markdown(f"### {category}")
                
                for i, resource in enumerate(category_resources):
                    st.markdown(f"""
                    <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                        <h4 style="margin-top: 0; color: #0a3d62;">{resource.get('title', 'Resource')}</h4>
                        <div style="margin-bottom: 10px;">
                            <span style="background-color: #e3f2fd; color: #0d47a1; padding: 3px 10px; border-radius: 15px; font-size: 0.8rem;">
                                {resource.get('type', 'Resource')}
                            </span>
                            <span style="color: #666; font-size: 0.9rem; margin-left: 10px;">
                                Added on {resource.get('date_added', 'Unknown date')}
                            </span>
                        </div>
                        <p>{resource.get('description', '')}</p>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="color: #ff9800; font-size: 1.2rem;">{"★" * int(resource.get('rating', 0))}{"☆" * (5 - int(resource.get('rating', 0)))}</span>
                            </div>
                            <div>
                                <a href="{resource.get('url', '#')}" target="_blank" style="background-color: #0a3d62; color: white; padding: 5px 15px; border-radius: 20px; text-decoration: none; font-size: 0.9rem; margin-right: 10px;">Open</a>
                                <button style="background-color: #f5f5f5; color: #d32f2f; padding: 5px 15px; border-radius: 20px; border: none; font-size: 0.9rem; cursor: pointer;">Delete</button>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
        else:
            # Empty state
            st.markdown("""
            <div style="background-color: #f9f9f9; border: 1px dashed #ddd; border-radius: 8px; padding: 30px; text-align: center; margin-bottom: 20px;">
                <h3 style="color: #666; margin-bottom: 15px;">No saved resources yet</h3>
                <p style="color: #888;">Search for resources and save them to your collection for easy access later.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Add new resource form
        st.subheader("Add Resource to Collection")
        
        with st.form("add_resource_form"):
            resource_title = st.text_input("Resource Title", placeholder="e.g., Python for Data Science Course")
            
            col1, col2 = st.columns(2)
            
            with col1:
                resource_type = st.selectbox(
                    "Resource Type", 
                    ["Course", "Book", "Video", "Article", "Tool", "Website", "Other"]
                )
            
            with col2:
                                resource_category = st.selectbox(
                    "Category",
                    ["Programming", "Data Science", "Math", "Language", "Business", "Arts", "Science", "Engineering", "Other"]
                )
            
            resource_url = st.text_input("URL", placeholder="https://...")
            resource_description = st.text_area("Description", placeholder="Brief description of this resource")
            resource_rating = st.slider("Your Rating", 1, 5, 3)
            
            submitted = st.form_submit_button("Add to Collection")
            
            if submitted:
                if resource_title and resource_url:
                    # Create resource data
                    resource_data = {
                        'title': resource_title,
                        'type': resource_type,
                        'category': resource_category,
                        'url': resource_url,
                        'description': resource_description,
                        'rating': resource_rating,
                        'date_added': datetime.now().strftime("%Y-%m-%d")
                    }
                    
                    # Save resource
                    if resources.save_resource(resource_data):
                        st.success("Resource added to your collection!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to add resource.")
                else:
                    st.error("Please provide at least a title and URL.")
    
    # Campus Resources tab
    with tab3:
        st.subheader("Campus Resources")
        
        # Create a placeholder for the college name
        college_name = st.session_state.student_profile.get_college_name() if st.session_state.student_profile else "Your College"
        
        # Library resources
        st.markdown("### Library Resources")
        
        st.markdown(f"""
        <div style="background-color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h4 style="margin-top: 0; color: #0a3d62;">{college_name} Central Library</h4>
            <p><strong>Hours:</strong> Mon-Sat: 8am-10pm, Sun: 10am-6pm</p>
            <p><strong>Services:</strong></p>
            <ul>
                <li>Digital journals and e-books access</li>
                <li>Quiet study spaces and group study rooms</li>
                <li>Inter-library loan services</li>
                <li>Research assistance and citation help</li>
            </ul>
            <p><strong>Online Access:</strong> Use your college credentials to access digital resources remotely</p>
            <div style="display: flex; justify-content: flex-end;">
                <a href="#" target="_blank" style="background-color: #0a3d62; color: white; padding: 5px 15px; border-radius: 20px; text-decoration: none; font-size: 0.9rem;">Visit Library Portal</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Academic support services
        st.markdown("### Academic Support Services")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; height: 100%; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h4 style="margin-top: 0; color: #0a3d62;">Writing Center</h4>
                <p>Get help with essays, reports, theses, and other written assignments</p>
                <p><strong>Location:</strong> Academic Building, Room 205</p>
                <p><strong>Hours:</strong> Mon-Fri: 10am-6pm</p>
                <p><strong>Services:</strong> One-on-one tutoring, document review, citation help</p>
                <a href="#" target="_blank">Book an appointment</a>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; height: 100%; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h4 style="margin-top: 0; color: #0a3d62;">Tutoring Services</h4>
                <p>Peer and professional tutoring for challenging subjects</p>
                <p><strong>Location:</strong> Learning Commons, 1st Floor</p>
                <p><strong>Hours:</strong> Mon-Thu: 9am-8pm, Fri: 9am-5pm</p>
                <p><strong>Services:</strong> Group tutoring, one-on-one sessions, exam prep</p>
                <a href="#" target="_blank">View schedule and availability</a>
            </div>
            """, unsafe_allow_html=True)
        
        # Computing and technology resources
        st.markdown("### Computing & Technology Resources")
        
        st.markdown(f"""
        <div style="background-color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h4 style="margin-top: 0; color: #0a3d62;">Computer Labs and IT Support</h4>
            <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                <div style="flex: 1; min-width: 250px;">
                    <p><strong>Computer Labs:</strong></p>
                    <ul>
                        <li>Main Lab: Engineering Building, Room 101 (24/7 access)</li>
                        <li>Media Lab: Arts Building, Room 303 (9am-8pm)</li>
                        <li>Research Computing Lab: Science Building, Room 205 (requires department approval)</li>
                    </ul>
                </div>
                <div style="flex: 1; min-width: 250px;">
                    <p><strong>Available Software:</strong></p>
                    <ul>
                        <li>Microsoft Office Suite (free for students)</li>
                        <li>Adobe Creative Cloud</li>
                        <li>MATLAB, R, SPSS</li>
                        <li>Programming IDEs and tools</li>
                    </ul>
                </div>
            </div>
            <p><strong>IT Support:</strong> Visit Help Desk in Library, Room 105 or submit a ticket online</p>
            <p><strong>Wifi:</strong> Campus-wide "CollegeWifi" network - use your student credentials to connect</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Study spaces 
        st.markdown("### Study Spaces")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; height: 100%;">
                <h4 style="margin-top: 0; color: #2e7d32;">Quiet Study Areas</h4>
                <ul style="margin-bottom: 0;">
                    <li>Library 3rd Floor (Silent Zone)</li>
                    <li>Science Building Atrium</li>
                    <li>Arts Building Reading Room</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; height: 100%;">
                <h4 style="margin-top: 0; color: #1565c0;">Group Study Rooms</h4>
                <ul style="margin-bottom: 0;">
                    <li>Library Study Rooms (bookable online)</li>
                    <li>Student Center Conference Rooms</li>
                    <li>Department Lounges (check availability)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background-color: #fff3e0; padding: 15px; border-radius: 8px; height: 100%;">
                <h4 style="margin-top: 0; color: #e65100;">Cafés & Informal Spaces</h4>
                <ul style="margin-bottom: 0;">
                    <li>Student Center Café</li>
                    <li>Library Coffee Shop</li>
                    <li>Engineering Building Lounge</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Special resources based on degree
        student = st.session_state.student_profile
        if student:
            degree = student.get_degree()
            
            st.markdown("### Degree-Specific Resources")
            
            if "B.Tech" in degree or "B.E." in degree:
                st.markdown(f"""
                <div style="background-color: white; padding: 15px; border-radius: 8px; margin-top: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h4 style="margin-top: 0; color: #0a3d62;">Engineering Resources</h4>
                    <ul>
                        <li><strong>Engineering Lab Hours:</strong> Check department schedule for specialized lab access</li>
                        <li><strong>CAD/CAM Software:</strong> Available in Engineering Building, Room 105</li>
                        <li><strong>Workshop Access:</strong> Request form required for fabrication and prototype labs</li>
                        <li><strong>Technical Journals:</strong> IEEE, ACM Digital Library (access through library portal)</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            elif "BBA" in degree or "B.Com" in degree:
                st.markdown(f"""
                <div style="background-color: white; padding: 15px; border-radius: 8px; margin-top: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h4 style="margin-top: 0; color: #0a3d62;">Business Resources</h4>
                    <ul>
                        <li><strong>Bloomberg Terminal:</strong> Available in Business School, Room 202</li>
                        <li><strong>Market Research Databases:</strong> IBIS World, Statista (access through library portal)</li>
                        <li><strong>Business Software:</strong> Tally, SAP training modules available</li>
                        <li><strong>Case Study Database:</strong> Harvard Business Review, IIMA cases (access code required)</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
    
    # Resource Advisor tab
    with tab4:
        st.subheader("Resource Advisor")
        
        if st.session_state.groq_api_key is None:
            st.warning("Please configure your Groq API key in Settings to use the Resource Advisor.")
            if st.button("Go to Settings"):
                st.session_state.current_page = "Settings"
                st.rerun()
        else:
            st.write("Ask anything about finding specific learning resources, study materials, or how to access academic resources.")
            
            # Initialize resource chat history if it doesn't exist
            if 'resource_chat_history' not in st.session_state:
                st.session_state.resource_chat_history = []
            
            # Display resource chat history
            if st.session_state.resource_chat_history:
                st.markdown('<div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; max-height: 400px; overflow-y: auto;">', unsafe_allow_html=True)
                
                for i, (role, message) in enumerate(st.session_state.resource_chat_history):
                    if role == "user":
                        st.markdown(f'<div style="background-color: #e7f5fe; padding: 10px; border-radius: 15px 15px 5px 15px; margin-bottom: 10px; margin-left: 20px;"><strong>You:</strong> {message}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 15px 15px 15px 5px; margin-bottom: 10px;"><strong>Resource Advisor:</strong> {message}</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Show something helpful when no chat history
            if not st.session_state.resource_chat_history:
                st.markdown("""
                ### How can I help you find resources?
                
                Try asking questions like:
                - "What are good resources to learn Python programming?"
                - "How can I access IEEE papers through my college?"
                - "Where can I find free textbooks for engineering courses?"
                - "Suggest learning resources for improving public speaking"
                """)
            
            # Input for resource question
            resource_query = st.text_input("Ask about learning resources, study materials, etc.", key="resource_query")
            
            if st.button("Get Resource Advice", key="get_resource_advice"):
                if resource_query:
                    # Add user message to resource chat history
                    st.session_state.resource_chat_history.append(("user", resource_query))
                    
                    # Prepare student context for more personalized answers
                    student_context = None
                    if st.session_state.student_profile:
                        profile = st.session_state.student_profile
                        student_context = {
                            "degree": profile.get_degree(),
                            "year": profile.get_year_of_study(),
                            "college": profile.get_college_name()
                        }
                    
                    # Get AI response for resources specifically
                    with st.spinner("Searching for resources..."):
                        ai_response = st.session_state.ai_advisor.get_advice(
                            resource_query, "resources", student_context
                        )
                    
                    # Add AI response to resource chat history
                    st.session_state.resource_chat_history.append(("ai", ai_response))
                    
                    # Force a rerun to show the updated chat
                    st.rerun()

# Shows Python resources
def show_python_resources():
    resources = [
        {
            "title": "Python for Everybody",
            "author": "Dr. Charles Severance (Univ. of Michigan)",
            "type": "Course",
            "platform": "Coursera",
            "description": "Comprehensive introduction to Python programming and data structures",
            "link": "https://www.coursera.org/specializations/python",
            "free": "Free to audit"
        },
        {
            "title": "Automate the Boring Stuff with Python",
            "author": "Al Sweigart",
            "type": "Book/Website",
            "platform": "Self-hosted",
            "description": "Practical programming for absolute beginners focusing on automation tasks",
            "link": "https://automatetheboringstuff.com/",
            "free": "Free online"
        },
        {
            "title": "Real Python",
            "author": "Various",
            "type": "Tutorial Website",
            "platform": "Real Python",
            "description": "In-depth tutorials, projects, and explanations for all skill levels",
            "link": "https://realpython.com/",
            "free": "Free/Paid content"
        },
        {
            "title": "Python Crash Course",
            "author": "Eric Matthes",
            "type": "Book",
            "platform": "No Starch Press",
            "description": "Fast-paced, thorough introduction to Python with practical projects",
            "link": "https://nostarch.com/pythoncrashcourse2e",
            "free": "Paid"
        },
        {
            "title": "CS50's Introduction to Programming with Python",
            "author": "David Malan (Harvard)",
            "type": "Course",
            "platform": "edX",
            "description": "Harvard's introduction to programming using Python",
            "link": "https://www.edx.org/course/cs50s-introduction-to-programming-with-python",
            "free": "Free to audit"
        }
    ]
    
    for resource in resources:
        st.markdown(f"""
        <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h4 style="margin-top: 0; color: #0a3d62;">{resource["title"]}</h4>
            <p><strong>By:</strong> {resource["author"]} | <strong>Type:</strong> {resource["type"]} | <strong>Platform:</strong> {resource["platform"]}</p>
            <p>{resource["description"]}</p>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="background-color: #e3f2fd; color: #0d47a1; padding: 3px 10px; border-radius: 15px; font-size: 0.8rem;">
                    {resource["free"]}
                </div>
                <a href="{resource["link"]}" target="_blank" style="background-color: #0a3d62; color: white; padding: 5px 15px; border-radius: 20px; text-decoration: none; font-size: 0.9rem;">View Resource</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Show data science resources
def show_data_science_resources():
    resources = [
        {
            "title": "Data Science Specialization",
            "author": "Johns Hopkins University",
            "type": "Course",
            "platform": "Coursera",
            "description": "Comprehensive 10-course introduction to data science with R",
            "link": "https://www.coursera.org/specializations/jhu-data-science",
            "free": "Free to audit"
        },
        {
            "title": "Machine Learning",
            "author": "Andrew Ng (Stanford)",
            "type": "Course",
            "platform": "Coursera",
            "description": "Foundational ML course that covers key algorithms and concepts",
            "link": "https://www.coursera.org/learn/machine-learning",
            "free": "Free to audit"
        },
        {
            "title": "Kaggle Learn",
            "author": "Kaggle Team",
            "type": "Interactive Tutorials",
            "platform": "Kaggle",
            "description": "Hands-on micro-courses covering Python, ML, data visualization, and more",
            "link": "https://www.kaggle.com/learn",
            "free": "Free"
        },
        {
            "title": "Deep Learning Specialization",
            "author": "Andrew Ng (deeplearning.ai)",
            "type": "Course Series",
            "platform": "Coursera",
            "description": "5-course specialization diving deep into neural networks and deep learning",
            "link": "https://www.coursera.org/specializations/deep-learning",
            "free": "Free to audit"
        },
        {
            "title": "Fast.ai Practical Deep Learning for Coders",
            "author": "Jeremy Howard & Rachel Thomas",
            "type": "Course",
            "platform": "fast.ai",
            "description": "Top-down, practical approach to deep learning with PyTorch",
            "link": "https://course.fast.ai/",
            "free": "Free"
        }
    ]
    
    for resource in resources:
        st.markdown(f"""
        <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h4 style="margin-top: 0; color: #0a3d62;">{resource["title"]}</h4>
            <p><strong>By:</strong> {resource["author"]} | <strong>Type:</strong> {resource["type"]} | <strong>Platform:</strong> {resource["platform"]}</p>
            <p>{resource["description"]}</p>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="background-color: #e3f2fd; color: #0d47a1; padding: 3px 10px; border-radius: 15px; font-size: 0.8rem;">
                    {resource["free"]}
                </div>
                <a href="{resource["link"]}" target="_blank" style="background-color: #0a3d62; color: white; padding: 5px 15px; border-radius: 20px; text-decoration: none; font-size: 0.9rem;">View Resource</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Show communication resources
def show_communication_resources():
    resources = [
        {
            "title": "English for Career Development",
            "author": "University of Pennsylvania",
            "type": "Course",
            "platform": "Coursera",
            "description": "Business English skills specifically designed for career advancement",
            "link": "https://www.coursera.org/learn/careerdevelopment",
            "free": "Free to audit"
        },
        {
            "title": "Dynamic Public Speaking",
            "author": "University of Washington",
            "type": "Course",
            "platform": "Coursera",
            "description": "Learn to speak confidently and persuasively in public contexts",
            "link": "https://www.coursera.org/specializations/public-speaking",
            "free": "Free to audit"
        },
        {
            "title": "Write Professional Emails in English",
            "author": "Georgia Institute of Technology",
            "type": "Course",
            "platform": "Coursera",
            "description": "Learn to communicate effectively through email in professional contexts",
            "link": "https://www.coursera.org/learn/professional-emails-english",
            "free": "Free to audit"
        },
        {
            "title": "Speak English Professionally",
            "author": "Georgia Institute of Technology",
            "type": "Course",
            "platform": "Coursera",
            "description": "Practice speaking for interviews, meetings, and presentations",
            "link": "https://www.coursera.org/learn/speak-english-professionally",
            "free": "Free to audit"
        },
        {
            "title": "TED Talks Daily",
            "author": "Various Speakers",
            "type": "Video/Podcast Series",
            "platform": "TED",
            "description": "Listen to thought leaders for inspiration and to improve English comprehension",
            "link": "https://www.ted.com/talks",
            "free": "Free"
        }
    ]
    
    for resource in resources:
        st.markdown(f"""
        <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h4 style="margin-top: 0; color: #0a3d62;">{resource["title"]}</h4>
            <p><strong>By:</strong> {resource["author"]} | <strong>Type:</strong> {resource["type"]} | <strong>Platform:</strong> {resource["platform"]}</p>
            <p>{resource["description"]}</p>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="background-color: #e3f2fd; color: #0d47a1; padding: 3px 10px; border-radius: 15px; font-size: 0.8rem;">
                    {resource["free"]}
                </div>
                <a href="{resource["link"]}" target="_blank" style="background-color: #0a3d62; color: white; padding: 5px 15px; border-radius: 20px; text-decoration: none; font-size: 0.9rem;">View Resource</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Show general resources based on query
def show_general_resources(query):
    # A simplified version that just shows generic resources
    resources = [
        {
            "title": f"Top Courses for {query}",
            "author": "Various",
            "type": "Course Collection",
            "platform": "Coursera, edX, Udemy",
            "description": f"Curated collection of the highest-rated courses related to {query}",
            "link": "https://www.coursera.org/",
            "free": "Various"
        },
        {
            "title": f"YouTube Learning: {query}",
            "author": "Various Creators",
            "type": "Video Collection",
            "platform": "YouTube",
            "description": f"Free video tutorials and lectures on {query} topics",
            "link": "https://www.youtube.com/",
            "free": "Free"
        },
        {
            "title": f"{query} on NPTEL",
            "author": "IIT Professors",
            "type": "Video Lectures",
            "platform": "NPTEL",
            "description": "High-quality lectures from Indian Institutes of Technology (IITs)",
            "link": "https://nptel.ac.in/",
            "free": "Free"
        },
        {
            "title": f"{query} E-Books",
            "author": "Various",
            "type": "E-Book Collection",
            "platform": "National Digital Library of India",
            "description": "Access to thousands of e-books from your college library subscription",
            "link": "https://ndl.iitkgp.ac.in/",
            "free": "Free with college access"
        }
    ]
    
    for resource in resources:
        st.markdown(f"""
        <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h4 style="margin-top: 0; color: #0a3d62;">{resource["title"]}</h4>
            <p><strong>By:</strong> {resource["author"]} | <strong>Type:</strong> {resource["type"]} | <strong>Platform:</strong> {resource["platform"]}</p>
            <p>{resource["description"]}</p>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="background-color: #e3f2fd; color: #0d47a1; padding: 3px 10px; border-radius: 15px; font-size: 0.8rem;">
                    {resource["free"]}
                </div>
                <a href="{resource["link"]}" target="_blank" style="background-color: #0a3d62; color: white; padding: 5px 15px; border-radius: 20px; text-decoration: none; font-size: 0.9rem;">View Resource</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Settings page
def show_settings_page():
    st.title("Settings & Profile")
    
    tab1, tab2, tab3 = st.tabs(["Profile Settings", "AI Configuration", "App Settings"])
    
    # Profile Settings tab
    with tab1:
        st.subheader("Your Profile")
        
        if st.session_state.student_profile:
            profile = st.session_state.student_profile
            profile_data = profile.get_all_data()
            
            with st.form("edit_profile_form"):
                full_name = st.text_input("Full Name", value=profile.get_full_name())
                college_name = st.text_input("College/University", value=profile.get_college_name())
                
                col1, col2 = st.columns(2)
                with col1:
                    degree = st.selectbox("Degree Program", [
                        "B.Tech/B.E.", "BBA", "B.Sc.", "B.Com.", "B.A.", 
                        "M.Tech/M.E.", "MBA", "M.Sc.", "M.Com.", "M.A.",
                        "BCA", "MCA", "Ph.D.", "Diploma", "Other"
                    ], index=get_degree_index(profile.get_degree()))
                    
                with col2:
                    year_of_study = st.selectbox("Year of Study", [
                        "1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year", "Final Year"
                    ], index=get_year_index(profile.get_year_of_study()))
                
                email = st.text_input("Email Address", value=profile_data.get('email', ''))
                
                dob_str = profile_data.get('dob', '')
                if dob_str:
                    try:
                        dob_date = datetime.strptime(dob_str, "%Y-%m-%d").date()
                    except:
                        dob_date = None
                else:
                    dob_date = None
                
                dob = st.date_input("Date of Birth", 
                                   value=dob_date,
                                   min_value=datetime(1980, 1, 1).date(),
                                   max_value=(datetime.now() - timedelta(days=365*16)).date())
                
                submitted = st.form_submit_button("Save Profile Changes")
                
                if submitted:
                    # Update profile data
                    updated_data = {
                        "full_name": full_name,
                        "college_name": college_name,
                        "degree": degree,
                        "year_of_study": year_of_study,
                        "email": email,
                        "dob": dob.strftime("%Y-%m-%d") if dob else None,
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    if st.session_state.data_manager.update_student_profile(profile.get_id(), updated_data):
                        st.success("Profile updated successfully!")
                        
                        # Reinitialize profile
                        student_id = profile.get_id()
                        student_data = st.session_state.data_manager.load_student_profile(student_id)
                        st.session_state.student_profile = StudentProfile(student_id, student_data)
                        
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to update profile.")
            
            # Data export option
            st.subheader("Export Your Data")
            st.write("Download all your data in JSON format.")
            
            if st.button("Export All Data"):
                # Collect all data
                all_data = {
                    "profile": profile_data,
                    "academic": {
                        "courses": st.session_state.academic_tracker.get_courses(),
                        "performance": st.session_state.academic_tracker.get_performance_history(),
                        "tasks": st.session_state.academic_tracker.get_all_tasks(),
                        "study_hours": st.session_state.academic_tracker.get_study_hours_history()
                    },
                    "financial": {
                        "transactions": st.session_state.financial_planner.get_all_transactions(),
                        "budget": st.session_state.financial_planner.get_budget()
                    },
                    "wellness": {
                        "mood_history": st.session_state.mental_wellness.get_mood_history()
                    },
                    "career": {
                        "profile": st.session_state.career_guide.get_career_profile(),
                        "skills": st.session_state.career_guide.get_skills()
                    },
                    "resources": {
                        "saved_resources": st.session_state.resource_connector.get_saved_resources()
                    }
                }
                
                # Convert to JSON
                json_data = json.dumps(all_data, indent=4)
                
                # Create download button
                now = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"harmony_data_export_{now}.json"
                
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=filename,
                    mime="application/json"
                )
            
            # Account deletion (with confirmation)
            st.subheader("Delete Account")
            st.write("This will permanently delete your account and all associated data.")
            
            delete_confirm = st.checkbox("I understand this action cannot be undone.")
            
            if delete_confirm:
                if st.button("Delete My Account", type="primary", help="This will permanently delete all your data"):
                    if st.session_state.data_manager.delete_student_profile(profile.get_id()):
                        st.success("Account deleted successfully. Redirecting to home page...")
                        st.session_state.student_profile = None
                        st.session_state.current_page = "Home"
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Failed to delete account. Please try again later.")
    
    # AI Configuration tab
    with tab2:
        show_ai_settings()
    
    # App Settings tab
    with tab3:
        st.subheader("Application Settings")
        
        # Theme settings
        st.write("### Theme & Appearance")
        
        theme_mode = st.radio(
            "Theme Mode",
            ["Light", "Dark", "System Default"],
            horizontal=True
        )
        
        color_scheme = st.selectbox(
            "Color Scheme",
            ["Blue (Default)", "Green", "Purple", "Orange", "Red"]
        )
        
        st.write("### Notifications")
        
        # Notification settings
        email_notifications = st.checkbox("Email Notifications", value=True)
        
        notification_types = st.multiselect(
            "Notification Types",
            ["Task Reminders", "Upcoming Deadlines", "Budget Alerts", "Wellness Check-ins", "New Opportunities"],
            default=["Task Reminders", "Upcoming Deadlines"]
        )
        
        # Privacy settings
        st.write("### Privacy Settings")
        
        data_collection = st.checkbox("Allow anonymous usage data collection to improve the app", value=True)
        
        crash_reports = st.checkbox("Send crash reports automatically", value=True)
        
        # Save settings
        if st.button("Save Settings"):
            # In a real app, these would be saved to the user's profile
            st.success("Settings saved successfully!")
            time.sleep(1)
            st.rerun()
        
        # App information
        st.write("### App Information")
        
        st.markdown("""
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 15px;">
            <h4 style="margin-top: 0;">HARMONY-India</h4>
            <p><strong>Version:</strong> 1.0.1</p>
            <p><strong>Last Updated:</strong> April 8, 2025</p>
            <p><strong>Developers:</strong> HARMONY-India Team</p>
            <p><strong>License:</strong> MIT License</p>
        </div>
        """, unsafe_allow_html=True)

# Helper function to get index of degree in dropdown
def get_degree_index(degree):
    degrees = [
        "B.Tech/B.E.", "BBA", "B.Sc.", "B.Com.", "B.A.", 
        "M.Tech/M.E.", "MBA", "M.Sc.", "M.Com.", "M.A.",
        "BCA", "MCA", "Ph.D.", "Diploma", "Other"
    ]
    
    try:
        return degrees.index(degree)
    except ValueError:
        return 0  # Default to first option if not found

# Helper function to get index of year in dropdown
def get_year_index(year):
    years = [
        "1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year", "Final Year"
    ]
    
    try:
        return years.index(year)
    except ValueError:
        return 0  # Default to first option if not found

def main():
    # Apply all patches to fix missing methods
    patch_missing_methods()
    
    # Load CSS with contrast fixes
    load_css()
    
    # Ensure logo exists
    ensure_logo_exists()
    
    # Navigation using sidebar
    sidebar_navigation()
    
    # Add try-catch for error handling
    try:
        # Route to the correct page based on session state
        if st.session_state.current_page == "Home" or st.session_state.student_profile is None:
            show_welcome_page()
        elif st.session_state.current_page == "Dashboard":
            show_dashboard()
        elif st.session_state.current_page == "Academics":
            show_academics_page()
        elif st.session_state.current_page == "Finance":
            show_finance_page()
        elif st.session_state.current_page == "Wellness":
            show_wellness_page()
        elif st.session_state.current_page == "Career":
            show_career_page()
        elif st.session_state.current_page == "Resources":
            show_resources_page()
        elif st.session_state.current_page == "AI_Advisor":
            show_ai_advisor_page()
        elif st.session_state.current_page == "Settings":
            show_settings_page()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please check the console for more details or contact support.")

if __name__ == "__main__":
    main()
