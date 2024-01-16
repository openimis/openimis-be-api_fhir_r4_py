import typing

SUPPORTED_FORMATS = ['json']

# fix of 'issue' type from https://github.com/nazrulworld/fhir.resources.R4B/blob/main/fhir/resources/operationoutcome.py#L31
# by overriding 'issue' property. Without this fix - there is no 'issue' field in 'OperationOutcome' model.
from fhir.resources.R4B import fhirtypes
from pydantic import Field
from fhir.resources.R4B.operationoutcome import OperationOutcome
from fhir.resources.R4B.usagecontext import UsageContext
from fhir.resources.R4B.coverage import Coverage, CoverageClass
from fhir.resources.R4B.contract import ContractSigner
from fhir.resources.R4B.claim import Claim, ClaimInsurance
from fhir.resources.R4B.claimresponse import ClaimResponse
from fhir.resources.R4B.coverageeligibilityrequest import CoverageEligibilityRequest


class OperationOutcomeV2(OperationOutcome):
    issue: typing.List[fhirtypes.OperationOutcomeIssueType] = Field(
        None,
        alias="issue",
        title="A single issue associated with the action",
        description=(
            "An error, warning, or information message that results from a system "
            "action."
        ),
        # if property is element of this resource.
        element_property=True,
    )


class UsageContextV2(UsageContext):
    code: fhirtypes.CodingType = Field(
        None,
        alias="code",
        title="Type of context being specified",
        description=(
            "A code that identifies the type of context being specified by this "
            "usage context."
        ),
        # if property is element of this resource.
        element_property=True,
    )


class CoverageV2(Coverage):
    payor: typing.List[fhirtypes.ReferenceType] = Field(
        None,
        alias="payor",
        title="Issuer of the policy",
        description=(
            "The program or plan underwriter or payor including both insurance and "
            "non-insurance agreements, such as patient-pay agreements."
        ),
        # if property is element of this resource.
        element_property=True,
        # note: Listed Resource Type(s) should be allowed as Reference.
        enum_reference_types=["Organization", "Patient", "RelatedPerson"],
    )


class CoverageClassV2(CoverageClass):
    type: fhirtypes.CodeableConceptType = Field(
        None,
        alias="type",
        title="Type of class such as 'group' or 'plan'",
        description=(
            "The type of classification for which an insurer-specific class label "
            "or number and optional name is provided, for example may be used to "
            "identify a class of coverage or employer group, Policy, Plan."
        ),
        # if property is element of this resource.
        element_property=True,
    )


class ContractSignerV2(ContractSigner):
    party: fhirtypes.ReferenceType = Field(
        None,
        alias="party",
        title="Contract Signatory Party",
        description="Party which is a signator to this Contract.",
        # if property is element of this resource.
        element_property=True,
        # note: Listed Resource Type(s) should be allowed as Reference.
        enum_reference_types=[
            "Organization",
            "Patient",
            "Practitioner",
            "PractitionerRole",
            "RelatedPerson",
        ],
    )

    type: fhirtypes.CodingType = Field(
        None,
        alias="type",
        title="Contract Signatory Role",
        description="Role of this Contract signer, e.g. notary, grantee.",
        # if property is element of this resource.
        element_property=True,
    )


