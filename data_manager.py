import os
import json
import pandas as pd
from datetime import datetime
import shutil

class DataManager:
    """
    Handles all data storage and retrieval operations for HARMONY-India
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the data manager with the data directory"""
        self.data_dir = data_dir
        
        # Create data directories if they don't exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "profiles"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "academic"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "financial"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "wellness"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "career"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "resources"), exist_ok=True)
    
    def _ensure_student_dirs(self, student_id: str) -> None:
        """Ensure that all necessary directories for a student exist"""
        dirs = [
            os.path.join(self.data_dir, "academic", student_id),
            os.path.join(self.data_dir, "financial", student_id),
            os.path.join(self.data_dir, "wellness", student_id),
            os.path.join(self.data_dir, "career", student_id),
            os.path.join(self.data_dir, "resources", student_id)
        ]
        
        for directory in dirs:
            os.makedirs(directory, exist_ok=True)
    
    def get_existing_profiles(self) -> list:
        """Get a list of existing student profiles"""
        profiles_dir = os.path.join(self.data_dir, "profiles")
        
        if not os.path.exists(profiles_dir):
            return []
        
        # List all JSON files in profiles directory
        return [f.split('.')[0] for f in os.listdir(profiles_dir) 
               if f.endswith('.json')]
    
    def get_profile_name(self, student_id: str) -> str:
        """Get the full name from a student profile"""
        profile = self.load_student_profile(student_id)
        
        if profile and 'full_name' in profile:
            return profile['full_name']
        
        return student_id
    
    def save_student_profile(self, student_id: str, profile_data: dict) -> bool:
        """Save a student profile"""
        try:
            profiles_dir = os.path.join(self.data_dir, "profiles")
            os.makedirs(profiles_dir, exist_ok=True)
            
            # Create the profile file
            profile_file = os.path.join(profiles_dir, f"{student_id}.json")
            
            with open(profile_file, 'w') as f:
                json.dump(profile_data, f, indent=2)
            
            # Create directories for this student
            self._ensure_student_dirs(student_id)
            
            return True
        except Exception as e:
            print(f"Error saving student profile: {e}")
            return False
    
    def load_student_profile(self, student_id: str) -> dict:
        """Load a student profile"""
        try:
            profile_file = os.path.join(self.data_dir, "profiles", f"{student_id}.json")
            
            if not os.path.exists(profile_file):
                return None
            
            with open(profile_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading student profile: {e}")
            return None
    
    def delete_student_profile(self, student_id: str) -> bool:
        """Delete a student profile and all associated data"""
        try:
            # Delete profile file
            profile_file = os.path.join(self.data_dir, "profiles", f"{student_id}.json")
            if os.path.exists(profile_file):
                os.remove(profile_file)
            
            # Delete student directories and all contents
            dirs = [
                os.path.join(self.data_dir, "academic", student_id),
                os.path.join(self.data_dir, "financial", student_id),
                os.path.join(self.data_dir, "wellness", student_id),
                os.path.join(self.data_dir, "career", student_id),
                os.path.join(self.data_dir, "resources", student_id)
            ]
            
            for directory in dirs:
                if os.path.exists(directory):
                    shutil.rmtree(directory)
            
            return True
        except Exception as e:
            print(f"Error deleting student profile: {e}")
            return False
    
    # Generic data operations
    def save_data(self, student_id: str, module: str, file_name: str, data: dict) -> bool:
        """Save data to a specific module directory"""
        try:
            # Ensure directory exists
            module_dir = os.path.join(self.data_dir, module, student_id)
            os.makedirs(module_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(module_dir, f"{file_name}.json")
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving data for {module}/{file_name}: {e}")
            return False
    
    def load_data(self, student_id: str, module: str, file_name: str) -> dict:
        """Load data from a specific module directory"""
        try:
            file_path = os.path.join(self.data_dir, module, student_id, f"{file_name}.json")
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading data for {module}/{file_name}: {e}")
            return None
    
    def get_data(self, student_id, data_type, default=None):
        """Get data from the data manager for a student."""
        try:
            # Check if student exists in data
            if student_id not in self.data:
                return default
                
            # Check if data_type exists for student
            if data_type not in self.data[student_id]:
                return default
                
            return self.data[student_id][data_type]
        except Exception as e:
            print(f"Error getting data: {e}")
            return default


    def save_dataframe(self, student_id: str, module: str, file_name: str, df: pd.DataFrame) -> bool:
        """Save a pandas DataFrame to CSV"""
        try:
            # Ensure directory exists
            module_dir = os.path.join(self.data_dir, module, student_id)
            os.makedirs(module_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(module_dir, f"{file_name}.csv")
            df.to_csv(file_path, index=False)
            
            return True
        except Exception as e:
            print(f"Error saving DataFrame for {module}/{file_name}: {e}")
            return False
    
    def load_dataframe(self, student_id: str, module: str, file_name: str) -> pd.DataFrame:
        """Load a pandas DataFrame from CSV"""
        try:
            file_path = os.path.join(self.data_dir, module, student_id, f"{file_name}.csv")
            
            if not os.path.exists(file_path):
                return pd.DataFrame()
            
            return pd.read_csv(file_path)
        except Exception as e:
            print(f"Error loading DataFrame for {module}/{file_name}: {e}")
            return pd.DataFrame()
    
    def append_to_list(self, student_id: str, module: str, file_name: str, new_item: dict) -> bool:
        """Append an item to a list stored in a JSON file"""
        try:
            existing_data = self.load_data(student_id, module, file_name) or []
            
            # Add a unique ID if not present
            if 'id' not in new_item and not any(key.endswith('_id') for key in new_item.keys()):
                # Find the appropriate ID field name
                id_field = f"{file_name[:-1]}_id" if file_name.endswith('s') else f"{file_name}_id"
                
                # Generate a new ID (just increment the highest existing ID)
                highest_id = 0
                for item in existing_data:
                    if id_field in item and item[id_field] > highest_id:
                        highest_id = item[id_field]
                
                new_item[id_field] = highest_id + 1
            
            # Add timestamp if not present
            if 'created_at' not in new_item:
                new_item['created_at'] = datetime.now().isoformat()
            
            # Append item
            existing_data.append(new_item)
            
            # Save updated list
            return self.save_data(student_id, module, file_name, existing_data)
        except Exception as e:
            print(f"Error appending to list {module}/{file_name}: {e}")
            return False
    
    def update_list_item(self, student_id: str, module: str, file_name: str, 
                        item_id: int, id_field: str, updated_data: dict) -> bool:
        """Update an item in a list stored in a JSON file"""
        try:
            existing_data = self.load_data(student_id, module, file_name) or []
            
            # Find the item with the given ID
            for i, item in enumerate(existing_data):
                if id_field in item and item[id_field] == item_id:
                    # Update the item
                    existing_data[i].update(updated_data)
                    
                    # Save updated list
                    return self.save_data(student_id, module, file_name, existing_data)
            
            return False  # Item not found
        except Exception as e:
            print(f"Error updating list item {module}/{file_name}: {e}")
            return False
    
    def delete_list_item(self, student_id: str, module: str, file_name: str, 
                        item_id: int, id_field: str) -> bool:
        """Delete an item from a list stored in a JSON file"""
        try:
            existing_data = self.load_data(student_id, module, file_name) or []
            
            # Filter out the item with the given ID
            new_data = [item for item in existing_data if id_field not in item or item[id_field] != item_id]
            
            # If no items were removed, return False
            if len(new_data) == len(existing_data):
                return False
            
            # Save updated list
            return self.save_data(student_id, module, file_name, new_data)
        except Exception as e:
            print(f"Error deleting list item {module}/{file_name}: {e}")
            return False
