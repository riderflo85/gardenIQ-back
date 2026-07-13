from rest_framework import serializers

from gardeniq.base.serializers import BaseSerializer
from gardeniq.base.serializers import NameMixinSerializer
from gardeniq.base.serializers import OptionalDescriptionMixinSerializer
from gardeniq.base.serializers import ReadOnlySerializer
from gardeniq.base.serializers.mixins import PKMixinSerializer
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import Pin

from .device import DeviceMinimalReadOnlySerializer


class ChannelSerializer(BaseSerializer, NameMixinSerializer, OptionalDescriptionMixinSerializer):
    class Meta:
        model = Channel


class ChannelReadOnlySerializer(ReadOnlySerializer, ChannelSerializer):
    pass


class PinSerializer(BaseSerializer):
    device = serializers.PrimaryKeyRelatedField(queryset=Device.objects.all())
    channel_choiced = serializers.PrimaryKeyRelatedField(queryset=Channel.objects.all())
    channels_available = serializers.PrimaryKeyRelatedField(queryset=Channel.objects.all(), many=True)
    pin_number = serializers.IntegerField()

    class Meta:
        model = Pin


class PinDetailReadOnlySerializer(ReadOnlySerializer, PinSerializer):
    channel_choiced = ChannelReadOnlySerializer(read_only=True)
    channels_available = ChannelReadOnlySerializer(many=True, read_only=True)
    device = DeviceMinimalReadOnlySerializer(read_only=True)


class PinMinimalReadOnlySerializer(ReadOnlySerializer, PKMixinSerializer):
    pin_number = serializers.IntegerField(read_only=True)
    channel_choiced = serializers.CharField(source="channel_choiced.name", read_only=True)
