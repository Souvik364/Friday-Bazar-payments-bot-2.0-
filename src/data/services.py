"""
Friday Bazar Payments - Services Catalog
=========================================
Definitions for all premium services and plans.
Now dynamically loaded via SettingsManager.
"""

from src.services.settings import settings_manager
from typing import Dict, Any, Optional

async def load_services():
    """Ensure services are loaded (helper)"""
    await settings_manager.initialize()

def get_service(service_id: str) -> Optional[Dict]:
    """Get service details by ID"""
    return settings_manager.get_service(service_id)

def get_all_services() -> Dict[str, Any]:
    """Get all services"""
    return settings_manager.get_all_services()

def get_service_button_text(service_id: str) -> str:
    """Get button text for service grid"""
    service = settings_manager.get_service(service_id)
    if service:
        return f"{service['emoji']} {service['name']}"
    return "Unknown Service"

def is_service_available(service_id: str) -> bool:
    """Check if service is available (not demo)"""
    service = settings_manager.get_service(service_id)
    if not service:
        return False
    return service.get("available", True)
