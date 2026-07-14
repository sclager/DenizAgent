from pydantic import BaseModel


class RequestModel(BaseModel):
    itsm_no: str = ""
    customer_name: str = ""
    request_date: str = ""
    problem: str = ""
    description: str = ""
    requirements: str = ""