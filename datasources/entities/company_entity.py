from dataclasses import dataclass


@dataclass
class CompanyEntity :
    name: str
    rating: int | None
    accreditation: bool
