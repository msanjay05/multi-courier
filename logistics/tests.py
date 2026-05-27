from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch

from logistics.couriers.base import CourierCreateResponse
from logistics.models import Shipment


def order_payload(order_id='ORD-1', courier_partner='urbanebolt'):
    address = {
        'name': 'Sanjay',
        'phone': '9999999999',
        'line1': 'MG Road',
        'city': 'Bengaluru',
        'state': 'KA',
        'postal_code': '560001',
        'country': 'IN',
    }
    return {
        'order_id': order_id,
        'courier_partner': courier_partner,
        'pickup_address': address,
        'drop_address': {**address, 'name': 'Customer'},
        'parcels': [{'weight_kg': '1.20', 'description': 'Books', 'declared_value': '500.00'}],
        'payment_method': 'PREPAID',
    }


class AuthTests(APITestCase):
    def test_signup_returns_jwt_tokens(self):
        response = self.client.post('/api/v1/auth/signup/', {
            'username': 'demo',
            'email': 'demo@example.com',
            'password': 'strong-pass-123',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])


class ShipmentApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='demo', password='strong-pass-123')
        self.access_token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_create_order_is_idempotent_per_user_order_id(self):
        courier_response = CourierCreateResponse(
            courier_order_id='UEB-1',
            awb_number='200000001170',
            status='CREATED',
            courier_request_payload={'manifest': []},
            courier_response_payload={'awb': '200000001170'},
        )

        with patch('logistics.couriers.urbanebolt.UrbaneBoltAdapter.create_order', return_value=courier_response):
            first = self.client.post('/api/v1/orders/', order_payload(), format='json')
            second = self.client.post('/api/v1/orders/', order_payload(), format='json')

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.data['idempotent'])
        self.assertEqual(Shipment.objects.count(), 1)

    def test_unknown_courier_returns_supported_couriers(self):
        response = self.client.post('/api/v1/orders/', order_payload(courier_partner='delhivery'), format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error']['code'], 'UNKNOWN_COURIER')
        self.assertEqual(response.data['error']['details']['supported_couriers'], ['urbanebolt'])

    def test_unauthenticated_order_request_is_rejected(self):
        self.client.credentials()
        response = self.client.post('/api/v1/orders/', order_payload(), format='json')

        self.assertEqual(response.status_code, 401)
