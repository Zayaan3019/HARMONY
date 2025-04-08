from datetime import datetime
from typing import Dict, Any, Optional

class StudentProfile:
    """
    Manages student profile data and preferences
    """
    
    def __init__(self, student_id: str, profile_data: Dict[str, Any]):
        """Initialize with student ID and profile data"""
        self.student_id = student_id
        self.profile_data = profile_data
        
        # Set defaults for any missing fields
        self._set_defaults()
    
    def _set_defaults(self) -> None:
        """Set default values for any missing profile fields"""
        defaults = {
            "full_name": "Student",
            "college_name": "College",
            "degree": "Degree",
            "year_of_study": "1st Year",
            "created_at": datetime.now().isoformat(),
            "preferences": {
                "theme": "light",
                "notifications_enabled": True,
                "privacy_level": "standard"
            }
        }
        
        for key, value in defaults.items():
            if key not in self.profile_data:
                self.profile_data[key] = value
    
    def get_full_name(self) -> str:
        """Get the student's full name"""
        return self.profile_data.get("full_name", "Student")
    
    def get_college_name(self) -> str:
        """Get the student's college/university name"""
        return self.profile_data.get("college_name", "College")
    
    def get_degree(self) -> str:
        """Get the student's degree program"""
        return self.profile_data.get("degree", "Degree")
    
    def get_year_of_study(self) -> str:
        """Get the student's year of study"""
        return self.profile_data.get("year_of_study", "1st Year")
    
    def get_email(self) -> Optional[str]:
        """Get the student's email address"""
        return self.profile_data.get("email")
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a specific preference value"""
        preferences = self.profile_data.get("preferences", {})
        return preferences.get(key, default)
    
    def update_profile(self, updates: Dict[str, Any]) -> bool:
        """Update the student profile with new values"""
        self.profile_data.update(updates)
        # In a real implementation, we would save the profile here
        return True
    
    def update_preference(self, key: str, value: Any) -> bool:
        """Update a specific preference"""
        if "preferences" not in self.profile_data:
            self.profile_data["preferences"] = {}
        
        self.profile_data["preferences"][key] = value
        # In a real implementation, we would save the profile here
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for storage"""
        return self.profile_data

    def get_all_data(self):
        """
        Return all profile data for the student
        Returns the entire profile data dict
        """
        try:
            # Return the entire profile data
            return self.profile_data
        except Exception as e:
            print(f"Error getting all profile data: {e}")
            return {}
