import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from datetime import datetime
from src.api.main import app
from src.schemas.models import HealthResponse

client = TestClient(app)

@patch('src.api.main.Database')
def test_health_check_healthy(mock_db):
    """Test health check endpoint when DB is healthy"""
    mock_db.check_connection.return_value = True
    mock_db.execute_query.return_value = [
        {'status': 'success', 'ended_at': datetime.now()}
    ]
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data['db_connected'] is True
    assert data['status'] == 'healthy'

@patch('src.api.main.Database')
def test_health_check_unhealthy(mock_db):
    """Test health check endpoint when DB is unhealthy"""
    mock_db.check_connection.return_value = False
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data['db_connected'] is False
    assert data['status'] == 'unhealthy'

@patch('src.api.main.Database')
def test_get_data_no_filters(mock_db):
    """Test /data endpoint without filters"""
    mock_db.execute_query.side_effect = [
        [{'total': 2}],  # count query
        [  # data query
            {
                'id': 1,
                'source': 'api',
                'source_id': '1',
                'name': 'Test 1',
                'value': 100.0,
                'description': 'Test',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            },
            {
                'id': 2,
                'source': 'api',
                'source_id': '2',
                'name': 'Test 2',
                'value': 200.0,
                'description': 'Test',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        ]
    ]
    
    response = client.get("/data?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 2
    assert len(data['data']) == 2
    assert data['page'] == 1
    assert data['has_more'] is False

@patch('src.api.main.Database')
def test_get_data_with_source_filter(mock_db):
    """Test /data endpoint with source filter"""
    mock_db.execute_query.side_effect = [
        [{'total': 1}],  # count query
        [  # data query
            {
                'id': 1,
                'source': 'csv',
                'source_id': '1',
                'name': 'CSV Record',
                'value': 150.0,
                'description': 'CSV',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        ]
    ]
    
    response = client.get("/data?page=1&page_size=10&source=csv")
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 1

@patch('src.api.main.Database')
def test_get_data_pagination(mock_db):
    """Test /data endpoint pagination"""
    mock_db.execute_query.side_effect = [
        [{'total': 25}],  # count query
        []  # data query (empty)
    ]
    
    response = client.get("/data?page=2&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 25
    assert data['page'] == 2
    assert data['has_more'] is True  # 25 records with page 2, size 10

@patch('src.api.main.Database')
def test_get_stats(mock_db):
    """Test /stats endpoint"""
    mock_db.execute_query.side_effect = [
        [  # stats query
            {
                'total_records': 3,
                'total_processed': 100,
                'total_duration': 50.5
            }
        ],
        [  # last runs query
            {
                'status': 'success',
                'ended_at': datetime.now(),
                'error_message': None
            }
        ]
    ]
    
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert data['total_records_processed'] == 100
    assert data['run_count'] == 3

@patch('src.api.main.Database')
def test_root_endpoint(mock_db):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert 'message' in data
    assert 'endpoints' in data
    assert data['message'] == 'ETL Data API'

@patch('src.api.main.Database')
def test_get_data_invalid_pagination(mock_db):
    """Test /data with invalid pagination parameters"""
    response = client.get("/data?page=-1&page_size=10")
    assert response.status_code == 422  # Validation error

@patch('src.api.main.Database')
def test_get_data_error_handling(mock_db):
    """Test /data endpoint error handling"""
    mock_db.execute_query.side_effect = Exception("Database error")
    
    response = client.get("/data?page=1&page_size=10")
    assert response.status_code == 500
