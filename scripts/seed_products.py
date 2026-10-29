from sqlalchemy import select

from app.database import SessionLocal
from app.models import Product


DEMO_STOCK_QUANTITY = 10

# Snapshot of product names, SKUs, listed prices, and images from the
# DataBlitz public catalog on 2026-10-29. Stock is demo inventory, not live stock.
PRODUCTS = [
    {
        "name": "Hitscan Hyperlight X Wireless Gaming Mouse (Black, White)",
        "sku": "0860013325428",
        "description": "Wireless gaming mouse, listed in black and white.",
        "price": "6550.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "0_f70680a8-8ae5-469b-8bed-f33e5e52b92e.jpg?v=1793243469"
        ),
    },
    {
        "name": "Gigabyte Radeon AI PRO R9700 AI TOP 32GB GDDR6 (Rev.1.0) Graphics Card",
        "sku": "0889523052266",
        "description": "Graphics card with 32GB GDDR6 memory.",
        "price": "150985.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "dgnmxfhm.jpg?v=1793246239"
        ),
    },
    {
        "name": "AMD Ryzen 5 5600X3D Processor",
        "sku": "0730143314978",
        "description": "AMD Ryzen 5 5600X3D desktop processor.",
        "price": "13195.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "rmndrym.jpg?v=1793243183"
        ),
    },
    {
        "name": "PS5 Planet of Lana II Children of the Leaf Kindred Sprits Edition (Eng/EU)",
        "sku": "3701529516832",
        "description": "PS5 game, English/European edition.",
        "price": "2350.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "yhmdt_6ccd63ac-a073-4b7d-867d-c32667af02d3.jpg?v=1793236480"
        ),
    },
    {
        "name": "Nintendo Switch Undergrounded (US) (Eng/FR)",
        "sku": "0810075730708",
        "description": "Nintendo Switch game, US English/French edition.",
        "price": "1895.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "srmdym.jpg?v=1791357057"
        ),
    },
    {
        "name": (
            "Nintendo Switch 2 Demon Slayer Kimetsu no Yaiba The Hinokami "
            "Chronicles 2 + Infinity Castle Character Pass (SEA)"
        ),
        "sku": "4974365871260",
        "description": "Nintendo Switch 2 game with Infinity Castle Character Pass.",
        "price": "2398.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "0_0568afdf-7a10-4381-9c90-6d10e4e9f03a.jpg?v=1793233087"
        ),
    },
    {
        "name": "Nintendo Switch 2 Pokemon Pokopia + Expansion Pass (SEA)",
        "sku": "4902370555080",
        "description": "Nintendo Switch 2 game with expansion pass.",
        "price": "5695.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "zdfbxvhmgjh.jpg?v=1791527311"
        ),
    },
    {
        "name": "Nintendo Switch 2 Pokemon Legends Z-A + Mega Dimension (SEA)",
        "sku": "4902370554977",
        "description": "Nintendo Switch 2 game with Mega Dimension content.",
        "price": "4295.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "0_a89e23bb-5f30-4492-a570-d3b405e1c929.jpg?v=1793000894"
        ),
    },
    {
        "name": (
            "Nintendo Switch 2 Carrying Case with Screen Protector "
            "The Legend of Zelda 40th Anniversary Edition"
        ),
        "sku": "4902370554557",
        "description": "Nintendo Switch 2 carrying case with screen protector.",
        "price": "2295.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "1_a15b92d2-ff62-44fd-9015-def4dc2023ca.jpg?v=1789719218"
        ),
    },
    {
        "name": (
            "Nintendo Switch 2 Console The Legend of Zelda 40th Anniversary "
            "Edition (BEE-S-KL5AE-PHL)"
        ),
        "sku": "4902370554618",
        "description": "Nintendo Switch 2 console, Zelda 40th Anniversary Edition.",
        "price": "36995.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "0_e1a8ae49-9609-47ce-ba1a-3235026e55fd.jpg?v=1792981336"
        ),
    },
    {
        "name": (
            "Nintendo Switch 2 Pro Controller + Display Stand "
            "The Legend of Zelda 40th Anniversary Edition (SEA) (BEE-A-FSTDA)"
        ),
        "sku": "4902370554588",
        "description": "Nintendo Switch 2 Pro Controller with display stand.",
        "price": "5795.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "1_93dff2db-abc0-48b7-bed1-5ec16cfbc779.jpg?v=1789792314"
        ),
    },
    {
        "name": (
            "Aurora M110A Black Desktop Gaming PC | AMD Ryzen 7 8700F | "
            "16GB (2x8GB) RAM | 1TB SSD | RTX 5060 Ti | Windows 11 Pro"
        ),
        "sku": "1000000022598",
        "description": (
            "Desktop gaming PC with Ryzen 7 8700F, 16GB RAM, "
            "1TB SSD, and RTX 5060 Ti."
        ),
        "price": "79350.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "Aurora-M110A-Black-main.jpg?v=1793198104"
        ),
    },
    {
        "name": "Nintendo Switch 2 Hello Kitty Party Land Day 1 Edition (SEA)",
        "sku": "8885011019461",
        "description": "Nintendo Switch 2 game, Southeast Asian edition.",
        "price": "2695.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "0_f37e4d40-2d7f-4cec-9336-e381ad0e1251.jpg?v=1793000612"
        ),
    },
    {
        "name": "Nintendo Switch Hello Kitty Party Land Day 1 (Asian)",
        "sku": "8885011019454",
        "description": "Nintendo Switch game, Asian edition.",
        "price": "2695.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "1_a3e49e79-7137-4478-a3ad-1274f8c7aea0.jpg?v=1793000761"
        ),
    },
    {
        "name": (
            "Optima D34 Black Desktop Gaming PC | AMD Ryzen 7 7800X3D | "
            "32GB (2x16GB) RAM | 1TB SSD | RX 9070 XT | Windows 11 Pro"
        ),
        "sku": "1000000022601",
        "description": (
            "Desktop gaming PC with Ryzen 7 7800X3D, 32GB RAM, "
            "1TB SSD, and RX 9070 XT."
        ),
        "price": "133150.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "Optima-D34-Black-main.jpg?v=1793198657"
        ),
    },
    {
        "name": (
            "Optima Ceres Snow White Desktop Gaming PC | AMD Ryzen 7 7800X3D | "
            "32GB (2x16GB) RAM | 1TB SSD | RX 9070 XT | Windows 11 Pro"
        ),
        "sku": "1000000022599",
        "description": (
            "White desktop gaming PC with Ryzen 7 7800X3D, 32GB RAM, "
            "1TB SSD, and RX 9070 XT."
        ),
        "price": "134250.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "optima-ceres-snow-white-main.jpg?v=1793197635"
        ),
    },
    {
        "name": (
            "JBL Pulse 6 Portable Speaker with JBL Legendary Sound and a "
            "Customizable 360 Lightshow (Black)"
        ),
        "sku": "0050036421997",
        "description": "Portable JBL speaker with customizable 360-degree lighting.",
        "price": "19999.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "JBL_PULSE_6_3_4_FRONT_0073_x5_a66a66e1-8df1-4458-8d85-7c6baaa10fa6.jpg"
            "?v=1793196878"
        ),
    },
    {
        "name": "Anker Solix C2000 Gen2 2048Wh / 2400W Portable Power Station",
        "sku": "0194644337759",
        "description": "Portable power station with 2048Wh capacity and 2400W output.",
        "price": "59250.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "A1783-US_1_527f2941-c39c-4d85-876d-d5954b5f7275.jpg"
            "?v=1793196375"
        ),
    },
    {
        "name": "Anker Solix C1000 Gen2 1024WH / 2000W Portable Power Station",
        "sku": "0194644305857",
        "description": "Portable power station with 1024Wh capacity and 2000W output.",
        "price": "38850.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "A17631A1_Product_Image_01_V1.jpg?v=1793195764"
        ),
    },
    {
        "name": "Anker SOLIX C300 AC 288Wh | 300W Portable Backup Power Station",
        "sku": "0194644273934",
        "description": "Portable backup power station with 288Wh capacity and 300W output.",
        "price": "15895.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "ANKER_SOLIX_C300_AC_Portable_Power_Station_288Wh_Front_Right_2500x_"
            "2bf14abc-c4a6-4346-b13d-7291df5d8557.jpg?v=1793194704"
        ),
    },
    {
        "name": (
            "Asus VY279HG2 27-inch FHD 144Hz 1ms MPRT IPS Eye Care "
            "Gaming Monitor with Tilt Adjustment"
        ),
        "sku": "0199291506220",
        "description": "27-inch FHD 144Hz IPS gaming monitor with tilt adjustment.",
        "price": "7995.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "fwebp_6_bfaee3f0-3513-4301-bace-fa904e4ac72d.jpg?v=1793193567"
        ),
    },
    {
        "name": (
            "SODI SP03 Privacy Screen Protector with Camera Protector "
            "for iPhone 16 Pro (2 Pack)"
        ),
        "sku": "6975969180732",
        "description": "Two-pack privacy screen and camera protectors for iPhone 16 Pro.",
        "price": "795.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "zdfnzxfdgn.jpg?v=1793192174"
        ),
    },
    {
        "name": "Thrustmaster TCA Sky Yoke for PS5 (4160953)",
        "sku": "0663296429148",
        "description": "Thrustmaster TCA Sky Yoke flight controller for PS5.",
        "price": "14695.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "OC_WhiteBG-TCASkyYoke_Sony-1_1000x1000_c2951994-abcd-440e-adc1-d72fce4d798c.jpg"
        ),
    },
    {
        "name": (
            "Hercules DJControl T10 Gig Pack Motorized DJ Controller "
            "+ Backpack (4781141)"
        ),
        "sku": "0663296427939",
        "description": "Motorized DJ controller gig pack with backpack.",
        "price": "102395.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "0663296427939.jpg?v=1793198976"
        ),
    },
    {
        "name": (
            "ASUS ZenScreen MB16NCG 16-inch WQXGA 155Hz 5ms GTG "
            "IPS Portable Monitor"
        ),
        "sku": "0199291223226",
        "description": "16-inch WQXGA 155Hz IPS portable monitor.",
        "price": "16295.00",
        "image_url": (
            "https://cdn.shopify.com/s/files/1/0355/8296/7943/files/"
            "0199291223226.jpg?v=1793198998"
        ),
    },
]


def seed_products() -> None:
    product_skus = [product["sku"] for product in PRODUCTS]

    with SessionLocal() as db:
        existing_skus = set(
            db.scalars(
                select(Product.sku).where(Product.sku.in_(product_skus))
            ).all()
        )

        added_count = 0
        skipped_count = 0

        for product_data in PRODUCTS:
            if product_data["sku"] in existing_skus:
                skipped_count += 1
                continue

            db.add(
                Product(
                    **product_data,
                    stock_quantity=DEMO_STOCK_QUANTITY,
                    is_active=True,
                )
            )
            added_count += 1

        db.commit()

    print(
        "Product seeding completed: "
        f"{added_count} added, {skipped_count} already existed."
    )


if __name__ == "__main__":
    seed_products()
