from sqlalchemy.orm import declarative_base

# The ORM Base for models to inherit from
Base = declarative_base()

# A "Stub" dependency. 
# It performs NO logic and has NO config.
# It exists ONLY for routers to import it as: Depends(get_db)
def get_db():
    raise NotImplementedError("Dependency Override Required: The consumer app must override get_db with a real connection.")
