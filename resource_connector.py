from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid

class ResourceConnector:
    """
    Connects students with campus and external resources
    """
    
    def __init__(self, student_id: str, data_manager):
        """Initialize the resource connector for a student"""
        self.student_id = student_id
        self.data_manager = data_manager
        
        # Load saved resource data
        self.resources = data_manager.load_data(student_id, "resources", "directory") or []
        self.bookmarks = data_manager.load_data(student_id, "resources", "bookmarks") or []
        self.usage_history = data_manager.load_data(student_id, "resources", "usage_history") or []


    def get_saved_resources(self):
        """Get saved resources for the student."""
        try:
            # Get saved resources from data manager
            resources = self.data_manager.get_data(
                self.student_id, "saved_resources", default=[]
            )
            return resources
        except Exception as e:
            print(f"Error getting saved resources: {e}")
            return []

    
    def get_campus_resources(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get campus resources, optionally filtered by category"""
        campus_resources = [r for r in self.resources if r.get("type") == "campus"]
        
        if not campus_resources:
            # Return default campus resources for Indian students
            campus_resources = [
                {
                    "resource_id": "cr1",
                    "name": "University Library",
                    "type": "campus",
                    "category": "academic",
                    "location": "Central Campus",
                    "contact": "library@college.edu",
                    "website": "library.college.edu",
                    "description": "Access to books, journals, and online databases",
                    "hours": "Mon-Sat: 8:00 AM - 10:00 PM, Sun: 10:00 AM - 6:00 PM"
                },
                {
                    "resource_id": "cr2",
                    "name": "Computer Lab",
                    "type": "campus",
                    "category": "technology",
                    "location": "Engineering Block",
                    "contact": "complab@college.edu",
                    "website": "tech.college.edu/labs",
                    "description": "Computers with specialized software for academic use",
                    "hours": "Mon-Fri: 9:00 AM - 8:00 PM, Sat: 9:00 AM - 5:00 PM"
                },
                {
                    "resource_id": "cr3",
                    "name": "Career Development Center",
                    "type": "campus",
                    "category": "career",
                    "location": "Administrative Block, 2nd Floor",
                    "contact": "careers@college.edu",
                    "website": "careers.college.edu",
                    "description": "Resume review, interview preparation, and job postings",
                    "hours": "Mon-Fri: 10:00 AM - 5:00 PM"
                },
                {
                    "resource_id": "cr4",
                    "name": "Student Counseling Services",
                    "type": "campus",
                    "category": "wellness",
                    "location": "Student Welfare Building",
                    "contact": "counseling@college.edu",
                    "website": "health.college.edu/counseling",
                    "description": "Mental health support and counseling",
                    "hours": "Mon-Fri: 9:00 AM - 4:00 PM"
                },
                {
                    "resource_id": "cr5",
                    "name": "Financial Aid Office",
                    "type": "campus",
                    "category": "financial",
                    "location": "Administrative Block, 1st Floor",
                    "contact": "finaid@college.edu",
                    "website": "finaid.college.edu",
                    "description": "Scholarships, loans, and financial assistance",
                    "hours": "Mon-Fri: 10:00 AM - 4:00 PM"
                }
            ]
        
        if category:
            return [r for r in campus_resources if r.get("category") == category]
        
        return campus_resources
    
    def get_external_resources(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get external resources, optionally filtered by category"""
        external_resources = [r for r in self.resources if r.get("type") == "external"]
        
        if not external_resources:
            # Return default external resources for Indian students
            external_resources = [
                {
                    "resource_id": "er1",
                    "name": "Swayam",
                    "type": "external",
                    "category": "academic",
                    "website": "https://swayam.gov.in/",
                    "description": "Free online courses from MHRD, Government of India",
                    "cost": "Free"
                },
                {
                    "resource_id": "er2",
                    "name": "National Digital Library of India",
                    "type": "external",
                    "category": "academic",
                    "website": "https://ndl.iitkgp.ac.in/",
                    "description": "Virtual repository of learning resources",
                    "cost": "Free"
                },
                {
                    "resource_id": "er3",
                    "name": "Internshala",
                    "type": "external",
                    "category": "career",
                    "website": "https://internshala.com/",
                    "description": "Internship and training platform for students",
                    "cost": "Free / Paid Training"
                },
                {
                    "resource_id": "er4",
                    "name": "National Scholarship Portal",
                    "type": "external",
                    "category": "financial",
                    "website": "https://scholarships.gov.in/",
                    "description": "Single portal for all government scholarships",
                    "cost": "Free"
                },
                {
                    "resource_id": "er5",
                    "name": "YourDost",
                    "type": "external",
                    "category": "wellness",
                    "website": "https://yourdost.com/",
                    "description": "Online counseling and emotional support",
                    "cost": "Free / Paid"
                }
            ]
        
        if category:
            return [r for r in external_resources if r.get("category") == category]
        
        return external_resources
    
    def add_resource(self, resource_data: Dict[str, Any]) -> bool:
        """Add a new resource"""
        # Generate a unique ID if not provided
        if "resource_id" not in resource_data:
            resource_data["resource_id"] = str(uuid.uuid4())
        
        # Add creation timestamp
        if "created_at" not in resource_data:
            resource_data["created_at"] = datetime.now().isoformat()
        
        # Add the resource
        self.resources.append(resource_data)
        
        # Save the updated resources list
        success = self.data_manager.save_data(
            self.student_id, "resources", "directory", self.resources
        )
        
        return success
    
    def bookmark_resource(self, resource_id: str, notes: Optional[str] = None) -> bool:
        """Bookmark a resource for future reference"""
        # Check if already bookmarked
        existing = [b for b in self.bookmarks if b.get("resource_id") == resource_id]
        
        if existing:
            # Update existing bookmark
            for bookmark in self.bookmarks:
                if bookmark.get("resource_id") == resource_id:
                    bookmark["notes"] = notes
                    bookmark["updated_at"] = datetime.now().isoformat()
        else:
            # Create new bookmark
            bookmark = {
                "bookmark_id": str(uuid.uuid4()),
                "resource_id": resource_id,
                "notes": notes,
                "created_at": datetime.now().isoformat()
            }
            self.bookmarks.append(bookmark)
        
        # Save the updated bookmarks list
        success = self.data_manager.save_data(
            self.student_id, "resources", "bookmarks", self.bookmarks
        )
        
        return success
    
    def remove_bookmark(self, resource_id: str) -> bool:
        """Remove a resource bookmark"""
        original_len = len(self.bookmarks)
        self.bookmarks = [b for b in self.bookmarks if b.get("resource_id") != resource_id]
        
        if len(self.bookmarks) < original_len:
            # Save the updated bookmarks list
            return self.data_manager.save_data(
                self.student_id, "resources", "bookmarks", self.bookmarks
            )
        
        return False  # Bookmark not found
    
    def get_bookmarks(self) -> List[Dict[str, Any]]:
        """Get the student's bookmarked resources"""
        result = []
        
        for bookmark in self.bookmarks:
            resource_id = bookmark.get("resource_id")
            
            # Find the resource details
            resource = None
            for r in self.resources:
                if r.get("resource_id") == resource_id:
                    resource = r
                    break
            
            # If not found in user's resources, check defaults
            if not resource:
                campus_resources = self.get_campus_resources()
                external_resources = self.get_external_resources()
                
                for r in campus_resources + external_resources:
                    if r.get("resource_id") == resource_id:
                        resource = r
                        break
            
            if resource:
                # Combine resource and bookmark info
                combined = {**resource, **bookmark}
                result.append(combined)
        
        return result
    
    def log_resource_usage(self, resource_id: str, usage_type: str = "viewed") -> bool:
        """Log the usage of a resource"""
        usage_log = {
            "log_id": str(uuid.uuid4()),
            "resource_id": resource_id,
            "usage_type": usage_type,
            "timestamp": datetime.now().isoformat()
        }
        
        self.usage_history.append(usage_log)
        
        # Save the updated usage history
        success = self.data_manager.save_data(
            self.student_id, "resources", "usage_history", self.usage_history
        )
        
        return success
    
    def get_scholarships(self) -> List[Dict[str, Any]]:
        """Get scholarship resources for Indian students"""
        scholarships = [
            {
                "name": "Central Sector Scheme of Scholarships",
                "provider": "Ministry of Education",
                "eligibility": "Top 20 percentile in Class 12 board exams",
                "amount": "₹10,000 per annum",
                "deadline": "October 31, 2025",
                "website": "https://scholarships.gov.in/"
            },
            {
                "name": "Post-Matric Scholarship for SC Students",
                "provider": "Ministry of Social Justice and Empowerment",
                "eligibility": "SC students with family income below ₹2.5 lakhs per annum",
                "amount": "Course fees and maintenance allowance",
                "deadline": "Varies by state",
                "website": "https://scholarships.gov.in/"
            },
            {
                "name": "Prime Minister's Scholarship Scheme",
                "provider": "Ministry of Defence",
                "eligibility": "Dependent wards of ex/serving Armed Forces personnel",
                "amount": "₹2,500 per month for boys, ₹3,000 per month for girls",
                "deadline": "September 30, 2025",
                "website": "https://ksb.gov.in/pm-scholarship.htm"
            },
            {
                "name": "INSPIRE Scholarship",
                "provider": "Department of Science & Technology",
                "eligibility": "Top 1% in Class 12 pursuing science degrees",
                "amount": "₹80,000 per annum",
                "deadline": "December 31, 2025",
                "website": "https://online-inspire.gov.in/"
            },
            {
                "name": "AICTE Pragati Scholarship for Girls",
                "provider": "AICTE",
                "eligibility": "Girl students in AICTE approved technical institutions",
                "amount": "₹50,000 per annum",
                "deadline": "November 30, 2025",
                "website": "https://www.aicte-india.org/schemes/students-development-schemes"
            }
        ]
        
        return scholarships
    
    def get_educational_resources_by_subject(self, subject: str) -> List[Dict[str, Any]]:
        """Get educational resources for a specific subject"""
        # Define resources for common subjects for Indian students
        subject_resources = {
            "mathematics": [
                {
                    "name": "NPTEL Mathematics Courses",
                    "type": "Online Courses",
                    "website": "https://nptel.ac.in/",
                    "free": True
                },
                {
                    "name": "Khan Academy Mathematics",
                    "type": "Video Tutorials",
                    "website": "https://www.khanacademy.org/math",
                    "free": True
                }
            ],
            "computer science": [
                {
                    "name": "GeeksforGeeks",
                    "type": "Tutorial Website",
                    "website": "https://www.geeksforgeeks.org/",
                    "free": True
                },
                {
                    "name": "CodeWithHarry",
                    "type": "YouTube Channel",
                    "website": "https://www.youtube.com/c/CodeWithHarry",
                    "free": True
                }
            ],
            "engineering": [
                {
                    "name": "NPTEL Engineering Courses",
                    "type": "Online Courses",
                    "website": "https://nptel.ac.in/",
                    "free": True
                },
                {
                    "name": "VirtualLabs",
                    "type": "Virtual Laboratories",
                    "website": "https://www.vlab.co.in/",
                    "free": True
                }
            ],
            "business": [
                {
                    "name": "IIM MOOC Courses",
                    "type": "Online Courses",
                    "website": "https://www.iimb.ac.in/eep/product/76/MOOC",
                    "free": True
                },
                {
                    "name": "InsideIIM",
                    "type": "Business Education Portal",
                    "website": "https://insideiim.com/",
                    "free": True
                }
            ]
        }
        
        # Search for the subject
        for key, resources in subject_resources.items():
            if subject.lower() in key or key in subject.lower():
                return resources
        
        # Return general educational resources if subject not found
        return [
            {
                "name": "Swayam Portal",
                "type": "Online Courses Platform",
                "website": "https://swayam.gov.in/",
                "free": True
            },
            {
                "name": "National Digital Library",
                "type": "Digital Repository",
                "website": "https://ndl.iitkgp.ac.in/",
                "free": True
            }
        ]
