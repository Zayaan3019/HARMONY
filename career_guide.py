from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid

class CareerGuide:
    """
    Provides career guidance, skill development tracking, and opportunity matching
    """
    
    def __init__(self, student_id: str, data_manager):
        """Initialize the career guide for a student"""
        self.student_id = student_id
        self.data_manager = data_manager
        
        # Load saved career data
        self.career_data = data_manager.load_data(student_id, "career", "data") or {}
        self.skills = data_manager.load_data(student_id, "career", "skills") or []
        self.experiences = data_manager.load_data(student_id, "career", "experiences") or []
        self.opportunities = data_manager.load_data(student_id, "career", "opportunities") or []
    
    def update_career_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Update career preferences and interests"""
        if not self.career_data:
            self.career_data = {}
        
        # Update preferences
        self.career_data.update(preferences)
        
        # Add update timestamp
        self.career_data["last_updated"] = datetime.now().isoformat()
        
        # Save the updated career data
        success = self.data_manager.save_data(
            self.student_id, "career", "data", self.career_data
        )
        
        return success
    
    def get_career_preferences(self) -> Dict[str, Any]:
        """Get career preferences and interests"""
        if not self.career_data:
            # Return default preferences for new students
            return {
                "interests": [
                    "Software Development", 
                    "Data Analysis",
                    "Product Management"
                ],
                "work_values": [
                    "Learning Opportunities",
                    "Work-Life Balance",
                    "Creativity"
                ],
                "preferred_work_environment": "Collaborative team with mentorship",
                "location_preferences": ["Bengaluru", "Hyderabad", "Remote"],
                "target_roles": ["Software Engineer", "Data Scientist"]
            }
        
        return self.career_data
    
    def add_skill(self, skill_data: Dict[str, Any]) -> bool:
        """Add a new skill"""
        # Generate a unique ID if not provided
        if "skill_id" not in skill_data:
            skill_data["skill_id"] = str(uuid.uuid4())
        
        # Add creation timestamp
        if "created_at" not in skill_data:
            skill_data["created_at"] = datetime.now().isoformat()
        
        # Add the skill
        self.skills.append(skill_data)
        
        # Save the updated skills list
        success = self.data_manager.save_data(
            self.student_id, "career", "skills", self.skills
        )
        
        return success
    
    def update_skill(self, skill_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing skill"""
        for i, skill in enumerate(self.skills):
            if skill.get("skill_id") == skill_id:
                self.skills[i].update(updates)
                
                # Add update timestamp
                self.skills[i]["updated_at"] = datetime.now().isoformat()
                
                # Save the updated skills list
                return self.data_manager.save_data(
                    self.student_id, "career", "skills", self.skills
                )
        
        return False  # Skill not found
    
    def delete_skill(self, skill_id: str) -> bool:
        """Delete a skill"""
        original_len = len(self.skills)
        self.skills = [skill for skill in self.skills if skill.get("skill_id") != skill_id]
        
        if len(self.skills) < original_len:
            # Save the updated skills list
            return self.data_manager.save_data(
                self.student_id, "career", "skills", self.skills
            )
        
        return False  # Skill not found
    
    def get_skills(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get skills, optionally filtered by category"""
        if not self.skills:
            # Return sample skills for new students
            return [
                {
                    "skill_id": "s1",
                    "name": "Python Programming",
                    "category": "Technical",
                    "proficiency": 3,
                    "description": "Experience with data analysis and web development"
                },
                {
                    "skill_id": "s2",
                    "name": "Project Management",
                    "category": "Soft Skills",
                    "proficiency": 2,
                    "description": "Led team projects in college"
                },
                {
                    "skill_id": "s3",
                    "name": "Public Speaking",
                    "category": "Communication",
                    "proficiency": 3,
                    "description": "Presented at college events and competitions"
                }
            ]
        
        if category:
            return [skill for skill in self.skills if skill.get("category") == category]
        
        return self.skills
    
    def add_experience(self, experience_data: Dict[str, Any]) -> bool:
        """Add a new experience (internship, project, etc.)"""
        # Generate a unique ID if not provided
        if "experience_id" not in experience_data:
            experience_data["experience_id"] = str(uuid.uuid4())
        
        # Add creation timestamp
        if "created_at" not in experience_data:
            experience_data["created_at"] = datetime.now().isoformat()
        
        # Add the experience
        self.experiences.append(experience_data)
        
        # Save the updated experiences list
        success = self.data_manager.save_data(
            self.student_id, "career", "experiences", self.experiences
        )
        
        return success
    
    def update_experience(self, experience_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing experience"""
        for i, experience in enumerate(self.experiences):
            if experience.get("experience_id") == experience_id:
                self.experiences[i].update(updates)
                
                # Add update timestamp
                self.experiences[i]["updated_at"] = datetime.now().isoformat()
                
                # Save the updated experiences list
                return self.data_manager.save_data(
                    self.student_id, "career", "experiences", self.experiences
                )
        
        return False  # Experience not found
    
    def delete_experience(self, experience_id: str) -> bool:
        """Delete an experience"""
        original_len = len(self.experiences)
        self.experiences = [exp for exp in self.experiences if exp.get("experience_id") != experience_id]
        
        if len(self.experiences) < original_len:
            # Save the updated experiences list
            return self.data_manager.save_data(
                self.student_id, "career", "experiences", self.experiences
            )
        
        return False  # Experience not found
    
    def get_experiences(self, experience_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get experiences, optionally filtered by type"""
        if not self.experiences:
            # Return sample experiences for new students
            return [
                {
                    "experience_id": "e1",
                    "title": "Software Development Intern",
                    "organization": "Tech Solutions Ltd.",
                    "type": "Internship",
                    "start_date": "2024-05-01",
                    "end_date": "2024-07-30",
                    "description": "Developed features for a web application using React and Node.js"
                },
                {
                    "experience_id": "e2",
                    "title": "College Fest Coordinator",
                    "organization": "College Technical Club",
                    "type": "Leadership",
                    "start_date": "2023-09-01",
                    "end_date": "2023-10-15",
                    "description": "Led a team of 10 students to organize the annual technical fest"
                }
            ]
        
        if experience_type:
            return [exp for exp in self.experiences if exp.get("type") == experience_type]
        
        return self.experiences
    
    def add_opportunity(self, opportunity_data: Dict[str, Any]) -> bool:
        """Add a new opportunity (job, internship, etc.)"""
        # Generate a unique ID if not provided
        if "opportunity_id" not in opportunity_data:
            opportunity_data["opportunity_id"] = str(uuid.uuid4())
        
        # Add creation timestamp
        if "created_at" not in opportunity_data:
            opportunity_data["created_at"] = datetime.now().isoformat()
        
        # Add the opportunity
        self.opportunities.append(opportunity_data)
        
        # Save the updated opportunities list
        success = self.data_manager.save_data(
            self.student_id, "career", "opportunities", self.opportunities
        )
        
        return success
    
    def get_opportunities(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get opportunities, optionally filtered by status"""
        if not self.opportunities:
            # Return sample opportunities for new students
            return [
                {
                    "opportunity_id": "o1",
                    "title": "Software Engineering Intern",
                    "company": "Google",
                    "location": "Bengaluru",
                    "type": "Internship",
                    "application_deadline": "2025-02-15",
                    "status": "Bookmarked"
                },
                {
                    "opportunity_id": "o2",
                    "title": "Data Science Intern",
                    "company": "Microsoft",
                    "location": "Hyderabad",
                    "type": "Internship",
                    "application_deadline": "2025-02-28",
                    "status": "Applied"
                }
            ]
        
        if status:
            return [opp for opp in self.opportunities if opp.get("status") == status]
        
        return self.opportunities
    
    def get_recommended_opportunities(self) -> List[Dict[str, Any]]:
        """Get opportunities recommended based on student's profile"""
        # In a real implementation, this would use matching algorithms
        # For this example, we'll return sample recommendations
        
        preferences = self.get_career_preferences()
        interests = preferences.get("interests", [])
        target_roles = preferences.get("target_roles", [])
        
        # Sample recommendations based on interests and target roles
        recommendations = [
            {
                "title": "Software Engineering Intern",
                "company": "Amazon",
                "location": "Bengaluru",
                "type": "Internship",
                "application_deadline": "2025-03-15",
                "match_score": 85
            },
            {
                "title": "Data Science Intern",
                "company": "Flipkart",
                "location": "Bengaluru",
                "type": "Internship",
                "application_deadline": "2025-03-10",
                "match_score": 78
            },
            {
                "title": "Product Management Intern",
                "company": "Swiggy",
                "location": "Bengaluru",
                "type": "Internship",
                "application_deadline": "2025-03-20",
                "match_score": 72
}
        ]
        
        return recommendations
    
    def get_career_readiness_score(self) -> float:
        """Calculate and return the student's career readiness score"""
        score = 0.0
        
        # Check for basic career components
        if self.career_data.get("interests"):
            score += 10
        
        if self.career_data.get("target_roles"):
            score += 10
        
        # Check for resume completion
        resume_data = self.career_data.get("resume", {})
        if resume_data:
            score += 15
        
        # Check skills
        if self.skills:
            score += min(20, len(self.skills) * 4)  # Up to 20 points for skills
        
        # Check experiences
        if self.experiences:
            score += min(25, len(self.experiences) * 8)  # Up to 25 points for experiences
        
        # Check network and connections
        network_size = self.career_data.get("network_size", 0)
        score += min(10, network_size / 5)  # Up to 10 points for network
        
        # Check for applications
        applications = [opp for opp in self.opportunities if opp.get("status") == "Applied"]
        score += min(10, len(applications) * 2)  # Up to 10 points for applications
        
        # Ensure score is in 0-100 range
        return min(100, max(0, score))
    
    def get_career_profile(self):
        """
        Get the career profile data for the student
        Returns the career profile dict or None if not found
        """
        try:
            # Try to get career profile from data manager
            profile = self.data_manager.get_data(
                self.student_id, "career_profile", default=None
            )
            return profile
        except Exception as e:
            print(f"Error getting career profile: {e}")
            return None
