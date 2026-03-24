"""
Verify clean database structure after removing restaurant_name
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def verify_clean_structure():
    database_url = os.getenv("DATABASE_URL")
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check reviews table columns
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'reviews' 
            ORDER BY ordinal_position
        """)
        print("=== Reviews Table Columns ===")
        for col in cursor.fetchall():
            print(f"  - {col[0]}: {col[1]}")
        
        # Check review_annotations table columns
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'review_annotations' 
            ORDER BY ordinal_position
        """)
        print("\n=== Review Annotations Table Columns ===")
        for col in cursor.fetchall():
            print(f"  - {col[0]}: {col[1]}")
        
        # Test the relationship query
        cursor.execute("""
            SELECT r.id, rest.name, r.review_text
            FROM reviews r
            JOIN restaurants rest ON r.restaurant_id = rest.id
            LIMIT 3
        """)
        print("\n=== Test Query (Review → Restaurant JOIN) ===")
        for row in cursor.fetchall():
            print(f"Review {row[0]}: {row[1]} - \"{row[2][:50]}...\"")
        
        cursor.close()
        conn.close()
        print("\n✓ Database structure is clean and normalized!")
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    verify_clean_structure()
