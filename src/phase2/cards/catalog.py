"""Product catalog for recommendation cards."""

from src.phase2.schemas import ProductItem
from src.shared.models.domain import Category

CATEGORY_PRODUCTS: dict[Category, list[ProductItem]] = {
    Category.HEALTH_WELLNESS: [
        ProductItem(
            product_id="hw001",
            name="Himalaya Ashwagandha Gummies",
            price_inr=299.0,
            mrp_inr=399.0,
            rating=4.6,
            discount_pct=25.0,
            competitor_price_inr=349.0,
        ),
        ProductItem(
            product_id="hw002",
            name="True Elements Chia Seeds 250g",
            price_inr=189.0,
            mrp_inr=249.0,
            rating=4.4,
            discount_pct=24.0,
        ),
    ],
    Category.PET_SUPPLIES: [
        ProductItem(
            product_id="ps001",
            name="Pedigree Adult Dog Treats 500g",
            price_inr=249.0,
            mrp_inr=299.0,
            rating=4.5,
            discount_pct=17.0,
            competitor_price_inr=279.0,
        ),
    ],
    Category.HOUSEHOLD: [
        ProductItem(
            product_id="hh001",
            name="Surf Excel Matic Liquid 2L",
            price_inr=399.0,
            mrp_inr=499.0,
            rating=4.7,
            discount_pct=20.0,
        ),
    ],
    Category.PERSONAL_CARE: [
        ProductItem(
            product_id="pc001",
            name="Dove Deep Moisture Body Wash 800ml",
            price_inr=349.0,
            mrp_inr=425.0,
            rating=4.5,
            discount_pct=18.0,
            competitor_price_inr=379.0,
        ),
    ],
    Category.SNACKS: [
        ProductItem(
            product_id="sn001",
            name="Lay's Classic Salted 52g",
            price_inr=20.0,
            mrp_inr=25.0,
            rating=4.3,
            discount_pct=20.0,
        ),
    ],
}

COMPETITOR_NAMES = ("Blinkit", "Zepto", "BigBasket")
