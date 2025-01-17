"""
Return tracking system implementation.
"""
import sqlite3
from datetime import datetime
from typing import Dict, Optional
import uuid

class ReturnTracker:
    """Handles return tracking operations."""
    
    def __init__(self, db_path: str = 'analysis/pepper_analysis.db'):
        """Initialize with database path."""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create return tracking table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS return_tracking (
            return_id TEXT PRIMARY KEY,
            order_id TEXT,
            product_id TEXT,
            user_id TEXT,
            original_order_date DATE,
            return_initiated_date DATE,
            return_received_date DATE,
            return_reason TEXT,
            size_returned TEXT,
            condition_rating INTEGER,
            refund_amount REAL,
            exchange_requested INTEGER,
            new_size_requested TEXT,
            notes TEXT,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create return reasons lookup
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS return_reasons (
            reason_id TEXT PRIMARY KEY,
            category TEXT,
            subcategory TEXT,
            description TEXT,
            active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        conn.close()
    
    def initiate_return(self, order_data: Dict) -> str:
        """
        Initiate a new return.
        
        Args:
            order_data: Dictionary containing return information
            
        Returns:
            return_id: Unique identifier for the return
        """
        return_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO return_tracking (
            return_id,
            order_id,
            product_id,
            user_id,
            original_order_date,
            return_initiated_date,
            status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            return_id,
            order_data['order_id'],
            order_data['product_id'],
            order_data['user_id'],
            order_data['order_date'],
            datetime.now().date().isoformat(),
            'Initiated'
        ))
        
        conn.commit()
        conn.close()
        
        return return_id
    
    def update_return_status(self, return_id: str, status: str, 
                           additional_data: Optional[Dict] = None):
        """
        Update return status and optional data.
        
        Args:
            return_id: Unique return identifier
            status: New status
            additional_data: Optional additional data to update
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        update_fields = ['status = ?', 'updated_at = CURRENT_TIMESTAMP']
        params = [status]
        
        if additional_data:
            for key, value in additional_data.items():
                if key in self._get_valid_fields():
                    update_fields.append(f'{key} = ?')
                    params.append(value)
        
        params.append(return_id)
        
        cursor.execute(f"""
        UPDATE return_tracking 
        SET {', '.join(update_fields)}
        WHERE return_id = ?
        """, params)
        
        conn.commit()
        conn.close()
    
    def _get_valid_fields(self) -> set:
        """Get valid field names for return tracking."""
        return {
            'return_reason',
            'size_returned',
            'condition_rating',
            'refund_amount',
            'exchange_requested',
            'new_size_requested',
            'notes',
            'return_received_date'
        }
    
    def get_return_metrics(self, segment: Optional[str] = None) -> Dict:
        """
        Get return metrics, optionally filtered by segment.
        
        Args:
            segment: Optional segment filter
            
        Returns:
            Dictionary of metrics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        where_clause = "WHERE sp.segment = ?" if segment else ""
        params = [segment] if segment else []
        
        query = f"""
        SELECT 
            'All' as segment,
            COUNT(DISTINCT rt.return_id) as total_returns,
            COUNT(DISTINCT rt.order_id) as returned_orders,
            ROUND(AVG(rt.refund_amount), 2) as avg_refund,
            COUNT(DISTINCT CASE WHEN rt.exchange_requested THEN rt.return_id END) as exchanges,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN rt.exchange_requested THEN rt.return_id END) /
                  NULLIF(COUNT(DISTINCT rt.return_id), 0), 2) as exchange_rate
        FROM return_tracking rt
        """
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        metrics = {}
        for row in results:
            metrics[row[0]] = {
                'total_returns': row[1],
                'returned_orders': row[2],
                'avg_refund': row[3],
                'exchanges': row[4],
                'exchange_rate': row[5]
            }
        
        conn.close()
        return metrics

if __name__ == "__main__":
    # Example usage
    tracker = ReturnTracker()
    
    # Example return initiation
    order_data = {
        'order_id': 'ORD123',
        'product_id': 'PRD456',
        'user_id': 'USR789',
        'order_date': '2025-01-17'
    }
    
    return_id = tracker.initiate_return(order_data)
    print(f"Initiated return: {return_id}")
    
    # Example status update
    tracker.update_return_status(
        return_id,
        'Received',
        {
            'return_reason': 'Size too small',
            'condition_rating': 5,
            'exchange_requested': 1,
            'new_size_requested': '34B'
        }
    )
    
    # Get metrics
    metrics = tracker.get_return_metrics()
    print("\nReturn Metrics:")
    for segment, data in metrics.items():
        print(f"\n{segment}:")
        for metric, value in data.items():
            print(f"  {metric}: {value}")
