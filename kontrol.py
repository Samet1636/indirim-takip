import sqlite3
c = sqlite3.connect("data/prices.db")

print("BİM kampanya tarihleri ve ürün sayıları:")
for r in c.execute("""SELECT s.valid_from, COUNT(*) FROM price_snapshots s
                      JOIN products p ON p.id = s.product_id
                      WHERE p.market = 'bim' GROUP BY s.valid_from ORDER BY 1"""):
    print("  ", r)

print("\nMigros'ta en çok indirimli 10 ürün:")
for r in c.execute("""SELECT name, regular_price, price, discount_pct FROM todays_discounts
                      WHERE market = 'migros' ORDER BY discount_pct DESC LIMIT 10"""):
    print("  ", r)