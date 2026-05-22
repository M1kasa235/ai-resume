import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, get_password_hash


class TestAuth:
    """认证相关测试"""
    
    def test_register_user(self, client: TestClient):
        """测试用户注册"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data
    
    def test_login_user(self, client: TestClient):
        """测试用户登录"""
        # 先注册用户
        user_data = {
            "username": "loginuser",
            "email": "login@example.com",
            "password": "loginpass123"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # 登录
        login_data = {
            "username": "loginuser",
            "password": "loginpass123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_get_current_user(self, client: TestClient):
        """测试获取当前用户信息"""
        # 注册并登录
        user_data = {
            "username": "currentuser",
            "email": "current@example.com",
            "password": "currentpass123"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        user_id = register_response.json()["id"]
        
        # 获取token
        login_data = {
            "username": "currentuser",
            "password": "currentpass123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        access_token = login_response.json()["access_token"]
        
        # 获取当前用户信息
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "currentuser"
        assert data["email"] == "current@example.com"
        assert data["is_admin"] is False  # 默认不是管理员
    
    def test_login_invalid_credentials(self, client: TestClient):
        """测试无效凭据登录"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpass"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
    
    def test_register_duplicate_username(self, client: TestClient):
        """测试重复用户名注册"""
        user_data = {
            "username": "duplicate",
            "email": "duplicate1@example.com",
            "password": "pass123"
        }
        # 第一次注册
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # 第二次注册相同用户名
        user_data["email"] = "duplicate2@example.com"
        response2 = client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "用户名已存在" in response2.json()["detail"]