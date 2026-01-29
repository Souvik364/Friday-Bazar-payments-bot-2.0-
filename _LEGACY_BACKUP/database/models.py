"""
Database Models
===============
Pydantic models for type safety and validation
"""

from datetime import datetime
from typing import Optional, Literal, List
from pydantic import BaseModel, Field
from enum import Enum


class MenuContentType(str, Enum):
    """Menu content types"""
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"


class ButtonType(str, Enum):
    """Button action types"""
    SUBMENU = "submenu"
    MESSAGE = "message"
    PAYMENT = "payment"
    URL = "url"
    ACTION = "action"


class PaymentStatus(str, Enum):
    """Payment status types"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AdminRole(str, Enum):
    """Admin permission roles"""
    SUPER_ADMIN = "super_admin"
    CONTENT_MANAGER = "content_manager"
    PAYMENT_APPROVER = "payment_approver"


# Menu Model
class Menu(BaseModel):
    """Menu definition model"""
    menu_id: str = Field(..., description="Unique menu identifier")
    name: str = Field(..., description="Menu display name")
    description: Optional[str] = Field(None, description="Menu description/welcome text")
    content_type: MenuContentType = Field(MenuContentType.TEXT, description="Type of content")
    content_data: str = Field(..., description="Text content or file_id")
    parent_menu_id: Optional[str] = Field(None, description="Parent menu if submenu")
    is_active: bool = Field(True, description="Whether menu is active")
    position: int = Field(0, description="Display order")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")

    class Config:
        from_attributes = True


# Button Model
class Button(BaseModel):
    """Button definition model"""
    button_id: str = Field(..., description="Unique button identifier")
    menu_id: str = Field(..., description="Parent menu ID")
    text: str = Field(..., description="Button display text")
    type: ButtonType = Field(..., description="Button action type")
    action_data: str = Field(..., description="Action target (menu_id, URL, plan_id, etc.)")
    row: int = Field(0, description="Row position (0-based)")
    column: int = Field(0, description="Column position (0-based)")
    is_active: bool = Field(True, description="Whether button is active")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

    class Config:
        from_attributes = True


# Payment Plan Model
class PaymentPlan(BaseModel):
    """Payment plan model"""
    plan_id: str = Field(..., description="Unique plan identifier")
    name: str = Field(..., description="Plan name")
    duration_days: int = Field(..., description="Plan duration in days")
    price: float = Field(..., description="Plan price")
    original_price: Optional[float] = Field(None, description="Original price for discount display")
    features: List[str] = Field(default_factory=list, description="List of features")
    qr_code_file_id: Optional[str] = Field(None, description="Telegram QR code file ID")
    button_text: str = Field(..., description="Button text for plan")
    is_active: bool = Field(True, description="Whether plan is active")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")

    class Config:
        from_attributes = True


# User Session Model
class UserSession(BaseModel):
    """User session tracking"""
    user_id: int = Field(..., description="Telegram user ID")
    current_menu_id: Optional[str] = Field(None, description="Current menu being viewed")
    session_data: dict = Field(default_factory=dict, description="Additional session context")
    state: str = Field("browsing", description="Current state (browsing, payment, etc.)")
    last_activity: datetime = Field(default_factory=datetime.now, description="Last activity timestamp")

    class Config:
        from_attributes = True


# Payment Record Model
class Payment(BaseModel):
    """Payment record"""
    payment_id: str = Field(..., description="Unique payment identifier")
    user_id: int = Field(..., description="Telegram user ID")
    plan_id: str = Field(..., description="Payment plan ID")
    amount: float = Field(..., description="Payment amount")
    screenshot_file_id: Optional[str] = Field(None, description="Payment screenshot file ID")
    status: PaymentStatus = Field(PaymentStatus.PENDING, description="Payment status")
    admin_id: Optional[int] = Field(None, description="Admin who processed payment")
    user_details: Optional[str] = Field(None, description="User provided details (email, etc.)")
    created_at: datetime = Field(default_factory=datetime.now, description="Payment creation timestamp")
    processed_at: Optional[datetime] = Field(None, description="Payment processing timestamp")

    class Config:
        from_attributes = True


# User Model (migrated from users.json)
class User(BaseModel):
    """User data model"""
    user_id: int = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(None, description="Telegram username")
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")
    coins: float = Field(0.0, description="User coin balance")
    referrer_id: Optional[int] = Field(None, description="Referrer user ID")
    total_referrals: int = Field(0, description="Total referrals count")
    total_earnings: float = Field(0.0, description="Total earnings from referrals")
    is_banned: bool = Field(False, description="Whether user is banned")
    has_premium: bool = Field(False, description="Whether user has premium subscription")
    premium_expires_at: Optional[datetime] = Field(None, description="Premium expiry timestamp")
    created_at: datetime = Field(default_factory=datetime.now, description="User registration timestamp")
    last_seen: datetime = Field(default_factory=datetime.now, description="Last activity timestamp")

    class Config:
        from_attributes = True


# Admin User Model
class AdminUser(BaseModel):
    """Admin user with role"""
    admin_id: int = Field(..., description="Admin Telegram user ID")
    role: AdminRole = Field(AdminRole.SUPER_ADMIN, description="Admin role")
    permissions: dict = Field(default_factory=dict, description="Custom permissions override")
    is_active: bool = Field(True, description="Whether admin is active")
    created_at: datetime = Field(default_factory=datetime.now, description="Admin creation timestamp")

    class Config:
        from_attributes = True
