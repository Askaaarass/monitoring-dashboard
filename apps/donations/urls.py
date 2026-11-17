from django.urls import path

from .views import (
    DonationCallbackView,
    DonationCreateView,
    DonationResultView,
    DonationStatisticsView,
    DonationStatusView,
)

urlpatterns = [
    path('create/', DonationCreateView.as_view(), name='donation-create'),
    path('callback/', DonationCallbackView.as_view(), name='donation-callback'),
    path('status/<uuid:donation_id>/', DonationStatusView.as_view(), name='donation-status'),
    path('statistics/', DonationStatisticsView.as_view(), name='donation-statistics'),
    path('result/', DonationResultView.as_view(), name='donation-result'),
]
