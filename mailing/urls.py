from django.urls import path

from mailing.views import (
    MailingToAllStaffApi,
    MailingToSpecificStaffApi,
    MailingToStaffWithLatestActivityApi,
)

urlpatterns = [
    path(
        r'all/',
        MailingToAllStaffApi.as_view(),
        name='mailing-to-all-staff',
    ),
    path(
        r'staff/',
        MailingToSpecificStaffApi.as_view(),
        name='mailing-to-specific-staff',
    ),
    path(
        r'last-active/',
        MailingToStaffWithLatestActivityApi.as_view(),
    ),
]
