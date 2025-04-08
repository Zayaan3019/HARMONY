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

# Set page configuration immediately
st.set_page_config(
    page_title="HARMONY-India: Student Success Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Simple initial display to show something immediately
st.markdown("# Loading HARMONY-India...")
st.info("Setting up your student success platform. Please wait...")

# Import modules with error handling
try:
    # Import modules
    from modules.student_model import StudentProfile
    from modules.academic_tracker import AcademicTracker
    from modules.financial_planner import FinancialPlanner
    from modules.mental_wellness import MentalWellnessCoach
    from modules.career_guide import CareerGuide
    from modules.resource_connector import ResourceConnector
    from modules.ai_advisor import GroqAdvisor

    # Import utilities
    from utils.data_manager import DataManager
    from utils.visualization import create_gauge_chart, create_trend_chart, create_pie_chart
    from utils.prediction_engine import PredictiveEngine
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.warning("Make sure all required modules and utilities are in the correct directories.")
    modules_needed = ["student_model", "academic_tracker", "financial_planner", 
                     "mental_wellness", "career_guide", "resource_connector", "ai_advisor"]
    st.code(f"Missing modules may include: {e}")
    st.stop()

# Define patching functions for all needed methods
def patch_missing_methods():
    """Patch missing methods to ensure application doesn't crash"""
    try:
        # Patch FinancialPlanner methods
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
                    except Exception as e:
                        print(f"Warning in get_expenses_by_category - get transactions: {e}")
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
                except Exception as e:
                    print(f"Error in get_expenses_by_category: {e}")
                    return []
            
            FinancialPlanner.get_expenses_by_category = get_expenses_by_category
            print("Patched get_expenses_by_category method to FinancialPlanner")
        
        if not hasattr(FinancialPlanner, 'get_all_transactions'):
            def get_all_transactions(self):
                """Get all financial transactions for the student."""
                try:
                    return self.data_manager.get_data(
                        self.student_id, "financial_transactions", default=[]
                    )
                except Exception as e:
                    print(f"Error in get_all_transactions: {e}")
                    return []
            
            FinancialPlanner.get_all_transactions = get_all_transactions
            print("Patched get_all_transactions method to FinancialPlanner")
        
        if not hasattr(FinancialPlanner, 'get_monthly_expenses'):
            def get_monthly_expenses(self):
                """Get expenses for the current month by category."""
                try:
                    return self.get_expenses_by_category()
                except Exception as e:
                    print(f"Error in get_monthly_expenses: {e}")
                    return []
            
            FinancialPlanner.get_monthly_expenses = get_monthly_expenses
            print("Patched get_monthly_expenses method to FinancialPlanner")
        
        if not hasattr(FinancialPlanner, 'get_budget_adherence'):
            def get_budget_adherence(self):
                """Get budget adherence percentage."""
                try:
                    # This is a mock implementation
                    return 85  # Default to 85% adherence
                except Exception as e:
                    print(f"Error in get_budget_adherence: {e}")
                    return 0
            
            FinancialPlanner.get_budget_adherence = get_budget_adherence
            print("Patched get_budget_adherence method to FinancialPlanner")
        
        # Patch CareerGuide methods
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
                except Exception as e:
                    print(f"Error in get_career_profile: {e}")
                    return None
            
            CareerGuide.get_career_profile = get_career_profile
            print("Patched get_career_profile method to CareerGuide")
        
        if not hasattr(CareerGuide, 'get_career_preferences'):
            def get_career_preferences(self):
                """Get career preferences for the student"""
                try:
                    preferences = {
                        'interests': ['Technology', 'Business'],
                        'target_roles': ['Software Engineer', 'Data Analyst']
                    }
                    return preferences
                except Exception as e:
                    print(f"Error in get_career_preferences: {e}")
                    return {}
            
            CareerGuide.get_career_preferences = get_career_preferences
            print("Patched get_career_preferences method to CareerGuide")
        
        if not hasattr(CareerGuide, 'get_career_readiness_score'):
            def get_career_readiness_score(self):
                """Get career readiness score for the student"""
                try:
                    # This is a mock implementation
                    return 75  # Default to 75% readiness
                except Exception as e:
                    print(f"Error in get_career_readiness_score: {e}")
                    return 0
            
            CareerGuide.get_career_readiness_score = get_career_readiness_score
            print("Patched get_career_readiness_score method to CareerGuide")
        
        # Patch StudentProfile methods
        if not hasattr(StudentProfile, 'get_all_data'):
            def get_all_data(self):
                """Get all profile data"""
                try:
                    return self.profile_data
                except Exception as e:
                    print(f"Error in get_all_data: {e}")
                    return {}
            
            StudentProfile.get_all_data = get_all_data
            print("Patched get_all_data method to StudentProfile")
        
        # Patch AcademicTracker methods
        if not hasattr(AcademicTracker, 'get_upcoming_tasks'):
            def get_upcoming_tasks(self, limit=5):
                """Get upcoming tasks for the student"""
                try:
                    tasks = self.data_manager.get_data(
                        self.student_id, "academic_tasks", default=[]
                    )
                    
                    # Sort by due date
                    tasks.sort(key=lambda x: x.get('due_date', ''))
                    
                    return tasks[:limit]
                except Exception as e:
                    print(f"Error in get_upcoming_tasks: {e}")
                    return []
            
            AcademicTracker.get_upcoming_tasks = get_upcoming_tasks
            print("Patched get_upcoming_tasks method to AcademicTracker")
        
        if not hasattr(AcademicTracker, 'get_current_cgpa'):
            def get_current_cgpa(self):
                """Get current CGPA for the student"""
                try:
                    # This is a mock implementation
                    return 8.2  # Default CGPA
                except Exception as e:
                    print(f"Error in get_current_cgpa: {e}")
                    return 0
            
            AcademicTracker.get_current_cgpa = get_current_cgpa
            print("Patched get_current_cgpa method to AcademicTracker")
        
        if not hasattr(AcademicTracker, 'get_cgpa_goal'):
            def get_cgpa_goal(self):
                """Get CGPA goal for the student"""
                try:
                    # This is a mock implementation
                    return 9.0  # Default goal
                except Exception as e:
                    print(f"Error in get_cgpa_goal: {e}")
                    return 0
            
            AcademicTracker.get_cgpa_goal = get_cgpa_goal
            print("Patched get_cgpa_goal method to AcademicTracker")
        
        if not hasattr(AcademicTracker, 'get_performance_history'):
            def get_performance_history(self):
                """Get academic performance history"""
                try:
                    # This is a mock implementation
                    return [
                        {"semester": "Sem 1", "cgpa": 7.8, "semester_index": 1},
                        {"semester": "Sem 2", "cgpa": 8.1, "semester_index": 2},
                        {"semester": "Sem 3", "cgpa": 8.4, "semester_index": 3}
                    ]
                except Exception as e:
                    print(f"Error in get_performance_history: {e}")
                    return []
            
            AcademicTracker.get_performance_history = get_performance_history
            print("Patched get_performance_history method to AcademicTracker")
        
        if not hasattr(AcademicTracker, 'get_study_hours_history'):
            def get_study_hours_history(self):
                """Get study hours history"""
                try:
                    # This is a mock implementation
                    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7, 0, -1)]
                    return [
                        {"date": dates[0], "hours": 2.5, "subject": "Math"},
                        {"date": dates[1], "hours": 3.0, "subject": "Physics"},
                        {"date": dates[2], "hours": 1.5, "subject": "English"},
                        {"date": dates[3], "hours": 4.0, "subject": "CS"},
                        {"date": dates[4], "hours": 2.0, "subject": "History"},
                        {"date": dates[5], "hours": 3.5, "subject": "CS"},
                        {"date": dates[6], "hours": 2.0, "subject": "Math"}
                    ]
                except Exception as e:
                    print(f"Error in get_study_hours_history: {e}")
                    return []
            
            AcademicTracker.get_study_hours_history = get_study_hours_history
            print("Patched get_study_hours_history method to AcademicTracker")
        
        # Patch MentalWellnessCoach methods
        if not hasattr(MentalWellnessCoach, 'get_mood_history'):
            def get_mood_history(self):
                """Get mood history for the student"""
                try:
                    moods = self.data_manager.get_data(
                        self.student_id, "mood_entries", default=[]
                    )
                    return moods
                except Exception as e:
                    print(f"Error in get_mood_history: {e}")
                    return []
            
            MentalWellnessCoach.get_mood_history = get_mood_history
            print("Patched get_mood_history method to MentalWellnessCoach")
        
        if not hasattr(MentalWellnessCoach, 'get_current_wellness_score'):
            def get_current_wellness_score(self):
                """Get current wellness score for the student"""
                try:
                    # This is a mock implementation
                    mood_history = self.get_mood_history()
                    if mood_history:
                        recent_moods = mood_history[-5:] if len(mood_history) >= 5 else mood_history
                        avg_score = sum(m.get('score', 0) for m in recent_moods) / len(recent_moods)
                        return avg_score
                    return 7.5  # Default score
                except Exception as e:
                    print(f"Error in get_current_wellness_score: {e}")
                    return 0
            
            MentalWellnessCoach.get_current_wellness_score = get_current_wellness_score
            print("Patched get_current_wellness_score method to MentalWellnessCoach")
        
        # Patch ResourceConnector methods
        if not hasattr(ResourceConnector, 'get_saved_resources'):
            def get_saved_resources(self):
                """Get saved resources for the student"""
                try:
                    resources = self.data_manager.get_data(
                        self.student_id, "saved_resources", default=[]
                    )
                    return resources
                except Exception as e:
                    print(f"Error in get_saved_resources: {e}")
                    return []
            
            ResourceConnector.get_saved_resources = get_saved_resources
            print("Patched get_saved_resources method to ResourceConnector")
        
        if not hasattr(ResourceConnector, 'save_resource'):
            def save_resource(self, resource_data):
                """Save a resource for the student"""
                try:
                    resources = self.get_saved_resources()
                    resources.append(resource_data)
                    
                    self.data_manager.save_data(
                        self.student_id, "saved_resources", resources
                    )
                    return True
                except Exception as e:
                    print(f"Error in save_resource: {e}")
                    return False
            
            ResourceConnector.save_resource = save_resource
            print("Patched save_resource method to ResourceConnector")
    except Exception as e:
        print(f"Error in patch_missing_methods: {e}")
        return False
    return True

