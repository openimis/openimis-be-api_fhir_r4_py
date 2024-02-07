from copy import deepcopy
from urllib import parse
import datetime
from fhir.resources.R4B.subscription import Subscription as FHIRSubscription

from api_fhir_r4.configurations import R4SubscriptionConfig
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from api_fhir_r4.exceptions import FHIRException
from api_fhir_r4.mapping.subscriptionMapping import SubscriptionChannelMapping, SubscriptionStatusMapping
from api_fhir_r4.models import Subscription
from api_fhir_r4.utils import TimeUtils


class SubscriptionConverter(BaseFHIRConverter):
    _error_unknown_imis_value = f'Unknown imis `%(attr)s`: %(val)s'
    _error_invalid_attr = f'Missing or invalid `%(attr)s` attribute'
    _error_forbidden_attr = f'`%(attr)s` attribute forbidden'

    @classmethod
    def to_fhir_obj(cls, imis_subscription, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_subscription = {}
        cls._build_fhir_id(fhir_subscription, imis_subscription)
        cls._build_fhir_status(fhir_subscription, imis_subscription)
        cls._build_fhir_end(fhir_subscription, imis_subscription)
        cls._build_fhir_reason(fhir_subscription, imis_subscription)
        cls._build_fhir_criteria(fhir_subscription, imis_subscription)
        cls._build_fhir_error(fhir_subscription, imis_subscription)
        cls._build_fhir_channel(fhir_subscription, imis_subscription)
        return FHIRSubscription.parse_obj(fhir_subscription)

    @classmethod
    def to_imis_obj(cls, fhir_subscription, audit_user_id):
        fhir_subscription = FHIRSubscription.parse_obj(fhir_subscription)
        imis_subscription = {}
        cls._build_imis_id(imis_subscription, fhir_subscription)
        cls._build_imis_status(imis_subscription, fhir_subscription)
        cls._build_imis_end(imis_subscription, fhir_subscription)
        cls._build_imis_criteria(imis_subscription, fhir_subscription)
        cls._validate_fhir_error(fhir_subscription)
        cls._build_imis_channel_type(imis_subscription, fhir_subscription)
        cls._build_imis_channel_endpoint(imis_subscription, fhir_subscription)
        cls._build_imis_channel_header(imis_subscription, fhir_subscription)
        return Subscription(**imis_subscription)

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return FHIRException("Subscription resource does not contain code identifier")

    @classmethod
    def _build_fhir_id(cls, fhir_subscription, imis_subscription):
        fhir_subscription['id'] = str(imis_subscription.id)

    @classmethod
    def _build_fhir_status(cls, fhir_subscription, imis_subscription):
        if imis_subscription.status in SubscriptionStatusMapping.to_fhir_status:
            fhir_subscription['status'] = SubscriptionStatusMapping.to_fhir_status[imis_subscription.status]
        else:
            raise FHIRException(
                cls._error_unknown_imis_value % {'attr': 'status', 'val': str(imis_subscription.status)})

    @classmethod
    def _build_fhir_end(cls, fhir_subscription, imis_subscription):
        date = imis_subscription.expiring.astimezone().isoformat()
        fhir_subscription['end'] = date

    @classmethod
    def _build_fhir_reason(cls, fhir_subscription, imis_subscription):
        fhir_subscription['reason'] = \
            imis_subscription.criteria[R4SubscriptionConfig.get_fhir_sub_criteria_key_resource()]

    @classmethod
    def _build_fhir_criteria(cls, fhir_subscription, imis_subscription):
        criteria = deepcopy(imis_subscription.criteria)
        resource = criteria.pop(R4SubscriptionConfig.get_fhir_sub_criteria_key_resource())
        resource_type = criteria.pop(R4SubscriptionConfig.get_fhir_sub_criteria_key_resource_type(), None)
        if resource_type:
            criteria['resourceType'] = resource_type
        fhir_subscription['criteria'] = \
            parse.urlunparse(('', '', resource, '', parse.urlencode(criteria, doseq=True), ''))

    @classmethod
    def _build_fhir_error(cls, fhir_subscription, imis_subscription):
        error = None  # TODO Add that after the error logging is added to the model
        if error:
            fhir_subscription['error'] = error

    @classmethod
    def _build_fhir_channel(cls, fhir_subscription, imis_subscription):
        fhir_channel = {}
        cls._build_fhir_channel_type(fhir_channel, imis_subscription)
        cls._build_fhir_channel_endpoint(fhir_channel, imis_subscription)
        cls._build_fhir_channel_header(fhir_channel, imis_subscription)
        fhir_subscription['channel'] = fhir_channel

    @classmethod
    def _build_fhir_channel_type(cls, fhir_channel, imis_subscription):
        if imis_subscription.channel in SubscriptionChannelMapping.to_fhir_channel:
            fhir_channel['type'] = SubscriptionChannelMapping.to_fhir_channel[imis_subscription.channel]
        else:
            raise FHIRException(
                cls._error_unknown_imis_value % {'attr': 'channel', 'val': str(imis_subscription.channel)})

    @classmethod
    def _build_fhir_channel_endpoint(cls, fhir_channel, imis_subscription):
        fhir_channel['endpoint'] = imis_subscription.endpoint

    @classmethod
    def _build_fhir_channel_header(cls, fhir_channel, imis_subscription):
        fhir_channel['header'] = [imis_subscription.headers]

    @classmethod
    def _build_imis_id(cls, imis_subscription, fhir_subscription):
        if fhir_subscription.id:
            imis_subscription['id'] = fhir_subscription.id

    @classmethod
    def _build_imis_status(cls, imis_subscription, fhir_subscription):
        if fhir_subscription.status and fhir_subscription.status in SubscriptionStatusMapping.to_imis_status:
            imis_subscription['status'] = SubscriptionStatusMapping.to_imis_status[fhir_subscription.status]
        else:
            raise FHIRException(cls._error_invalid_attr % {'attr': 'status'})

    @classmethod
    def _build_imis_end(cls, imis_subscription, fhir_subscription):
        if fhir_subscription.end:
            imis_subscription['expiring'] = TimeUtils.str_iso_to_date(fhir_subscription.end).astimezone(
                datetime.timezone.utc)
        else:
            raise FHIRException(cls._error_invalid_attr % {'attr': 'end'})

    @classmethod
    def _build_imis_criteria(cls, imis_subscription, fhir_subscription):
        if fhir_subscription.criteria:
            parsed_criteria = parse.urlparse(fhir_subscription.criteria)
            imis_criteria = dict(parse.parse_qsl(parsed_criteria.query))
            resource_type = imis_criteria.pop('resourceType', None)
            if resource_type:
                imis_criteria[R4SubscriptionConfig.get_fhir_sub_criteria_key_resource_type()] = resource_type
            imis_criteria[R4SubscriptionConfig.get_fhir_sub_criteria_key_resource()] = parsed_criteria.path.strip('/')
            imis_subscription['criteria'] = imis_criteria
            cls._validate_fhir_reason(imis_subscription, fhir_subscription)
        else:
            raise FHIRException(cls._error_invalid_attr % {'attr': 'criteria'})

    @classmethod
    def _validate_fhir_reason(cls, imis_subscription, fhir_subscription):
        # there is no imis reason so validation only
        if 'criteria' not in imis_subscription:
            raise FHIRException(cls._error_invalid_attr % {'attr': 'criteria'})
        if fhir_subscription.reason.lower() \
                != imis_subscription['criteria'][R4SubscriptionConfig.get_fhir_sub_criteria_key_resource()].lower():
            raise FHIRException(cls._error_invalid_attr % {'attr': 'reason'})

    @classmethod
    def _validate_fhir_error(cls, fhir_subscription):
        # there should not be error attribute in fhir input
        if fhir_subscription.error:
            raise FHIRException(cls._error_forbidden_attr % {'attr': 'error'})

    @classmethod
    def _build_imis_channel_type(cls, imis_subscription, fhir_subscription):
        if fhir_subscription.channel.type \
                and fhir_subscription.channel.type in SubscriptionChannelMapping.to_imis_channel:
            imis_subscription['channel'] = SubscriptionChannelMapping.to_imis_channel[fhir_subscription.channel.type]
        else:
            raise FHIRException(cls._error_invalid_attr % {'attr': 'channel.type'})

    @classmethod
    def _build_imis_channel_endpoint(cls, imis_subscription, fhir_subscription):
        if fhir_subscription.channel.endpoint:
            imis_subscription['endpoint'] = str(fhir_subscription.channel.endpoint)
        else:
            raise FHIRException(cls._error_invalid_attr % {'attr': 'channel.endpoint'})

    @classmethod
    def _build_imis_channel_header(cls, imis_subscription, fhir_subscription):
        if fhir_subscription.channel.header:
            imis_subscription['headers'] = fhir_subscription.channel.header[0]
