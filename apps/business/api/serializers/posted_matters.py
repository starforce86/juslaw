from django.core.exceptions import ValidationError

from rest_framework import serializers

from apps.core.api.serializers import BaseSerializer
from apps.forums.api.serializers import PracticeAreaSerializer
from apps.forums.models import ForumPracticeAreas
from apps.users.api.serializers import (
    AppUserWithoutTypeSerializer,
    AttorneyOverviewSerializer,
    ClientInfoSerializer,
    CurrenciesSerializer,
)

from ...models import PostedMatter, Proposal


class ProposalShortSerializer(BaseSerializer):
    """Serializes attorney proposals on posted matters"""
    name = serializers.CharField(
        source='attorney.user.full_name',
        read_only=True
    )
    attorney_data = AppUserWithoutTypeSerializer(
        source='attorney.user',
        read_only=True
    )
    currency_data = CurrenciesSerializer(
        source='currency',
        read_only=True
    )

    class Meta:
        model = Proposal
        fields = (
            'id',
            'name',
            'created',
            'rate',
            'rate_type',
            'description',
            'attorney_data',
            'status',
            'status_modified',
            'currency',
            'currency_data',
            'is_hidden_for_client',
            'is_hidden_for_attorney',
        )


class ProposalSerializer(BaseSerializer):
    """Serializes attorney proposals on posted matters"""
    name = serializers.CharField(
        source='attorney.user.full_name',
        read_only=True
    )
    post = serializers.PrimaryKeyRelatedField(
        queryset=PostedMatter.objects.all(),
        write_only=True
    )
    attorney_data = AttorneyOverviewSerializer(
        source='attorney', read_only=True
    )
    currency_data = CurrenciesSerializer(
        source='currency',
        read_only=True
    )

    def validate(self, attrs):
        if not hasattr(self.user, 'attorney'):
            raise ValidationError('Only attorney can submit proposal')
        if attrs['post'].status == PostedMatter.STATUS_INACTIVE:
            raise ValidationError('Engagement is inactive')
        attrs['attorney'] = self.user.attorney
        return super().validate(attrs)

    class Meta:
        model = Proposal
        fields = (
            'id',
            'name',
            'created',
            'rate',
            'description',
            'rate_type',
            'rate_detail',
            'post',
            'attorney',
            'attorney_data',
            'status',
            'status_modified',
            'post_id',
            'currency',
            'currency_data',
            'is_hidden_for_client',
            'is_hidden_for_attorney',
        )
        read_only_fields = (
            'id',
            'name',
            'created',
            'status',
            'post_id'
        )
        extra_kwargs = {
            'attorney': {
                'required': False
            },
            'rate_detail': {
                'required': False
            },
            'currency': {
                'required': False
            },
        }


class PostedMatterSerializer(BaseSerializer):
    """Serializes matters posted by client."""
    budget_min = serializers.CharField(required=False, allow_blank=True)
    proposals = serializers.SerializerMethodField(read_only=True)
    practice_area_data = PracticeAreaSerializer(
        source='practice_area', read_only=True
    )
    client_data = ClientInfoSerializer(source='client', read_only=True)
    currency_data = CurrenciesSerializer(source='currency', read_only=True)

    def get_proposals(self, obj):
        """
        Returns only attorney proposals if authenticated user
        is attorney else all proposals on the posted matter
        """
        proposals = []
        if self.context.get('request'):
            attorney = getattr(
                self.context.get('request').user,
                'attorney',
                None
            )
            if attorney:
                for proposal in obj.proposals.all():
                    if proposal.attorney == attorney and \
                            proposal.status != 'withdrawn':
                        proposals.append(proposal)
        if not proposals:
            for proposal in obj.proposals.all():
                if proposal.status != 'withdrawn':
                    proposals.append(proposal)
        return ProposalShortSerializer(proposals, many=True).data

    def validate(self, attrs):
        if not hasattr(self.user, 'client'):
            raise ValidationError('Can not post matter')
        attrs['client'] = self.user.client
        return super().validate(attrs)

    class Meta:
        model = PostedMatter
        fields = (
            'id',
            'title',
            'description',
            'budget_min',
            'budget_max',
            'budget_type',
            'budget_detail',
            'practice_area',
            'created',
            'proposals',
            'client',
            'client_data',
            'practice_area_data',
            'currency',
            'currency_data',
            'status',
            'status_modified',
            'is_hidden_for_client',
            'is_hidden_for_attorney',
        )
        read_only_fields = (
            'status',
            'status_modified',
            'currency_data'
        )
        extra_kwargs = {
            'client': {
                'required': False
            },
            'budget_detail': {
                'required': False
            }
        }


class PostedMatterShortSerializer(BaseSerializer):
    """Serializes matters posted by client."""

    client_data = ClientInfoSerializer(source='client', read_only=True)
    practice_area_data = PracticeAreaSerializer(
        source='practice_area',
        read_only=True
    )

    class Meta:
        model = PostedMatter
        fields = (
            'id',
            'title',
            'description',
            'budget_min',
            'budget_max',
            'budget_type',
            'budget_detail',
            'practice_area',
            'practice_area_data',
            'created',
            'client',
            'client_data',
            'status',
            'is_hidden_for_client',
            'is_hidden_for_attorney',
        )


class PostedMattersByPracticeAreaSerializer(BaseSerializer):
    """Serializes posted matters by practice area."""
    posted_matters_count = serializers.SerializerMethodField(read_only=True)
    posted_matters = serializers.SerializerMethodField(read_only=True)
    last_posted = serializers.SerializerMethodField(read_only=True)
    latest_posted_matter_created = serializers.SerializerMethodField(
        read_only=True
    )

    def get_latest_posted_matter_created(self, obj):
        if obj.posted_matter.count():
            return obj.posted_matter.all()[0].created

    def get_posted_matters(self, obj):
        return PostedMatterSerializer(
            obj.posted_matter.all(),
            read_only=True,
            many=True,
            context=self.context
        ).data

    def get_posted_matters_count(self, obj):
        return obj.posted_matter.count()

    def get_last_posted(self, obj):
        objs = obj.posted_matter.all()
        if len(objs) > 0:
            return objs[0].created
        else:
            return None

    class Meta:
        model = ForumPracticeAreas
        fields = (
            'id',
            'title',
            'description',
            'last_posted',
            'posted_matters_count',
            'posted_matters',
            'created',
            'latest_posted_matter_created'
        )
        read_only_fields = (
            'created',
        )


class AttorneyProposalSerializer(BaseSerializer):
    """Serializes attorney proposals"""
    post_data = PostedMatterShortSerializer(source='post', read_only=True)
    currency = CurrenciesSerializer(
        source='attorney.fee_currency',
        read_only=True
    )

    class Meta:
        model = Proposal
        fields = (
            'id',
            'rate',
            'rate_type',
            'description',
            'created',
            'post_data',
            'currency',
            'status',
            'status_modified',
            'is_hidden_for_client',
            'is_hidden_for_attorney',
        )