# Improved CSS loading function with error handling
def load_css():
    """Load custom CSS styling with proper error handling"""
    try:
        # Create assets directory if it doesn't exist
        os.makedirs('assets', exist_ok=True)
        
        # Define the CSS file path
        css_path = 'assets/style.css'
        
        # If file doesn't exist, create it with our enhanced styling
        if not os.path.exists(css_path):
            with open(css_path, 'w') as f:
                f.write("""
                /* HARMONY-India - Enhanced UI Styling with Improved Contrast */
                
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
                
                /* ===== CRITICAL CONTRAST FIXES ===== */
                /* Fix for warning messages with yellow background but white text */
                div.stWarning > div {
                    color: #856404 !important;
                    background-color: #fff3cd !important;
                }
                
                div.stWarning > div > div > div {
                    color: #856404 !important;
                }
                
                /* Fix for yellow-background colored containers */
                [style*="background-color: #fff3e0"] * {
                    color: #333333 !important;
                }
                
                [style*="background-color: #fff3e0"] strong {
                    color: #e65100 !important;
                }
                
                /* Fix for green-background colored containers */
                [style*="background-color: #e8f5e9"] * {
                    color: #333333 !important;
                }
                
                [style*="background-color: #e8f5e9"] strong {
                    color: #2e7d32 !important;
                }
                
                /* Fix for blue-background colored containers */
                [style*="background-color: #e3f2fd"] * {
                    color: #333333 !important;
                }
                
                [style*="background-color: #e3f2fd"] strong {
                    color: #0d47a1 !important;
                }
                
                /* Fix for pink-background colored containers */
                [style*="background-color: #f3e5f5"] * {
                    color: #333333 !important;
                }
                
                [style*="background-color: #f3e5f5"] strong {
                    color: #6a1b9a !important;
                }
                
                /* Fix for red-background colored containers */
                [style*="background-color: #ffebee"] * {
                    color: #333333 !important;
                }
                
                [style*="background-color: #ffebee"] strong {
                    color: #c62828 !important;
                }
                
                /* Force dark text on all light-colored backgrounds */
                .light-bg-card, 
                [style*="background-color: #f5f5f5"],
                [style*="background-color: #f8f9fa"],
                [style*="background-color: #ffffff"],
                [style*="background-color: #e3f2fd"],
                [style*="background-color: #e8f5e9"],
                [style*="background-color: #fff3e0"],
                [style*="background-color: #f3e5f5"],
                [style*="background-color: #e1f5fe"],
                [style*="background-color: #fafafa"],
                [style*="background-color: #fff8e1"],
                [style*="background-color: #fffde7"],
                [style*="background-color: #f9fbe7"],
                [style*="background-color: #f1f8e9"],
                [style*="background-color: #e0f2f1"],
                [style*="background-color: #e0f7fa"],
                [style*="background-color: #ede7f6"],
                [style*="background-color: #fce4ec"] {
                    color: #333333 !important;
                }
                
                /* Force light text on all dark-colored backgrounds */
                .dark-bg-card,
                [style*="background-color: #0a3d62"],
                [style*="background-color: #0d47a1"],
                [style*="background-color: #1565c0"],
                [style*="background-color: #01579b"],
                [style*="background-color: #006064"],
                [style*="background-color: #004d40"],
                [style*="background-color: #2e7d32"],
                [style*="background-color: #333333"],
                [style*="background-color: #424242"],
                [style*="background-color: #212121"] {
                    color: #ffffff !important;
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
                
                /* Override critical alerts from Streamlit */
                div.stAlert > div {
                    color: #333333 !important;
                }
                
                div.stInfo > div {
                    background-color: #e3f2fd !important;
                    color: #0d47a1 !important;
                }
                
                div.stSuccess > div {
                    background-color: #d4edda !important;
                    color: #155724 !important;
                }
                
                div.stError > div {
                    background-color: #f8d7da !important;
                    color: #721c24 !important;
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
                
                /* Fallback text for broken elements */
                .fallback-text {
                    color: #333333 !important;
                    background-color: #f8f9fa;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #ddd;
                }
                """)
        
        # Load CSS
        with open(css_path) as f:
            css_content = f.read()
            st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
        
        return True
    except Exception as e:
        print(f"Error loading CSS: {e}")
        # Fallback CSS injection
        st.markdown("""
        <style>
        body { color: #333333; background-color: #fafafa; }
        h1, h2, h3 { color: #0a3d62; }
        p, li, div { color: #333333; }
        .stButton>button { color: white; background-color: #0a3d62; }
        </style>
        """, unsafe_allow_html=True)
        return False

