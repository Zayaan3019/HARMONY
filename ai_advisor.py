import os
import json
import requests
from typing import Dict, List, Any, Optional

class GroqAdvisor:
    """
    AI advisor powered by Groq API to provide personalized guidance
    on mental health, academics, career, and finances
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the AI advisor with Groq API key"""
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama3-8b-8192"  # Using Llama 3 8B model
        
        # Domain-specific system prompts
        self.domain_prompts = {
            "mental_health": """You are a supportive mental wellness advisor for Indian college students.
                Provide empathetic, practical advice for managing stress, anxiety, and maintaining 
                well-being in a high-pressure academic environment. Focus on realistic strategies considering
                the Indian context. Never provide medical diagnoses or replace professional help.
                Always encourage seeking professional support for serious concerns.""",
                
            "academic": """You are an academic success advisor for Indian college students.
                Provide practical study strategies, time management techniques, and academic resources
                relevant to the Indian education system. Consider the competitive nature of Indian academics
                and suggest balanced approaches that promote learning while managing stress.
                Tailor advice to different fields of study in the Indian context.""",
                
            "career": """You are a career development advisor for Indian college students.
                Provide guidance on career planning, skill development, and job preparation
                specifically for the Indian job market. Include advice on internships, campus placements,
                competitive exams, and industry-specific opportunities in India. Address common challenges
                faced by fresh graduates in India's job market.""",
                
            "financial": """You are a financial wellness advisor for Indian college students.
                Provide practical financial advice on managing educational expenses, scholarships,
                educational loans, and basic budgeting for students in India. Include information about
                government schemes, bank loans, and financial support systems available specifically
                for Indian students. Focus on realistic financial strategies for students."""
        }
        
    def get_advice(self, query: str, domain: str, student_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Get AI-generated advice for a specific domain
        
        Args:
            query: The student's question or concern
            domain: The advice domain (mental_health, academic, career, or financial)
            student_context: Optional context about the student for personalized advice
            
        Returns:
            AI-generated advice text
        """
        if not self.api_key:
            return "Error: Groq API key is not configured. Please set up the API key in settings."
        
        # Select the appropriate system prompt
        system_prompt = self.domain_prompts.get(domain, self.domain_prompts["academic"])
        
        # Add student context to system prompt if available
        if student_context:
            context_str = "\n\nStudent context: "
            for key, value in student_context.items():
                context_str += f"{key}: {value}. "
            system_prompt += context_str
        
        # Prepare the messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        # Prepare the API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        try:
            # Make the API call
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            # Parse the response
            result = response.json()
            advice = result["choices"][0]["message"]["content"]
            
            return advice
        
        except requests.exceptions.RequestException as e:
            return f"Error connecting to Groq AI: {str(e)}"
        except (KeyError, IndexError) as e:
            return f"Error processing AI response: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    def classify_query_domain(self, query: str) -> str:
        """
        Determine the appropriate domain for a query
        
        Args:
            query: The student's question
            
        Returns:
            Domain classification (mental_health, academic, career, or financial)
        """
        # Simple keyword-based classification
        query_lower = query.lower()
        
        mental_keywords = ["stress", "anxiety", "depression", "mental health", 
                          "feeling", "overwhelmed", "sleep", "lonely", "sad", 
                          "tired", "exhausted", "pressure", "bullying"]
        
        academic_keywords = ["study", "exam", "grade", "class", "course", 
                            "assignment", "professor", "lecture", "gpa", "cgpa", 
                            "attendance", "project", "learning", "semester"]
        
        career_keywords = ["job", "intern", "resume", "interview", "skill", 
                          "placement", "company", "industry", "salary", 
                          "profession", "career", "opportunity"]
        
        financial_keywords = ["money", "loan", "scholarship", "fee", "stipend", 
                             "budget", "expense", "cost", "payment", "financial", 
                             "fund", "saving", "bank", "rupee", "rs"]
        
        # Count keyword matches for each domain
        mental_count = sum(1 for word in mental_keywords if word in query_lower)
        academic_count = sum(1 for word in academic_keywords if word in query_lower)
        career_count = sum(1 for word in career_keywords if word in query_lower)
        financial_count = sum(1 for word in financial_keywords if word in query_lower)
        
        # Determine the domain with the most matches
        counts = {
            "mental_health": mental_count,
            "academic": academic_count,
            "career": career_count, 
            "financial": financial_count
        }
        
        # Return the domain with the highest match count
        return max(counts, key=counts.get)
