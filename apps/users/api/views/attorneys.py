from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from django.db.models.query import Prefetch
from django.http.response import Http404
from django.shortcuts import get_object_or_404

from rest_framework import generics, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.business.api.serializers.external_overview import (
    AttorneyDetailedOverviewSerializer,
    LeadAndClientSerializer,
)
from apps.business.api.serializers.posted_matters import (
    AttorneyProposalSerializer,
)
from apps.business.models import PostedMatter, Proposal
from apps.business.models.matter import Lead, Matter
from apps.core.api.views import BaseViewSet
from apps.finance.services import stripe_subscriptions_service
from apps.social.models import Chats
from apps.users import services

from ...api import permissions, serializers
from ...models import Attorney, Client, Invite
from ..filters import (
    AttorneyFilter,
    IndustryContactsSearchFilter,
    IndustryContactsTypeFilter,
    LeadClientFilter,
    LeadClientSearchFilter,
)
from ..serializers.industry_contacts import (
    IndustryContactAttorneyDetails,
    IndustryContactParalegalDetails,
    IndustryContactSerializer,
)
from .utils.verification import complete_signup


class AttorneyViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """View for registration and search of attorneys.


    Endpoint for registration, retrieval and search of users' attorney profiles

    To get attorneys, that users follows you should do request like this:
    `users/attorneys/?followed=true`.

    This view is read only(except for registration), since user can only edit
    it's own attorney profile.
    Note: user can create attorney profile only once
    Edit functionality is presented in CurrentAttorneyView

    """
    permissions_map = {
        'default': (IsAuthenticated,),
        'create': (AllowAny,),
        'follow': (permissions.CanFollow,),
        'unfollow': (permissions.CanFollow,),
        'overview': (IsAuthenticated, permissions.IsAttorneyFreeAccess,),
        'update_contact': (IsAuthenticated, permissions.IsAttorneyFreeAccess,
                           permissions.IsOwner,),
    }
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.AttorneySerializer
    serializers_map = {
        'create': serializers.AttorneyRegisterSerializer,
        'retrieve': serializers.AttorneyDetailSerializer,
        'validate_registration': serializers.AttorneyRegisterSerializer,
        'leads_and_clients': LeadAndClientSerializer,
    }
    queryset = Attorney.objects.real_users().select_related(
        'user',
        'user__client',
        'user__owned_enterprise',
        'user__paralegal',
        'fee_currency',
    ).prefetch_related(
        Prefetch(
            'matters', queryset=Matter.objects.order_by('-modified')
        ),
        Prefetch(
            'user__chats', queryset=Chats.objects.annotate(
                msg_count=Count('messages')
            ).filter(msg_count__gt=0).prefetch_related(
                'messages', 'participants'
            ).order_by('-modified')
        ),
        'matters__client',
        'matters__attorney',
        'matters__speciality',
        'matters__fee_type',
        'followers',
        'education',
        'education__university',
        'user__specialities',
        'firm_locations',
        'firm_locations__country',
        'firm_locations__state',
        'firm_locations__city',
        'firm_locations__city__region',
        'practice_jurisdictions',
        'practice_jurisdictions__country',
        'practice_jurisdictions__state',
        'fee_types',
        'appointment_type',
        'payment_type',
        'spoken_language',
        'registration_attachments',
        'user__billing_item__billing_items_invoices',
    )
    filterset_class = AttorneyFilter
    search_fields = [
        '@user__first_name',
        '@user__last_name',
        'user__email',
    ]
    ordering_fields = [
        'featured',
        'distance',
        'modified',
        'user__email',
        'user__first_name',
        'user__last_name',
    ]
    # Explanation:
    #    We changed lookup_value_regex to avoid views sets urls collapsing
    #    for example when you have view set at `users` and at `users/attorney`
    #    without it view set will collapse with at `users` in a way that
    #    users view set we use 'attorney' part of url as pk for search in
    #    retrieve method
    lookup_value_regex = '[0-9]+'

    def get_queryset(self):
        """Add distance to qs, using data from query_params."""
        qs = super().get_queryset()
        qp = self.request.query_params
        if qp.get('is_verified') == "true":
            return qs.verified()
        return qs.with_distance(
            longitude=qp.get('longitude'),
            latitude=qp.get('latitude')
        )

    def create(self, request, *args, **kwargs):
        """Register user and return attorney profile.

        There is following workflow:
        1. Create new user
        2. Create attorney and related objects
        3. Create new customer with set up payment method (based on related
        SetupIntent).

        """
        serializer = serializers.AttorneyRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        #  If the view produces an exception, rolls back the transaction
        #  of creation user and attorney.
        headers = self.get_success_headers(data)
        payment_method = data.get('payment_method', None)
        with transaction.atomic():
            user = serializer.save(self.request)
            if payment_method is not None:
                stripe_subscriptions_service.\
                    create_customer_with_attached_card(
                        user=user,
                        payment_method=payment_method
                    )
        serializer = serializers.AttorneySerializer(
            instance=user.attorney
        )

        complete_signup(
            self.request._request,
            user,
            settings.ACCOUNT_EMAIL_VERIFICATION,
            None
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(methods=['post'], detail=True, url_path='onboarding', )
    def onboarding(self, request, **kwargs):
        """Onboarding attorney"""
        attorney_id = self.kwargs['pk']
        serializer = serializers.AttorneyOnboardingSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        attorney = serializer.update(attorney_id, data)
        serializer = serializers.AttorneySerializer(
            instance=attorney
        )
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=True, url_path='follow', )
    def follow(self, request, **kwargs):
        """Follow attorney."""
        attorney = self.get_object()
        attorney.followers.add(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True, url_path='unfollow', )
    def unfollow(self, request, **kwargs):
        """Unfollow attorney."""
        attorney = self.get_object()
        attorney.followers.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=False, url_path='validate-registration')
    def validate_registration(self, request, **kwargs):
        """Validate attorney registration steps.

        App has a multistage registration process on 3 pages, which is not
        convenient to validate with one request. To make it more easy to use
        there are added separate API endpoints to validate each registration
        page separately. It allows to prevent redirecting user to next
        registration stage if current one is not valid in frontend.

        Current registration validation allows to check only steps:

            - 1st - `email`, `password1`, `password2`
            - 2d - all left attorney registration fields except `Stripe`
                payment info.

        """
        stage_serializer = serializers.AttorneyRegisterValidateSerializer(
            data=request.query_params
        )
        stage_serializer.is_valid(raise_exception=True)
        stage = stage_serializer.validated_data['stage']
        reg_stage_serializer_map = {
            'first': serializers.AttorneyRegisterValidateFirstStepSerializer,
            'second': serializers.AttorneyRegisterValidateSecondStepSerializer
        }
        serializer = reg_stage_serializer_map[stage](data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['GET'])
    def overview(self, request, *args, **kwargs):
        """Returns Overview details for attorney dashboard."""
        attorney = get_object_or_404(self.queryset, **kwargs)
        serializer = AttorneyDetailedOverviewSerializer(attorney, context={
            'request': request
        })
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['PUT'])
    def share_contact(self, request, *args, **kwargs):
        """Shares contact with other attorneys"""
        # Validating attorney permissions.
        self.get_object()

        object_map = {
            True: Invite,
            False: Client
        }
        from apps.social.api.serializers import ContactShareSerializer
        serializer = ContactShareSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_pending = serializer.validated_data['is_pending']

        try:
            contact = object_map[is_pending].objects.get(
                pk=request.data.get('contact_id')
            )
        except Exception:
            raise Http404('No %s matches the given query.' %
                          object_map[is_pending]._meta.object_name)

        contact.shared_with.add(*serializer.validated_data['shared_with'])

        return Response(
            data={},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['GET'])
    def leads_and_clients(self, request, *args, **kwargs):
        """Returns attorney's leads and clients."""
        attorney = get_object_or_404(self.queryset, **kwargs)
        try:
            search_filter = LeadClientSearchFilter()
            type_filter = LeadClientFilter()

            leads_clients = Client.attorney_clients_and_leads(attorney).\
                select_related(
                    'user',
                    'country',
                    'state',
                    'city',
                    'city__region',
                ).prefetch_related(
                    Prefetch(
                        'matters',
                        queryset=Matter.objects.filter(attorney=attorney)
                    ),
                    Prefetch(
                        'leads',
                        queryset=Lead.objects.filter(
                            status=Lead.STATUS_CONVERTED, attorney=attorney
                        )
                    ),
                ).distinct()
            leads_clients = search_filter.search_lead_client(
                request, leads_clients
            )
            leads_clients = type_filter.filter_type(request, leads_clients)

            invites = Invite.get_pending_attorney_invites(attorney).\
                select_related(
                    'country',
                    'state',
                    'city',
                    'city__region',
                ).prefetch_related(
                    'matters'
                )
            invites = search_filter.search_lead_client(request, invites)
            invites = type_filter.filter_type(request, invites)

            leads_and_clients = set(leads_clients) | set(invites)

            page = self.paginate_queryset(queryset=list(leads_and_clients))
            ordering_fields = request.GET.getlist('ordering', [])
            if page is not None:
                serializer = LeadAndClientSerializer(
                    page,
                    many=True,
                    context={'request': request}
                )
            else:
                serializer = LeadAndClientSerializer(
                    leads_and_clients,
                    many=True,
                    context={'request': request}
                )
            data = serializer.data
            for field in ordering_fields:
                reverse = False
                if field.startswith('-'):
                    reverse = True
                    field = field[1:]
                data = sorted(
                    data,
                    key=lambda k: (k[field] is not None, k[field]),
                    reverse=reverse
                )
            if page is not None:
                return self.get_paginated_response(data)
            else:
                return Response(
                    data=data,
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['DELETE'])
    def remove_leads_and_clients(self, request, *args, **kwargs):
        """Remove leads and clients in contact list"""
        attorney = self.get_object()
        try:
            user_id = request.data.get('user_id', None)
            is_invite = False
            try:
                is_invite = not isinstance(int(user_id), int)
            except ValueError:
                is_invite = True
            if is_invite:
                Invite.objects.filter(uuid=user_id).delete()
            else:
                Lead.objects.filter(
                    attorney=attorney, client=user_id
                ).delete()
                Matter.objects.filter(
                    attorney=attorney, client=user_id
                ).delete()
            return Response(
                data={"success": True},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(e)
            return Response(
                data={"success": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['POST'])
    def change_user_type(self, request, *args, **kwargs):
        """Attorney allow to change user types(lead, client)"""
        attorney = self.get_object()
        user_id = request.data.get('user_id')
        type = request.data.get('type', 'client')
        try:
            is_invite = False
            try:
                is_invite = not isinstance(int(user_id), int)
            except ValueError:
                is_invite = True
            if is_invite:
                Invite.objects.filter(uuid=user_id).update(client_type=type)
            else:
                lead = attorney.leads.get(client=user_id)
                if type == 'client':
                    lead.status = Lead.STATUS_CONVERTED
                elif type == 'lead' and \
                        Matter.objects.filter(
                            client=lead.client, attorney=attorney
                        ).count() == 0:
                    lead.status = Lead.STATUS_ACTIVE
                else:
                    return Response(
                        data={
                            "success": False,
                            "detail": "Client who has matters can not changed"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                lead.save()
        except Lead.DoesNotExist:
            return Response(
                data={"success": False},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            data={"success": True},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['GET'])
    def industry_contacts(self, request, *args, **kwargs):
        """Returns attorney industry contacts"""

        attorney = get_object_or_404(self.queryset, **kwargs)
        filterer = IndustryContactsSearchFilter()
        type_filterer = IndustryContactsTypeFilter()

        invites = Invite.get_pending_attorney_invites_for_industry_contacts(
            attorney
        )
        invites = filterer.filter_queryset(request, invites, None)
        invites = type_filterer.filter_contact_type(request, invites)
        contacts = attorney.industry_contacts.all()
        contacts = filterer.filter_queryset(request, contacts, None)
        contacts = type_filterer.filter_contact_type(request, contacts)

        industry_contacts = set(invites) | set(contacts)

        page = self.paginate_queryset(queryset=list(industry_contacts))
        ordering_fields = request.GET.getlist('ordering', [])
        if page is not None:
            serializer = IndustryContactSerializer(page, many=True)
        else:
            serializer = IndustryContactSerializer(
                industry_contacts,
                many=True
            )

        data = serializer.data
        for field in ordering_fields:
            reverse = False
            if field.startswith('-'):
                reverse = True
                field = field[1:]
            data = sorted(
                data,
                key=lambda k: (k[field] is not None, k[field]),
                reverse=reverse
            )

        if page is not None:
            return self.paginator.get_paginated_response(data)
        else:
            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )

    @action(detail=True, methods=['GET'])
    def industry_contact_detail(self, request, *args, **kwargs):
        """Return details of attorney industry contact"""
        self.get_object()
        user_id = request.query_params.get('user_id', None)
        if not user_id:
            return Http404('Invalid request data.')

        try:
            contact = get_user_model().objects.get(pk=user_id)
        except Exception:
            raise Http404('No %s matches the given query.' %
                          get_user_model()._meta.object_name)

        if contact.user_type == 'paralegal':
            serializer = IndustryContactParalegalDetails(contact)
        else:
            serializer = IndustryContactAttorneyDetails(contact)

        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['POST'])
    def add_industrial_contact(self, request, *args, **kwargs):
        """Adds new industrial contact"""

        attorney = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            raise Http404('Invalid request data.')

        try:
            new_industry_contact = get_user_model().objects.get(pk=user_id)
            if new_industry_contact.user_type == 'client':
                raise Http404('Invalid request data.')
            attorney.industry_contacts.add(
                new_industry_contact
            )
            return Response(
                status=status.HTTP_200_OK,
                data={"success": True}
            )
        except get_user_model().DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"success": False}
            )

    @action(detail=True, methods=['DELETE'])
    def remove_industrial_contact(self, request, *args, **kwargs):
        """Removes industrial contact"""

        attorney = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Http404('Invalid request data.')

        try:
            attorney.industry_contacts.remove(
                get_user_model().objects.get(pk=user_id)
            )
            return Response(
                status=status.HTTP_200_OK,
                data={"success": True}
            )
        except get_user_model().DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"success": False}
            )

    @action(detail=True, methods=['POST'])
    def add_contact(self, request, *args, **kwargs):
        """Add client as contact"""

        attorney = self.get_object()
        client_id = request.data.get("client", None)
        try:
            client = Client.objects.get(pk=client_id)
            Lead.objects.get_or_create(attorney=attorney, client=client)
            return Response(
                status=status.HTTP_200_OK,
                data={"success": True}
            )
        except Client.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "success": False,
                    "detail": "Client profile does not exist"
                }
            )
        except ValueError as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "success": False,
                    "detail": str(e)
                }
            )

    @action(detail=True, methods=['PUT'])
    def update_contact(self, request, *args, **kwargs):
        # Validating attorney permissions.
        attorney = self.get_object()

        object_map = {
            True: Invite,
            False: Client
        }
        from apps.users.api.serializers import (
            UpdateClientSerializer,
            UpdateInviteSerializer,
        )

        serializer_map = {
            True: UpdateInviteSerializer,
            False: UpdateClientSerializer
        }
        is_pending = request.data.get('is_pending', False)

        contact_model = object_map.get(is_pending)
        contact_id = request.data.get('contact_id')

        try:
            contact = get_object_or_404(contact_model, **{'pk': contact_id})
        except Exception:
            raise Http404('Invalid contact details.')

        if not contact:
            raise Http404('Invalid contact details.')

        serializer_class = serializer_map[is_pending]
        serializer = serializer_class(
            instance=contact,
            data=request.data['contact_data'],
            context={'request': request},
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        return Response(
            LeadAndClientSerializer(
                updated_instance, context={'request': request}
            ).data,
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True)
    def engagements(self, request, **kwargs):
        """View for getting attorney engagements."""

        attorney = self.request.user.attorney

        proposals = Proposal.objects.filter(attorney=attorney).select_related(
            'attorney',
            'attorney__user',
            'currency'
        ).prefetch_related(
            'post',
            'post__practice_area',
            'post__client',
        )

        status_required = request.GET.get('status')
        is_hidden_for_attorney = \
            request.query_params.get('is_hidden_for_attorney')
        if status_required:
            proposals = proposals.filter(status=status_required)
        else:
            is_active = request.GET.get('is_active')
            if is_active == '1':
                proposals = proposals.filter(
                    status__in=[
                        Proposal.STATUS_PENDING, Proposal.STATUS_REVOKED
                    ],
                    post__status=PostedMatter.STATUS_ACTIVE
                )
            elif is_active == '0':
                proposals = proposals.exclude(
                    status__in=[
                        Proposal.STATUS_PENDING, Proposal.STATUS_WITHDRAWN
                    ]
                ) | proposals.filter(post__status=PostedMatter.STATUS_INACTIVE)
        if is_hidden_for_attorney == 'true':
            proposals = proposals.filter(is_hidden_for_attorney=True)
        elif is_hidden_for_attorney == 'false':
            proposals = proposals.filter(is_hidden_for_attorney=False)
        page = self.paginate_queryset(proposals)
        if page is not None:
            serializer = AttorneyProposalSerializer(page, many=True)
            return self.paginator.get_paginated_response(data=serializer.data)

        serializer = AttorneyProposalSerializer(attorney)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True)
    def get_all_contacts(self, request, *args, **kwargs):
        attorney = self.get_object()
        industry_contacts = set(
            attorney.industry_contacts.values_list(
                'id', flat=True
            )
        )
        opportunities = set(
            attorney.opportunities.values_list(
                'client__user', flat=True
            )
        )
        leads = set(
            attorney.leads.values_list(
                'client__user',
                flat=True
            )
        )
        clients = set(
            attorney.matters.values_list(
                'client__user',
                flat=True
            )
        )
        contacts = industry_contacts | opportunities | leads | clients
        attorney_contacts = get_user_model().objects.filter(
            id__in=contacts
        )

        page = self.paginate_queryset(attorney_contacts)
        if page is not None:
            serializer = serializers.AppUserShortSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = serializers.AppUserShortSerializer(
            attorney_contacts,
            many=True
        )
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )


