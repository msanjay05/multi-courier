from logistics.couriers.urbanebolt import UrbaneBoltAdapter
from logistics.couriers.mock_courier import MockCourierAdapter


class CourierRegistry:
    def __init__(self):
        self._adapters = {}

    def register(self, adapter_class):
        adapter = adapter_class()
        self._adapters[adapter.code] = adapter

    def get(self, courier_partner):
        return self._adapters.get(courier_partner)

    def supported(self):
        return sorted(self._adapters.keys())


registry = CourierRegistry()
registry.register(UrbaneBoltAdapter)
registry.register(MockCourierAdapter)
