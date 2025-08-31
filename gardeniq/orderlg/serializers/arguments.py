from rest_framework.serializers import ModelSerializer

from gardeniq.orderlg.models import Argument
from gardeniq.orderlg.models import Order


class ArgumentMinimalSerializer(ModelSerializer):
    class Meta:
        model = Argument
        fields = [
            "slug",
            "required",
            "is_option",
            "description",
        ]


class ArgumentSerializer(ArgumentMinimalSerializer):
    class Meta(ArgumentMinimalSerializer.Meta):
        fields = "__all__"


class OrderSerializer(ModelSerializer):
    arguments = ArgumentMinimalSerializer(many=True)

    class Meta:
        model = Order
        fields = "__all__"
