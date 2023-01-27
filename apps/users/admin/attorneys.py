from django.contrib import admin, messages
from django.contrib.gis.admin import OSMGeoAdmin
from django.shortcuts import redirect, reverse
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from libs.utils import json_prettified

from ...business import models as business_models
from ...core.admin import BaseAdmin
from ...promotion import models as promotion_models
from ...social import models as social_models
from .. import models
from .forms import AttorneyForm, CancelSubscriptionForm, VerifyWithTrialForm


class PracticeJurisdictionItemInline(admin.TabularInline):
    """Used to show attorney practice jurisdictions."""
    autocomplete_fields = ('jurisdiction',)
    model = models.Attorney.practice_jurisdictions.through
    verbose_name = _("Attorney's practice jurisdiction")
    verbose_name_plural = _("Attorney's practice jurisdictions")


class FirmLocationItemInline(admin.TabularInline):
    """Used to show attorney firm locations."""
    autocomplete_fields = ('firmlocation',)
    model = models.Attorney.firm_locations.through
    verbose_name = _("Attorney's firm locations")
    verbose_name_plural = _("Attorney's firm locations")


class FeeKindItemInline(admin.TabularInline):
    """Used to show attorney fee kinds."""
    autocomplete_fields = ('feekind',)
    model = models.Attorney.fee_types.through
    verbose_name = _("Attorney's fee kind")
    verbose_name_plural = _("Attorney's fee kinds")


class AttorneyEducationItemInline(admin.TabularInline):
    """Used to show attorney education"""
    autocomplete_fields = ('university',)
    model = models.AttorneyEducation
    verbose_name = _("Attorney's education")
    verbose_name_plural = _("Attorney's education")


class AttorneyRegistrationAttachmentItemInline(admin.TabularInline):
    """Used to show attorney attachments on registration"""
    model = models.AttorneyRegistrationAttachment
    verbose_name = _("Attorney's attachments")
    verbose_name_plural = _("Attorney's attachments")

    def get_queryset(self, request):
        return super().get_queryset(request=request).select_related(
            'attorney',
            'attorney__user',
        )


# Usage in change statuses in attorney admin
VERIFICATION_ERROR_MSG = _(
    "You can’t change the attorney's status after creating a subscription."
)


class AttorneyVerificationMixin:
    """Mixin to provide Attorney verification functionality."""
    change_actions = [
        'verify_attorney',
        'decline_attorney',
        'cancel_subscription'
    ]

    def verify_attorney(self, request, attorney: models.Attorney):
        """Verify attorney profile and send notification email."""
        if attorney.user.has_active_subscription:
            self.message_user(request, VERIFICATION_ERROR_MSG, messages.ERROR)
            return
        return self.verify_attorney_view(request, attorney)

    verify_attorney.label = _('Verify')
    verify_attorney.short_description = _('Verify attorney profile')

    def decline_attorney(self, request, attorney: models.Attorney):
        """Decline attorney profile and send notification email."""
        if attorney.user.has_active_subscription:
            self.message_user(request, VERIFICATION_ERROR_MSG, messages.ERROR)
            return
        attorney.decline_by_admin()

    decline_attorney.label = _('Decline')
    decline_attorney.short_description = _(
        'Decline attorney profile verification'
    )

    def cancel_subscription(self, request, attorney: models.Attorney):
        """Cancel attorney subscription"""
        if not attorney.user.customer:
            self.message_user(request, VERIFICATION_ERROR_MSG, messages.ERROR)
            return
        return self.cancel_subscription_view(request, attorney)

    cancel_subscription.label = _('Cancel Subscription')
    cancel_subscription.short_description = _(
        "Cancel active subscription of attonrey"
    )

    def verify_attorney_view(self, request, attorney: models.Attorney):
        """Separate view to provide attorney verification.

        This view allows admin to select trial period for a not verified yet
        user.

        """

        form = VerifyWithTrialForm(request.POST or None)

        # if form is valid -> perform attorney verification
        if request.method == 'POST' and form.is_valid():
            attorney.verify_by_admin(
                trial_end=form.cleaned_data['trial_end']
            )
            return redirect(reverse(
                'admin:users_attorney_change',
                kwargs={'object_id': attorney.pk}
            ))

        context = self.admin_site.each_context(request)
        context['title'] = _('Verify attorney profile')
        context['form'] = form
        context['opts'] = self.model._meta
        context['object'] = attorney
        request.current_app = self.admin_site.name
        return TemplateResponse(
            request,
            'users/verify_with_trial.html',
            context
        )

    def cancel_subscription_view(self, request, attorney: models.Attorney):
        """Separate view to cancel attorney subscription.

        This view allows admin to cancel attorney subscription
        immediately or not.

        """

        form = CancelSubscriptionForm(request.POST or None)

        # if form is valid -> perform attorney verification
        if request.method == 'POST' and form.is_valid():
            from apps.finance.services import stripe_subscriptions_service
            at_period_end = form.cleaned_data['at_period_end']
            if attorney.user.customer:
                stripe_subscriptions_service(attorney.user).\
                    cancel_current_subscription(at_period_end)
            return redirect(reverse(
                'admin:users_attorney_change',
                kwargs={'object_id': attorney.pk}
            ))

        context = self.admin_site.each_context(request)
        context['title'] = _('Cancel attorney subscription')
        context['form'] = form
        context['opts'] = self.model._meta
        context['object'] = attorney
        request.current_app = self.admin_site.name
        return TemplateResponse(
            request,
            'users/verify_with_trial.html',
            context
        )


