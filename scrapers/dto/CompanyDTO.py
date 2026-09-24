from dataclasses import dataclass


@dataclass
class CompanyDTO:
    name: str
    rating: int | None
    accreditation: bool