class CurrentAttorneyView(
    generics.UpdateAPIView,
    generics.RetrieveAPIView,
    generics.GenericAPIView
):
    """Retrieve and update user's attorney profile.

    Accepts GET, PUT and PATCH methods.
    Read-only fields:
        * first_name
        * last_name
        * user
        * is_verified
        * specialities_data
        * fee_types_data
    """
    serializer_class = serializers.AttorneyDetailSerializer
    permission_classes = (
        IsAuthenticated,
        permissions.IsAttorneyFreeAccess,
    )
    queryset = Attorney.objects.real_users().\
        select_related(
        'user',
        'fee_currency',
    ).prefetch_related(
        'followers',
        'practice_jurisdictions',
        'education',
        'education__university',
        'user__specialities',
        'firm_locations',
        'firm_locations__country',
        'firm_locations__state',
        'firm_locations__city',
        'firm_locations__city__region',
        'practice_jurisdictions',
        'practice_jurisdictions__country',
        'practice_jurisdictions__state',
        'fee_types',
        'appointment_type',
        'payment_type',
        'spoken_language',
        'registration_attachments',
    )

    def get_object(self):
        """Get user's attorney profile."""
        return self.queryset.get(user=self.request.user)

    def get_serializer_class(self):
        """Return serializer for update on `PUT` or `PATCH` requests.

        Can't use ActionSerializerMixin since it's not view-set.

        """
        if self.request.method in ('PUT', 'PATCH',):
            return serializers.UpdateAttorneySerializer
        return super().get_serializer_class()


