from fastapi import APIRouter, Depends

from app.api.deps.auth import get_current_user
from app.main import app
from app.models.user import User

# Temporary test route
router = APIRouter()


@router.get("/test-auth")
async def check_auth(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email}


app.include_router(router)


def test_authenticated_route(authenticated_client, mock_user):
    response = authenticated_client.get("/test-auth")
    assert response.status_code == 200
    assert response.json() == {"email": mock_user.email}


def test_unauthenticated_route(client):
    response = client.get("/test-auth")
    assert response.status_code == 401
