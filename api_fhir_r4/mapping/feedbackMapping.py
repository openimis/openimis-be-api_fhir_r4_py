from claim.models import Claim


class FeedbackStatus(object):
    
    @classmethod
    def map_status(cls, code):
        codes = {
            Claim.FEEDBACK_SELECTED: "active",
            Claim.FEEDBACK_DELIVERED: "completed",
            Claim.FEEDBACK_BYPASSED: "revoked",
        }
        return codes.get(code, "unknown")

    @classmethod
    def map_code_display(cls, code):
        codes = {
            Claim.FEEDBACK_SELECTED: "Selected",
            Claim.FEEDBACK_DELIVERED: "Delivered",
            Claim.FEEDBACK_BYPASSED: "Bypassed",
        }
        return codes.get(code, 'Unknown')
