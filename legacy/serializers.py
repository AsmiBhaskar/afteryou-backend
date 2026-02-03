from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import LegacyMessage

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'bio']
        read_only_fields = ['id']

class LegacyMessageSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        # Only update fields present in validated_data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    id = serializers.CharField(read_only=True)
    title = serializers.CharField()
    content = serializers.CharField()
    recipient_email = serializers.EmailField()
    delivery_date = serializers.DateTimeField()
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    sent_at = serializers.DateTimeField(allow_null=True, required=False, read_only=True)
    user_email = serializers.CharField(source='user_id', read_only=True)
    job_id = serializers.CharField(allow_null=True, required=False, read_only=True)
    
    # Chain fields
    parent_message = serializers.CharField(allow_null=True, required=False, read_only=True)
    chain_id = serializers.CharField(read_only=True)
    generation = serializers.IntegerField(read_only=True)
    sender_name = serializers.CharField(allow_null=True, required=False, read_only=True)
    recipient_access_token = serializers.CharField(read_only=True)

    def to_representation(self, instance):
        data = {
            'id': str(instance.id),
            'title': instance.title,
            'content': instance.content,
            'recipient_email': instance.recipient_email,
            'delivery_date': instance.delivery_date.isoformat() if instance.delivery_date else None,
            'status': instance.status,
            'created_at': instance.created_at.isoformat() if instance.created_at else None,
            'sent_at': instance.sent_at.isoformat() if instance.sent_at else None,
            'user_email': getattr(instance, 'user_id', None),
            'job_id': getattr(instance, 'job_id', None),
            'parent_message': str(instance.parent_message.id) if instance.parent_message else None,
            'chain_id': str(instance.chain_id) if instance.chain_id else None,
            'generation': getattr(instance, 'generation', 1),
            'sender_name': getattr(instance, 'sender_name', None),
            'recipient_access_token': str(instance.recipient_access_token) if instance.recipient_access_token else None,
        }
        return data

class LegacyMessageCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    content = serializers.CharField(allow_blank=True)
    recipient_email = serializers.EmailField()
    delivery_date = serializers.DateTimeField()

    def validate_delivery_date(self, value):
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError("Delivery date must be in the future.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        message = LegacyMessage(
            user_id=str(user.id),
            title=validated_data['title'],
            content=validated_data['content'],
            recipient_email=validated_data['recipient_email'],
            delivery_date=validated_data['delivery_date'],
            status='created'
        )
        message.save()
        return message

    def to_representation(self, instance):
        """Return the full message data including ID after creation"""
        return {
            'id': str(instance.id),
            'title': instance.title,
            'content': instance.content,
            'recipient_email': instance.recipient_email,
            'delivery_date': instance.delivery_date.isoformat() if instance.delivery_date else None,
            'status': instance.status,
            'created_at': instance.created_at.isoformat() if instance.created_at else None,
            'chain_id': str(instance.chain_id) if instance.chain_id else None,
            'generation': getattr(instance, 'generation', 1),
            'recipient_access_token': str(instance.recipient_access_token) if instance.recipient_access_token else None,
        }