@admin.register(models.Attorney)
class AttorneyAdmin(
    AttorneyVerificationMixin,
    OSMGeoAdmin,
    BaseAdmin
):
    """Attorney representation for admin."""
    form = AttorneyForm
    autocomplete_fields = (
        'user',
    )
    list_display = (
        'pk',
        'user',
        'email',
        'verification_status'
    )
    list_display_links = (
        'pk',
        'user',
        'email',
    )
    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name',
    )
    list_filter = (
        'featured',
        'sponsored',
        'verification_status',
    )
    autocomplete_list_filter = (
        'user',
    )
    ordering = (
        '-pk',
        'user',
        'verification_status'
    )
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'user',
                '_link_to_user',
                'email',
                'verification_status',
                'followers_count',
                'featured',
            )
        }),
        (_('Sponsor info'), {
            'fields': (
                'sponsored',
                'sponsor_link',
            )
        }),
        (_('Finance info'), {
            'fields': (
                '_subscription',
                '_subscription_status',
                '_is_paid',
                '_canceled_at',
                'trial_end',
            )
        }),
        (_('Practice information'), {
            'fields': (
                'license_info',
                'practice_description',
                'years_of_experience',
            )
        }),
        (_('Speciality'), {
            'fields': (
                'have_speciality',
                'speciality_time',
                'speciality_matters_count',
            )
        }),
        (_('Fees'), {
            'fields': (
                'fee_rate',
            )
        }),
        (_('Extra info'), {
            'fields': (
                'extra_info',
                'charity_organizations',
                'keywords',
            )
        }),
    )
    readonly_fields = (
        'verification_status',
        'email',
        'followers_count',
        '_is_paid',
        '_subscription',
        '_subscription_status',
        '_canceled_at',
        '_link_to_user',
    )
    create_only_fields = (
        'user',
    )
    inlines = (
        AttorneyRegistrationAttachmentItemInline,
        PracticeJurisdictionItemInline,
        FirmLocationItemInline,
        AttorneyEducationItemInline,
        FeeKindItemInline,
    )
    related_models = (
        business_models.Matter,
        business_models.Lead,
        business_models.Stage,
        business_models.ChecklistEntry,
        promotion_models.Event,
        social_models.AttorneyPost,
    )
    change_actions = AttorneyVerificationMixin.change_actions + \
        ['get_account_proxy']

    def _link_to_user(self, obj: models.Attorney):
        """Return HTML link to `user`."""
        return self._admin_url(obj.user)

    _link_to_user.short_description = _('Link to user')

    def _subscription(self, attorney):
        """Return info about current attorney subscription."""
        subscription = attorney.user.active_subscription
        return self._admin_url(subscription) if subscription else '-'

    _subscription.short_description = _('Subscription')

    def _subscription_status(self, attorney):
        """Return info about current attorney subscription status."""
        subscription = attorney.user.active_subscription
        return subscription.status.capitalize() if subscription else '-'

    _subscription_status.short_description = _('Subscription status')

    def _is_paid(self, attorney):
        """Return info about current attorney subscription payment."""
        subscription = attorney.user.active_subscription
        is_paid = subscription.is_active if subscription else False
        return 'Yes' if is_paid else 'No'

    _is_paid.short_description = _('Is subscription paid')

    def _canceled_at(self, attorney):
        """Return info about current attorney subscription cancel."""
        subscription = attorney.user.active_subscription
        return subscription.canceled_at.date() \
            if subscription.canceled_at else '-'

    _canceled_at.short_description = _('Canceled at')

    def _firm_place_id(self, attorney):
        """Return a link to google maps, which shows location."""
        if not attorney.firm_place_id:
            return None
        place_id = attorney.firm_place_id
        url = f'https://www.google.com/maps/place/?q=place_id:{place_id}'
        link = format_html(
            "<a href='{0}'>Open in google maps</a>", url, place_id
        )
        return link

    _firm_place_id.short_description = _('Link to place')

    def _firm_location(self, attorney):
        """Return a link to google maps, which shows location of attorney."""
        if not attorney.firm_location:
            return None
        lon, lat = attorney.firm_location
        url = f'http://maps.google.com/maps?t=h&q=loc:{lat},{lon}'
        link = format_html("<a href='{0}'>{1}, {2}</a>", url, lat, lon)
        return link

    _firm_location.short_description = _('Coordinates (latitude, longitude)')

    def firm_location_data_prettified(self, attorney):
        """Prettify location data."""
        return json_prettified(attorney.firm_location_data)

    def followers_count(self, attorney):
        """Return followers count."""
        return attorney.followers.count()

    followers_count.short_description = _('Followers count')

    def get_account_proxy(self, request, attorney: models.Attorney):
        """Get attorney's `AccountProxy`."""
        deposit_account = attorney.user.deposit_account
        if not deposit_account:
            msg = 'Attorney has no direct deposit account yet'
            self.message_user(request, msg, messages.ERROR)
            return
        return redirect(self._get_admin_url(deposit_account))

    get_account_proxy.label = _('Account Proxy')
    get_account_proxy.short_description = _(
        "Attorney's direct deposit account"
    )
