"""
ShopEasy Smart Notifications - Realistic Message Catalog
At least 12-15 diverse messages per category with realistic products,
brands, discounts, and order numbers.
"""

MESSAGES = {
    "offer": [
        "Weekend sale: up to 50% off fashion essentials and footwear",
        "Flash Deal: Extra 20% off Nike & Adidas running shoes until midnight",
        "Kitchen upgrade: 30% off barista espresso machines and blenders",
        "Tech Mega Sale: Save $150 on Ultra HD 4K OLED gaming monitors",
        "Buy 1 Get 1 Free on all organic skincare & wellness gift bundles",
        "Exclusive member coupon: $25 off orders above $100 this Friday",
        "Home Decor Fest: 40% off minimalist wool rugs, lamps, and cushions",
        "Outdoor gear clearance: 35% off waterproof backpacks and tents",
        "Denim days: Flat 45% off premium slim & relaxed selvedge jeans",
        "Mid-season treats: Up to 60% off bestselling smart watches & bands",
        "Books & games bundle discount: Save 25% when you buy any three",
        "Audio lovers deal: 30% off noise-cancelling wireless ANC earbuds",
        "Winter warmers: 40% off cashmere knit sweaters and thermal coats",
        "Gourmet food week: 20% off single-origin coffees and artisanal teas"
    ],
    "new_arrival": [
        "New sneakers just landed in your size: CloudStrider Pro Edition",
        "Fresh in stock: Minimalist Linen Over-shirts in 6 modern earth tones",
        "Just dropped: Mechanical tactile keyboards with hot-swappable switches",
        "New collection: Sustainable bamboo activewear & workout essentials",
        "Trending now: Ceramic pour-over coffee sets handcrafted in Kyoto",
        "New season: Wool blend tailored trench coats have just arrived",
        "Fresh release: Ultra-lightweight polarized titanium travel sunglasses",
        "Just launched: Smart ambient bedside lamps with sunrise sleep alarm",
        "New in audio: Hi-Fi studio monitor headphones with spatial audio support",
        "Backpack restock: Anti-theft commuters with padded 16\" laptop sleeve",
        "Just arrived: Ergonomic motorized standing desks with dual silent motors",
        "Fresh apparel: Retro graphic tees in heavyweight 100% organic cotton",
        "Just in: Wireless MagSafe charging pads in matte space gray",
        "New release: Stainless steel vacuum insulated water bottles (32 oz)"
    ],
    "price_drop": [
        "The Sony WH-1000XM5 headphones you saved just dropped by $60",
        "Price alert: Dyson V11 cordless vacuum is now at its lowest recorded price",
        "Good news! The Italian leather messenger bag in your wishlist is $35 off",
        "Price cut: AeroPress Go travel coffee press dropped to $31.99 today",
        "The Garmin Forerunner smartwatch you viewed is now 25% cheaper",
        "Price drop: Kindle Paperwhite 16GB dropped by $25 for the next 48 hours",
        "Item in your cart: Enamelled cast iron Dutch oven 6Qt just dropped 30%",
        "Price slashed: Wireless ergonomic gaming mouse is now $49 (was $79)",
        "Wishlist update: Anker portable power bank 20,000mAh dropped by $15",
        "Price drop: Organic bamboo memory foam pillows are now 40% off",
        "Tracked item deal: Smart WiFi learning thermostat is $40 cheaper today",
        "Instant discount: Ultra-slim 1TB portable external SSD dropped to $89",
        "Price alert: Ray-Ban classic Aviators just dropped by $32",
        "Good news: Mechanical drip coffee brewer is now $85 (was $120)"
    ],
    "order_update": [
        "Your order #SE-4921 is out for delivery. Estimated arrival by 3:30 PM",
        "Order #SE-3819 confirmed: We are carefully packing your items now",
        "Package on the move: Order #SE-5102 arrived at the local distribution hub",
        "Delivered! Your package #SE-3819 was placed securely at your front door",
        "Ready for pickup: Order #SE-6704 is waiting for you at ShopEasy Hub",
        "Shipping update: Order #SE-8192 has been dispatched via Express Air",
        "Delivery scheduled: Order #SE-7201 will arrive tomorrow morning",
        "Item verified: Quality inspection complete for refurbished tablet order #SE-6014",
        "Driver nearby: Carrier is 3 stops away with order #SE-9411",
        "Return processed: $64.50 refund credited to your original payment card",
        "Order #SE-1038 packed: Your live GPS tracking link is now active",
        "Signature required: Delivery courier is arriving between 1:00 PM and 2:00 PM",
        "Order #SE-2245 confirmed: Thank you for shopping with ShopEasy",
        "Package delayed slightly: New delivery window for #SE-8192 is tomorrow 10 AM"
    ]
}


def get_message_for_customer(customer_id, ntype, index):
    """
    Deterministically retrieves a non-repeating message for a customer.
    Uses customer_id hash offset + index mod len.
    """
    pool = MESSAGES[ntype]
    seed_offset = sum(ord(c) for c in str(customer_id))
    msg_idx = (seed_offset + index) % len(pool)
    return pool[msg_idx]