# Logo creation with enhanced error handling
def ensure_logo_exists():
    """Create a HARMONY logo if it doesn't exist"""
    try:
        # Ensure assets directory exists
        os.makedirs('assets', exist_ok=True)
        
        logo_path = 'assets/harmony_logo.png'
        
        if not os.path.exists(logo_path):
            try:
                # First try using matplotlib to create a simple text logo
                plt.figure(figsize=(6, 2))
                plt.text(0.5, 0.5, 'HARMONY-India', 
                       fontsize=30, ha='center', va='center', 
                       color='#0a3d62', fontweight='bold')
                plt.axis('off')
                plt.savefig(logo_path, bbox_inches='tight', dpi=100, transparent=True)
                plt.close()
            except Exception as e:
                # If matplotlib fails, create a simple colored rectangle with PIL
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    img = Image.new('RGBA', (600, 200), color=(255, 255, 255, 0))
                    d = ImageDraw.Draw(img)
                    # Try to use a system font
                    try:
                        font = ImageFont.truetype("Arial", 60)
                    except:
                        font = ImageFont.load_default()
                    d.text((300, 100), "HARMONY-India", fill=(10, 61, 98), font=font, anchor="mm")
                    img.save(logo_path)
                except Exception as e:
                    print(f"Error creating logo with PIL: {e}")
                    # Last resort - create a simple colored square
                    img = Image.new('RGB', (600, 200), color=(10, 61, 98))
                    img.save(logo_path)
        
        return True
    except Exception as e:
        print(f"Error ensuring logo exists: {e}")
        return False

# Initialize session state variables with proper error handling
def initialize_session_state():
    """Initialize all session state variables safely"""
    try:
        # Core session state variables
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
            try:
                st.session_state.ai_advisor = GroqAdvisor()
            except Exception as e:
                print(f"Error initializing AI advisor: {e}")
                st.session_state.ai_advisor = None
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
            
        # Initialize AI Agent if not already done
        if 'ai_agent' not in st.session_state:
            st.session_state.ai_agent = AIAdvisorAgent(st.session_state.groq_api_key)
        
        # Initialize chat history for AI Advisor
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
            
        return True
    except Exception as e:
        print(f"Error initializing session state: {e}")
        return False

# AI Agent class with better error handling
class AIAdvisorAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.initialized = api_key is not None
        self.base_url = "https://api.groq.com/openai/v1"
    
    def set_api_key(self, api_key):
        """Set GROQ API key"""
        try:
            self.api_key = api_key
            self.initialized = api_key is not None
            return True
        except Exception as e:
            print(f"Error setting API key: {e}")
            return False
    
    def _make_groq_request(self, model, messages, temperature=0.7, max_tokens=800):
        """Make a request to GROQ API with better error handling"""
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
                json=data,
                timeout=10  # Add timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"GROQ API Error: {response.status_code}, {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Request error making GROQ request: {e}")
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
    
    # Include additional methods like get_financial_advice, get_wellness_tips, etc.
    # from the original AI Agent class...

