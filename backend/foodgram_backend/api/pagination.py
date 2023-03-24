from rest_framework.pagination import PageNumberPagination


class SubscriptionPagination(PageNumberPagination):
    page_size = 6
