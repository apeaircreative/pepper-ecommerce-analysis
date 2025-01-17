"""
Tests for return tracking system.
"""
import unittest
import sqlite3
from datetime import datetime, date
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from utils.return_tracking import ReturnTracker

class TestReturnTracker(unittest.TestCase):
    """Test cases for ReturnTracker class."""
    
    def setUp(self):
        """Set up test database."""
        self.test_db = 'test_returns.db'
        self.tracker = ReturnTracker(self.test_db)
        
        # Add test data
        self.test_order = {
            'order_id': 'TEST_ORD_001',
            'product_id': 'TEST_PRD_001',
            'user_id': 'TEST_USR_001',
            'order_date': '2025-01-17'
        }
    
    def tearDown(self):
        """Clean up test database."""
        Path(self.test_db).unlink(missing_ok=True)
    
    def test_return_initiation(self):
        """Test return initiation process."""
        return_id = self.tracker.initiate_return(self.test_order)
        
        # Verify return was created
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM return_tracking WHERE return_id = ?", (return_id,))
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[1], self.test_order['order_id'])
        self.assertEqual(result[2], self.test_order['product_id'])
        self.assertEqual(result[3], self.test_order['user_id'])
        self.assertEqual(result[14], 'Initiated')
    
    def test_status_update(self):
        """Test return status updates."""
        return_id = self.tracker.initiate_return(self.test_order)
        
        update_data = {
            'return_reason': 'Size too small',
            'condition_rating': 5,
            'exchange_requested': True,
            'new_size_requested': '34B'
        }
        
        self.tracker.update_return_status(return_id, 'Received', update_data)
        
        # Verify updates
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM return_tracking WHERE return_id = ?", (return_id,))
        result = cursor.fetchone()
        conn.close()
        
        self.assertEqual(result[14], 'Received')
        self.assertEqual(result[7], update_data['return_reason'])
        self.assertEqual(result[9], update_data['condition_rating'])
        self.assertEqual(result[11], update_data['exchange_requested'])
        self.assertEqual(result[12], update_data['new_size_requested'])
    
    def test_metrics_calculation(self):
        """Test return metrics calculation."""
        # Add test orders and returns
        for i in range(5):
            order = {
                'order_id': f'TEST_ORD_{i:03d}',
                'product_id': f'TEST_PRD_{i:03d}',
                'user_id': f'TEST_USR_{i:03d}',
                'order_date': '2025-01-17'
            }
            return_id = self.tracker.initiate_return(order)
            
            # Make some exchanges
            if i % 2 == 0:
                self.tracker.update_return_status(
                    return_id,
                    'Received',
                    {
                        'exchange_requested': True,
                        'refund_amount': 50.00
                    }
                )
            else:
                self.tracker.update_return_status(
                    return_id,
                    'Received',
                    {
                        'exchange_requested': False,
                        'refund_amount': 50.00
                    }
                )
        
        # Get metrics
        metrics = self.tracker.get_return_metrics()
        
        # Basic validation of metrics structure
        self.assertIn('All', metrics)
        self.assertEqual(metrics['All']['total_returns'], 5)
        self.assertEqual(metrics['All']['exchanges'], 3)
        self.assertEqual(metrics['All']['exchange_rate'], 60.0)

if __name__ == '__main__':
    unittest.main()
