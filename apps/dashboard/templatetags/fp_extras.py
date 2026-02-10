"""Template tags for FleetPredict Pro."""

from django import template

register = template.Library()


@register.filter
def pagination_window(page_obj, size=5):
    """
    Return a list of page numbers to display, with None for ellipsis.
    E.g. for 10 pages, current 5, size 3: [1, None, 4, 5, 6, None, 10]
    """
    if not page_obj or not hasattr(page_obj.paginator, 'num_pages'):
        return []
    num_pages = page_obj.paginator.num_pages
    current = page_obj.number
    if num_pages <= size + 2:
        return list(range(1, num_pages + 1))
    half = size // 2
    start = max(1, current - half)
    end = min(num_pages, current + half)
    if start <= 2 and end >= num_pages - 1:
        return list(range(1, num_pages + 1))
    out = []
    if start > 1:
        out.append(1)
        if start > 2:
            out.append(None)
    out.extend(range(start, end + 1))
    if end < num_pages:
        if end < num_pages - 1:
            out.append(None)
        out.append(num_pages)
    return out
