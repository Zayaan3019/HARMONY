from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import random

class MentalWellnessCoach:
    """
    Tracks and provides guidance for mental wellness and stress management
    """
    
    def __init__(self, student_id: str, data_manager):
        """Initialize the mental wellness coach for a student"""
        self.student_id = student_id
        self.data_manager = data_manager
        
        # Load saved wellness data
        self.mood_entries = data_manager.load_data(student_id, "wellness", "mood") or []
        self.sleep_data = data_manager.load_data(student_id, "wellness", "sleep") or []
        self.coping_strategies = data_manager.load_data(student_id, "wellness", "coping_strategies") or []
        self.resources = data_manager.load_data(student_id, "wellness", "resources") or []
        self.habits = data_manager.load_data(student_id, "wellness", "habits") or []
    
    def log_mood(self, mood_data: Dict[str, Any]) -> bool:
        """Log a new mood entry"""
        # Generate a unique ID if not provided
        if "entry_id" not in mood_data:
            mood_data["entry_id"] = str(uuid.uuid4())
        
        # Add timestamp if not provided
        if "created_at" not in mood_data:
            mood_data["created_at"] = datetime.now().isoformat()
        
        # Add the mood entry
        self.mood_entries.append(mood_data)
        
        # Extract sleep data if provided
        if "sleep_hours" in mood_data:
            sleep_entry = {
                "date": mood_data.get("date", datetime.now().isoformat()),
                "hours": mood_data["sleep_hours"],
                "entry_id": str(uuid.uuid4())
            }
            
            self.sleep_data.append(sleep_entry)
            self.data_manager.save_data(self.student_id, "wellness", "sleep", self.sleep_data)
        
        # Save the updated mood entries
        success = self.data_manager.save_data(
            self.student_id, "wellness", "mood", self.mood_entries
        )
        
        return success
    
    def get_mood_history(self) -> List[Dict[str, Any]]:
        """Get the student's mood history"""
        if not self.mood_entries:
            # Return sample data for new students
            sample_dates = [
                (datetime.now() - timedelta(days=i)).isoformat()
                for i in range(14, 0, -1)
            ]
            
            return [
                {"date": date, "score": 5 + random.randint(-2, 2)}
                for date in sample_dates
            ]
        
        # Format for display (select date and score only)
        return [
            {"date": entry.get("date", ""), "score": entry.get("score", 0)}
            for entry in self.mood_entries
        ]
    
    def get_current_wellness_score(self) -> float:
        """Get the student's current wellness score"""
        if not self.mood_entries:
            return 7.0  # Default score
        
        # Get the most recent entry
        sorted_entries = sorted(
            self.mood_entries,
            key=lambda x: x.get("date", ""),
            reverse=True
        )
        
        if sorted_entries:
            return sorted_entries[0].get("score", 7.0)
        
        return 7.0  # Default score
    
    def add_coping_strategy(self, strategy_data: Dict[str, Any]) -> bool:
        """Add a new coping strategy"""
        # Generate a unique ID if not provided
        if "strategy_id" not in strategy_data:
            strategy_data["strategy_id"] = str(uuid.uuid4())
        
        # Add timestamp if not provided
        if "created_at" not in strategy_data:
            strategy_data["created_at"] = datetime.now().isoformat()
        
        # Add the strategy
        self.coping_strategies.append(strategy_data)
        
        # Save the updated strategies
        success = self.data_manager.save_data(
            self.student_id, "wellness", "coping_strategies", self.coping_strategies
        )
        
        return success
    
    def log_strategy_usage(self, strategy_id: str) -> bool:
        """Log the usage of a coping strategy"""
        for i, strategy in enumerate(self.coping_strategies):
            if strategy.get("strategy_id") == strategy_id:
                # Increment usage count
                if "usage_count" in strategy:
                    self.coping_strategies[i]["usage_count"] += 1
                else:
                    self.coping_strategies[i]["usage_count"] = 1
                
                # Add last used timestamp
                self.coping_strategies[i]["last_used"] = datetime.now().isoformat()
                
                # Save the updated strategies
                return self.data_manager.save_data(
                    self.student_id, "wellness", "coping_strategies", self.coping_strategies
                )
        
        return False  # Strategy not found
    
    def get_coping_strategies(self) -> List[Dict[str, Any]]:
        """Get the student's coping strategies"""
        if not self.coping_strategies:
            # Return sample strategies for new students
            return [
                {
                    "strategy_id": "s1",
                    "name": "Deep Breathing",
                    "category": "Mindfulness",
                    "effectiveness": 8,
                    "usage_count": 5
                },
                {
                    "strategy_id": "s2",
                    "name": "Going for a Walk",
                    "category": "Physical Activity",
                    "effectiveness": 7,
                    "usage_count": 3
                },
                {
                    "strategy_id": "s3",
                    "name": "Talking with Friends",
                    "category": "Social Connection",
                    "effectiveness": 9,
                    "usage_count": 4
                }
            ]
        
        return self.coping_strategies
    
    def get_stress_factors_analysis(self) -> Dict[str, Any]:
        """Analyze stress factors from mood entries"""
        if not self.mood_entries:
            return {"factors": []}
        
        # Extract all stress factors
        all_factors = []
        for entry in self.mood_entries:
            if "stress_factors" in entry and entry["stress_factors"]:
                all_factors.extend(entry["stress_factors"])
        
        # Count factor frequencies
        factor_counts = {}
        for factor in all_factors:
            if factor in factor_counts:
                factor_counts[factor] += 1
            else:
                factor_counts[factor] = 1
        
        # Format for display
        factors = [
            {"factor": factor, "count": count}
            for factor, count in factor_counts.items()
        ]
        
        # Sort by count (descending)
        factors.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "factors": factors,
            "total_entries": len(self.mood_entries),
            "entries_with_factors": len([e for e in self.mood_entries if "stress_factors" in e and e["stress_factors"]])
        }
    
    def get_strategies_for_factor(self, factor: str) -> List[str]:
        """Get recommended strategies for a specific stress factor"""
        # Define recommendations for common stress factors
        recommendations = {
            "Academic pressure": [
                "Break large tasks into smaller, manageable steps",
                "Use the Pomodoro technique (25 min work, 5 min break)",
                "Form or join a study group for difficult subjects",
                "Talk to your professors during office hours"
            ],
            "Exam stress": [
                "Create a realistic study schedule",
                "Practice with past papers or sample questions",
                "Use memory techniques like spaced repetition",
                "Get enough sleep the night before exams"
            ],
            "Assignment deadlines": [
                "Start assignments early, even with a small step",
                "Create a timeline with milestones for larger projects",
                "Use calendar reminders for upcoming deadlines",
                "Reach out to teaching assistants for clarification"
            ],
            "Financial concerns": [
                "Create a detailed monthly budget",
                "Look into scholarship or grant opportunities",
                "Consider part-time work that fits your schedule",
                "Speak with your university financial aid office"
            ],
            "Family expectations": [
                "Have an honest conversation about realistic goals",
                "Set boundaries while respecting family values",
                "Seek support from university counseling services",
                "Connect with others facing similar pressures"
            ],
            "Relationship issues": [
                "Practice active listening and open communication",
                "Take time for self-reflection on your needs and feelings",
                "Maintain other supportive friendships",
                "Consider speaking with a counselor for guidance"
            ],
            "Health problems": [
                "Don't skip medical appointments",
                "Inform professors if health is affecting academics",
                "Explore campus health resources",
                "Prioritize sleep, nutrition, and movement"
            ],
            "Homesickness": [
                "Create a space with familiar items from home",
                "Schedule regular calls with family and friends",
                "Join campus groups to build a new community",
                "Explore your new surroundings with others"
            ],
            "Career uncertainty": [
                "Visit your campus career center",
                "Arrange informational interviews in fields of interest",
                "Join clubs related to potential career paths",
                "Remember that many successful people changed paths"
            ]
        }
        
        # Return recommendations for the specific factor
        for key, strategies in recommendations.items():
            if factor.lower() in key.lower() or key.lower() in factor.lower():
                return strategies
        
        # Default recommendations if no specific match
        return [
            "Practice deep breathing for immediate stress relief",
            "Physical activity helps reduce stress hormones",
            "Maintain social connections for support",
            "Ensure you're getting adequate sleep"
        ]
    
    def get_sleep_data(self) -> List[Dict[str, Any]]:
        """Get the student's sleep data"""
        if not self.sleep_data:
            # Return sample data for new students
            sample_dates = [
                (datetime.now() - timedelta(days=i)).isoformat()
                for i in range(14, 0, -1)
            ]
            
            return [
                {"date": date, "hours": 6 + random.randint(-1, 2)}
                for date in sample_dates
            ]
        
        return self.sleep_data
    
    def get_sleep_mood_correlation(self) -> float:
        """Calculate correlation between sleep hours and mood scores"""
        if not self.sleep_data or not self.mood_entries or len(self.sleep_data) < 5:
            return 0.0
        
        # Create dictionaries mapping dates to values
        sleep_by_date = {entry.get("date", ""): entry.get("hours", 0) for entry in self.sleep_data}
        mood_by_date = {entry.get("date", ""): entry.get("score", 0) for entry in self.mood_entries}
        
        # Find dates that have both sleep and mood data
        common_dates = set(sleep_by_date.keys()).intersection(set(mood_by_date.keys()))
        
        if len(common_dates) < 5:
            return 0.0
        
        # Extract paired data
        sleep_values = [sleep_by_date[date] for date in common_dates]
        mood_values = [mood_by_date[date] for date in common_dates]
        
        # Calculate correlation (simple approach)
        try:
            import numpy as np
            correlation = np.corrcoef(sleep_values, mood_values)[0, 1]
            return correlation
        except:
            # Fallback if numpy is not available
            n = len(sleep_values)
            sum_x = sum(sleep_values)
            sum_y = sum(mood_values)
            sum_xy = sum(x * y for x, y in zip(sleep_values, mood_values))
            sum_x2 = sum(x * x for x in sleep_values)
            sum_y2 = sum(y * y for y in mood_values)
            
            numerator = n * sum_xy - sum_x * sum_y
            denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
            
            if denominator == 0:
                return 0.0
            
            return numerator / denominator
    
    def add_resource(self, resource_data: Dict[str, Any]) -> bool:
        """Add a mental health resource"""
        # Generate a unique ID if not provided
        if "resource_id" not in resource_data:
            resource_data["resource_id"] = str(uuid.uuid4())
        
        # Add timestamp if not provided
        if "created_at" not in resource_data:
            resource_data["created_at"] = datetime.now().isoformat()
        
        # Add the resource
        self.resources.append(resource_data)
        
        # Save the updated resources
        success = self.data_manager.save_data(
            self.student_id, "wellness", "resources", self.resources
        )
        
        return success
    
    def get_campus_resources(self) -> List[Dict[str, Any]]:
        """Get campus mental health resources"""
        campus_resources = [r for r in self.resources if r.get("type") == "Campus"]
        
        if not campus_resources:
            # Return sample campus resources
            return [
                {
                    "name": "University Counseling Center",
                    "location": "Student Welfare Building, Room 102",
                    "contact": "counseling@university.edu",
                    "services": "Individual counseling, group therapy, crisis intervention"
                },
                {
                    "name": "Student Health Services",
                    "location": "Health Center",
                    "contact": "health@university.edu",
                    "services": "Basic health services, psychiatric consultations"
                },
                {
                    "name": "Peer Support Network",
                    "location": "Student Union, Room 205",
                    "contact": "peers@university.edu",
                    "services": "Peer counseling, support groups, wellness workshops"
                }
            ]
        
        return campus_resources
    
    def add_wellness_habit(self, habit_data: Dict[str, Any]) -> bool:
        """Add a new wellness habit to track"""
        # Generate a unique ID if not provided
        if "habit_id" not in habit_data:
            habit_data["habit_id"] = str(uuid.uuid4())
        
        # Initialize tracking fields
        habit_data["current_streak"] = 0
        habit_data["longest_streak"] = 0
        habit_data["start_date"] = datetime.now().isoformat()
        habit_data["last_completed"] = None
        habit_data["completion_history"] = []
        
        # Add the habit
        self.habits.append(habit_data)
        
        # Save the updated habits
        success = self.data_manager.save_data(
            self.student_id, "wellness", "habits", self.habits
        )
        
        return success
    
    def log_habit_completion(self, habit_id: str) -> bool:
        """Log the completion of a wellness habit"""
        for i, habit in enumerate(self.habits):
            if habit.get("habit_id") == habit_id:
                today = datetime.now().date().isoformat()
                
                # Check if already completed today
                completion_history = habit.get("completion_history", [])
                if completion_history and completion_history[-1] == today:
                    return False  # Already completed today
                
                # Add to completion history
                completion_history.append(today)
                self.habits[i]["completion_history"] = completion_history
                
                # Update last completed
                self.habits[i]["last_completed"] = today
                
                # Update streak
                last_completed = habit.get("last_completed")
                if last_completed:
                    yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
                    if last_completed == yesterday:
                        # Consecutive day, increment streak
                        self.habits[i]["current_streak"] = habit.get("current_streak", 0) + 1
                    else:
                        # Streak broken, reset
                        self.habits[i]["current_streak"] = 1
                else:
                    # First completion
                    self.habits[i]["current_streak"] = 1
                
                # Update longest streak
                current_streak = self.habits[i].get("current_streak", 0)
                longest_streak = self.habits[i].get("longest_streak", 0)
                
                if current_streak > longest_streak:
                    self.habits[i]["longest_streak"] = current_streak
                
                # Save the updated habits
                return self.data_manager.save_data(
                    self.student_id, "wellness", "habits", self.habits
                )
        
        return False  # Habit not found
    
    def get_wellness_habits(self) -> List[Dict[str, Any]]:
        """Get the student's wellness habits"""
        if not self.habits:
            # Return sample habits for new students
            return [
                {
                    "habit_id": "h1",
                    "name": "Meditation",
                    "category": "Mindfulness",
                    "current_streak": 3,
                    "longest_streak": 5
                },
                {
                    "habit_id": "h2",
                    "name": "Physical Activity",
                    "category": "Exercise",
                    "current_streak": 1,
                    "longest_streak": 7
                },
                {
                    "habit_id": "h3",
                    "name": "Gratitude Journal",
                    "category": "Positive Psychology",
                    "current_streak": 0,
                    "longest_streak": 4
                }
            ]
        
        return self.habits
    
    def get_habit_history(self, habit_id: str) -> List[Dict[str, Any]]:
        """Get completion history for a specific habit"""
        for habit in self.habits:
            if habit.get("habit_id") == habit_id:
                completion_history = habit.get("completion_history", [])
                
                # Convert to format for display
                return [
                    {"date": date, "completed": True}
                    for date in completion_history
                ]
        
        return []  # Habit not found
