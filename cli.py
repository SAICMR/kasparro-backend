#!/usr/bin/env python
"""
CLI tool for manual ETL operations
Usage: python cli.py --help
"""

import argparse
import logging
from src.core.config import API_HOST, CSV_URL, API_KEY, LOG_LEVEL
from src.core.logger import setup_logging
from src.core.database import Database
from src.etl.pipeline import ETLPipeline

setup_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

def run_etl():
    """Run the ETL pipeline"""
    logger.info("Starting manual ETL run")
    try:
        Database.initialize()
        pipeline = ETLPipeline()
        headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
        success = pipeline.run(f"{API_HOST}/posts", CSV_URL, headers)
        
        if success:
            logger.info("✓ ETL completed successfully")
        else:
            logger.error("✗ ETL failed")
            return 1
    except Exception as e:
        logger.error(f"ETL error: {e}")
        return 1
    finally:
        Database.close()
    return 0

def get_stats():
    """Display ETL statistics"""
    try:
        Database.initialize()
        
        stats = Database.execute_query("""
            SELECT 
                COUNT(*) as total_runs,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_runs,
                SUM(records_processed) as total_records,
                AVG(duration_seconds) as avg_duration,
                MAX(ended_at) as last_run
            FROM etl_runs
        """)
        
        if stats:
            print("\n📊 ETL Statistics")
            print("─" * 40)
            for key, value in stats[0].items():
                if value is not None:
                    print(f"{key.replace('_', ' ').title()}: {value}")
        
        # Data counts
        data_counts = Database.execute_query("""
            SELECT source, COUNT(*) as count 
            FROM normalized_data 
            GROUP BY source
        """)
        
        print("\n📈 Data by Source")
        print("─" * 40)
        for row in data_counts:
            print(f"{row['source'].upper()}: {row['count']} records")
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return 1
    finally:
        Database.close()
    return 0

def reset_database():
    """Reset the database (drops all tables)"""
    try:
        Database.initialize()
        tables = [
            'etl_runs',
            'etl_checkpoint',
            'normalized_data',
            'raw_api_data',
            'raw_csv_data'
        ]
        
        for table in tables:
            Database.execute_update(f"DROP TABLE IF EXISTS {table} CASCADE")
        
        logger.info("✓ Database reset successfully")
        
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return 1
    finally:
        Database.close()
    return 0

def main():
    parser = argparse.ArgumentParser(
        description='ETL Pipeline CLI Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py run           # Run ETL pipeline
  python cli.py stats         # Show statistics
  python cli.py reset         # Reset database
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Run command
    subparsers.add_parser('run', help='Run the ETL pipeline')
    
    # Stats command
    subparsers.add_parser('stats', help='Display ETL statistics')
    
    # Reset command
    subparsers.add_parser('reset', help='Reset the database')
    
    args = parser.parse_args()
    
    if args.command == 'run':
        return run_etl()
    elif args.command == 'stats':
        return get_stats()
    elif args.command == 'reset':
        confirm = input("Are you sure you want to reset the database? (yes/no): ")
        if confirm.lower() == 'yes':
            return reset_database()
        else:
            print("Cancelled")
            return 0
    else:
        parser.print_help()
        return 0

if __name__ == '__main__':
    exit(main())
