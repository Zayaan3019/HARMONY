import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class PredictiveEngine:
    """
    Provides predictive analytics and personalized recommendations
    """
    
    def __init__(self, student_id: str, data_manager):
        """Initialize the prediction engine for a student"""
        self.student_id = student_id
        self.data_manager = data_manager
        
        # Load student data
        self.student_profile = data_manager.load_student_profile(student_id)
        
        # Cache for recommendations
        self.recommendations_cache = None
        self.last_update = None
    
    def get_personalized_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate personalized recommendations for the student
        
        Returns:
            List of recommendation dictionaries with title, description, and priority
        """
        # Check if we have recent cached recommendations
        if (self.recommendations_cache and self.last_update and 
            datetime.now() - self.last_update < timedelta(hours=1)):
            return self.recommendations_cache
        
        # Generate new recommendations
        recommendations = []
        
        # Academic recommendations
        academic_recs = self._generate_academic_recommendations()
        recommendations.extend(academic_recs)
        
        # Financial recommendations
        financial_recs = self._generate_financial_recommendations()
        recommendations.extend(financial_recs)
        
        # Wellness recommendations
        wellness_recs = self._generate_wellness_recommendations()
        recommendations.extend(wellness_recs)
        
        # Career recommendations
        career_recs = self._generate_career_recommendations()
        recommendations.extend(career_recs)
        
        # Sort recommendations by priority
        priority_order = {"high": 3, "medium": 2, "low": 1}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 0), reverse=True)
        
        # Cache the results
        self.recommendations_cache = recommendations
        self.last_update = datetime.now()
        
        return recommendations
    
    def _generate_academic_recommendations(self) -> List[Dict[str, Any]]:
        """Generate academic recommendations"""
        recommendations = []
        
        # Load academic data
        academic_data = self.data_manager.load_data(self.student_id, "academic", "data")
        tasks = self.data_manager.load_data(self.student_id, "academic", "tasks") or []
        courses = self.data_manager.load_data(self.student_id, "academic", "courses") or []
        performance = self.data_manager.load_data(self.student_id, "academic", "performance") or []
        
        # Check for upcoming deadlines
        now = datetime.now()
        upcoming_tasks = [
            task for task in tasks 
            if task.get("due_date") and 
            datetime.fromisoformat(task["due_date"]) - now <= timedelta(days=3) and
            task.get("status") != "completed"
        ]
        
        if upcoming_tasks:
            if len(upcoming_tasks) >= 3:
                recommendations.append({
                    "title": "Multiple Deadlines Approaching",
                    "description": f"You have {len(upcoming_tasks)} tasks due in the next 3 days. Consider creating a study plan.",
                    "priority": "high"
                })
            else:
                task = upcoming_tasks[0]
                recommendations.append({
                    "title": f"{task['type']} Due Soon",
                    "description": f"Your {task['title']} for {task['course_code']} is due in {(datetime.fromisoformat(task['due_date']) - now).days} days.",
                    "priority": "medium"
                })
        
        # Check CGPA trend
        if performance and len(performance) >= 2:
            sorted_perf = sorted(performance, key=lambda x: x.get("semester_index", 0))
            latest_cgpa = sorted_perf[-1].get("cgpa", 0)
            previous_cgpa = sorted_perf[-2].get("cgpa", 0)
            
            if latest_cgpa < previous_cgpa:
                recommendations.append({
                    "title": "CGPA Declining",
                    "description": f"Your CGPA dropped from {previous_cgpa:.2f} to {latest_cgpa:.2f}. Consider seeking academic support.",
                    "priority": "high"
                })
        
        # Check study hours
        study_data = self.data_manager.load_data(self.student_id, "academic", "study_hours") or []
        if study_data:
            recent_study = [
                session for session in study_data 
                if datetime.fromisoformat(session["date"]) > now - timedelta(days=7)
            ]
            
            if not recent_study:
                recommendations.append({
                    "title": "No Recent Study Sessions",
                    "description": "You haven't logged any study sessions in the past week. Regular study helps retain information.",
                    "priority": "medium"
                })
            elif sum(session.get("hours", 0) for session in recent_study) < 10:
                recommendations.append({
                    "title": "Low Study Hours",
                    "description": "You've logged less than 10 hours of study in the past week. Consider increasing your study time.",
                    "priority": "medium"
                })
        
        return recommendations
    
    def _generate_financial_recommendations(self) -> List[Dict[str, Any]]:
        """Generate financial recommendations"""
        recommendations = []
        
        # Load financial data
        transactions = self.data_manager.load_data(self.student_id, "financial", "transactions") or []
        budget = self.data_manager.load_data(self.student_id, "financial", "budget") or {}
        financial_aid = self.data_manager.load_data(self.student_id, "financial", "financial_aid") or []
        
        # Check if budget is set up
        if not budget:
            recommendations.append({
                "title": "Set Up Your Budget",
                "description": "Creating a budget is the first step to managing your finances effectively.",
                "priority": "high"
            })
        else:
            # Check for over-budget categories
            now = datetime.now()
            current_month_start = datetime(now.year, now.month, 1).isoformat()
            
            month_expenses = {}
            for transaction in transactions:
                if transaction.get("date") >= current_month_start and transaction.get("amount", 0) < 0:
                    category = transaction.get("category", "Other")
                    month_expenses[category] = month_expenses.get(category, 0) + abs(transaction.get("amount", 0))
            
            over_budget_categories = []
            for category, budgeted in budget.items():
                if budgeted > 0 and category in month_expenses and month_expenses[category] > budgeted:
                    over_budget_categories.append({
                        "category": category,
                        "budget": budgeted,
                        "actual": month_expenses[category],
                        "percent_over": (month_expenses[category] - budgeted) / budgeted * 100
                    })
            
            if over_budget_categories:
                # Find the most over-budget category
                most_over = max(over_budget_categories, key=lambda x: x["percent_over"])
                
                recommendations.append({
                    "title": f"Budget Alert: {most_over['category']}",
                    "description": f"You've exceeded your {most_over['category']} budget by ₹{most_over['actual'] - most_over['budget']:.0f} ({most_over['percent_over']:.0f}%).",
                    "priority": "high" if most_over["percent_over"] > 50 else "medium"
                })
        
        # Check for financial aid opportunities
        if not financial_aid:
            recommendations.append({
                "title": "Explore Scholarship Opportunities",
                "description": "Check the Financial Planner section to find scholarships you may be eligible for.",
                "priority": "medium"
            })
        
        # Check for emergency fund
        financial_goals = self.data_manager.load_data(self.student_id, "financial", "goals") or []
        has_emergency_fund = any(
            goal.get("name", "").lower().find("emergency") >= 0 for goal in financial_goals
        )
        
        if not has_emergency_fund:
            recommendations.append({
                "title": "Start an Emergency Fund",
                "description": "Even a small emergency fund can help you handle unexpected expenses.",
                "priority": "medium"
            })
        
        return recommendations
    
    def _generate_wellness_recommendations(self) -> List[Dict[str, Any]]:
        """Generate wellness recommendations"""
        recommendations = []
        
        # Load wellness data
        mood_data = self.data_manager.load_data(self.student_id, "wellness", "mood") or []
        sleep_data = self.data_manager.load_data(self.student_id, "wellness", "sleep") or []
        
        # Check mood trends
        if mood_data:
            recent_mood = [
                entry for entry in mood_data 
                if datetime.fromisoformat(entry["date"]) > datetime.now() - timedelta(days=7)
            ]
            
            if recent_mood:
                avg_mood = sum(entry.get("score", 0) for entry in recent_mood) / len(recent_mood)
                
                if avg_mood < 4:
                    recommendations.append({
                        "title": "Your Mood Has Been Low",
                        "description": "Your recent mood scores are below average. Consider using some stress management techniques.",
                        "priority": "high"
                    })
                
                # Check for stress factors
                stress_factors = []
                for entry in recent_mood:
                    if "stress_factors" in entry:
                        stress_factors.extend(entry["stress_factors"])
                
                if stress_factors:
                    # Count factor frequencies
                    factor_counts = {}
                    for factor in stress_factors:
                        factor_counts[factor] = factor_counts.get(factor, 0) + 1
                    
                    # Find the most common factor
                    most_common = max(factor_counts.items(), key=lambda x: x[1])
                    
                    if most_common[1] >= 3:  # If it appears at least 3 times
                        recommendations.append({
                            "title": f"Managing {most_common[0]}",
                            "description": f"{most_common[0]} appears to be a recurring stress factor. Check out the Stress Management section for strategies.",
                            "priority": "medium"
                        })
        else:
            recommendations.append({
                "title": "Start Tracking Your Mood",
                "description": "Regular mood tracking helps you identify patterns and manage your mental health better.",
                "priority": "low"
            })
        
        # Check sleep patterns
        if sleep_data:
            recent_sleep = [
                entry for entry in sleep_data 
                if datetime.fromisoformat(entry["date"]) > datetime.now() - timedelta(days=7)
            ]
            
            if recent_sleep:
                avg_sleep = sum(entry.get("hours", 0) for entry in recent_sleep) / len(recent_sleep)
                
                if avg_sleep < 6:
                    recommendations.append({
                        "title": "Improve Sleep Habits",
                        "description": f"You're averaging only {avg_sleep:.1f} hours of sleep. Aim for 7-9 hours for better academic performance.",
                        "priority": "high"
                    })
        
        return recommendations
    
    def _generate_career_recommendations(self) -> List[Dict[str, Any]]:
        """Generate career recommendations"""
        recommendations = []
        
        # Load career data
        career_data = self.data_manager.load_data(self.student_id, "career", "data") or {}
        skills = self.data_manager.load_data(self.student_id, "career", "skills") or []
        experiences = self.data_manager.load_data(self.student_id, "career", "experiences") or []
        
        # Check if career interests are defined
        if not career_data.get("interests"):
            recommendations.append({
                "title": "Define Your Career Interests",
                "description": "Identifying your interests helps align your academic and extracurricular activities.",
                "priority": "medium"
            })
        
        # Check for skills development
        if not skills:
            recommendations.append({
                "title": "Start Tracking Skills",
                "description": "Documenting and developing your skills is essential for career readiness.",
                "priority": "low"
            })
        
        # Check for experiences (internships, projects, etc.)
        if not experiences:
            # Check student's year of study
            year_of_study = self.student_profile.get("year_of_study", "")
            
            if year_of_study in ["2nd Year", "3rd Year", "4th Year", "Final Year"]:
                recommendations.append({
                    "title": "Gain Practical Experience",
                    "description": "Consider applying for internships or working on projects to build your resume.",
                    "priority": "high" if year_of_study in ["3rd Year", "4th Year", "Final Year"] else "medium"
                })
        
        return recommendations
