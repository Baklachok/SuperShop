from django.core.paginator import PageNotAnInteger, EmptyPage, InvalidPage
from django.http import JsonResponse
from rest_framework import pagination, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response


class CustomPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100
    page_query_param = 'page'

    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate a queryset if required, either returning a
        page object, or `None` if pagination is not configured for this view.
        """
        self.request = request
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        page_number = self.get_page_number(request, paginator)

        try:
            self.page = paginator.page(page_number)
        except InvalidPage as exc:
            msg = self.invalid_page_message.format(
                page_number=page_number, message=str(exc)
            )
            return

        if paginator.num_pages > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True

        return list(self.page)

    def get_paginated_response(self, data):
        return Response(data)
