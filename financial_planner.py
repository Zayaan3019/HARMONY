from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import random

class FinancialPlanner:
    """
    Manages student financial information, budgeting, and financial aid
    """
    
    def __init__(self, student_id: str, data_manager):
        """Initialize the financial planner for a student"""
        self.student_id = student_id
        self.data_manager = data_manager
        
        # Load saved financial data
        self.transactions = data_manager.load_data(student_id, "financial", "transactions") or []
        self.budget = data_manager.load_data(student_id, "financial", "budget") or {}
        self.financial_aid = data_manager.load_data(student_id, "financial", "financial_aid") or []
        self.fee_payments = data_manager.load_data(student_id, "financial", "fee_payments") or []
        self.goals = data_manager.load_data(student_id, "financial", "goals") or []
    
    def add_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        """Add a new financial transaction"""
        # Generate a unique ID if not provided
        if "transaction_id" not in transaction_data:
            transaction_data["transaction_id"] = str(uuid.uuid4())
        
        # Add timestamp if not provided
        if "created_at" not in transaction_data:
            transaction_data["created_at"] = datetime.now().isoformat()
        
        # Add the transaction
        self.transactions.append(transaction_data)
        
        # Save the updated transactions list
        success = self.data_manager.save_data(
            self.student_id, "financial", "transactions", self.transactions
        )
        
        return success
    
    def get_transactions(self, start_date: Optional[str] = None, 
                       end_date: Optional[str] = None, 
                       category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get transactions, optionally filtered by date range and category"""
        filtered = self.transactions
        
        if start_date:
            filtered = [t for t in filtered if t.get("date", "") >= start_date]
        
        if end_date:
            filtered = [t for t in filtered if t.get("date", "") <= end_date]
        
        if category:
            filtered = [t for t in filtered if t.get("category") == category]
        
        return filtered
    
    def get_recent_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent transactions, limited to a specific count"""
        if not self.transactions:
            # Return sample data for new students
            sample_dates = [
                (datetime.now() - timedelta(days=i)).isoformat()
                for i in range(10, 0, -1)
            ]
            categories = ["Food", "Transportation", "Books & Supplies", "Entertainment"]
            
            return [
                {
                    "date": date,
                    "amount": -random.randint(50, 500) if i % 3 != 0 else random.randint(500, 2000),
                    "description": f"Sample {'expense' if i % 3 != 0 else 'income'} {i}",
                    "category": random.choice(categories) if i % 3 != 0 else "Pocket Money"
                }
                for i, date in enumerate(sample_dates)
            ]
        
        # Sort transactions by date (newest first)
        sorted_transactions = sorted(
            self.transactions,
            key=lambda x: x.get("date", ""),
            reverse=True
        )
        
        if limit:
            return sorted_transactions[:limit]
        return sorted_transactions
    
    def get_all_transactions(self):
        """Get all financial transactions for the student."""
        try:
            transactions = self.data_manager.get_data(
                self.student_id, "financial_transactions", default=[]
            )
            return transactions
        except Exception as e:
            print(f"Error getting transactions: {e}")
            return []

    
    def set_budget(self, budget_data: Dict[str, float]) -> bool:
        """Set or update the student's budget"""
        # Update the budget
        self.budget = budget_data
        
        # Save the updated budget
        success = self.data_manager.save_data(
            self.student_id, "financial", "budget", self.budget
        )
        
        return success
    
    def get_budget(self) -> Dict[str, float]:
        """Get the student's budget"""
        if not self.budget:
            # Return default budget for new students
            return {
                "Food & Dining": 3000,
                "Transportation": 1000,
                "Books & Supplies": 2000,
                "Rent & Utilities": 5000,
                "Entertainment": 1000,
                "Personal Care": 500,
                "Mobile & Internet": 500,
                "Clothing": 1000,
                "Miscellaneous": 1000
            }
        
        return self.budget
    
    def get_actual_spending(self) -> Dict[str, float]:
        """Get actual spending by category for the current month"""
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1).isoformat()
        
        # Filter transactions for current month
        month_transactions = [
            t for t in self.transactions 
            if t.get("date", "") >= month_start and t.get("amount", 0) < 0
        ]
        
        # Group by category
        spending = {}
        for transaction in month_transactions:
            category = transaction.get("category", "Other")
            amount = abs(transaction.get("amount", 0))
            
            if category in spending:
                spending[category] += amount
            else:
                spending[category] = amount
        
        return spending
    
    def get_budget_adherence(self) -> float:
        """Get overall budget adherence as a percentage"""
        if not self.budget:
            return 0.0
        
        actual_spending = self.get_actual_spending()
        
        total_budget = sum(self.budget.values())
        total_spending = sum(actual_spending.values())
        
        if total_budget == 0:
            return 0.0
        
        adherence = (1 - (total_spending / total_budget)) * 100
        return max(0, min(100, adherence))  # Clamp to 0-100 range
    
    def add_financial_aid(self, aid_data: Dict[str, Any]) -> bool:
        """Add a new financial aid entry"""
        # Generate a unique ID if not provided
        if "aid_id" not in aid_data:
            aid_data["aid_id"] = str(uuid.uuid4())
        
        # Add timestamp if not provided
        if "created_at" not in aid_data:
            aid_data["created_at"] = datetime.now().isoformat()
        
        # Add the financial aid entry
        self.financial_aid.append(aid_data)
        
        # Save the updated financial aid list
        success = self.data_manager.save_data(
            self.student_id, "financial", "financial_aid", self.financial_aid
        )
        
        return success
    
    def get_financial_aid(self) -> List[Dict[str, Any]]:
        """Get the student's financial aid information"""
        if not self.financial_aid:
            # Return sample data for new students
            return [
                {
                    "type": "scholarship",
                    "name": "Merit Scholarship",
                    "amount": 50000,
                    "provider": "University Grants Commission",
                    "status": "received",
                    "duration": "1 year"
                },
                {
                    "type": "loan",
                    "name": "Education Loan",
                    "amount": 200000,
                    "provider": "State Bank of India",
                    "status": "approved",
                    "duration": "Full course",
                    "interest_rate": 8.5,
                    "repayment_start": "After graduation"
                }
            ]
        
        return self.financial_aid
    
    def get_fee_payments(self) -> List[Dict[str, Any]]:
        """Get the student's fee payment information"""
        if not self.fee_payments:
            # Return sample data for new students
            return [
                {
                    "term": "Monsoon 2024",
                    "amount": 45000,
                    "due_date": (datetime.now() - timedelta(days=60)).isoformat(),
                    "status": "Paid",
                    "payment_date": (datetime.now() - timedelta(days=70)).isoformat()
                },
                {
                    "term": "Winter 2025",
                    "amount": 45000,
                    "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
                    "status": "Pending"
                }
            ]
        
        return self.fee_payments
    
    def get_fee_structure(self) -> Dict[str, float]:
        """Get the fee structure for the student's program"""
        # This would typically come from the university's fee structure
        # For this example, we'll return a sample fee structure
        return {
            "Tuition Fee": 80000,
            "Development Fee": 10000,
            "Library Fee": 5000,
            "Laboratory Fee": 8000,
            "Student Activities": 3000,
            "Technology Fee": 4000
        }
    
    def add_financial_goal(self, goal_data: Dict[str, Any]) -> bool:
        """Add a new financial goal"""
        # Generate a unique ID if not provided
        if "goal_id" not in goal_data:
            goal_data["goal_id"] = str(uuid.uuid4())
        
        # Add timestamp if not provided
        if "created_at" not in goal_data:
            goal_data["created_at"] = datetime.now().isoformat()
        
        # Add the goal
        self.goals.append(goal_data)
        
        # Save the updated goals list
        success = self.data_manager.save_data(
            self.student_id, "financial", "goals", self.goals
        )
        
        return success
    
    def update_financial_goal(self, goal_id: str, current_amount: float) -> bool:
        """Update the current amount of a financial goal"""
        for i, goal in enumerate(self.goals):
            if goal.get("goal_id") == goal_id:
                self.goals[i]["current_amount"] = current_amount
                
                # Check if goal is completed
                if current_amount >= self.goals[i].get("target_amount", 0):
                    self.goals[i]["status"] = "completed"
                    self.goals[i]["completion_date"] = datetime.now().isoformat()
                
                # Save the updated goals list
                return self.data_manager.save_data(
                    self.student_id, "financial", "goals", self.goals
                )
        
        return False  # Goal not found
    
    def delete_financial_goal(self, goal_id: str) -> bool:
        """Delete a financial goal"""
        original_len = len(self.goals)
        self.goals = [goal for goal in self.goals if goal.get("goal_id") != goal_id]
        
        if len(self.goals) < original_len:
            # Save the updated goals list
            return self.data_manager.save_data(
                self.student_id, "financial", "goals", self.goals
            )
        
        return False  # Goal not found
    
    def get_financial_goals(self) -> List[Dict[str, Any]]:
        """Get the student's financial goals"""
        return self.goals
    
    def get_financial_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of the student's financial situation"""
        # Calculate current balance
        current_balance = sum(t.get("amount", 0) for t in self.transactions)
        
        # Calculate income and expenses for current month
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1).isoformat()
        
        month_transactions = [t for t in self.transactions if t.get("date", "") >= month_start]
        income_this_month = sum(t.get("amount", 0) for t in month_transactions if t.get("amount", 0) > 0)
        expenses_this_month = sum(abs(t.get("amount", 0)) for t in month_transactions if t.get("amount", 0) < 0)
        
        # Calculate expenses by category
        expenses_by_category = {}
        for t in month_transactions:
            if t.get("amount", 0) < 0:
                category = t.get("category", "Other")
                amount = abs(t.get("amount", 0))
                
                if category in expenses_by_category:
                    expenses_by_category[category] += amount
                else:
                    expenses_by_category[category] = amount
        
        # Calculate expense trend (compare to previous month)
        prev_month_start = (datetime(now.year, now.month, 1) - timedelta(days=1)).replace(day=1).isoformat()
        prev_month_end = (datetime(now.year, now.month, 1) - timedelta(days=1)).isoformat()
        
        prev_month_transactions = [
            t for t in self.transactions 
            if t.get("date", "") >= prev_month_start and t.get("date", "") <= prev_month_end
        ]
        
        prev_month_expenses = sum(abs(t.get("amount", 0)) for t in prev_month_transactions if t.get("amount", 0) < 0)
        
        if prev_month_expenses > 0:
            expense_trend = ((expenses_this_month - prev_month_expenses) / prev_month_expenses) * 100
        else:
            expense_trend = 0
        
        # Calculate budget adherence
        budget_adherence = self.get_budget_adherence()
        
        return {
            "current_balance": current_balance,
            "income_this_month": income_this_month,
            "expenses_this_month": expenses_this_month,
            "expenses_by_category": expenses_by_category,
            "expense_trend": expense_trend,
            "budget_adherence": budget_adherence
        }
    
    def get_monthly_expenses(self) -> List[Dict[str, Any]]:
        """Get monthly expenses for visualization"""
        expenses = self.get_actual_spending()
        
        return [{"category": cat, "amount": amt} for cat, amt in expenses.items()]
    
    def get_expenses_by_category(self):
        """
        Get expenses categorized by category
        Returns a list of dicts with category and total amount
        """
        try:
            # Get all transactions
            transactions = self.get_all_transactions()
            
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
            
            # Sort by amount (largest first)
            result.sort(key=lambda x: x["amount"], reverse=True)
            
            return result
        except Exception as e:
            print(f"Error getting expenses by category: {e}")
            return []