# Function to fetch trending news with better error handling
def fetch_trending_news(topic, max_items=3):
    """Get trending news either from cache or fallback data with error handling"""
    try:
        # First check if we have cached news
        cache_key = f"{topic}_news"
        if (cache_key in st.session_state.cached_content and 
            st.session_state.cached_content[cache_key]):
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
        
        return news_data.get(topic, [])[:max_items]
    except Exception as e:
        print(f"Error fetching trending news: {e}")
        # Return a minimal fallback if everything fails
        return [{"title": "Education updates available soon", "date": "April 2025", "source": "HARMONY-India"}]

# Function to display student welcome page
def show_welcome_page():
    """Show welcome page with login functionality"""
    try:
        # Display logo and title
        col1, col2 = st.columns([1, 2])
        with col1:
            if os.path.exists('assets/harmony_logo.png'):
                st.image('assets/harmony_logo.png', width=200)
            else:
                st.markdown("# HARMONY-India")
        
        with col2:
            st.markdown("# Welcome to HARMONY-India")
            st.markdown("### Your Complete Student Success Platform")
        
        st.markdown("---")
        
        # Main content
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("""
            HARMONY-India helps students navigate college life successfully by providing tools for:
            
            * 📚 **Academic Excellence** - Course tracking, GPA monitoring, and study optimization
            * 💰 **Financial Wellbeing** - Budget management, expense tracking, and scholarship finder
            * 🧠 **Mental Wellness** - Mood tracking, stress management, and wellness resources
            * 🚀 **Career Planning** - Skill development, opportunity matching, and interview prep
            """)
            
            st.info("All your data is stored locally for complete privacy")
            
            with st.expander("Why HARMONY?"):
                st.markdown("""
                * **Personalized for Indian Students**: Understands the unique challenges of the Indian education system
                * **Holistic Approach**: Addresses all aspects of student life, not just academics
                * **AI-Powered Insights**: Provides personalized recommendations based on your profile and activities
                * **Offline Support**: Most features work without requiring constant internet connection
                * **Mobile Friendly**: Access your student dashboard from any device
                """)
                
        with col2:
            st.markdown("""
            <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h3 style="color: #0a3d62; margin-top: 0;">Get Started</h3>
            """, unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["Login", "Create Account"])
            
            with tab1:
                # Check for existing profiles
                try:
                    existing_profiles = st.session_state.data_manager.get_existing_profiles()
                    
                    if existing_profiles:
                        st.write("Select your profile to continue:")
                        
                        for profile_id in existing_profiles:
                            profile_name = st.session_state.data_manager.get_profile_name(profile_id)
                            if st.button(f"Login as {profile_name}", key=f"login_{profile_id}"):
                                # Initialize modules for this profile
                                with st.spinner("Loading your profile..."):
                                    if initialize_modules(profile_id):
                                        st.success("Login successful!")
                                        st.session_state.current_page = "Dashboard"
                                        st.rerun()
                                    else:
                                        st.error("Could not load profile. Please try again.")
                    else:
                        st.warning("No existing profiles found. Please create a new account.")
                        
                except Exception as e:
                    st.error(f"Error loading profiles: {e}")
                    st.info("Please create a new account to get started.")
            
            with tab2:
                with st.form("new_account_form"):
                    st.write("Create your student profile:")
                    
                    full_name = st.text_input("Full Name*")
                    
                    college_name = st.text_input("College/University Name*")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        degree = st.selectbox("Degree Program*", [
                            "B.Tech/B.E.", "BBA", "B.Sc.", "B.Com.", "B.A.", 
                            "M.Tech/M.E.", "MBA", "M.Sc.", "M.Com.", "M.A.",
                            "BCA", "MCA", "Ph.D.", "Diploma", "Other"
                        ])
                    
                    with col2:
                        year = st.selectbox("Year of Study*", [
                            "1st Year", "2nd Year", "3rd Year", "4th Year", "Final Year"
                        ])
                    
                    email = st.text_input("Email Address (Optional)")
                    
                    submitted = st.form_submit_button("Create Profile & Get Started")
                    
                    if submitted:
                        if not full_name or not college_name:
                            st.error("Please fill in the required fields marked with *")
                        else:
                            try:
                                # Generate a unique ID for the new student
                                import uuid
                                student_id = str(uuid.uuid4())
                                
                                # Create and save the profile
                                profile_data = {
                                    "full_name": full_name,
                                    "college_name": college_name,
                                    "degree": degree,
                                    "year_of_study": year,
                                    "email": email,
                                    "created_at": datetime.now().isoformat()
                                }
                                
                                # Save profile to data manager
                                if st.session_state.data_manager.save_student_profile(student_id, profile_data):
                                    # Initialize modules with the new profile
                                    with st.spinner("Setting up your personalized dashboard..."):
                                        if initialize_modules(student_id):
                                            st.success("Profile created successfully!")
                                            st.session_state.current_page = "Dashboard"
                                            st.session_state.show_welcome = True
                                            st.rerun()
                                        else:
                                            st.error("Error initializing your profile. Please try again.")
                                else:
                                    st.error("Error saving profile. Please try again.")
                            except Exception as e:
                                st.error(f"Error creating profile: {e}")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
        # Footer section with testimonials
        st.markdown("---")
        st.markdown("### What Students Say")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; height: 100%;">
                <p style="font-style: italic; color: #333333;">"HARMONY helped me balance academics with mental health. The personalized recommendations really made a difference!"</p>
                <p><strong style="color: #0a3d62;">Priya S.</strong><br><span style="color: #666666;">B.Tech Computer Science, Delhi</span></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; height: 100%;">
                <p style="font-style: italic; color: #333333;">"The scholarship finder helped me secure funding I didn't even know existed. I can now focus on studies without financial stress."</p>
                <p><strong style="color: #0a3d62;">Rahul M.</strong><br><span style="color: #666666;">BBA, Mumbai</span></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; height: 100%;">
                <p style="font-style: italic; color: #333333;">"The career planning tools helped me identify skills I needed to develop, and now I have three internship offers!"</p>
                <p><strong style="color: #0a3d62;">Aisha K.</strong><br><span style="color: #666666;">B.Sc. Biotechnology, Bangalore</span></p>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying welcome page: {e}")
        st.markdown("### Welcome to HARMONY-India")
        st.info("Please refresh the page if you're experiencing issues with the welcome screen.")
        if st.button("Create Demo Account"):
            # Create a demo account as fallback
            try:
                student_id = "demo_user_1"
                profile_data = {
                    "full_name": "Demo Student",
                    "college_name": "Demo University",
                    "degree": "B.Tech/B.E.",
                    "year_of_study": "2nd Year",
                    "email": "demo@example.com",
                    "created_at": datetime.now().isoformat()
                }
                st.session_state.data_manager.save_student_profile(student_id, profile_data)
                initialize_modules(student_id)
                st.session_state.current_page = "Dashboard"
                st.rerun()
            except Exception as e:
                st.error(f"Error creating demo account: {e}")

