from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas, models
from ..database import get_db
from ..deps import require_admin

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/me", response_model=schemas.CompanyOut)
def get_my_company(
    db: Session = Depends(get_db),
    admin_user: models.Employee = Depends(require_admin),
):
    company = db.query(models.Company).filter(models.Company.id == admin_user.company_id).first()
    return company
