from django.contrib import admin
from .models import Subscription, SubscriptionNotificationResult


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'channel', 'endpoint', 'expiring', 'user_created', 'date_created']
    list_filter = ['status', 'channel', 'date_created']
    search_fields = ['endpoint', 'criteria']
    readonly_fields = ['id', 'date_created', 'user_created']


@admin.register(SubscriptionNotificationResult)
class SubscriptionNotificationResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'subscription', 'notified_successfully', 'notification_time', 'error']
    list_filter = ['notified_successfully', 'notification_time']
    search_fields = ['subscription__endpoint', 'error']
    readonly_fields = ['id', 'notification_time']
