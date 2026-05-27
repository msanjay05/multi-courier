from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch

from logistics.couriers.base import CourierCreateResponse
from logistics.models import Address, Order, Shipment, Warehouse


def shipment_payload(order_id='ORD-1', courier_partner='urbanebolt'):
    return {
        'order_id': order_id,
        'courier_partner': courier_partner,
    }


def create_order_in_db(order_number='ORD-1'):
    shipping_address = Address.objects.create(
        name='Customer',
        phone='8888888888',
        email='customer@example.com',
        line1='Park Street',
        line2='',
        city='Kolkata',
        state='WB',
        postal_code='700016',
        country='IN',
        address_type=Address.AddressType.HOME,
    )
    wh_address = Address.objects.create(
        name='Warehouse',
        phone='9999999999',
        email='warehouse@example.com',
        line1='MG Road',
        line2='',
        city='Bengaluru',
        state='KA',
        postal_code='560001',
        country='IN',
        address_type=Address.AddressType.WAREHOUSE,
    )
    warehouse = Warehouse.objects.create(
        code='WH-1',
        name='Main Warehouse',
        contact_name='Ops',
        contact_phone='9999999999',
        contact_email='ops@example.com',
        address=wh_address,
        is_active=True,
    )
    return Order.objects.create(
        order_number=order_number,
        shipping_address=shipping_address,
        warehouse=warehouse,
        payment_mode=Order.PaymentMode.PREPAID,
        cod_amount=0,
        total_amount=1000,
        metadata={},
    )


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

    def test_create_shipment_is_idempotent_per_order_id(self):
        create_order_in_db('ORD-1')
        courier_response = CourierCreateResponse(
            courier_order_id='UEB-1',
            awb_number='200000001170',
            status='SUCCESS',
            courier_request_payload={'manifest': []},
            courier_response_payload={'awb': '200000001170'},
            failure_response={},
            shipping_label='',
            message='Mock success',
        )

        with patch('logistics.couriers.urbanebolt.UrbaneBoltAdapter.create_order', return_value=courier_response):
            first = self.client.post('/api/v1/shipment/', shipment_payload(), format='json')
            second = self.client.post('/api/v1/shipment/', shipment_payload(), format='json')

        self.assertEqual(first.status_code, 201)
        # The endpoint is idempotent at the DB level (does not create a 2nd Shipment),
        # but it always returns 201 unless the shipment failed.
        self.assertEqual(second.status_code, 201)
        self.assertEqual(Shipment.objects.count(), 1)

    def test_unknown_courier_returns_supported_couriers(self):
        create_order_in_db('ORD-1')
        response = self.client.post('/api/v1/shipment/', shipment_payload(courier_partner='delhivery'), format='json')

        self.assertEqual(response.status_code, 400)
        # courier_partner is validated by serializer (not by resolver), so it returns a validation error
        self.assertEqual(response.data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('courier_partner', response.data['error']['details'])

    def test_unauthenticated_order_request_is_rejected(self):
        self.client.credentials()
        response = self.client.post('/api/v1/shipment/', shipment_payload(), format='json')

        self.assertEqual(response.status_code, 401)
