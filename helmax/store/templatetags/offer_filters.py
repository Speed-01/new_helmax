from django import template

register = template.Library()

@register.filter
def calculate_offer_price(price, discount_percentage):
    """Calculate the offer price based on original price and discount percentage."""
    try:
        discount = (float(discount_percentage) / 100) * float(price)
        return float(price) - discount
    except (ValueError, TypeError):
        return price