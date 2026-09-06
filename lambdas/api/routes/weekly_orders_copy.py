import json

EXPECTED_OUTPUT = {
    "data": {
        "created_at": {
            "0": "2026-08-10 21:24:59",
            "1": "2026-08-10 21:14:01",
        },
        "email": {
            "0": "john.doe@gmail.com",
            "1": "john.doe+1@gmail.com",
        },
        "Crushed Tomatoes - $5.55 per 28oz can": {"0": 1, "1": 1},
        "Cantaloupe - $5.55 each": {"0": 1, "1": ""},
    }
}

SAMPLE_CATALOG = {  ## LEGACY CATALOG
        "Items": [
            {
                "name": "Cantaloupe",
                "unit": "each",
                "price": 3.25,
                "category": "Produce",
            },
            {
                "name": "Crushed Tomatoes",
                "unit": "28oz can",
                "price": 5.55,
                "category": "Produce",
            },
        ],
        "updated_at": "2026-07-21T15:52:10.899511",
        "expries_at": "2026-07-26T15:52:10.899511",
    }


SAMPLE_ORDERS = {
    "Items": [
        {
            "SK":"abc-def",
            "created_at": "2026-08-10 21:24:59",
            "email": "john.doe@gmail.com",
            "firstName": "John",
            "lastName": "Doe",
            "phone": "+1234567890",
            "comments": "",
            "donation": 1,
            "menu_version": "ABC",
            "tip": 1,
            "products": [
                {
                    "id": "Cantaloupe",
                    "product_category": "Produce",
                    "product_name": "Cantaloupe",
                    "product_quantity": 1,
                    "product_unit": "each",
                    "unit_price": 3.25,
                },
                {
                    "id": "Crushed Tomatoes",
                    "product_category": "Produce",
                    "product_name": "Crushed Tomatoes",
                    "product_quantity": 1,
                    "product_unit": "28oz can",
                    "unit_price": 5.55,
                },
            ],
        },
        {
            "SK":"xyz-abc",
            "created_at": "2026-08-10 21:14:01",
            "email": "john.doe+1@gmail.com",
            "firstName": "John",
            "lastName": "Doe",
            "phone": "+1234567890",
            "comments": "",
            "donation": 0,
            "menu_version": "ABC",
            "tip": 0,
            "products": [
                {
                    "id": "Cantaloupe",
                    "product_category": "Produce",
                    "product_name": "Cantaloupe",
                    "product_quantity": 1,
                    "product_unit": "each",
                    "unit_price": 3.25,
                }
            ],
        },
    ]
}

def get_long_name(row):
    if row['unit'] == "each":
        return f"{row['name']} - ${row['price']:.2f} each"
    return f"{row['name']} - ${row['price']:.2f} per {row['unit']}"

def weekly_orders(week: str):
    try:

        items = SAMPLE_ORDERS.get('Items')

        if not items:
            return {"ok": True, "data": {}, "message":"No orders this week"}

        products_list = SAMPLE_CATALOG.get("Items",[])

        orders_information = ["order_id", "created_at", "menu_version", "email", "firstName", "lastName", "phone", "comments", "donation"]

        results = {column_name:{} for column_name in orders_information}


        # Explode embedded products into one row per order+product for pivot
        for id, item in enumerate(items):
            results["created_at"][id] = item.get("created_at", "")
            results["order_id"][id] = item["SK"]
            results["email"][id] = item.get("email", "")
            results["firstName"][id] = item.get("firstName", "")
            results["lastName"][id] = item.get("lastName", "")
            results["phone"][id] = item.get("phone", "")
            results["comments"][id] = item.get("comments", "")
            results["donation"][id] = item.get("donation", "")
            results["menu_version"][id] = item.get("menu_version", "")

            if "tip" in item.keys():
                if "tip" not in results:
                    results["tip"] = {}
            
                results["tip"][id] = item.get("tip","")

            ## TODO: convert from UTC to US/Eastern 

            order_product_names = {p["product_name"]:p for p in item.get("products", [])}
            for product in products_list:
                long_name = get_long_name(product)
                product_name = product.get("name","")

                if long_name not in results:
                    results[long_name] = {}

                if product_name in order_product_names.keys():
                    results[long_name][id] = order_product_names.get(product_name,{}).get("product_quantity","")
                else:
                    results[long_name][id] = ""


        order_count = len(items)
        print("Returning weekly orders for week %s: %d rows", week, order_count)


        return json.dumps({"ok": True, "data": results})

    except Exception as e:
        return {"error": "Error processing weekly orders", "details": str(e)}

if __name__ == "__main__":
    print(weekly_orders('2026-01'))
    print("hello")