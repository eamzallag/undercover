"""The shapes of the API's requests and responses."""

from datetime import date, datetime
from typing import Annotated, Literal, Self

from pydantic import AfterValidator, BaseModel, Field, model_validator

Status = Literal["waiting", "in_progress", "waiting_for_sign_off", "decided"]
DecisionName = Literal["approve", "decline", "refer"]
StepKind = Literal["tool", "message"]


def to_cents(amount: float) -> float:
    """Round an amount to the cent."""
    return round(amount, 2)


Money = Annotated[float, Field(ge=0), AfterValidator(to_cents)]
Text = Annotated[str, Field(min_length=1)]


class Item(BaseModel):
    description: str
    category: str
    amount: float


class Document(BaseModel):
    name: str
    type: str
    content: str


class Decision(BaseModel):
    decision: DecisionName
    payout: float
    reasons: str
    policy_section: str
    decided_at: datetime


class Payment(BaseModel):
    amount: float
    paid_at: datetime
    signed_off_by: str | None


class ClaimSummary(BaseModel):
    claim_id: str
    customer_name: str
    claim_type: str
    summary: str
    submitted_on: date
    amount_claimed: float
    status: Status
    decision: DecisionName | None
    payout: float | None


class ClaimState(BaseModel):
    claim_id: str
    status: Status
    thread_id: str | None
    decision: Decision | None
    payment: Payment | None


class Claim(ClaimState):
    policy_id: str
    customer_id: str
    customer_name: str
    claim_type: str
    submitted_on: date
    incident_date: date
    incident_location: str
    summary: str
    story: str
    items: list[Item]
    amount_claimed: float
    documents: list[Document]


class Trip(BaseModel):
    destination: str
    departs_on: date
    returns_on: date
    trip_cost: float


class Plan(BaseModel):
    plan: str
    name: str
    trip_cancellation_max: float
    trip_delay_waiting_hours: int
    trip_delay_max: float
    baggage_delay_waiting_hours: int
    baggage_delay_max: float
    baggage_max: float
    per_item_limit: float
    passport_max: float
    emergency_medical_max: float
    deductible: float


class AddOn(BaseModel):
    add_on: str
    name: str
    effect: str
    electronics_per_item_limit: float | None = None


class Policy(BaseModel):
    policy_id: str
    customer_id: str
    plan: str
    add_ons: list[str]
    purchased_on: date
    sold_through: str
    trip: Trip
    travelers: list[str]
    status: str
    plan_details: Plan
    add_on_details: list[AddOn]


class PreviousClaim(BaseModel):
    claim_id: str
    filed_on: date
    incident_date: date
    claim_type: str
    summary: str
    outcome: str
    amount_paid: float


class ClaimHistory(BaseModel):
    customer_id: str
    name: str
    customer_since: date
    previous_claims: list[PreviousClaim]


class PolicyWording(BaseModel):
    version: str
    text: str


class Instructions(BaseModel):
    text: str


class Step(BaseModel):
    step_id: int
    kind: StepKind
    title: str
    detail: str
    created_at: datetime


class StartRequest(BaseModel):
    thread_id: Text


class StepRequest(BaseModel):
    kind: StepKind
    title: Text
    detail: str


class DecisionRequest(BaseModel):
    decision: DecisionName
    payout: Money
    reasons: Text
    policy_section: Text

    @model_validator(mode="after")
    def payout_fits_decision(self) -> Self:
        """Approvals pay something; declines and referrals pay nothing."""
        if self.decision == "approve" and self.payout == 0:
            raise ValueError("An approval needs a payout above $0")
        if self.decision != "approve" and self.payout != 0:
            raise ValueError("A decline or a referral has a payout of $0")
        return self


class PaymentRequest(BaseModel):
    amount: Money


class SignOffRequest(BaseModel):
    handler_id: Text
