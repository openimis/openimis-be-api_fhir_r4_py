import logging
from typing import Union

from django.http.response import HttpResponseBase
from fhir.resources.R4B import FHIRAbstractModel
from rest_framework import serializers

from api_fhir_r4.configurations import GeneralConfiguration, R4IssueTypeConfig
from api_fhir_r4.converters import (
    BaseFHIRConverter,
    OperationOutcomeConverter,
    ReferenceConverterMixin,
)
from core.models import User, TechnicalUser

try:
    from sentry_sdk import capture_exception
except ImportError:  # sentry_sdk is optional (see sentry-requirements.txt)
    def capture_exception(_exception):
        """No-op when sentry_sdk is not installed."""
        return None


logger = logging.getLogger(__name__)


class BaseFHIRSerializer(serializers.Serializer):
    fhirConverter = BaseFHIRConverter
    user = None

    def __init__(self, *args, user=None, **kwargs):
        self._reference_type = kwargs.pop(
            "reference_type", ReferenceConverterMixin.UUID_REFERENCE_TYPE
        )
        if user:
            self.user = user
        else:
            context = kwargs.get("context", None)
            if context and hasattr(context, "user"):
                self.user = context.user
        super().__init__(*args, **kwargs)

    def to_representation(self, obj):
        try:
            if isinstance(obj, HttpResponseBase):
                return OperationOutcomeConverter.to_fhir_obj(obj).dict()
            elif isinstance(obj, FHIRAbstractModel):
                return obj.dict()
            return (
                self.fhirConverter(user=self.user)
                .to_fhir_obj(obj, self.reference_type)
                .dict()
            )
        except Exception as e:
            from django.conf import settings

            if settings.DEBUG:
                self._print_debug_log(e)
            if isinstance(self.parent, serializers.ListSerializer):
                return self._unrenderable_entry(obj, e)
            raise e

    def _unrenderable_entry(self, obj, error):
        """
        In a list, a record that can't be converted (e.g. an invoice whose type
        isn't mapped) used to fail the whole Bundle with a 500. It is reported to
        Sentry and rendered as an OperationOutcome in its place, so the Bundle's
        total and paging still count it (OP-3254).
        """
        record = f"{type(obj).__name__} {getattr(obj, 'pk', '')}".strip()
        capture_exception(error)
        logger.exception("FHIR list: %s could not be rendered", record)
        outcome = OperationOutcomeConverter.build_outcome(
            "error",
            R4IssueTypeConfig.get_fhir_code_for_exception(),
            details_text=f"{record} could not be rendered: {type(error).__name__}: {error}",
        ).dict()
        if getattr(obj, "pk", None) is not None:
            outcome["id"] = str(obj.pk)
        return outcome

    def to_internal_value(self, data):
        audit_user_id = self.get_audit_user_id()
        imis_obj = self.fhirConverter(user=self.user).to_imis_obj(data, audit_user_id)
        # Filter out special attributes
        return {
            k: v
            for k, v in imis_obj.__dict__.items()
            if not k.startswith("_") and v is not None
        }

    def create(self, validated_data):
        raise NotImplementedError("`create()` must be implemented.")  # pragma: no cover

    def update(self, instance, validated_data):
        raise NotImplementedError("`update()` must be implemented.")  # pragma: no cover

    def get_audit_user_id(self):
        # the audit user is the user
        if self.user:
            return self.user.id_for_audit or -1
        audit_user_id = GeneralConfiguration.get_default_audit_user_id()
        if isinstance(audit_user_id, int):
            return audit_user_id
        else:
            raise ValueError("User not available from the request for audit trail")
            # return self.__get_technical_audit_user(audit_user_id)

    @property
    def reference_type(self):
        return self._reference_type

    @reference_type.getter
    def reference_type(self):
        return self._reference_type

    @reference_type.setter
    def reference_type(
        self,
        reference_type: Union[
            ReferenceConverterMixin.UUID_REFERENCE_TYPE,
            ReferenceConverterMixin.CODE_REFERENCE_TYPE,
            ReferenceConverterMixin.DB_ID_REFERENCE_TYPE,
        ],
    ):
        self._reference_type = reference_type

    def __get_technical_audit_user(self, technical_user_uuid):
        technical_user = TechnicalUser.objects.get(id=technical_user_uuid)
        core_user = User.objects.filter(t_user=technical_user_uuid).first()
        interactive_user = core_user.i_user
        return interactive_user.id if interactive_user else technical_user.id_for_audit

    def _print_debug_log(self, e):
        import traceback

        debug_log = (
            "FHIR Mapping for Serializer {self} has failed with exception {e}. Traceback: \n"
            + str(traceback.format_stack())
        )
        logger.debug(debug_log)
