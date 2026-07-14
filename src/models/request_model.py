from pydantic import BaseModel


class RequestModel(BaseModel):
    itsm_no: str = ""
    request_form_no: str = ""
    request_date: str = ""
    customer_name: str = ""
    country: str = ""
    category: str = ""
    request_title: str = ""
    description: str = ""
    requirements: str = ""