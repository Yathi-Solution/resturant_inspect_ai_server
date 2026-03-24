"""
Script to update existing restaurant names from 'Demo Restaurant' to 'Niloufer'
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def update_restaurant_names():
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("✗ DATABASE_URL not found in environment variables")
        return
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Update reviews table
        cursor.execute(
            "UPDATE reviews SET restaurant_name = 'Niloufer' WHERE restaurant_name = 'Demo Restaurant' OR restaurant_name IS NULL"
        )
        conn.commit()
        
        # Check how many records exist
        cursor.execute("SELECT COUNT(*) FROM reviews WHERE restaurant_name = 'Niloufer'")
        count = cursor.fetchone()[0]
        
        print(f"✓ Updated reviews table: {count} reviews now have restaurant_name = 'Niloufer'")
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM reviews")
        total = cursor.fetchone()[0]
        print(f"✓ Total reviews in database: {total}")
        
        cursor.close()
        conn.close()
        print("\n✓ Database update completed successfully!")
        
    except Exception as e:
        print(f"✗ Error updating database: {e}")
        if conn:
            conn.rollback()

if __name__ == "__main__":
    update_restaurant_names()