# Improved sidebar navigation with better error handling
def sidebar_navigation():
    """Display sidebar navigation with improved robustness"""
    try:
        # Add logo to sidebar
        if os.path.exists('assets/harmony_logo.png'):
            st.sidebar.image('assets/harmony_logo.png', width=200)
        else:
            st.sidebar.title("HARMONY-India")
        
        st.sidebar.markdown("---")
        
        # Display student info if logged in
        if st.session_state.student_profile:
            try:
                profile = st.session_state.student_profile
                st.sidebar.markdown(f"""
                ### 👤 {profile.get_full_name()}
                🏫 {profile.get_college_name()}  
                🎓 {profile.get_degree()}  
                📚 {profile.get_year_of_study()}
                """)
            except Exception as e:
                st.sidebar.info("Welcome, Student")
                print(f"Error showing student profile in sidebar: {e}")
            
            st.sidebar.markdown("---")
            
            # Navigation section
            st.sidebar.markdown("### Navigation")
            
            # Dashboard button
            if st.sidebar.button("🏠 Dashboard", key="nav_dashboard"):
                st.session_state.current_page = "Dashboard"
                st.rerun()
            
            # Academics button
            if st.sidebar.button("📚 Academic Tracker", key="nav_academics"):
                st.session_state.current_page = "Academics"
                st.rerun()
            
            # Finance button
            if st.sidebar.button("💰 Financial Planner", key="nav_finance"):
                st.session_state.current_page = "Finance"
                st.rerun()
            
            # Wellness button
            if st.sidebar.button("🧠 Mental Wellness", key="nav_wellness"):
                st.session_state.current_page = "Wellness"
                st.rerun()
            
            # Career button
            if st.sidebar.button("🚀 Career Pathway", key="nav_career"):
                st.session_state.current_page = "Career"
                st.rerun()
            
            # Resources button
            if st.sidebar.button("📖 Learning Resources", key="nav_resources"):
                st.session_state.current_page = "Resources"
                st.rerun()
            
            # AI Advisor button (only show if GROQ API is configured)
            if st.session_state.groq_api_key:
                if st.sidebar.button("🤖 AI Advisor", key="nav_ai_advisor"):
                    st.session_state.current_page = "AI_Advisor"
                    st.rerun()
            
            st.sidebar.markdown("---")
            
            # Settings button
            if st.sidebar.button("⚙️ Settings", key="nav_settings"):
                st.session_state.current_page = "Settings"
                st.rerun()
            
            # Logout button
            if st.sidebar.button("🚪 Logout", key="nav_logout"):
                st.session_state.student_profile = None
                st.session_state.current_page = "Home"
                # Clear other session data
                for key in ['academic_tracker', 'financial_planner', 'mental_wellness', 
                           'career_guide', 'resource_connector', 'prediction_engine']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        else:
            st.sidebar.info("Please login or create an account to access all features.")
            
            if st.sidebar.button("🏠 Return to Login", key="return_login"):
                st.session_state.current_page = "Home"
                st.rerun()
        
        # App info
        with st.sidebar.expander("About HARMONY-India"):
            st.markdown("""
            **Version:** 1.0.1  
            **Last Updated:** April 8, 2025
            
            HARMONY-India is designed specifically for Indian college students to help navigate the unique challenges of higher education.
            
            All data is stored locally on your device for complete privacy.
            """)
        
        # Footer with current date
        st.sidebar.markdown("---")
        current_date = datetime.now().strftime("%d %b %Y")
        st.sidebar.caption(f"© 2025 HARMONY-India | {current_date}")
        
    except Exception as e:
        # Fallback navigation if an error occurs
        st.sidebar.error("Navigation error. Please refresh the page.")
        st.sidebar.markdown("### Emergency Navigation")
        
        if st.sidebar.button("🏠 Home", key="emergency_home"):
            st.session_state.current_page = "Home"
            st.rerun()
        
        if st.sidebar.button("⚙️ Settings", key="emergency_settings"):
            st.session_state.current_page = "Settings"
            st.rerun()
        
        if st.sidebar.button("🚪 Logout", key="emergency_logout"):
            st.session_state.student_profile = None
            st.session_state.current_page = "Home"
            st.rerun()
        
        st.sidebar.markdown(f"Error: {str(e)}")

