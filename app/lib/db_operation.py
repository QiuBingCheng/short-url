from app import db
from app import app
from app.database.models import UrlMapping, User
import base62
import random
import logging


def admin_id():
    admin = db.session.query(User).filter_by(
        email=app.config["MAIL"]).first()

    if admin is None:
        raise Exception("[Error] Cannot find the admin user record.")
    return admin.id


def generate_tracing_code():
    logging.info("next_token is called")
    # get max id
    max_id = db.session.query(db.func.max(UrlMapping.id)).scalar()
    max_id = max_id + 1 if max_id is not None else 1
    # encode
    token = base62.encode(max_id+random.randint(10000, 20000))
    return token


def get_record_by_id(model: db.Model, record_id: int):
    try:
        # Find the record by ID
        logging.info(
            f"Fetching record from {model.__tablename__} with ID {record_id}")
        record = model.query.get(record_id)

        if record:
            _repr_ = repr(record)
            logging.info(f"Record {_repr_} fetched successfully")
            return record
        else:
            logging.warning("Record not found.")
            return None
    except Exception as e:
        logging.error(f"Error occurred while fetching record: {str(e)}")
        return None
    finally:
        db.session.close()


def delete_records(model: db.Model, criteria: dict):
    try:
        logging.info(
            f"Deleting records from {model.__tablename__} where {criteria}")

        records_to_delete = model.query.filter_by(**criteria).all()

        if records_to_delete is None:
            logging.warning("No records found for deletion.")

        for record in records_to_delete:
            _repr_ = repr(record)
            db.session.delete(record)
            logging.info(f"{_repr_} has been deleted")

        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error occurred while deleting record: {str(e)}")
        return False
    finally:
        db.session.close()


def delete_all_records(model: db.Model):
    try:
        # Begin a transaction
        db.session.begin()
        # Use SQLAlchemy's delete method to delete all records
        db.session.query(model).delete()
        # Commit the transaction
        db.session.commit()
        print(f"All records in {model.__tablename__} deleted successfully!")
    except Exception as e:
        # Roll back the transaction on error
        db.session.rollback()
        print(f"Error: {str(e)}")
