"""
Dhvaani - Verified Service Catalog (Phase 6)
============================================
Defines the authoritative service layer for government schemes and civic grievances.

Principles:
1. Every service has an authoritative jurisdiction and official authority.
2. Submission modes are truthful:
   - "official_portal": Direct citizen portal requiring citizen auth/OTP.
   - "assisted_handoff": Dhvaani structures the complaint and hands off to the official portal.
   - "api": Only when a genuine, documented public API is integrated.
   - "information_only": Information and guidelines service.
3. No fake government reference IDs or simulated submissions are ever produced.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class ServiceIdentity:
    service_id: str
    official_name: str
    local_names: Dict[str, str] = field(default_factory=dict)
    service_type: str = "scheme"  # "scheme" | "grievance" | "certificate" | "welfare_service" | "information_service"
    category: str = "general"
    department: str = ""
    ministry: str = ""
    jurisdiction: str = "India"  # "India", "Tamil Nadu", "Municipal"


@dataclass
class ServiceOfficialInfo:
    portal_name: str
    portal_url: str
    information_url: str
    application_url: str = ""
    status_tracking_url: str = ""
    helpline: str = ""
    authority_name: str = ""


@dataclass
class ServiceRequirements:
    eligibility_criteria: List[str] = field(default_factory=list)
    exclusions: List[str] = field(default_factory=list)
    required_documents: List[str] = field(default_factory=list)
    target_groups: List[str] = field(default_factory=list)
    occupation: List[str] = field(default_factory=list)
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    gender: List[str] = field(default_factory=list)
    income_limit: Optional[str] = None


@dataclass
class ServiceWorkflow:
    submission_mode: str = "official_portal"  # "api" | "official_portal" | "assisted_handoff" | "information_only"
    api_available: bool = False
    requires_citizen_auth: bool = True
    auth_methods: List[str] = field(default_factory=lambda: ["OTP", "Aadhaar", "Citizen Login"])
    application_steps: List[str] = field(default_factory=list)
    estimated_resolution_days: Optional[int] = None


@dataclass
class ServiceVerification:
    verification_status: str = "verified"  # "verified" | "partially_verified" | "needs_verification"
    source_type: str = "central_portal"  # "central_portal" | "state_portal" | "ministry_website" | "myscheme"
    source_url: str = ""
    last_verified: str = "2024-11-15"
    truthful_notes: str = ""


@dataclass
class ServiceItem:
    identity: ServiceIdentity
    official_info: ServiceOfficialInfo
    requirements: ServiceRequirements
    workflow: ServiceWorkflow
    verification: ServiceVerification

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_id": self.identity.service_id,
            "official_name": self.identity.official_name,
            "local_names": self.identity.local_names,
            "service_type": self.identity.service_type,
            "category": self.identity.category,
            "department": self.identity.department,
            "ministry": self.identity.ministry,
            "jurisdiction": self.identity.jurisdiction,
            "portal_name": self.official_info.portal_name,
            "portal_url": self.official_info.portal_url,
            "information_url": self.official_info.information_url,
            "application_url": self.official_info.application_url,
            "status_tracking_url": self.official_info.status_tracking_url,
            "helpline": self.official_info.helpline,
            "authority_name": self.official_info.authority_name,
            "eligibility_criteria": self.requirements.eligibility_criteria,
            "exclusions": self.requirements.exclusions,
            "required_documents": self.requirements.required_documents,
            "target_groups": self.requirements.target_groups,
            "occupation": self.requirements.occupation,
            "age_min": self.requirements.age_min,
            "age_max": self.requirements.age_max,
            "gender": self.requirements.gender,
            "income_limit": self.requirements.income_limit,
            "submission_mode": self.workflow.submission_mode,
            "api_available": self.workflow.api_available,
            "requires_citizen_auth": self.workflow.requires_citizen_auth,
            "auth_methods": self.workflow.auth_methods,
            "application_steps": self.workflow.application_steps,
            "estimated_resolution_days": self.workflow.estimated_resolution_days,
            "verification_status": self.verification.verification_status,
            "source_type": self.verification.source_type,
            "source_url": self.verification.source_url,
            "last_verified": self.verification.last_verified,
            "truthful_notes": self.verification.truthful_notes,
        }


# ─────────────────────────────────────────────────────────────────────────────
# GRIEVANCE SERVICES CATALOG (8 Official Civic Departments)
# ─────────────────────────────────────────────────────────────────────────────

GRIEVANCE_SERVICES: Dict[str, ServiceItem] = {
    "electricity": ServiceItem(
        identity=ServiceIdentity(
            service_id="grievance_electricity",
            official_name="Electricity / TANGEDCO Grievance Redressal",
            local_names={"hi": "बिजली शिकायत निवारण", "ta": "மின்சார குறைதீர்ப்பு"},
            service_type="grievance",
            category="electricity",
            department="Tamil Nadu Generation and Distribution Corporation (TANGEDCO)",
            ministry="Ministry of Power / TN Energy Department",
            jurisdiction="Tamil Nadu",
        ),
        official_info=ServiceOfficialInfo(
            portal_name="TANGEDCO Consumer Grievance Portal",
            portal_url="https://grievances.tneb.in",
            information_url="https://www.tangedco.gov.in",
            application_url="https://grievances.tneb.in",
            status_tracking_url="https://grievances.tneb.in/status",
            helpline="TANGEDCO: 94987-94987 / 1912",
            authority_name="Superintending Engineer / Executive Engineer (O&M)",
        ),
        requirements=ServiceRequirements(
            required_documents=["Electricity Consumer Number (EB Service No.)", "Contact Phone Number", "Premises Address"],
            target_groups=["Electricity consumers", "Residents"],
        ),
        workflow=ServiceWorkflow(
            submission_mode="assisted_handoff",
            api_available=False,
            requires_citizen_auth=True,
            auth_methods=["Consumer Number Verification", "Mobile OTP"],
            application_steps=[
                "Dhvaani structures your grievance summary and issue category.",
                "Click 'Continue to Official Portal' to open the TANGEDCO grievance portal.",
                "Enter your Consumer Service Number and mobile number for verification.",
                "Paste the complaint text provided by Dhvaani and submit.",
                "Note down your official TANGEDCO Grievance Number for tracking.",
            ],
            estimated_resolution_days=3,
        ),
        verification=ServiceVerification(
            verification_status="verified",
            source_type="state_portal",
            source_url="https://grievances.tneb.in",
            last_verified="2024-11-01",
            truthful_notes="Direct public API does not exist; requires consumer number and mobile OTP on tneb.in.",
        ),
    ),
    "streetlight": ServiceItem(
        identity=ServiceIdentity(
            service_id="grievance_streetlight",
            official_name="Municipal Street Lighting & Electrical Works",
            local_names={"hi": "नगर निगम – स्ट्रीट लाइट शिकायत", "ta": "நகராட்சி – தெரு விளக்கு குறைதீர்ப்பு"},
            service_type="grievance",
            category="streetlight",
            department="Greater Chennai Corporation / Urban Local Bodies",
            ministry="Municipal Administration & Water Supply Department",
            jurisdiction="Municipal",
        ),
        official_info=ServiceOfficialInfo(
            portal_name="GCC 1913 Grievance Portal / Namma Chennai",
            portal_url="https://www.chennaicorporation.gov.in",
            information_url="https://www.chennaicorporation.gov.in",
            application_url="https://www.chennaicorporation.gov.in/",
            status_tracking_url="https://www.chennaicorporation.gov.in/",
            helpline="GCC: 1913 / Urban Local Bodies: 1800-425-4788",
            authority_name="Assistant Engineer (Electrical) / Ward Office",
        ),
        requirements=ServiceRequirements(
            required_documents=["Ward / Zone Number", "Street Name & Landmark", "Lamp Post Number (if visible)"],
            target_groups=["Urban and rural residents", "Pedestrians", "Motorists"],
        ),
        workflow=ServiceWorkflow(
            submission_mode="assisted_handoff",
            api_available=False,
            requires_citizen_auth=True,
            auth_methods=["Mobile OTP", "Namma Chennai App Auth"],
            application_steps=[
                "Dhvaani formats the exact location, duration, and lamp post details.",
                "Proceed to GCC Portal or call 1913 toll-free.",
                "Provide the Dhvaani summary to the operator or paste into the web portal.",
                "Receive SMS with official GCC Complaint Reference Number.",
            ],
            estimated_resolution_days=5,
        ),
        verification=ServiceVerification(
            verification_status="verified",
            source_type="state_portal",
            source_url="https://www.chennaicorporation.gov.in",
            last_verified="2024-11-01",
            truthful_notes="Official grievance submission is protected by CAPTCHA/mobile OTP on the GCC portal.",
        ),
    ),
    "water": ServiceItem(
        identity=ServiceIdentity(
            service_id="grievance_water",
            official_name="Water Supply & Sewage Redressal",
            local_names={"hi": "जल आपूर्ति एवं सीवेज शिकायत", "ta": "குடிநீர் வழங்கல் & கழிவுநீர் குறைதீர்ப்பு"},
            service_type="grievance",
            category="water",
            department="Tamil Nadu Water Supply & Drainage (TWAD) Board / CMWSSB",
            ministry="Municipal Administration & Water Supply Department",
            jurisdiction="Tamil Nadu",
        ),
        official_info=ServiceOfficialInfo(
            portal_name="Tamil Nadu Grievance Redressal / MetroWater",
            portal_url="https://www.twadboard.tn.gov.in/",
            information_url="https://www.twadboard.tn.gov.in",
            application_url="https://cmhelpline.tnega.org/",
            status_tracking_url="https://cmhelpline.tnega.org/",
            helpline="TWAD Board: 1800-425-1530 / MetroWater: 044-45674567",
            authority_name="Executive Engineer (Water Supply)",
        ),
        requirements=ServiceRequirements(
            required_documents=["Water Connection Consumer No. (if individual connection)", "Locality/Street address", "Contact Phone"],
            target_groups=["Residents", "Communities experiencing water disruption"],
        ),
        workflow=ServiceWorkflow(
            submission_mode="assisted_handoff",
            api_available=False,
            requires_citizen_auth=True,
            auth_methods=["Citizen Portal Login / Mobile OTP"],
            application_steps=[
                "Dhvaani builds an urgent civic alert summary.",
                "Visit TN Grievance Portal or MetroWater 24/7 desk.",
                "Submit with your area and consumer details.",
                "Track using the official government reference number generated.",
            ],
            estimated_resolution_days=5,
        ),
        verification=ServiceVerification(
            verification_status="verified",
            source_type="state_portal",
            source_url="https://www.twadboard.tn.gov.in/",
            last_verified="2024-11-01",
            truthful_notes="Official portal requires TN e-Gov citizen authentication.",
        ),
    ),
    "road": ServiceItem(
        identity=ServiceIdentity(
            service_id="grievance_road",
            official_name="Public Works / Highway & Road Grievance",
            local_names={"hi": "सड़क एवं लोक निर्माण शिकायत", "ta": "சாலை & பொதுப்பணி குறைதீர்ப்பு"},
            service_type="grievance",
            category="road",
            department="Public Works Department (PWD) / Municipal Corporation",
            ministry="Ministry of Road Transport and Highways / State PWD",
            jurisdiction="India",
        ),
        official_info=ServiceOfficialInfo(
            portal_name="CPGRAMS / State PWD Portal",
            portal_url="https://pgportal.gov.in",
            information_url="https://morth.nic.in",
            application_url="https://pgportal.gov.in/Signin",
            status_tracking_url="https://pgportal.gov.in/Status",
            helpline="PWD Helpline: 1800-425-0086 / CPGRAMS: 1800-11-4000",
            authority_name="Executive Engineer (Highways/PWD)",
        ),
        requirements=ServiceRequirements(
            required_documents=["Road/Street Name", "Prominent Landmark", "Photo (recommended on portal)"],
            target_groups=["Road users", "Local residents"],
        ),
        workflow=ServiceWorkflow(
            submission_mode="assisted_handoff",
            api_available=False,
            requires_citizen_auth=True,
            auth_methods=["CPGRAMS Login / Mobile OTP"],
            application_steps=[
                "Dhvaani structures the pothole / road hazard report.",
                "Open CPGRAMS or State PWD portal.",
                "Paste the complaint and upload photos if requested.",
                "Save your central/state CPGRAMS registration number.",
            ],
            estimated_resolution_days=15,
        ),
        verification=ServiceVerification(
            verification_status="verified",
            source_type="central_portal",
            source_url="https://pgportal.gov.in",
            last_verified="2024-11-01",
            truthful_notes="CPGRAMS requires citizen registration and CAPTCHA.",
        ),
    ),
    "ration": ServiceItem(
        identity=ServiceIdentity(
            service_id="grievance_ration",
            official_name="Public Distribution System (PDS) / Ration Redressal",
            local_names={"hi": "राशन एवं नागरिक आपूर्ति शिकायत", "ta": "ரேஷன் & குடிமைப்பொருள் குறைதீர்ப்பு"},
            service_type="grievance",
            category="ration",
            department="Department of Food and Civil Supplies",
            ministry="Ministry of Consumer Affairs, Food and Public Distribution",
            jurisdiction="Tamil Nadu",
        ),
        official_info=ServiceOfficialInfo(
            portal_name="Tamil Nadu PDS Citizen Portal (TNPDS)",
            portal_url="https://www.tnpds.gov.in",
            information_url="https://www.tnpds.gov.in",
            application_url="https://www.tnpds.gov.in/pages/register-complaint.xhtml",
            status_tracking_url="https://www.tnpds.gov.in/pages/complaint-status.xhtml",
            helpline="Tamil Nadu Food Helpline: 1967 / 1800-425-5901",
            authority_name="Taluk Supply Officer (TSO) / DSO",
        ),
        requirements=ServiceRequirements(
            required_documents=["Smart Ration Card Number", "Ration Shop (FPS) Code", "Registered Mobile Number"],
            target_groups=["PDS cardholders", "BPL / AAY beneficiaries"],
        ),
        workflow=ServiceWorkflow(
            submission_mode="assisted_handoff",
            api_available=False,
            requires_citizen_auth=True,
            auth_methods=["Smart Ration Card No + OTP verification"],
            application_steps=[
                "Dhvaani prepares the PDS irregularity statement.",
                "Open TNPDS Register Complaint portal.",
                "Enter Smart Card No. and OTP sent to your registered phone.",
                "Submit and receive immediate TNPDS reference number.",
            ],
            estimated_resolution_days=7,
        ),
        verification=ServiceVerification(
            verification_status="verified",
            source_type="state_portal",
            source_url="https://www.tnpds.gov.in",
            last_verified="2024-11-01",
            truthful_notes="TNPDS citizen portal enforces registered mobile OTP verification.",
        ),
    ),
    "police": ServiceItem(
        identity=ServiceIdentity(
            service_id="grievance_police",
            official_name="Police Department / Public Grievance Portal",
            local_names={"hi": "पुलिस विभाग शिकायत", "ta": "காவல்துறை குறைதீர்ப்பு"},
            service_type="grievance",
            category="police",
            department="Tamil Nadu Police / State Police",
            ministry="Home Department",
            jurisdiction="Tamil Nadu",
        ),
        official_info=ServiceOfficialInfo(
            portal_name="Tamil Nadu Police Citizen Portal",
            portal_url="https://eservices.tnpolice.gov.in/",
            information_url="https://eservices.tnpolice.gov.in",
            application_url="https://eservices.tnpolice.gov.in/",
            status_tracking_url="https://eservices.tnpolice.gov.in/",
            helpline="Emergency: 100 / Women: 1091 / Child: 1098",
            authority_name="Station House Officer (SHO) / Superintendent of Police",
        ),
        requirements=ServiceRequirements(
            required_documents=["Aadhaar / ID Proof", "Incident date, time, and location", "Witness/Suspect details if known"],
            target_groups=["Citizens needing non-emergency police reporting"],
        ),
        workflow=ServiceWorkflow(
            submission_mode="assisted_handoff",
            api_available=False,
            requires_citizen_auth=True,
            auth_methods=["CCTNS Citizen Portal Login", "Mobile OTP"],
            application_steps=[
                "For emergencies, call 100 immediately.",
                "Dhvaani summarizes non-emergency civic/theft/missing incidents.",
                "Continue to TN Police CCTNS citizen portal to file a formal complaint/CSR.",
                "Obtain CSR (Community Service Register) number or FIR number.",
            ],
            estimated_resolution_days=1,
        ),
        verification=ServiceVerification(
            verification_status="verified",
            source_type="state_portal",
            source_url="https://eservices.tnpolice.gov.in/",
            last_verified="2024-11-01",
            truthful_notes="Legal FIR/CSR generation strictly requires citizen authentication on CCTNS.",
        ),
    ),
    "health": ServiceItem(
        identity=ServiceIdentity(
            service_id="grievance_health",
            official_name="Public Health & Hospital Services Redressal",
            local_names={"hi": "स्वास्थ्य एवं अस्पताल शिकायत", "ta": "பொது சுகாதாரம் & மருத்துவமனை குறைதீர்ப்பு"},
            service_type="grievance",
            category="health",
            department="Health and Family Welfare Department",
            ministry="Ministry of Health and Family Welfare",
            jurisdiction="Tamil Nadu",
        ),
        official_info=ServiceOfficialInfo(
            portal_name="Tamil Nadu Health Portal",
            portal_url="https://www.tnhealth.tn.gov.in",
            information_url="https://www.nhm.tn.gov.in",
            application_url="https://cmhelpline.tnega.org/",
            status_tracking_url="https://cmhelpline.tnega.org/",
            helpline="Medical Helpline: 104 / Emergency Ambulance: 108",
            authority_name="Joint Director of Health Services / PHC Medical Officer",
        ),
        requirements=ServiceRequirements(
            required_documents=["Hospital / PHC Name", "Date of Visit / Admission", "OP / IP Slip (if available)"],
            target_groups=["Patients and attendants at government hospitals / PHCs"],
        ),
        workflow=ServiceWorkflow(
            submission_mode="assisted_handoff",
            api_available=False,
            requires_citizen_auth=True,
            auth_methods=["Mobile OTP", "TN e-Gov Auth"],
            application_steps=[
                "For medical emergencies, dial 108 immediately.",
                "Dhvaani records service gaps (doctor absence, medicine unavailability).",
                "Submit through TN e-Grievance portal or 104 helpline.",
                "Retain the government complaint token for follow-up.",
            ],
            estimated_resolution_days=3,
        ),
        verification=ServiceVerification(
            verification_status="verified",
            source_type="state_portal",
            source_url="https://www.tnhealth.tn.gov.in",
            last_verified="2024-11-01",
            truthful_notes="Grievances regarding PHC/GH facilities are logged on state e-governance desk.",
        ),
    ),
    "municipal": ServiceItem(
        identity=ServiceIdentity(
            service_id="grievance_municipal",
            official_name="Municipal Sanitation, Garbage & Public Works",
            local_names={"hi": "नगर निगम स्वच्छता एवं कचरा शिकायत", "ta": "நகராட்சி சுகாதாரம் & குப்பை குறைதீர்ப்பு"},
            service_type="grievance",
            category="municipal",
            department="Municipal Corporation / Directorate of Municipal Administration",
            ministry="Department of Municipal Administration and Water Supply",
            jurisdiction="Municipal",
        ),
        official_info=ServiceOfficialInfo(
            portal_name="Greater Chennai Corporation / TN Urban Portals",
            portal_url="https://www.chennaicorporation.gov.in",
            information_url="https://www.chennaicorporation.gov.in/",
            application_url="https://www.chennaicorporation.gov.in/",
            status_tracking_url="https://www.chennaicorporation.gov.in/",
            helpline="GCC: 1913 / TN Urban Local Bodies: 1800-425-4788",
            authority_name="Zonal Officer / Sanitary Inspector",
        ),
        requirements=ServiceRequirements(
            required_documents=["Ward / Zone Number", "Street Address & Landmark", "Description of Sanitation issue"],
            target_groups=["All urban residents and business owners"],
        ),
        workflow=ServiceWorkflow(
            submission_mode="assisted_handoff",
            api_available=False,
            requires_citizen_auth=True,
            auth_methods=["Mobile OTP", "Citizen Portal Login"],
            application_steps=[
                "Dhvaani formats the sanitation issue with exact neighborhood details.",
                "Open municipal portal or dial 1913.",
                "Submit the pre-filled issue summary.",
                "Receive tracking SMS from the Municipal Corporation.",
            ],
            estimated_resolution_days=7,
        ),
        verification=ServiceVerification(
            verification_status="verified",
            source_type="state_portal",
            source_url="https://www.chennaicorporation.gov.in",
            last_verified="2024-11-01",
            truthful_notes="Municipal complaints routed through 1913/GCC portal with SMS verification.",
        ),
    ),
}


class ServiceCatalog:
    """Central authority catalog for all government services and schemes."""

    @classmethod
    def get_service(cls, service_id: str) -> Optional[ServiceItem]:
        """Look up a service by ID (schemes or grievances)."""
        # Check grievance services first
        clean_id = service_id.replace("grievance_", "")
        if clean_id in GRIEVANCE_SERVICES:
            return GRIEVANCE_SERVICES[clean_id]
        if service_id in GRIEVANCE_SERVICES:
            return GRIEVANCE_SERVICES[service_id]
        return None

    @classmethod
    def list_grievance_services(cls) -> List[Dict[str, Any]]:
        """List all verified grievance services."""
        return [svc.to_dict() for svc in GRIEVANCE_SERVICES.values()]

    @classmethod
    def get_submission_pathway(cls, category: str) -> Dict[str, Any]:
        """Get the legitimate official submission pathway for a category."""
        clean_cat = category.lower().replace("grievance_", "")
        svc = GRIEVANCE_SERVICES.get(clean_cat)
        if not svc:
            # Fallback to general municipal/CPGRAMS
            svc = GRIEVANCE_SERVICES["municipal"]
        
        return {
            "service_id": svc.identity.service_id,
            "department": svc.identity.department,
            "official_portal": svc.official_info.portal_url,
            "portal_name": svc.official_info.portal_name,
            "application_url": svc.official_info.application_url,
            "status_tracking_url": svc.official_info.status_tracking_url,
            "helpline": svc.official_info.helpline,
            "submission_mode": svc.workflow.submission_mode,
            "api_available": svc.workflow.api_available,
            "requires_citizen_auth": svc.workflow.requires_citizen_auth,
            "required_documents": svc.requirements.required_documents,
            "steps": svc.workflow.application_steps,
            "verification_status": svc.verification.verification_status,
            "source_url": svc.verification.source_url,
            "truthful_notes": svc.verification.truthful_notes,
        }
