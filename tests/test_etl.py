import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.etl.pipeline import ETLPipeline
from src.schemas.models import DataRecord

@pytest.fixture
def etl_pipeline():
    """Create ETL pipeline instance for testing"""
    return ETLPipeline()

def test_normalize_api_data(etl_pipeline):
    """Test API data normalization"""
    raw_data = [
        {
            'id': 1,
            'title': 'Test Post',
            'body': 'Test body',
            'userId': 1
        },
        {
            'id': 2,
            'title': 'Another Post',
            'body': 'Another body',
            'userId': 2
        }
    ]
    
    normalized = etl_pipeline.normalize_data('api', raw_data)
    
    assert len(normalized) == 2
    assert normalized[0].source == 'api'
    assert normalized[0].name == 'Test Post'
    assert normalized[1].name == 'Another Post'

def test_normalize_csv_data(etl_pipeline):
    """Test CSV data normalization"""
    raw_data = [
        {
            'ID': '1',
            'NAME': 'John Doe',
            'VALUE': '100.5',
            'description': 'Test user'
        },
        {
            'ID': '2',
            'NAME': 'Jane Doe',
            'VALUE': '200.3',
            'description': 'Another user'
        }
    ]
    
    normalized = etl_pipeline.normalize_data('csv', raw_data)
    
    assert len(normalized) == 2
    assert normalized[0].source == 'csv'
    assert normalized[0].value == 100.5
    assert normalized[1].value == 200.3

def test_safe_float_conversion(etl_pipeline):
    """Test safe float conversion"""
    assert etl_pipeline._safe_float('100.5') == 100.5
    assert etl_pipeline._safe_float('invalid') is None
    assert etl_pipeline._safe_float(None) is None
    assert etl_pipeline._safe_float(42) == 42.0

def test_ingest_api_data_success(etl_pipeline):
    """Test successful API ingestion"""
    mock_response = Mock()
    mock_response.json.return_value = [{'id': 1, 'name': 'Test'}]
    
    with patch('requests.get', return_value=mock_response):
        data = etl_pipeline.ingest_api_data('http://api.example.com')
        assert len(data) == 1
        assert data[0]['id'] == 1

def test_ingest_api_data_failure(etl_pipeline):
    """Test API ingestion failure handling"""
    with patch('requests.get', side_effect=Exception('Connection error')):
        data = etl_pipeline.ingest_api_data('http://api.example.com')
        assert data == []
        assert len(etl_pipeline.errors) > 0

def test_ingest_csv_data_success(etl_pipeline):
    """Test successful CSV ingestion"""
    csv_content = "id,name,value\n1,Test,100\n2,Test2,200"
    mock_response = Mock()
    mock_response.text = csv_content
    
    with patch('requests.get', return_value=mock_response):
        data = etl_pipeline.ingest_csv_data('http://example.com/data.csv')
        assert len(data) == 2
        assert data[0]['name'] == 'Test'

def test_ingest_csv_data_failure(etl_pipeline):
    """Test CSV ingestion failure handling"""
    with patch('requests.get', side_effect=Exception('Download error')):
        data = etl_pipeline.ingest_csv_data('http://example.com/data.csv')
        assert data == []
        assert len(etl_pipeline.errors) > 0

@patch('src.etl.pipeline.Database')
def test_record_run_success(mock_db, etl_pipeline):
    """Test recording successful ETL run"""
    etl_pipeline.start_time = datetime.now()
    etl_pipeline.record_run(True, 100)
    
    # Verify execute_update was called
    assert mock_db.execute_update.called

@patch('src.etl.pipeline.Database')
def test_record_run_failure(mock_db, etl_pipeline):
    """Test recording failed ETL run"""
    etl_pipeline.start_time = datetime.now()
    etl_pipeline.record_run(False, 50, 'Test error')
    
    # Verify execute_update was called
    assert mock_db.execute_update.called

def test_data_record_validation():
    """Test Pydantic schema validation"""
    valid_record = DataRecord(
        source='api',
        source_id='1',
        name='Test Record',
        value=100.5,
        description='Test description',
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    assert valid_record.source == 'api'
    assert valid_record.value == 100.5

def test_data_record_validation_failure():
    """Test schema validation failure"""
    with pytest.raises(Exception):
        DataRecord(
            source='api',
            source_id='1',
            name='Test',
            # Missing required created_at and updated_at
        )
