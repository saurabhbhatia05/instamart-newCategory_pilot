"""Sample purchase history for development and demos."""

from datetime import datetime, timedelta

from src.shared.models.domain import Category, PurchaseHistory, PurchaseRecord


def sample_history(user_id: str = "user_001") -> PurchaseHistory:
    """Working professional with repetitive milk/bread/fruits weekly shops."""
    base = datetime.utcnow()
    milk = Category.MILK
    bread = Category.BREAD
    fruits = Category.FRUITS

    records = [
        PurchaseRecord(user_id=user_id, product_id="p001", product_name="Amul Milk 1L", category=milk, quantity=2, price_inr=56.0, purchased_at=base - timedelta(days=28)),
        PurchaseRecord(user_id=user_id, product_id="p002", product_name="Britannia Bread", category=bread, quantity=1, price_inr=40.0, purchased_at=base - timedelta(days=28)),
        PurchaseRecord(user_id=user_id, product_id="p003", product_name="Banana 1kg", category=fruits, quantity=1, price_inr=48.0, purchased_at=base - timedelta(days=21)),
        PurchaseRecord(user_id=user_id, product_id="p004", product_name="Amul Milk 1L", category=milk, quantity=2, price_inr=56.0, purchased_at=base - timedelta(days=21)),
        PurchaseRecord(user_id=user_id, product_id="p005", product_name="Amul Milk 1L", category=milk, quantity=2, price_inr=56.0, purchased_at=base - timedelta(days=14)),
        PurchaseRecord(user_id=user_id, product_id="p006", product_name="Britannia Bread", category=bread, quantity=1, price_inr=40.0, purchased_at=base - timedelta(days=14)),
        PurchaseRecord(user_id=user_id, product_id="p007", product_name="Amul Milk 1L", category=milk, quantity=2, price_inr=56.0, purchased_at=base - timedelta(days=7)),
        PurchaseRecord(user_id=user_id, product_id="p008", product_name="Amul Milk 1L", category=milk, quantity=2, price_inr=56.0, purchased_at=base - timedelta(days=7)),
        PurchaseRecord(user_id=user_id, product_id="p009", product_name="Amul Milk 1L", category=milk, quantity=2, price_inr=56.0, purchased_at=base - timedelta(days=1)),
        PurchaseRecord(user_id=user_id, product_id="p010", product_name="Britannia Bread", category=bread, quantity=1, price_inr=40.0, purchased_at=base - timedelta(days=1)),
    ]
    return PurchaseHistory(user_id=user_id, records=records)