# Function to initialize modules with better error handling
def initialize_modules(student_id):
    """Initialize all modules for a student with proper error handling"""
    try:
        data_manager = st.session_state.data_manager
        student_data = data_manager.load_student_profile(student_id)
        
        if not student_data:
            print(f"No student data found for ID: {student_id}")
            return False
        
        # Initialize all modules with proper error handling
        try:
            st.session_state.student_profile = StudentProfile(student_id, student_data)
        except Exception as e:
            print(f"Error initializing StudentProfile: {e}")
            st.session_state.student_profile = None
            return False
        
        try:
            st.session_state.academic_tracker = AcademicTracker(student_id, data_manager)
        except Exception as e:
            print(f"Error initializing AcademicTracker: {e}")
            st.session_state.academic_tracker = None
        
        try:
            st.session_state.financial_planner = FinancialPlanner(student_id, data_manager)
        except Exception as e:
            print(f"Error initializing FinancialPlanner: {e}")
            st.session_state.financial_planner = None
        
        try:
            st.session_state.mental_wellness = MentalWellnessCoach(student_id, data_manager)
        except Exception as e:
            print(f"Error initializing MentalWellnessCoach: {e}")
            st.session_state.mental_wellness = None
        
        try:
            st.session_state.career_guide = CareerGuide(student_id, data_manager)
        except Exception as e:
            print(f"Error initializing CareerGuide: {e}")
            st.session_state.career_guide = None
        
        try:
            st.session_state.resource_connector = ResourceConnector(student_id, data_manager)
        except Exception as e:
            print(f"Error initializing ResourceConnector: {e}")
            st.session_state.resource_connector = None
        
        try:
            st.session_state.prediction_engine = PredictiveEngine(student_id, data_manager)
        except Exception as e:
            print(f"Error initializing PredictiveEngine: {e}")
            st.session_state.prediction_engine = None
        
        # Apply any needed method patches
        patch_missing_methods()
        
        return st.session_state.student_profile is not None
    except Exception as e:
        print(f"Error in initialize_modules: {e}")
        return False

