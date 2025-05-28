import json

def escape_sql_string(s):
    return s.replace("'", "''")

# Load JSON data from file
with open('result.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

sql_lines = []

# Disable FK checks and truncate tables
sql_lines.append("SET FOREIGN_KEY_CHECKS = 0;")
tables = [
    "categories", "cats_meta", "categories_children", "child_cats_meta",
    "category_images", "sub_subcategories", "cat_attribute", "seller_skills"
]
for table in tables:
    sql_lines.append(f"TRUNCATE TABLE {table};")
    sql_lines.append(f"ALTER TABLE {table} AUTO_INCREMENT = 1;")
sql_lines.append("SET FOREIGN_KEY_CHECKS = 1;\n")

language_id = 1
user_id = 1  # for uploaded_by in category_images

for main_cat, sub_cats in data.items():
    cat_url = main_cat.lower().replace(" & ", "-and-").replace(" ", "-")
    cat_image = f"{cat_url}.jpg"

    # Insert main category
    sql_lines.append(
        f"INSERT INTO categories (cat_url, cat_image, cat_featured, enable_watermark, isS3) "
        f"VALUES ('{cat_url}', '{cat_image}', 'yes', 1, 0);"
    )
    sql_lines.append("SET @cat_id = LAST_INSERT_ID();")

    # Insert categories meta
    sql_lines.append(
        f"INSERT INTO cats_meta (cat_id, language_id, cat_title, cat_desc) "
        f"VALUES (@cat_id, {language_id}, '{main_cat}', 'Description for {main_cat}');"
    )

    # Insert a general child category
    general_child_url = f"{cat_url}-general"
    sql_lines.append(
        f"INSERT INTO categories_children (child_url, child_parent_id) VALUES ('{general_child_url}', @cat_id);"
    )
    sql_lines.append("SET @general_child_id = LAST_INSERT_ID();")

    # Insert child category meta
    sql_lines.append(
        f"INSERT INTO child_cats_meta (child_id, child_parent_id, language_id, child_title, child_desc) "
        f"VALUES (@general_child_id, @cat_id, {language_id}, 'General', 'General image for {main_cat}');"
    )

    # Insert category image
    sql_lines.append(
        f"INSERT INTO category_images (cat_id, child_id, attr_id, file_name, file_path, uploaded_by, uploaded_at) "
        f"VALUES (@cat_id, @general_child_id, 0, 'main_{cat_url}.jpg', '/images/main_{cat_url}.jpg', {user_id}, CURRENT_TIMESTAMP);"
    )

    child_id_counter = 1  # To simulate subcategory id variables (categories_children)
    attr_id_counter = 1   # To simulate cat_attribute attr_id variables

    for sub_cat, attrs in sub_cats.items():
        # Insert subcategory as child of main category
        child_url = sub_cat.lower().replace(" & ", "-and-").replace(" ", "-")
        sql_lines.append(
            f"INSERT INTO categories_children (child_url, child_parent_id) VALUES ('{child_url}', @cat_id);"
        )
        sql_lines.append(f"SET @child_id_{child_id_counter} = LAST_INSERT_ID();")
        current_child_var = f"@child_id_{child_id_counter}"

        # Insert child meta
        sql_lines.append(
            f"INSERT INTO child_cats_meta (child_id, child_parent_id, language_id, child_title, child_desc) "
            f"VALUES ({current_child_var}, @cat_id, {language_id}, '{sub_cat}', 'Description for {sub_cat}');"
        )

        # Loop over attributes inside this subcategory
        for attr_name, skill_obj in attrs.items():
            attr_url = attr_name.lower().replace(" ", "-")

            # Insert cat_attribute metadata (including child_parent_id)
            sql_lines.append(
                f"INSERT INTO cat_attribute (child_id, child_parent_id, cat_attr, language_id) "
                f"VALUES ({current_child_var}, @cat_id, '{attr_url}', {language_id});"
            )
            sql_lines.append(f"SET @attr_id_{attr_id_counter} = LAST_INSERT_ID();")
            current_attr_var = f"@attr_id_{attr_id_counter}"

            # Insert sub_subcategory with attr_id
            image_path = f"/images/{attr_url}.jpg"
            sql_lines.append(
                f"INSERT INTO sub_subcategories (subcategory_id, attr_id, sub_subcategory_name, image, language_id) "
                f"VALUES ({current_child_var}, {current_attr_var}, '{attr_name}', '{image_path}', {language_id});"
            )

            # Insert skills for this attribute
            skills = skill_obj.get("skill", [])
            for skill in skills:
                skill_url = skill.lower().replace(" ", "-")
                skill_full = escape_sql_string(f"{skill} ({attr_name})")

                sql_lines.append(
                    f"INSERT INTO seller_skills (cat_id, child_id, sub_child_id, skill_title, skill_url) "
                    f"VALUES (@cat_id, {current_child_var}, {current_attr_var}, '{skill_full}', '{skill_url}');"
                )

            attr_id_counter += 1

        child_id_counter += 1

# Write all SQL lines to output file
output_sql = "\n".join(sql_lines)
with open('output.sql', 'w', encoding='utf-8') as f:
    f.write(output_sql)
