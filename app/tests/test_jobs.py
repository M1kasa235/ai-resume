import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token


class TestJobs:
    """岗位相关测试"""
    
    def test_get_jobs_list(self, client: TestClient):
        """测试获取岗位列表"""
        response = client.get("/api/v1/jobs/list")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["items"], list)
    
    def test_get_jobs_with_filters(self, client: TestClient):
        """测试带筛选条件的岗位列表"""
        params = {
            "keyword": "Python",
            "city": "北京",
            "page": 1,
            "page_size": 10
        }
        response = client.get("/api/v1/jobs/list", params=params)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
    
    def test_get_hot_jobs(self, client: TestClient):
        """测试获取热门岗位"""
        response = client.get("/api/v1/jobs/hot")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_latest_jobs(self, client: TestClient):
        """测试获取最新岗位"""
        response = client.get("/api/v1/jobs/latest")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_job_statistics(self, client: TestClient):
        """测试获取岗位统计"""
        response = client.get("/api/v1/jobs/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "today_new" in data
        assert "top_cities" in data
    
    def test_get_job_detail_unauthorized(self, client: TestClient):
        """测试未授权获取岗位详情"""
        response = client.get("/api/v1/jobs/1")
        assert response.status_code == 401
    
    def test_get_job_detail_authorized(self, client: TestClient):
        """测试授权获取岗位详情"""
        # 先注册用户
        user_data = {
            "username": "jobuser",
            "email": "job@example.com",
            "password": "jobpass123"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # 登录获取token
        login_data = {
            "username": "jobuser",
            "password": "jobpass123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        access_token = login_response.json()["access_token"]
        
        # 尝试获取岗位详情（可能不存在，但应该返回404而不是401）
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/v1/jobs/999", headers=headers)
        # 可能返回404或200（如果岗位存在）
        assert response.status_code in [200, 404]
    
    def test_get_category_tree(self, client: TestClient):
        """测试获取岗位分类树"""
        response = client.get("/api/v1/jobs/categories/tree")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_category_list(self, client: TestClient):
        """测试获取岗位分类列表"""
        response = client.get("/api/v1/jobs/categories/list")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_add_favorite_unauthorized(self, client: TestClient):
        """测试未授权收藏岗位"""
        response = client.post("/api/v1/jobs/1/favorite")
        assert response.status_code == 401
    
    def test_get_favorites_unauthorized(self, client: TestClient):
        """测试未授权获取收藏列表"""
        response = client.get("/api/v1/jobs/user/favorites")
        assert response.status_code == 401