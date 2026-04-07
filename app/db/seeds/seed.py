from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import CAGReferenceData, PromptTemplate
from sentence_transformers import SentenceTransformer
from app.db.seeds.reference_data_seed import REFERENCE_DATA_SEED
from app.db.seeds.prompt_templates_seed import PROMPT_TEMPLATES_SEED

# Load SentenceTransformer model for embeddings
embedding_model = SentenceTransformer("all-mpnet-base-v2")


def seed_cag_reference_data(session: Session):
    rows = []

    for styles, text in REFERENCE_DATA_SEED:
        rows.append(
            CAGReferenceData(
                dining_styles=styles,
                reference_text=text,
                embedding=embedding_model.encode(text).tolist(),
            )
        )

    session.bulk_save_objects(rows)
    print(f"Seeded {len(rows)} CAG reference rows.")


def seed_prompt_templates(session: Session):
    rows = []

    for item in PROMPT_TEMPLATES_SEED:
        rows.append(
            PromptTemplate(
                template=item["template"],
                template_type=item["template_type"],
                version=item["version"],
            )
        )

    session.bulk_save_objects(rows)
    print(f"Seeded {len(rows)} prompt templates.")


def seed():
    session: Session = SessionLocal()

    try:
        seed_cag_reference_data(session)
        seed_prompt_templates(session)

        session.commit()
        print("Seeding completed successfully.")

    except Exception as e:
        session.rollback()
        print("Seeding failed:", e)

    finally:
        session.close()


if __name__ == "__main__":
    seed()