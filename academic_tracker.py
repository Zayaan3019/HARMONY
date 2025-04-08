from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

class AcademicTracker:
    """
    Tracks academic performance, courses, assignments, and study patterns
    """
    
    def __init__(self, student_id: str, data_manager):
        """Initialize the academic tracker for a student"""
        self.student_id = student_id
        self.data_manager = data_manager
        
        # Load saved academic data
        self.courses = data_manager.load_data(student_id, "academic", "courses") or []
        self.tasks = data_manager.load_data(student_id, "academic", "tasks") or []
        self.performance = data_manager.load_data(student_id, "academic", "performance") or []
        self.study_sessions = data_manager.load_data(student_id, "academic", "study_sessions") or []
        self.goals = data_manager.load_data(student_id, "academic", "goals") or []
    
    def get_courses(self, current_only: bool = False) -> List[Dict[str, Any]]:
        """Get the student's courses, optionally only current ones"""
        if current_only:
            return [course for course in self.courses if course.get("is_current", True)]
        return self.courses
    
    def add_course(self, course_data: Dict[str, Any]) -> bool:
        """Add a new course"""
        # Generate a unique ID if not provided
        if "course_id" not in course_data:
            course_data["course_id"] = str(uuid.uuid4())
        
        # Add creation timestamp
        if "created_at" not in course_data:
            course_data["created_at"] = datetime.now().isoformat()
        
        # Add the course
        self.courses.append(course_data)
        
        # Save the updated courses list
        success = self.data_manager.save_data(
            self.student_id, "academic", "courses", self.courses
        )
        
        return success
    
    def update_course(self, course_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing course"""
        for i, course in enumerate(self.courses):
            if course.get("course_id") == course_id:
                self.courses[i].update(updates)
                
                # Save the updated courses list
                return self.data_manager.save_data(
                    self.student_id, "academic", "courses", self.courses
                )
        
        return False  # Course not found
    
    def delete_course(self, course_id: str) -> bool:
        """Delete a course"""
        original_len = len(self.courses)
        self.courses = [course for course in self.courses if course.get("course_id") != course_id]
        
        if len(self.courses) < original_len:
            # Save the updated courses list
            return self.data_manager.save_data(
                self.student_id, "academic", "courses", self.courses
            )
        
        return False  # Course not found
    
    def get_course_by_code(self, course_code: str) -> Optional[Dict[str, Any]]:
        """Get a course by its code"""
        for course in self.courses:
            if course.get("code") == course_code:
                return course
        return None
    
    def get_course_performance(self, course_code: str) -> List[Dict[str, Any]]:
        """Get performance data for a specific course"""
        # Normally this would be loaded from a separate file or database
        # For this example, we'll generate some sample data
        return [
            {"title": "Quiz 1", "score": 8, "max_score": 10, "percentage": 80},
            {"title": "Assignment 1", "score": 17, "max_score": 20, "percentage": 85},
            {"title": "Midterm", "score": 27, "max_score": 30, "percentage": 90}
        ]
    
    def get_upcoming_tasks(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get upcoming tasks, optionally limited to a specific count"""
        now = datetime.now()
        
        # Sort tasks by due date
        upcoming = sorted(
            [task for task in self.tasks if task.get("status") != "completed"],
            key=lambda x: datetime.fromisoformat(x.get("due_date", now.isoformat()))
        )
        
        if limit:
            return upcoming[:limit]
        return upcoming
    
    def add_task(self, task_data: Dict[str, Any]) -> bool:
        """Add a new task"""
        # Generate a unique ID if not provided
        if "task_id" not in task_data:
            task_data["task_id"] = str(uuid.uuid4())
        
        # Add creation timestamp
        if "created_at" not in task_data:
            task_data["created_at"] = datetime.now().isoformat()
        
        # Add the task
        self.tasks.append(task_data)
        
        # Save the updated tasks list
        success = self.data_manager.save_data(
            self.student_id, "academic", "tasks", self.tasks
        )
        
        return success
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing task"""
        for i, task in enumerate(self.tasks):
            if task.get("task_id") == task_id:
                self.tasks[i].update(updates)
                
                # Save the updated tasks list
                return self.data_manager.save_data(
                    self.student_id, "academic", "tasks", self.tasks
                )
        
        return False  # Task not found
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        original_len = len(self.tasks)
        self.tasks = [task for task in self.tasks if task.get("task_id") != task_id]
        
        if len(self.tasks) < original_len:
            # Save the updated tasks list
            return self.data_manager.save_data(
                self.student_id, "academic", "tasks", self.tasks
            )
        
        return False  # Task not found
    
    def get_performance_history(self) -> List[Dict[str, Any]]:
        """Get the student's academic performance history"""
        if not self.performance:
            # Return sample data for new students
            return [
                {"semester": "Semester 1", "semester_index": 1, "sgpa": 8.5, "cgpa": 8.5, "credits": 20},
                {"semester": "Semester 2", "semester_index": 2, "sgpa": 8.7, "cgpa": 8.6, "credits": 22}
            ]
        
        return self.performance
    
    def add_semester_performance(self, performance_data: Dict[str, Any]) -> bool:
        """Add performance data for a new semester"""
        # Calculate CGPA based on previous performance
        if "sgpa" in performance_data and "credits" in performance_data:
            # Sort existing performance by semester index
            sorted_performance = sorted(
                self.performance, 
                key=lambda x: x.get("semester_index", 0)
            )
            
            if not sorted_performance:
                # First semester, CGPA equals SGPA
                performance_data["cgpa"] = performance_data["sgpa"]
            else:
                # Calculate weighted average for CGPA
                total_credits = sum(sem.get("credits", 0) for sem in sorted_performance)
                total_credits += performance_data["credits"]
                
                weighted_sum = sum(
                    sem.get("sgpa", 0) * sem.get("credits", 0) 
                    for sem in sorted_performance
                )
                weighted_sum += performance_data["sgpa"] * performance_data["credits"]
                
                performance_data["cgpa"] = weighted_sum / total_credits if total_credits > 0 else 0
        
        # Add the performance data
        self.performance.append(performance_data)
        
        # Save the updated performance list
        success = self.data_manager.save_data(
            self.student_id, "academic", "performance", self.performance
        )
        
        return success
    
    def get_current_cgpa(self) -> float:
        """Get the student's current CGPA"""
        if not self.performance:
            return 0.0
        
        # Find the semester with the highest index
        latest = max(self.performance, key=lambda x: x.get("semester_index", 0))
        return latest.get("cgpa", 0.0)
    
    def get_cgpa_goal(self) -> float:
        """Get the student's CGPA goal"""
        for goal in self.goals:
            if goal.get("goal_type") == "cgpa":
                return goal.get("target_value", 8.0)
        
        return 8.0  # Default goal
    
    def add_study_session(self, session_data: Dict[str, Any]) -> bool:
        """Add a new study session"""
        # Generate a unique ID if not provided
        if "session_id" not in session_data:
            session_data["session_id"] = str(uuid.uuid4())
        
        # Add timestamp if not provided
        if "created_at" not in session_data:
            session_data["created_at"] = datetime.now().isoformat()
        
        # Add the session
        self.study_sessions.append(session_data)
        
        # Save the updated sessions list
        success = self.data_manager.save_data(
            self.student_id, "academic", "study_sessions", self.study_sessions
        )
        
        return success
    
    def get_study_hours_history(self) -> List[Dict[str, Any]]:
        """Get the student's study hours history"""
        if not self.study_sessions:
            # Return sample data for new students
            sample_dates = [
                (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range(7, 0, -1)
            ]
            return [
                {"date": date, "hours": 2 + (i % 3), "subject": "Sample"}
                for i, date in enumerate(sample_dates)
            ]
        
        return self.study_sessions
    
    def get_study_hours_by_subject(self) -> List[Dict[str, Any]]:
        """Get study hours grouped by subject"""
        if not self.study_sessions:
            return []
        
        # Group hours by subject
        subjects = {}
        for session in self.study_sessions:
            subject = session.get("subject", "Other")
            hours = session.get("hours", 0)
            
            if subject in subjects:
                subjects[subject] += hours
            else:
                subjects[subject] = hours
        
        # Convert to list format
        return [{"subject": subject, "hours": hours} for subject, hours in subjects.items()]
    
    def add_academic_goal(self, goal_data: Dict[str, Any]) -> bool:
        """Add a new academic goal"""
        # Generate a unique ID if not provided
        if "goal_id" not in goal_data:
            goal_data["goal_id"] = str(uuid.uuid4())
        
        # Add creation timestamp
        if "created_at" not in goal_data:
            goal_data["created_at"] = datetime.now().isoformat()
        
        # Add the goal
        self.goals.append(goal_data)
        
        # Save the updated goals list
        success = self.data_manager.save_data(
            self.student_id, "academic", "goals", self.goals
        )
        
        return success
    
    def update_academic_goal(self, goal_id: str, current_value: float) -> bool:
        """Update the current value of an academic goal"""
        for i, goal in enumerate(self.goals):
            if goal.get("goal_id") == goal_id:
                self.goals[i]["current_value"] = current_value
                
                # Check if goal is completed
                if current_value >= self.goals[i].get("target_value", 0):
                    self.goals[i]["status"] = "completed"
                    self.goals[i]["completion_date"] = datetime.now().isoformat()
                
                # Save the updated goals list
                return self.data_manager.save_data(
                    self.student_id, "academic", "goals", self.goals
                )
        
        return False  # Goal not found
    
    def delete_academic_goal(self, goal_id: str) -> bool:
        """Delete an academic goal"""
        original_len = len(self.goals)
        self.goals = [goal for goal in self.goals if goal.get("goal_id") != goal_id]
        
        if len(self.goals) < original_len:
            # Save the updated goals list
            return self.data_manager.save_data(
                self.student_id, "academic", "goals", self.goals
            )
        
        return False  # Goal not found
    
    def get_academic_goals(self) -> List[Dict[str, Any]]:
        """Get the student's academic goals"""
        return self.goals
