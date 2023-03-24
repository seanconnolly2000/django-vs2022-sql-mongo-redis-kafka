from django import template

register = template.Library()

@register.filter(name='format')
def format(value, fmt):
    a = fmt.format(value)
    return a


@register.filter
def percentage(value, fmt):
    a = fmt.format(value * 100) + "%"
    return a


@register.filter
def milliseconds(value, fmt):
    a = fmt.format(value * 1000) + "ms"
    return a
