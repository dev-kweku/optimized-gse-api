import logging
import sys
from app.core.database import init_db, SessionLocal
from app.core.scrapper import GSEEngine


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("GSE_MAIN")

def run_pipeline():
    logger.info("Starting GSE Data Sync Pipeline...")
    
    
    init_db()
    
    
    db = SessionLocal()
    
    try:
    
        engine = GSEEngine(db)
        engine.sync()
        logger.info("Pipeline executed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    run_pipeline()