from django.contrib.auth import get_user_model
from rest_framework import serializers

from documents.models import Document
from notifications.models import Notification
from organizations.models import Organization

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")
        read_only_fields = ("id", "username", "email")


class OrganizationSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ("id", "name", "slug", "role")

    def get_role(self, obj):
        request = self.context.get("request")
        return obj.get_role(request.user) if request else None


class DocumentSerializer(serializers.ModelSerializer):
    # Write tags as a list of names; they are rendered back in to_representation.
    tags = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)

    class Meta:
        model = Document
        fields = ("id", "title", "description", "file", "tags", "created_at")
        read_only_fields = ("id", "created_at")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["tags"] = [t.name for t in instance.tags.all()]
        return data

    def _save_tags(self, instance, tags):
        if tags is not None:
            instance.tags.set(tags, clear=True)

    def create(self, validated_data):
        tags = validated_data.pop("tags", None)
        instance = super().create(validated_data)
        self._save_tags(instance, tags)
        return instance

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        instance = super().update(instance, validated_data)
        self._save_tags(instance, tags)
        return instance


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id", "verb", "url", "unread", "created_at")
        read_only_fields = fields
