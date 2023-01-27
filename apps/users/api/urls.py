from django.urls import re_path

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(
    r'users',
    views.AppUserViewSet,
    basename='users'
)
router.register(
    r'users/support',
    views.SupportViewSet,
    basename='support'
)
router.register(
    r'users/clients',
    views.ClientViewSet,
    basename='clients'
)
router.register(
    r'users/invites',
    views.InviteViewSet,
    basename='invites'
)
router.register(
    r'users/attorneys',
    views.AttorneyViewSet,
    basename='attorneys'
)
router.register(
    r'users/paralegals',
    views.ParalegalViewSet,
    basename='paralegals'
)
router.register(
    r'users/enterprises',
    views.EnterpriseViewSet,
    basename='enterprises'
)
router.register(
    r'users/firm-sizes',
    views.FirmSizeViewSet,
    basename='enterprise_firm_size'
)
router.register(
    r'users/specialities',
    views.SpecialityViewSet,
    basename='attorney_specialities'
)
router.register(
    r'users/fee-types',
    views.FeeKindViewSet,
    basename='attorney_fee_types'
)
router.register(
    r'users/attorneys/universities',
    views.AttorneyUniversityViewSet,
    basename='attorney_institutions'
)
router.register(
    r'users/attorneys/current',
    views.CurrentAttorneyActionsViewSet,
    basename='current_attorney_actions'
)
router.register(
    r'users/appointment-types',
    views.AppointmentTypeViewSet,
    basename='attorney_appointment_types'
)
router.register(
    r'users/payment-types',
    views.PaymentTypeViewSet,
    basename='attorney_payment_types'
)
router.register(
    r'users/languages',
    views.LanguageViewSet,
    basename='attorney_languages'
)
router.register(
    r'users/currencies',
    views.CurrenciesViewSet,
    basename='attorney_currencies'
)
router.register(
    r'users/timezones',
    views.TimezoneViewSet,
    basename='attorney_currencies'
)
router.register(
    r'users/clients/current/favorite',
    views.CurrentClientFavoriteViewSet,
    basename='current_client_favorite'
)

urlpatterns = router.urls

urlpatterns += [
    re_path(
        '^users/support/current/$',
        views.CurrentSupportView.as_view(),
        name='current_support'
    ),
    re_path(
        '^users/clients/current/$',
        views.CurrentClientView.as_view(),
        name='current_client'
    ),
    re_path(
        r'^users/attorneys/current/$',
        views.CurrentAttorneyView.as_view(),
        name='current_attorney'
    ),
    re_path(
        r'^users/paralegals/current/$',
        views.CurrentParalegalView.as_view(),
        name='current_paralegal'
    ),
    re_path(
        r'^users/enterprises/current/$',
        views.CurrentEnterpriseView.as_view(),
        name='current_enterprise'
    ),
    # Auth urls
    # URLs that do not require a session or valid token
    re_path(
        r'^auth/login/$',
        views.AppUserLoginView.as_view(),
        name='login'
    ),
    re_path(
        r'^auth/login/validate/$',
        views.ValidateCredentialView.as_view(),
        name='validate_credential'
    ),
    re_path(
        r'^auth/password/reset/$',
        views.PasswordResetView.as_view(),
        name='password_reset'
    ),
    re_path(
        r'^auth/password/reset/confirm/$',
        views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),
    # URLs that require a user to be logged in with a valid session / token.
    re_path(
        r'^auth/logout/$',
        views.LogoutView.as_view(),
        name='logout'
    ),
    re_path(
        r'^auth/password/change/$',
        views.PasswordChangeView.as_view(),
        name='password_change'
    ),
    re_path(
        r'^auth/account-confirm-email/',
        views.VerifyEmailView.as_view(),
        name='account_email_verification_sent',
    ),
    re_path(
        r'^auth/account-confirm-twofa/',
        views.VerifyCodeView.as_view(),
        name='account_twofa_verification'
    ),
    re_path(
        r'^auth/account-resend-confirm-email/',
        views.ResendEmailConfirmation.as_view(),
        name='account_email_verification_resent'
    ),
    re_path(
        r'^sync-plan',
        views.SyncPlanView.as_view(),
        name='sync_plan'
    )
]