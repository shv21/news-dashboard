import os
import shutil
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

def init_db(app):
    """Binds SQLAlchemy to the Flask app, ensures directory exists, and initializes tables/seed db."""
    db.init_app(app)
    with app.app_context():
        try:
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if db_uri.startswith('sqlite:///') and not db_uri.startswith('sqlite:///:memory:'):
                db_path = db_uri.replace('sqlite:///', '')
                db_dir = os.path.dirname(os.path.abspath(db_path))
                if db_dir:
                    os.makedirs(db_dir, exist_ok=True)
                
                # Copy packaged seed database if present and target is missing or 0 bytes
                if not app.config.get('TESTING'):
                    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
                        root = Path(app.root_path) if hasattr(app, 'root_path') else Path.cwd()
                        seed_db = root / 'data' / 'news.db'
                        if seed_db.exists() and seed_db.resolve().as_posix() != Path(db_path).resolve().as_posix():
                            try:
                                shutil.copy2(seed_db, db_path)
                            except Exception as e:
                                app.logger.warning(f"Could not copy seed database: {e}")
        except Exception as err:
            app.logger.warning(f"Database directory setup error: {err}")

        # Create tables
        db.create_all()

        # Fallback seed if DB remains empty and not in testing mode
        if not app.config.get('TESTING'):
            seed_fallback_articles(app)

def seed_fallback_articles(app):
    """Populates initial sample news articles if DB is empty."""
    try:
        from database.models import News
        if News.query.count() == 0:
            sample_news = [
                News(
                    title="Global Markets Surge as Tech Stocks Reach Record Highs",
                    source="BBC News",
                    summary="Major indices across Europe and Asia gained momentum following strong earnings reports from top technology companies.",
                    article_url="https://www.bbc.com/news/business-tech-record-highs",
                    image_url="https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=600&q=80",
                    country="US"
                ),
                News(
                    title="RBI Keeps Repo Rate Unchanged at 6.5% Amid Inflation Control",
                    source="India Today",
                    summary="The Reserve Bank of India announced its monetary policy decision today, prioritizing price stability while supporting GDP growth.",
                    article_url="https://www.indiatoday.in/business/rbi-repo-rate-policy-2026",
                    image_url="https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=600&q=80",
                    country="IN"
                ),
                News(
                    title="AI Breakthroughs Drive Next-Gen Quantum Computing Chips",
                    source="TechCrunch",
                    summary="Researchers unveil a silicon-based quantum processor operating at room temperature with high qubit fidelity.",
                    article_url="https://techcrunch.com/quantum-ai-chip-breakthrough",
                    image_url="https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80",
                    country="US"
                ),
                News(
                    title="Clean Energy Transition Accelerates Across European Power Grids",
                    source="The Verge",
                    summary="Solar and wind power generation surpassed fossil fuels in quarterly capacity across major EU member states.",
                    article_url="https://theverge.com/clean-energy-transition-europe",
                    image_url="https://images.unsplash.com/photo-1466611653911-95081537e5b7?auto=format&fit=crop&w=600&q=80",
                    country="UK"
                ),
                News(
                    title="Canada Expands Clean Energy Investments in Renewable Infrastructure",
                    source="CBC News",
                    summary="Federal funding allocates new resources for hydroelectric power expansion and rural grid modernization in Canada.",
                    article_url="https://www.cbc.ca/news/canada-clean-energy-investments-2026",
                    image_url="https://images.unsplash.com/photo-1509391365360-2e959784a276?auto=format&fit=crop&w=600&q=80",
                    country="CA"
                ),
                News(
                    title="Australia Unveils Major Marine Conservation Initiative for Great Barrier Reef",
                    source="ABC News Australia",
                    summary="Environmental authorities commit new research grants to protect coral reef biodiversity against ocean warming.",
                    article_url="https://www.abc.net.au/news/australia-marine-conservation-reef-2026",
                    image_url="https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=600&q=80",
                    country="AU"
                ),
                News(
                    title="Germany Sets Record in Industrial Automation and Robotics Production",
                    source="DW News",
                    summary="German manufacturing sectors report strong growth driven by advanced robotic automation and exports.",
                    article_url="https://www.dw.com/en/germany-robotics-manufacturing-surge-2026",
                    image_url="https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=600&q=80",
                    country="DE"
                ),
                News(
                    title="Japan Advances Next-Generation High-Speed Rail Tech",
                    source="Japan Today",
                    summary="New maglev prototype achieves record-breaking stability during high-speed tests outside Tokyo.",
                    article_url="https://japantoday.com/news/japan-maglev-bullet-train-record-2026",
                    image_url="https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=600&q=80",
                    country="JP"
                )
            ]
            db.session.bulk_save_objects(sample_news)
            db.session.commit()
            app.logger.info("Successfully seeded fallback news articles into database.")
    except Exception as e:
        db.session.rollback()
        app.logger.warning(f"Fallback article seeding failed: {e}")
