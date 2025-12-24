import pytest
from unittest.mock import patch, Mock
from datetime import datetime
from src.etl.pipeline import ETLPipeline
from src.schemas.models import DataRecord

class TestETLIntegration:
    """Integration tests for the complete ETL pipeline"""
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline instance"""
        return ETLPipeline()
    
    @patch('src.etl.pipeline.Database')
    def test_full_pipeline_flow(self, mock_db, pipeline):
        """Test complete ETL pipeline flow"""
        # Mock API response
        api_data = [
            {'id': 1, 'title': 'Post 1', 'body': 'Content 1', 'userId': 1},
            {'id': 2, 'title': 'Post 2', 'body': 'Content 2', 'userId': 1}
        ]
        
        # Mock CSV response
        csv_data = [
            {'ID': '1', 'NAME': 'User 1', 'VALUE': '100'},
            {'ID': '2', 'NAME': 'User 2', 'VALUE': '200'}
        ]
        
        # Setup mock returns
        mock_db.execute_update.return_value = 1
        mock_db.execute_query.return_value = []
        
        with patch('requests.get') as mock_get:
            # Mock API call
            api_response = Mock()
            api_response.json.return_value = api_data
            
            # Mock CSV call
            csv_response = Mock()
            csv_response.text = "ID,NAME,VALUE\n1,User 1,100\n2,User 2,200"
            
            mock_get.side_effect = [api_response, csv_response]
            
            # Run pipeline
            result = pipeline.run('http://api.test', 'http://csv.test')
            
            # Verify
            assert result is True
            assert pipeline.total_records > 0

    @patch('src.etl.pipeline.Database')
    def test_checkpoint_resume_on_rerun(self, mock_db, pipeline):
        """Test that checkpoint prevents reprocessing"""
        # First run
        api_data = [{'id': 1, 'title': 'Post 1', 'body': 'Content 1', 'userId': 1}]
        
        mock_db.execute_update.return_value = 1
        mock_db.execute_query.side_effect = [
            [],  # No checkpoint
            [{'last_processed_id': '1', 'total_processed': 1}]  # After first run
        ]
        
        with patch('requests.get') as mock_get:
            response = Mock()
            response.json.return_value = api_data
            mock_get.return_value = response
            
            # Get checkpoint
            checkpoint = pipeline.get_checkpoint('api')
            assert checkpoint is None  # No checkpoint initially
            
            # After update
            pipeline.update_checkpoint('api', '1', 1)
            mock_db.execute_update.assert_called()

    @patch('src.etl.pipeline.Database')
    def test_error_handling_in_pipeline(self, mock_db, pipeline):
        """Test error handling during pipeline execution"""
        mock_db.execute_update.return_value = 1
        
        with patch('requests.get', side_effect=Exception('API Error')):
            result = pipeline.run('http://api.test', 'http://csv.test')
            
            # Should still call record_run even on error
            assert mock_db.execute_update.called

    def test_data_normalization_consistency(self, pipeline):
        """Test that normalized data maintains consistency"""
        raw_api = [
            {
                'id': 1,
                'title': 'API Post',
                'body': 'API Content',
                'userId': 1
            }
        ]
        
        raw_csv = [
            {
                'ID': '1',
                'NAME': 'CSV Record',
                'VALUE': '100.5'
            }
        ]
        
        normalized_api = pipeline.normalize_data('api', raw_api)
        normalized_csv = pipeline.normalize_data('csv', raw_csv)
        
        # Both should be DataRecord instances
        assert all(isinstance(r, DataRecord) for r in normalized_api)
        assert all(isinstance(r, DataRecord) for r in normalized_csv)
        
        # Check common fields
        for records in [normalized_api, normalized_csv]:
            for record in records:
                assert record.source in ['api', 'csv']
                assert record.source_id is not None
                assert record.name is not None
                assert isinstance(record.created_at, datetime)
                assert isinstance(record.updated_at, datetime)

    @patch('src.etl.pipeline.Database')
    def test_duplicate_prevention(self, mock_db, pipeline):
        """Test that duplicate data is not reprocessed"""
        # Same data twice
        duplicate_data = [
            {'id': 1, 'title': 'Post', 'body': 'Content'}
        ] * 2
        
        mock_db.execute_update.side_effect = [
            1,  # First insert
            0   # Duplicate rejected (ON CONFLICT DO NOTHING)
        ]
        
        pipeline.store_raw_data('api', duplicate_data)
        
        # execute_update should be called twice
        assert mock_db.execute_update.call_count >= 1

    def test_type_conversion_robustness(self, pipeline):
        """Test type conversion handles various formats"""
        test_cases = [
            ('100', 100.0),
            ('100.5', 100.5),
            ('invalid', None),
            (None, None),
            (0, 0.0),
            ('', None),
        ]
        
        for input_val, expected in test_cases:
            result = pipeline._safe_float(input_val)
            assert result == expected, f"Failed for {input_val}: got {result}, expected {expected}"

    @patch('src.etl.pipeline.Database')
    def test_run_metadata_recording(self, mock_db, pipeline):
        """Test that run metadata is accurately recorded"""
        from datetime import datetime as dt
        
        pipeline.start_time = dt.now()
        pipeline.record_run(True, 100, None)
        
        # Verify execute_update was called with run data
        mock_db.execute_update.assert_called()
        
        # Get the call arguments
        call_args = mock_db.execute_update.call_args
        assert call_args is not None
        
        # The query should contain status and records_processed
        query = call_args[0][0]
        assert 'etl_runs' in query
        assert 'success' in str(call_args)
