import uuid
from unittest.mock import patch, MagicMock
from django.test import TestCase

# Import the signal binding function
from api_fhir_r4.signals import bind_service_signals

class TestClaimSubscriptionSignal(TestCase):

    @patch('api_fhir_r4.signals.imis_modules', ['claim'])
    @patch('api_fhir_r4.signals.R4ClaimConfig.get_subscribe_claim_signal')
    @patch('api_fhir_r4.signals.bind_service_signal')
    @patch('api_fhir_r4.signals.notify_subscribers')
    @patch('api_fhir_r4.signals.User.objects.get')
    def test_claim_create_or_update_signal(
            self, mock_user_get, mock_notify, mock_bind_service_signal, mock_get_config
    ):
        # 1. Setup mocks
        mock_get_config.return_value = True
        
        # Create a dummy user
        dummy_user = MagicMock()
        dummy_user.username = "testadmin"
        mock_user_get.return_value = dummy_user

        # Create a dummy claim model
        dummy_model = MagicMock()
        dummy_model.uuid = uuid.uuid4()

        # 2. Call bind_service_signals, which should register the claim signal handler
        bind_service_signals()

        # Check that bind_service_signal was called for 'claim.enter_and_submit_claim'
        # and capture the handler function
        claim_handler = None
        for call_args in mock_bind_service_signal.call_args_list:
            if call_args[0][0] == 'claim.enter_and_submit_claim':
                claim_handler = call_args[0][1]
                break

        self.assertIsNotNone(claim_handler, "Signal handler for claim.enter_and_submit_claim was not bound")

        # 3. Simulate firing the signal by calling the handler directly
        kwargs = {
            'result': dummy_model,
            'data': [[{'admin_id': 123}]]
        }
        claim_handler(**kwargs)

        # 4. Assert the user was fetched with the correct admin_id
        mock_user_get.assert_called_once_with(claim_admin_id=123)

        # 5. Assert notify_subscribers was called correctly
        mock_notify.assert_called_once()
        args, kwargs = mock_notify.call_args
        self.assertEqual(args[0], dummy_model)
        # Verify the converter is a ClaimResponseConverter
        self.assertEqual(args[1].__class__.__name__, 'ClaimResponseConverter')
        self.assertEqual(args[2], 'Claim')
        self.assertIsNone(args[3])
