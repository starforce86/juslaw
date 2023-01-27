from .base import BaseNotificationResource
from .business import (
    MatterReferredResource,
    MatterSharedResource,
    MatterStageUpdateNotificationResource,
    MatterStatusUpdateNotificationResource,
    NewBillingItemNotificationResource,
    NewChatNotificationResource,
    NewInvoiceNotificationResource,
    NewMatterResource,
    NewMessageNotificationResource,
    NewProposalNotificationResource,
    NewVideoCallResource,
    PostDeactivatedNotificationResource,
    PostReactivatedNotificationResource,
    ProposalAcceptedNotificationResource,
    ProposalWithDrawnNotificationResource,
    ReferralAcceptedResource,
    ReferralDeclinedResource,
)
from .documents import (
    DocumentSharedNotificationResource,
    DocumentUploadedNotificationResource,
    DocumentUploadedToMatterNotificationResource,
)
from .forums import (
    NewAttorneyCommentNotificationResource,
    NewCommentNotificationResource,
    NewPostNotificationResource,
)
from .promotion import NewAttorneyEventNotificationResource
from .social import NewChatResource, NewSingleGroupChatResource
from .users import (
    AdminNewUserRegisteredNotificationResource,
    NewSharedContactClientNotificationResource,
    NewSharedContactInviteNotificationResource,
    OpportunitiesNotificationResource,
)

NOTIFICATION_RESOURCES = (
    AdminNewUserRegisteredNotificationResource,
    NewMessageNotificationResource,
    NewChatNotificationResource,
    NewVideoCallResource,
    OpportunitiesNotificationResource,
    DocumentSharedNotificationResource,
    DocumentUploadedNotificationResource,
    DocumentUploadedToMatterNotificationResource,
    MatterStatusUpdateNotificationResource,
    NewBillingItemNotificationResource,
    NewAttorneyEventNotificationResource,
    NewAttorneyCommentNotificationResource,
    NewInvoiceNotificationResource,
    NewPostNotificationResource,
    NewCommentNotificationResource,
    NewMatterResource,
    NewChatResource,
    NewSharedContactClientNotificationResource,
    NewSharedContactInviteNotificationResource,
    NewSingleGroupChatResource,
    MatterSharedResource,
    MatterReferredResource,
    ReferralAcceptedResource,
    ReferralDeclinedResource,
    MatterStageUpdateNotificationResource,
    NewProposalNotificationResource,
    ProposalWithDrawnNotificationResource,
    ProposalAcceptedNotificationResource,
    PostDeactivatedNotificationResource,
    PostReactivatedNotificationResource,
)

RESOURCE_MAPPING = {
    resource.runtime_tag: resource
    for resource in NOTIFICATION_RESOURCES
}

__all__ = tuple(
    resource.__name__ for resource in NOTIFICATION_RESOURCES
) + (
    'BaseNotificationResource',
    'RESOURCE_MAPPING',
)
