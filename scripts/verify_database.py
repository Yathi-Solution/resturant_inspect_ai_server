"""
Verify the new database structure
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def verify_database():
    database_url = os.getenv("DATABASE_URL")
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check restaurants table
        cursor.execute("SELECT id, name, address FROM restaurants")
        restaurants = cursor.fetchall()
        print("=== Restaurants Table ===")
        for r in restaurants:
            print(f"ID: {r[0]}, Name: {r[1]}, Address: {r[2]}")
        
        # Check reviews with restaurant relationship
        cursor.execute("""
            SELECT r.id, r.restaurant_id, rest.name 
            FROM reviews r
            JOIN restaurants rest ON r.restaurant_id = rest.id
            LIMIT 5
        """)
        reviews = cursor.fetchall()
        print("\n=== Sample Reviews (showing restaurant relationship) ===")
        for rev in reviews:
            print(f"Review ID: {rev[0]}, Restaurant ID: {rev[1]}, Restaurant Name: {rev[2]}")
        
        # Count total reviews
        cursor.execute("SELECT COUNT(*) FROM reviews WHERE restaurant_id IS NOT NULL")
        count = cursor.fetchone()[0]
        print(f"\n✓ Total reviews linked to restaurants: {count}")
        
        cursor.close()
        conn.close()
        print("\n✓ Database structure verified successfully!")
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    verify_database()