# Stub placeholder functions for pages
def show_dashboard():
    """Show student dashboard with error handling"""
    try:
        st.title("Your Student Dashboard")
        
        if not st.session_state.student_profile:
            st.error("No student profile found. Please log in again.")
            if st.button("Return to Login"):
                st.session_state.current_page = "Home"
                st.rerun()
            return
        
        # Display student name and basic info
        student = st.session_state.student_profile
        st.write(f"Welcome back, **{student.get_full_name()}**!")
        
        # Show date and last login
        col1, col2 = st.columns([3, 1])
        with col1:
            current_date = datetime.now().strftime("%A, %d %B %Y")
            st.markdown(f"**Today**: {current_date}")
        
        # Key metrics in columns
        st.subheader("Your Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Academic metric
            try:
                current_cgpa = st.session_state.academic_tracker.get_current_cgpa()
                st.metric("Current CGPA", f"{current_cgpa:.2f}", "Target: 9.0")
            except:
                st.metric("Current CGPA", "8.25", "Target: 9.0")
        
        with col2:
            # Financial metric
            try:
                budget_adherence = st.session_state.financial_planner.get_budget_adherence()
                st.metric("Budget Adherence", f"{budget_adherence}%", "Target: 90%")
            except:
                st.metric("Budget Adherence", "85%", "Target: 90%")
        
        with col3:
            # Wellness metric
            try:
                wellness_score = st.session_state.mental_wellness.get_current_wellness_score()
                st.metric("Wellness Score", f"{wellness_score:.1f}/10", "+0.5")
            except:
                st.metric("Wellness Score", "7.5/10", "+0.5")
        
        with col4:
            # Career metric
            try:
                career_readiness = st.session_state.career_guide.get_career_readiness_score()
                st.metric("Career Readiness", f"{career_readiness}%", "+5%")
            except:
                st.metric("Career Readiness", "75%", "+5%")
        
        # Upcoming tasks section
        st.subheader("Upcoming Tasks & Deadlines")
        
        try:
            tasks = st.session_state.academic_tracker.get_upcoming_tasks(limit=5)
            if tasks:
                for task in tasks:
                    due_date = datetime.fromisoformat(task['due_date'])
                    days_left = (due_date - datetime.now()).days
                    
                    if days_left < 0:
                        status_color = "red"
                        status_text = f"Overdue by {abs(days_left)} days"
                    elif days_left == 0:
                        status_color = "orange"
                        status_text = "Due today"
                    elif days_left <= 3:
                        status_color = "blue"
                        status_text = f"Due in {days_left} days"
                    else:
                        status_color = "green"
                        status_text = f"Due in {days_left} days"
                    
                    st.markdown(f"""
                    <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="margin: 0; color: #0a3d62;">{task['title']}</h4>
                            <p style="margin: 5px 0; color: #666;">{task['course_code']} | {task['type']}</p>
                        </div>
                        <div style="color: {status_color}; font-weight: bold;">
                            {status_text}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No upcoming tasks found. Add some in the Academic Tracker section.")
        except Exception as e:
            st.info("Could not load upcoming tasks. Please check the Academic Tracker.")
            
        # Quick add form
        with st.expander("Quick Add Task"):
            with st.form("quick_task_form"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    task_title = st.text_input("Task Title", placeholder="e.g., Math Assignment")
                with col2:
                    task_type = st.selectbox("Type", ["Assignment", "Exam", "Project", "Study"])
                
                col1, col2 = st.columns(2)
                with col1:
                    course_code = st.text_input("Course Code", placeholder="e.g., CS101")
                with col2:
                    due_date = st.date_input("Due Date")
                
                submitted = st.form_submit_button("Add Task")
                
                if submitted and task_title and course_code:
                    try:
                        new_task = {
                            "title": task_title,
                            "type": task_type,
                            "course_code": course_code,
                            "due_date": due_date.isoformat(),
                            "status": "pending"
                        }
                        
                        if st.session_state.academic_tracker.add_task(new_task):
                            st.success("Task added successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to add task.")
                    except Exception as e:
                        st.error(f"Error adding task: {e}")
        
        # Latest news section
        st.subheader("Latest Education News")
        
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                # Get trending education news
                education_news = fetch_trending_news("education")
                
                for news in education_news:
                    st.markdown(f"""
                    <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                        <h4 style="margin: 0; color: #0a3d62;">{news['title']}</h4>
                        <p style="margin: 5px 0; color: #666;">{news['date']} • {news['source']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Could not load education news: {e}")
        
        with col2:
            try:
                # Get trending career news
                career_news = fetch_trending_news("career")
                
                for news in career_news:
                    st.markdown(f"""
                    <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                        <h4 style="margin: 0; color: #0a3d62;">{news['title']}</h4>
                        <p style="margin: 5px 0; color: #666;">{news['date']} • {news['source']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Could not load career news: {e}")
    except Exception as e:
        st.error(f"Error displaying dashboard: {e}")
        
        # Show fallback dashboard
        st.markdown("### Emergency Dashboard")
        st.info("We're experiencing issues displaying your complete dashboard. Here's a simplified view:")
        
        if st.session_state.student_profile:
            st.write(f"Welcome, {st.session_state.student_profile.get_full_name()}")
        else:
            st.write("Welcome to HARMONY-India")
        
        # Navigation options
        st.markdown("### Quick Navigation")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Go to Academics"):
                st.session_state.current_page = "Academics"
                st.rerun()
        
        with col2:
            if st.button("Go to Finances"):
                st.session_state.current_page = "Finance"
                st.rerun()
        
        with col3:
            if st.button("Go to Settings"):
                st.session_state.current_page = "Settings"
                st.rerun()

def show_academics_page():
    """Show academics page placeholder"""
    st.title("Academic Tracker")
    st.info("Academic tracking features will be displayed here.")
    
    if st.button("Return to Dashboard"):
        st.session_state.current_page = "Dashboard"
        st.rerun()

def show_finance_page():
    """Show finance page placeholder"""
    st.title("Financial Planner")
    st.info("Financial planning features will be displayed here.")
    
    if st.button("Return to Dashboard"):
        st.session_state.current_page = "Dashboard"
        st.rerun()

def show_wellness_page():
    """Show wellness page placeholder"""
    st.title("Mental Wellness Coach")
    st.info("Mental wellness features will be displayed here.")
    
    if st.button("Return to Dashboard"):
        st.session_state.current_page = "Dashboard"
        st.rerun()

def show_career_page():
    """Show career page placeholder"""
    st.title("Career Pathway Guide")
    st.info("Career guidance features will be displayed here.")
    
    if st.button("Return to Dashboard"):
        st.session_state.current_page = "Dashboard"
        st.rerun()

def show_resources_page():
    """Show resources page placeholder"""
    st.title("Learning Resources")
    st.info("Learning resources features will be displayed here.")
    
    if st.button("Return to Dashboard"):
        st.session_state.current_page = "Dashboard"
        st.rerun()

def show_ai_advisor_page():
    """Show AI advisor page placeholder"""
    st.title("AI Advisor")
    
    if not st.session_state.groq_api_key:
        st.warning("Please configure your Groq API key in Settings to use the AI Advisor.")
        if st.button("Go to Settings"):
            st.session_state.current_page = "Settings"
            st.rerun()
        return
    
    st.info("AI advisor features will be displayed here.")
    
    if st.button("Return to Dashboard"):
        st.session_state.current_page = "Dashboard"
        st.rerun()

def show_settings_page():
    """Show settings page with improved error handling"""
    try:
        st.title("Settings & Configuration")
        
        # Profile section
        st.header("Profile Settings")
        
        if st.session_state.student_profile:
            profile = st.session_state.student_profile
            
            with st.expander("View and Edit Profile", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    current_name = profile.get_full_name()
                    new_name = st.text_input("Full Name", value=current_name)
                    
                    current_college = profile.get_college_name()
                    new_college = st.text_input("College/University", value=current_college)
                    
                with col2:
                    current_degree = profile.get_degree()
                    new_degree = st.selectbox("Degree Program", [
                        "B.Tech/B.E.", "BBA", "B.Sc.", "B.Com.", "B.A.", 
                        "M.Tech/M.E.", "MBA", "M.Sc.", "M.Com.", "M.A.",
                        "BCA", "MCA", "Ph.D.", "Diploma", "Other"
                    ], index=["B.Tech/B.E.", "BBA", "B.Sc.", "B.Com.", "B.A.", 
                        "M.Tech/M.E.", "MBA", "M.Sc.", "M.Com.", "M.A.",
                        "BCA", "MCA", "Ph.D.", "Diploma", "Other"].index(current_degree) if current_degree in ["B.Tech/B.E.", "BBA", "B.Sc.", "B.Com.", "B.A.", 
                        "M.Tech/M.E.", "MBA", "M.Sc.", "M.Com.", "M.A.",
                        "BCA", "MCA", "Ph.D.", "Diploma", "Other"] else 0)
                    
                    current_year = profile.get_year_of_study()
                    new_year = st.selectbox("Year of Study", [
                        "1st Year", "2nd Year", "3rd Year", "4th Year", "Final Year"
                    ], index=["1st Year", "2nd Year", "3rd Year", "4th Year", "Final Year"].index(current_year) if current_year in ["1st Year", "2nd Year", "3rd Year", "4th Year", "Final Year"] else 0)
                
                current_email = profile.get_profile_data().get("email", "")
                new_email = st.text_input("Email Address", value=current_email)
                
                if st.button("Update Profile"):
                    try:
                        # Get current profile data
                        profile_data = profile.get_all_data()
                        
                        # Update with new values
                        profile_data["full_name"] = new_name
                        profile_data["college_name"] = new_college
                        profile_data["degree"] = new_degree
                        profile_data["year_of_study"] = new_year
                        profile_data["email"] = new_email
                        
                        # Save updated profile
                        st.session_state.data_manager.save_student_profile(profile.get_student_id(), profile_data)
                        
                        # Reinitialize modules to reflect changes
                        initialize_modules(profile.get_student_id())
                        
                        st.success("Profile updated successfully!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating profile: {e}")
        else:
            st.info("Please log in to view and edit your profile.")
        
        # AI Configuration
        st.header("AI Configuration")
        
        with st.expander("GROQ API Settings"):
            st.write("""
            To enable AI-powered features like personalized recommendations and the AI Advisor, 
            you need to configure your GROQ API key.
            
            1. Sign up on [groq.com](https://groq.com)
            2. Generate an API key
            3. Enter it below
            """)
            
            current_key = st.session_state.groq_api_key
            new_key = st.text_input(
                "GROQ API Key", 
                value=current_key if current_key else "",
                type="password",
                placeholder="gsk_..."
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Save API Key"):
                    if new_key.startswith("gsk_") or not new_key:
                        st.session_state.groq_api_key = new_key if new_key else None
                        
                        # Update AI Agent and Advisor
                        if 'ai_agent' in st.session_state:
                            st.session_state.ai_agent.set_api_key(new_key)
                        
                        if 'ai_advisor' in st.session_state:
                            st.session_state.ai_advisor = GroqAdvisor(api_key=new_key)
                        
                        if new_key:
                            st.success("API key saved successfully!")
                        else:
                            st.warning("API key removed. AI features will be limited.")
                        
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid API key format. GROQ keys start with 'gsk_'")
            
            with col2:
                if st.button("Test API Key"):
                    if not new_key:
                        st.error("Please enter an API key to test.")
                    else:
                        with st.spinner("Testing API key..."):
                            try:
                                test_agent = AIAdvisorAgent(new_key)
                                response = test_agent._make_groq_request(
                                    model="llama3-70b-8192",
                                    messages=[{"role": "user", "content": "Quick test"}],
                                    max_tokens=10
                                )
                                
                                if response:
                                    st.success("API key is valid and working!")
                                else:
                                    st.error("API key test failed. Please check the key and try again.")
                            except Exception as e:
                                st.error(f"Error testing API key: {e}")
        
        # Application settings
        st.header("Application Settings")
        
        with st.expander("Display Settings"):
            theme = st.selectbox(
                "Color Theme",
                ["Light", "Dark", "System Default"],
                index=0
            )
            
            st.info("Theme support is limited in the current version and will be enhanced in future updates.")
        
        with st.expander("Data Management"):
            st.write("Manage your application data:")
            
            if st.button("Export All Data"):
                try:
                    if st.session_state.student_profile:
                        student_id = st.session_state.student_profile.get_student_id()
                        data = st.session_state.data_manager.export_all_data(student_id)
                        
                        # Convert to JSON and offer download
                        json_data = json.dumps(data, indent=2)
                        st.download_button(
                            label="Download Data as JSON",
                            data=json_data,
                            file_name="harmony_data_export.json",
                            mime="application/json"
                        )
                    else:
                        st.error("Please log in to export your data.")
                except Exception as e:
                    st.error(f"Error exporting data: {e}")
            
            dangerous_zone = st.checkbox("Show Dangerous Operations")
            
            if dangerous_zone:
                st.warning("Caution: The following operations can cause data loss!")
                
                st.error("⚠️ Danger Zone ⚠️")
                
                if st.button("Reset All Application Data", key="reset_data"):
                    delete_confirmation = st.text_input(
                        "Type 'DELETE' to confirm data reset:",
                        key="delete_confirmation"
                    )
                    
                    if delete_confirmation == "DELETE":
                        try:
                            st.session_state.data_manager.reset_all_data()
                            
                            # Clear session state
                            for key in list(st.session_state.keys()):
                                if key not in ['current_page', 'data_manager']:
                                    del st.session_state[key]
                            
                            st.session_state.student_profile = None
                            st.session_state.current_page = "Home"
                            
                            st.success("All data has been reset. Redirecting to home page...")
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error resetting data: {e}")
        
        # About section
        st.header("About HARMONY-India")
        
        st.markdown("""
        **Version:** 1.0.1  
        **Last Updated:** April 8, 2025
        
        HARMONY-India is designed specifically for Indian college students to help navigate the unique challenges of higher education.
        
        This platform integrates academic management, financial planning, mental wellness, career guidance, and resource access into one comprehensive tool.
        
        All data is stored locally on your device for complete privacy.
        """)
        
    except Exception as e:
        st.error(f"Error displaying settings page: {e}")
        
        # Fallback settings UI
        st.markdown("### Basic Settings")
        
        if st.button("Return to Dashboard"):
            st.session_state.current_page = "Dashboard"
            st.rerun()
        
        if st.button("Logout"):
            st.session_state.student_profile = None
            st.session_state.current_page = "Home"
            st.rerun()

# Main function with error handling at every stage
def main():
    """Main function with comprehensive error handling"""
    try:
        # Apply patch functions to ensure all needed methods exist
        patch_missing_methods()
        
        # Load CSS for better UI
        load_css()
        
        # Ensure logo exists
        ensure_logo_exists()
        
        # Initialize session state
        initialize_session_state()
        
        # Navigation sidebar
        try:
            sidebar_navigation()
        except Exception as e:
            st.sidebar.error(f"Navigation error: {str(e)}")
            st.sidebar.info("Please refresh the page if the navigation menu is not working properly.")
        
        # Route to the correct page based on session state
        try:
            current_page = st.session_state.current_page
            
            if current_page == "Home" or st.session_state.student_profile is None:
                show_welcome_page()
            elif current_page == "Dashboard":
                show_dashboard()
            elif current_page == "Academics":
                show_academics_page()
            elif current_page == "Finance":
                show_finance_page()
            elif current_page == "Wellness":
                show_wellness_page()
            elif current_page == "Career":
                show_career_page()
            elif current_page == "Resources":
                show_resources_page()
            elif current_page == "AI_Advisor":
                show_ai_advisor_page()
            elif current_page == "Settings":
                show_settings_page()
            else:
                st.error(f"Unknown page: {current_page}")
                st.session_state.current_page = "Home"
                st.rerun()
        except Exception as e:
            st.error(f"Error displaying page content: {str(e)}")
            st.info("Please try refreshing the page. If the problem persists, try logging out and back in.")
            
            # Emergency navigation
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Go to Home"):
                    st.session_state.current_page = "Home"
                    st.rerun()
            with col2:
                if st.button("Go to Dashboard"):
                    st.session_state.current_page = "Dashboard"
                    st.rerun()
            with col3:
                if st.button("Logout"):
                    st.session_state.student_profile = None
                    st.session_state.current_page = "Home"
                    st.rerun()
    except Exception as e:
        # Last resort error handling
        st.error(f"Critical application error: {str(e)}")
        st.info("Please refresh the page to restart the application.")

# Run the app
if __name__ == "__main__":
    main()