class ClaimV2(Claim):
    insurance: typing.List[fhirtypes.ClaimInsuranceType] = Field(
        None,
        alias="insurance",
        title="Patient insurance information",
        description=(
            "Financial instruments for reimbursement for the health care products "
            "and services specified on the claim."
        ),
        # if property is element of this resource.
        element_property=True,
    )

    patient: fhirtypes.ReferenceType = Field(
        None,
        alias="patient",
        title="The recipient of the products and services",
        description=(
            "The party to whom the professional services and/or products have been "
            "supplied or are being considered and for whom actual or forecast "
            "reimbursement is sought."
        ),
        # if property is element of this resource.
        element_property=True,
        # note: Listed Resource Type(s) should be allowed as Reference.
        enum_reference_types=["Patient"],
    )

    priority: fhirtypes.CodeableConceptType = Field(
        None,
        alias="priority",
        title="Desired processing ugency",
        description=(
            "The provider-required urgency of processing the request. Typical "
            "values include: stat, routine deferred."
        ),
        # if property is element of this resource.
        element_property=True,
    )

    provider: fhirtypes.ReferenceType = Field(
        None,
        alias="provider",
        title="Party responsible for the claim",
        description=(
            "The provider which is responsible for the claim, predetermination or "
            "preauthorization."
        ),
        # if property is element of this resource.
        element_property=True,
        # note: Listed Resource Type(s) should be allowed as Reference.
        enum_reference_types=["Practitioner", "PractitionerRole", "Organization"],
    )

    type: fhirtypes.CodeableConceptType = Field(
        None,
        alias="type",
        title="Category or discipline",
        description=(
            "The category of claim, e.g. oral, pharmacy, vision, institutional, "
            "professional."
        ),
        # if property is element of this resource.
        element_property=True,
    )


class ClaimInsuranceV2(ClaimInsurance):
    coverage: fhirtypes.ReferenceType = Field(
        None,
        alias="coverage",
        title="Insurance information",
        description=(
            "Reference to the insurance card level information contained in the "
            "Coverage resource. The coverage issuing insurer will use these details"
            " to locate the patient's actual coverage within the insurer's "
            "information system."
        ),
        # if property is element of this resource.
        element_property=True,
        # note: Listed Resource Type(s) should be allowed as Reference.
        enum_reference_types=["Coverage"],
    )


class ClaimResponseV2(ClaimResponse):
    insurer: fhirtypes.ReferenceType = Field(
        None,
        alias="insurer",
        title="Party responsible for reimbursement",
        description=(
            "The party responsible for authorization, adjudication and "
            "reimbursement."
        ),
        # if property is element of this resource.
        element_property=True,
        # note: Listed Resource Type(s) should be allowed as Reference.
        enum_reference_types=["Organization"],
    )

    patient: fhirtypes.ReferenceType = Field(
        None,
        alias="patient",
        title="The recipient of the products and services",
        description=(
            "The party to whom the professional services and/or products have been "
            "supplied or are being considered and for whom actual for facast "
            "reimbursement is sought."
        ),
        # if property is element of this resource.
        element_property=True,
        # note: Listed Resource Type(s) should be allowed as Reference.
        enum_reference_types=["Patient"],
    )

    type: fhirtypes.CodeableConceptType = Field(
        None,
        alias="type",
        title="More granular claim type",
        description=(
            "A finer grained suite of claim type codes which may convey additional "
            "information such as Inpatient vs Outpatient and/or a specialty "
            "service."
        ),
        # if property is element of this resource.
        element_property=True,
    )


class CoverageEligibilityRequestV2(CoverageEligibilityRequest):
    insurer: fhirtypes.ReferenceType = Field(
        None,
        alias="insurer",
        title="Coverage issuer",
        description=(
            "The Insurer who issued the coverage in question and is the recipient "
            "of the request."
        ),
        # if property is element of this resource.
        element_property=True,
        # note: Listed Resource Type(s) should be allowed as Reference.
        enum_reference_types=["Organization"],
    )

    patient: fhirtypes.ReferenceType = Field(
        None,
        alias="patient",
        title="Intended recipient of products and services",
        description=(
            "The party who is the beneficiary of the supplied coverage and for whom"
            " eligibility is sought."
        ),
        # if property is element of this resource.
        element_property=True,
        # note: Listed Resource Type(s) should be allowed as Reference.
        enum_reference_types=["Patient"],
    )

    type: fhirtypes.CodeableConceptType = Field(
        None,
        alias="type",
        title="More granular claim type",
        description=(
            "A finer grained suite of claim type codes which may convey additional "
            "information such as Inpatient vs Outpatient and/or a specialty "
            "service."
        ),
        # if property is element of this resource.
        element_property=True,
    )
