"""
Friday Bazar Payments - Subscription Service
=============================================
Manages subscription lifecycle, expiry tracking, and activation
"""

from datetime import datetime, timedelta
from typing import Optional
from src.services.db import db


class SubscriptionService:
    """Handles all subscription-related operations"""
    
    def calculate_expiry_date(self, plan_duration: str) -> datetime:
        """
        Calculate expiry date based on plan duration
        
        Args:
            plan_duration: Plan duration string (e.g., "1 Month", "1 Year")
        
        Returns:
            Expiry datetime
        """
        now = datetime.now()
        
        # Parse duration
        duration_lower = plan_duration.lower()
        
        if "month" in duration_lower:
            months = int(duration_lower.split()[0])
            # Approximate: 30 days per month
            return now + timedelta(days=months * 30)
        
        elif "year" in duration_lower:
            years = int(duration_lower.split()[0])
            return now + timedelta(days=years * 365)
        
        elif "day" in duration_lower:
            days = int(duration_lower.split()[0])
            return now + timedelta(days=days)
        
        else:
            # Default to 30 days if unknown format
            return now + timedelta(days=30)
    
    async def activate_subscription(
        self,
        user_id: int,
        service_name: str,
        plan_duration: str
    ) -> dict:
        """
        Activate subscription for a user
        
        Args:
            user_id: User ID
            service_name: Name of the service
            plan_duration: Plan duration
        
        Returns:
            Updated user data
        """
        expiry_date = self.calculate_expiry_date(plan_duration)
        
        await db.update_user(user_id, {
            "subscription_plan": plan_duration,
            "subscription_service": service_name,
            "subscription_expiry": expiry_date.isoformat(),
            "subscription_status": "active"
        })
        
        return await db.get_user(user_id)
    
    async def is_subscription_active(self, user_id: int) -> bool:
        """
        Check if user has an active subscription
        
        Args:
            user_id: User ID
        
        Returns:
            True if subscription is active, False otherwise
        """
        user = await db.get_user(user_id)
        
        if user.get('subscription_status') != 'active':
            return False
        
        # Check expiry date
        expiry_str = user.get('subscription_expiry')
        if not expiry_str:
            return False
        
        expiry_date = datetime.fromisoformat(expiry_str)
        return datetime.now() < expiry_date
    
    async def get_subscription_info(self, user_id: int) -> dict:
        """
        Get subscription information for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with subscription details
        """
        user = await db.get_user(user_id)
        
        expiry_str = user.get('subscription_expiry')
        expiry_date = None
        days_remaining = 0
        
        if expiry_str:
            expiry_date = datetime.fromisoformat(expiry_str)
            days_remaining = max(0, (expiry_date - datetime.now()).days)
        
        is_active = await self.is_subscription_active(user_id)
        
        return {
            "is_active": is_active,
            "service": user.get('subscription_service'),
            "plan": user.get('subscription_plan'),
            "expiry_date": expiry_date,
            "days_remaining": days_remaining,
            "status": user.get('subscription_status', 'none')
        }
    
    async def extend_subscription(
        self,
        user_id: int,
        additional_duration: str
    ) -> dict:
        """
        Extend existing subscription
        
        Args:
            user_id: User ID
            additional_duration: Additional duration to add
        
        Returns:
            Updated user data
        """
        user = await db.get_user(user_id)
        current_expiry_str = user.get('subscription_expiry')
        
        if current_expiry_str:
            current_expiry = datetime.fromisoformat(current_expiry_str)
            # If already expired, start from now
            if current_expiry < datetime.now():
                new_expiry = self.calculate_expiry_date(additional_duration)
            else:
                # Add to existing expiry
                additional_days = (self.calculate_expiry_date(additional_duration) - datetime.now()).days
                new_expiry = current_expiry + timedelta(days=additional_days)
        else:
            new_expiry = self.calculate_expiry_date(additional_duration)
        
        await db.update_user(user_id, {
            "subscription_expiry": new_expiry.isoformat(),
            "subscription_status": "active"
        })
        
        return await db.get_user(user_id)
    
    async def check_and_expire_subscriptions(self):
        """
        Background task to check and expire subscriptions
        Should be called periodically (e.g., daily)
        """
        # This would need to iterate through all users
        # For JSON-based storage, this is expensive
        # In production, use a proper database with queries
        pass


# Global subscription service instance
subscription_service = SubscriptionService()
