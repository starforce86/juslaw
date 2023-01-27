from django.contrib import admin, messages
from django.contrib.gis.admin import OSMGeoAdmin
from django.shortcuts import redirect, reverse
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from libs.utils import json_prettified

# from ...business import models as business_models
from ...core.admin import BaseAdmin
# from ...promotion import models as promotion_models
# from ...social import models as social_models
from .. import models
from .forms import ParalegalForm, VerifyWithTrialForm


class PracticeJurisdictionItemInline(admin.TabularInline):
    """Used to show paralegal practice jurisdictions."""
    autocomplete_fields = ('jurisdiction',)
    model = models.Paralegal.practice_jurisdictions.through
    verbose_name = _("Paralegal's practice jurisdiction")
    verbose_name_plural = _("Paralegal's practice jurisdictions")


class FirmLocationItemInline(admin.TabularInline):
    """Used to show paralegal firm locations."""
    autocomplete_fields = ('firmlocation',)
    model = models.Paralegal.firm_locations.through
    verbose_name = _("paralegal's firm locations")
    verbose_name_plural = _("Paralegal's firm locations")


class FeeKindItemInline(admin.TabularInline):
    """Used to show paralegal fee kinds."""
    autocomplete_fields = ('feekind',)
    model = models.Paralegal.fee_types.through
    verbose_name = _("Paralegal's fee kind")
    verbose_name_plural = _("Paralegal's fee kinds")


class ParalegalEducationItemInline(admin.TabularInline):
    """Used to show paralegal education"""
    autocomplete_fields = ('university',)
    model = models.ParalegalEducation
    verbose_name = _("Paralegal's education")
    verbose_name_plural = _("Paralegal's education")


class ParalegalRegistrationAttachmentItemInline(admin.TabularInline):
    """Used to show paralegal attachments on registration"""
    model = models.ParalegalRegistrationAttachment
    verbose_name = _("Paralegal's attachments")
    verbose_name_plural = _("Paralegal's attachments")

    def get_queryset(self, request):
        return super().get_queryset(request=request).select_related(
            'paralegal',
            'paralegal__user',
        )


# Usage in change statuses in paralegal admin
VERIFICATION_ERROR_MSG = _(
    "You can’t change the paralegal's status after creating a subscription."
)


class ParalegalVerificationMixin:
    """Mixin to provide Paralegal verification functionality."""
    change_actions = [
        'verify_paralegal',
        'decline_paralegal'
    ]

    def verify_paralegal(self, request, paralegal: models.Paralegal):
        """Verify paralegal profile and send notification email."""
        if paralegal.user.has_active_subscription:
            self.message_user(request, VERIFICATION_ERROR_MSG, messages.ERROR)
            return
        return self.verify_paralegal_view(request, paralegal)

    verify_paralegal.label = _('Verify')
    verify_paralegal.short_description = _('Verify paralegal profile')

    def decline_paralegal(self, request, paralegal: models.Paralegal):
        """Decline paralegal profile and send notification email."""
        if paralegal.user.has_active_subscription:
            self.message_user(request, VERIFICATION_ERROR_MSG, messages.ERROR)
            return
        paralegal.decline_by_admin()

    decline_paralegal.label = _('Decline')
    decline_paralegal.short_description = _(
        'Decline paralegal profile verification'
    )

    def verify_paralegal_view(self, request, paralegal: models.Paralegal):
        """Separate view to provide paralegal verification.

        This view allows admin to select trial period for a not verified yet
        user.

        """

        form = VerifyWithTrialForm(request.POST or None)

        # if form is valid -> perform paralegal verification
        if request.method == 'POST' and form.is_valid():
            paralegal.verify_by_admin(
                trial_end=form.cleaned_data['trial_end']
            )
            return redirect(reverse(
                'admin:users_paralegal_change',
                kwargs={'object_id': paralegal.pk}
            ))

        context = self.admin_site.each_context(request)
        context['title'] = _('Verify paralegal profile')
        context['form'] = form
        context['opts'] = self.model._meta
        context['object'] = paralegal
        request.current_app = self.admin_site.name
        return TemplateResponse(
            request,
            'users/verify_with_trial.html',
            context
        )


