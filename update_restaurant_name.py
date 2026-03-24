"""Update restaurant name from Demo Restaurant to Niloufer"""
from app.db.database import SessionLocal

def main():
    session = SessionLocal()
    try:
        # Update all reviews
        result = session.execute(
            "UPDATE reviews SET restaurant_name = 'Niloufer' WHERE restaurant_name = 'Demo Restaurant'"
        )
        session.commit()
        
        # Check count
        count = session.execute("SELECT COUNT(*) FROM reviews WHERE restaurant_name = 'Niloufer'").scalar()
        print(f"✓ Successfully updated {count} reviews to 'Niloufer'")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main()
