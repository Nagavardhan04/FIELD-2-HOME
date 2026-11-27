# ==========================================
# FIELD 2 HOME - PRODUCT SERVICE
# ==========================================

# Empty product list.
# Farmers will add products through the app.

products = []


# ==========================================
# 1. ADD PRODUCT
# ==========================================

def add_product(product_list, product):

    product_list.append(product)

    return True


# ==========================================
# 2. SEARCH PRODUCTS
# ==========================================

def search_products(product_list, keyword):

    result = []

    for product in product_list:

        if (keyword.lower() in product["name"].lower()
                or keyword.lower() in product["farmer"].lower()):

            result.append(product)

    return result


# ==========================================
# 3. FILTER PRODUCTS
# ==========================================

def filter_by_category(product_list, category):

    result = []

    for product in product_list:

        if category == "All" or product["category"] == category:

            result.append(product)

    return result


# ==========================================
# 4. SORT PRODUCTS
# ==========================================

def sort_by_price(product_list, order):

    if order == "Low to High":

        return sorted(
            product_list,
            key=lambda item: item["price"]
        )

    elif order == "High to Low":

        return sorted(
            product_list,
            key=lambda item: item["price"],
            reverse=True
        )

    return product_list


# ==========================================
# 5. CALCULATE DISCOUNT
# ==========================================

def calculate_discount(original_price, selling_price):

    if original_price <= 0:
        return 0

    discount = (
        (original_price - selling_price)
        / original_price
    ) * 100

    return round(discount)