class CurrentAttorneyActionsViewSet(BaseViewSet):
    """View for retrieving different current Attorney related info.

    As far as original `CurrentAttorneyView` is a simple generics view we
    couldn't easily add different named actions to it only `get`, `put` and etc
    methods.

    This viewset solves the issue and allows to define actions with different
    names. So all related to current attorney actions can be placed here.

    """
    permission_classes = (
        IsAuthenticated,
        permissions.IsAttorneyHasActiveSubscription,
    )
    base_filter_backends = None
    pagination_class = None

    @action(methods=['get'], url_path='statistics/current', detail=False)
    def current_statistics(self, request, *args, **kwargs):
        """Get attorney current statistics.

        Current attorney statistics is a statistics for current period of time.
        Current attorney statistics includes:
            Count of active leads,
            Count of active matters,
            Count of documents,
            Count of opportunities

        """
        return Response(
            data=services.get_attorney_statistics(request.user.attorney),
        )

    @action(methods=['get'], url_path='statistics/period', detail=False)
    def period_statistics(self, request, *args, **kwargs):
        """Get attorney statistics for for time period.

        Period attorney statistics is a statistics for selected period of time,
        where some of them (time_billed for now) divided by time frame.
        Period attorney statistics includes:
            Amount of billed time (divided by `time frame`),
            Count of active leads for period of time,
            Count of active matters for period of time,
            Count of opportunities for period of time,
            Count of converted leads for period of time

        """
        serializer = serializers.AttorneyPeriodStatsQueryParamsSerializer(
            data=request.query_params
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=services.get_attorney_period_statistic(
                request.user.attorney, **serializer.data
            )
        )
