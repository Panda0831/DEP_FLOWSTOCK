"""Pagination standard de l’API."""

from rest_framework.pagination import PageNumberPagination


class PaginationStandard(PageNumberPagination):
    """Limite les réponses paginées à une taille explicite et bornée."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
