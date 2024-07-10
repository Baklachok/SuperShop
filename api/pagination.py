from rest_framework import pagination

class CustomPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100
    page_query_param = 'page'
    def paginate_queryset(self, queryset, request, view=None):
        # Пытаемся получить объект страницы
        try:
            self.page = self.paginate_queryset(queryset)
        except pagination.PageNotAnInteger:
            self.page = self.page.paginator.page(1)
        except pagination.EmptyPage:
            self.page = []
        
        if not self.page:
            return None
        
        self.request = request
        return list(self.page)
    
    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'results': data
        })
