from django.urls import path
from mailing.views import (ClientListView, ClientCreateView, ClientUpdateView, ClientDeleteView, MessageListView,
                           MessageCreateView, MessageUpdateView, MessageDeleteView, MailingListView, MailingCreateView,
                           MailingUpdateView, MailingDeleteView, send_mailing_now, statistics)

app_name = 'mailing'

urlpatterns = [
    path('clients/', ClientListView.as_view(), name='client_list'),
    path('clients/create/', ClientCreateView.as_view(), name='client_create'),
    path('clients/<int:pk>/edit/', ClientUpdateView.as_view(), name='client_update'),
    path('clients/<int:pk>/delete/', ClientDeleteView.as_view(), name='client_delete'),
    path('messages/', MessageListView.as_view(), name='message_list'),
    path('messages/create/', MessageCreateView.as_view(), name='message_create'),
    path('messages/<int:pk>/edit/', MessageUpdateView.as_view(), name='message_update'),
    path('messages/<int:pk>/delete/', MessageDeleteView.as_view(), name='message_delete'),
    path('mailings/', MailingListView.as_view(), name='mailing_list'),
    path('mailings/create/', MailingCreateView.as_view(), name='mailing_create'),
    path('mailings/<int:pk>/edit/', MailingUpdateView.as_view(), name='mailing_update'),
    path('mailings/<int:pk>/delete/', MailingDeleteView.as_view(), name='mailing_delete'),
    path('mailings/<int:pk>/send/', send_mailing_now, name='mailing_send'),
    path('statistics/', statistics, name='statistics'),
]