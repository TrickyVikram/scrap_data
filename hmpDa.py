import json

# Load Fiverr-style category data
with open("./fiverr_categories.json", "r", encoding="utf-8") as f:
    data = json.load(f)

sql_lines = []

# Step 1: Disable FK checks, Truncate, Reset Auto Increment
sql_lines.append("SET FOREIGN_KEY_CHECKS = 0;")
tables = [
    "sub_subcategories", "category_images", "cat_attribute",
    "child_cats_meta", "categories_children", "cats_meta", "categories"
]
for table in tables:
    sql_lines.append(f"TRUNCATE TABLE {table};")
    sql_lines.append(f"ALTER TABLE {table} AUTO_INCREMENT = 1;")
sql_lines.append("SET FOREIGN_KEY_CHECKS = 1;")

language_id = 1
uploaded_by = 1

# Utility functions
def clean_filename(text):
    return text.replace("&", "and").replace("/", "-").replace("’", "").replace(",", "").replace(".", "") \
               .replace("(", "").replace(")", "").replace(":", "").replace("?", "").replace("'", "") \
               .replace("-", "_").replace(" ", "_").lower()

def clean_url(text):
    return text.replace("&", "and").replace("/", "-").replace("’", "").replace(",", "").replace(".", "") \
               .replace("(", "").replace(")", "").replace(":", "").replace("?", "").replace("'", "") \
               .strip().replace(" ", "-").lower()

def sql_escape(value: str) -> str:
    if not isinstance(value, str):
        return value
    return value.replace("'", "''")  # Escape single quotes by doubling them

# Step 2: Insert data
for main_cat, sub_cats in data.items():
    cat_url = clean_url(main_cat)
    cat_image = f"{cat_url}.jpg"

    sql_lines.append(
        f"INSERT INTO categories (cat_url, cat_image, cat_featured, enable_watermark, isS3) "
        f"VALUES ('{cat_url}', '{cat_image}', 'yes', 1, 0);"
    )

    sql_lines.append(
        f"INSERT INTO cats_meta (cat_id, language_id, cat_title, cat_desc) "
        f"SELECT LAST_INSERT_ID(), {language_id}, '{sql_escape(main_cat)}', 'Description for {sql_escape(main_cat)}';"
    )

    for sub_cat, attributes in sub_cats.items():
        child_url = clean_url(sub_cat)

        sql_lines.append(
            f"INSERT INTO categories_children (child_url, child_parent_id) "
            f"SELECT '{child_url}', cat_id FROM categories WHERE cat_url = '{cat_url}';"
        )

        sql_lines.append(
            f"INSERT INTO child_cats_meta (child_id, child_parent_id, language_id, child_title, child_desc) "
            f"SELECT LAST_INSERT_ID(), cat_id, {language_id}, '{sql_escape(sub_cat)}', 'Description for {sql_escape(sub_cat)}' "
            f"FROM categories WHERE cat_url = '{cat_url}';"
        )

        for attr in attributes:
            cat_attr = attr
            attr_url = clean_url(attr)
            file_name = f"{attr_url}.jpg"
            file_path = f"/images/{file_name}"

            sql_lines.append(
                f"INSERT INTO cat_attribute (child_id, child_parent_id, cat_attr, language_id) "
                f"SELECT child_id, cat_id, '{sql_escape(cat_attr)}', {language_id} "
                f"FROM categories_children "
                f"JOIN categories ON categories.cat_id = categories_children.child_parent_id "
                f"WHERE categories.cat_url = '{cat_url}' AND categories_children.child_url = '{child_url}';"
            )

            sql_lines.append(
                f"INSERT INTO category_images (cat_id, child_id, attr_id, file_name, file_path, uploaded_by, uploaded_at) "
                f"SELECT cat_id, child_id, LAST_INSERT_ID(), '{file_name}', '{file_path}', {uploaded_by}, CURRENT_TIMESTAMP "
                f"FROM categories_children "
                f"JOIN categories ON categories.cat_id = categories_children.child_parent_id "
                f"WHERE categories.cat_url = '{cat_url}' AND categories_children.child_url = '{child_url}';"
            )

            sql_lines.append(
                f"INSERT INTO sub_subcategories (attr_id, subcategory_id, sub_subcategory_name, image, language_id) "
                f"SELECT cat_attribute.attr_id, cat_attribute.child_id, '{sql_escape(attr)}', '{file_path}', {language_id} "
                f"FROM cat_attribute "
                f"JOIN categories_children ON cat_attribute.child_id = categories_children.child_id "
                f"JOIN categories ON categories.cat_id = categories_children.child_parent_id "
                f"WHERE categories.cat_url = '{cat_url}' AND categories_children.child_url = '{child_url}' AND cat_attribute.cat_attr = '{sql_escape(cat_attr)}';"
            )

# Step 3: Write to file
output_file_path = "./subsub.sql"
with open(output_file_path, "w", encoding="utf-8") as f:
    f.write("\n".join(sql_lines))

print(f"✅ SQL script generated and saved to {output_file_path}")
