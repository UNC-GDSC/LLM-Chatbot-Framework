"""Admin dashboard API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.admin_service import AdminService
from app.services.user_service import UserService

router = APIRouter()


# Dependency to check admin status
async def require_admin(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> str:
    """Check if user is admin."""
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)

    if not user or not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return user_id


class SystemStatsResponse(BaseModel):
    """Response schema for system statistics."""

    users: dict
    content: dict
    usage_last_30_days: dict
    feedback: dict


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SystemStatsResponse:
    """Get overall system statistics (admin only)."""
    admin_service = AdminService(db)

    stats = await admin_service.get_system_stats()

    return SystemStatsResponse(**stats)


@router.get("/users")
async def list_users(
    limit: int = 50,
    offset: int = 0,
    active_only: bool = False,
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)."""
    admin_service = AdminService(db)

    users = await admin_service.list_users(limit, offset, active_only)

    return [
        {
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "is_active": u.is_active,
            "is_superuser": u.is_superuser,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed user information (admin only)."""
    admin_service = AdminService(db)

    details = await admin_service.get_user_details(user_id)

    if not details:
        raise HTTPException(status_code=404, detail="User not found")

    return details


@router.post("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: str,
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Activate/deactivate a user (admin only)."""
    admin_service = AdminService(db)

    user = await admin_service.toggle_user_status(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "username": user.username,
        "is_active": user.is_active,
    }


@router.delete("/users/{user_id}/data", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_data(
    user_id: str,
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete all user data (admin only)."""
    admin_service = AdminService(db)

    success = await admin_service.delete_user_data(user_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user data")


@router.get("/activity/recent")
async def get_recent_activity(
    hours: int = 24,
    limit: int = 100,
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get recent system activity (admin only)."""
    admin_service = AdminService(db)

    activity = await admin_service.get_recent_activity(hours, limit)

    return activity


@router.post("/cleanup")
async def cleanup_old_data(
    days: int = 90,
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Clean up old data (admin only)."""
    admin_service = AdminService(db)

    result = await admin_service.cleanup_old_data(days)

    return {
        "message": "Cleanup completed",
        "deleted": result,
    }
