from .attorney_links import (
    AttorneyUniversityAdmin,
    FeeKindAdmin,
    LanguageAdmin,
    SpecialityAdmin,
)
from .attorneys import AttorneyAdmin
from .clients import ClientAdmin
from .enterprise import EnterpriseAdmin
from .invites import InviteAdmin
from .paralegal import ParalegalAdmin
from .paralegal_links import ParalegalUniversityAdmin
from .support import SupportAdmin
from .users import AppUserAdmin

__all__ = (
    'AppUserAdmin',
    'ClientAdmin',
    'AttorneyAdmin',
    'ParalegalAdmin',
    'SupportAdmin',
    'AttorneyUniversityAdmin',
    'FeeKindAdmin',
    'SpecialityAdmin',
    'InviteAdmin',
    'LanguageAdmin'
    'ParalegalUniversityAdmin',
    'EnterpriseAdmin'
)