@admin.register(models.Paralegal)
class ParalegalAdmin(
    ParalegalVerificationMixin,
    OSMGeoAdmin,
    BaseAdmin
):
    """Paralegal representation for admin."""
    form = ParalegalForm
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
        ParalegalRegistrationAttachmentItemInline,
        PracticeJurisdictionItemInline,
        FirmLocationItemInline,
        ParalegalEducationItemInline,
        FeeKindItemInline,
    )
    # related_models = (
    #     business_models.Matter,
    #     business_models.Lead,
    #     business_models.Stage,
    #     business_models.ChecklistEntry,
    #     promotion_models.Event,
    #     social_models.AttorneyPost,
    # )
    change_actions = ParalegalVerificationMixin.change_actions + \
        ['get_account_proxy']

    def _link_to_user(self, obj: models.Paralegal):
        """Return HTML link to `user`."""
        return self._admin_url(obj.user)

    _link_to_user.short_description = _('Link to user')

    def _subscription(self, paralegal):
        """Return info about current paralegal subscription."""
        subscription = paralegal.user.active_subscription
        return self._admin_url(subscription) if subscription else '-'

    _subscription.short_description = _('Subscription')

    def _subscription_status(self, paralegal):
        """Return info about current paralegal subscription status."""
        subscription = paralegal.user.active_subscription
        return subscription.status.capitalize() if subscription else '-'

    _subscription_status.short_description = _('Subscription status')

    def _is_paid(self, paralegal):
        """Return info about current paralegal subscription payment."""
        subscription = paralegal.user.active_subscription
        is_paid = subscription.is_active if subscription else False
        return 'Yes' if is_paid else 'No'

    _is_paid.short_description = _('Is subscription paid')

    def _canceled_at(self, paralegal):
        """Return info about current paralegal subscription cancel."""
        subscription = paralegal.user.active_subscription
        return subscription.canceled_at.date() \
            if subscription.canceled_at else '-'

    _canceled_at.short_description = _('Canceled at')

    def _firm_place_id(self, paralegal):
        """Return a link to google maps, which shows location."""
        if not paralegal.firm_place_id:
            return None
        place_id = paralegal.firm_place_id
        url = f'https://www.google.com/maps/place/?q=place_id:{place_id}'
        link = format_html(
            "<a href='{0}'>Open in google maps</a>", url, place_id
        )
        return link

    _firm_place_id.short_description = _('Link to place')

    def _firm_location(self, paralegal):
        """Return a link to google maps, which shows location of paralegal."""
        if not paralegal.firm_location:
            return None
        lon, lat = paralegal.firm_location
        url = f'http://maps.google.com/maps?t=h&q=loc:{lat},{lon}'
        link = format_html("<a href='{0}'>{1}, {2}</a>", url, lat, lon)
        return link

    _firm_location.short_description = _('Coordinates (latitude, longitude)')

    def firm_location_data_prettified(self, paralegal):
        """Prettify location data."""
        return json_prettified(paralegal.firm_location_data)

    def followers_count(self, paralegal):
        """Return followers count."""
        return paralegal.followers.count()

    followers_count.short_description = _('Followers count')

    def get_account_proxy(self, request, paralegal: models.Paralegal):
        """Get paralegal's `AccountProxy`."""
        deposit_account = paralegal.user.deposit_account
        if not deposit_account:
            msg = 'Paralegal has no direct deposit account yet'
            self.message_user(request, msg, messages.ERROR)
            return
        return redirect(self._get_admin_url(deposit_account))

    get_account_proxy.label = _('Account Proxy')
    get_account_proxy.short_description = _(
        "Paralegal's direct deposit account"
    )
