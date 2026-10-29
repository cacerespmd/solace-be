
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Product


def serialize_product(product: Product) -> dict:
    return {
        "id": product.id,
        "name": product.name,
        "sku": product.sku,
        "description": product.description,
        "price": str(product.price),
        "stock_quantity": product.stock_quantity,
        "is_available": (
            product.is_active
            and product.stock_quantity > 0
        ),
        "image_url": product.image_url,
    }


def search_products(
    db: Session,
    query: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock_only: bool = False,
    sort_by: str = "relevance",
    limit: int = 10,
) -> dict:
    """
    Search the active product catalog.

    Supports:
    - Product name
    - SKU
    - Description
    - Price range
    - Stock availability
    - Price sorting
    """

    statement = select(Product).where(
        Product.is_active.is_(True)
    )

    if query and query.strip():
        search_term = f"%{query.strip()}%"

        statement = statement.where(
            or_(
                Product.name.ilike(search_term),
                Product.sku.ilike(search_term),
                Product.description.ilike(search_term),
            )
        )

    if min_price is not None:
        if min_price < 0:
            return {
                "error": "Minimum price cannot be negative."
            }

        statement = statement.where(
            Product.price >= Decimal(str(min_price))
        )

    if max_price is not None:
        if max_price < 0:
            return {
                "error": "Maximum price cannot be negative."
            }

        statement = statement.where(
            Product.price <= Decimal(str(max_price))
        )

    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):
        return {
            "error": "Minimum price cannot exceed maximum price."
        }

    if in_stock_only:
        statement = statement.where(
            Product.stock_quantity > 0
        )

    if sort_by == "price_asc":
        statement = statement.order_by(
            Product.price.asc(),
            Product.id.asc(),
        )

    elif sort_by == "price_desc":
        statement = statement.order_by(
            Product.price.desc(),
            Product.id.asc(),
        )

    elif sort_by == "newest":
        statement = statement.order_by(
            Product.created_at.desc(),
            Product.id.desc(),
        )

    else:
        statement = statement.order_by(
            Product.id.asc()
        )

    safe_limit = max(1, min(limit, 20))

    products = db.scalars(
        statement.limit(safe_limit)
    ).all()

    return {
        "query": query,
        "filters": {
            "min_price": min_price,
            "max_price": max_price,
            "in_stock_only": in_stock_only,
            "sort_by": sort_by,
        },
        "count": len(products),
        "products": [
            serialize_product(product)
            for product in products
        ],
    }


def lookup_product_stock(
    db: Session,
    product_id: Optional[int] = None,
    sku: Optional[str] = None,
    product_name: Optional[str] = None,
) -> dict:
    """
    Check stock for a specific product.

    Prefer product ID or SKU for exact matches.
    Product name supports partial matching.
    """

    if product_id is not None:
        statement = select(Product).where(
            Product.id == product_id,
            Product.is_active.is_(True),
        )

    elif sku and sku.strip():
        statement = select(Product).where(
            func.lower(Product.sku) == sku.strip().lower(),
            Product.is_active.is_(True),
        )

    elif product_name and product_name.strip():
        statement = select(Product).where(
            Product.name.ilike(
                f"%{product_name.strip()}%"
            ),
            Product.is_active.is_(True),
        )

    else:
        return {
            "error": (
                "Provide a product ID, SKU, "
                "or product name."
            )
        }

    products = db.scalars(
        statement.order_by(Product.id.asc()).limit(10)
    ).all()

    if not products:
        return {
            "found": False,
            "message": "No matching active products found.",
            "products": [],
        }

    return {
        "found": True,
        "count": len(products),
        "products": [
            serialize_product(product)
            for product in products
        ],
    }
