import os
import re
import sys

MIGRATIONS_DIR = "alembic/versions"


def main():
    """
    Main function to check migration files for completeness.
    """
    print(f"Checking for migration files in: {MIGRATIONS_DIR}")

    has_errors = False

    for filename in os.listdir(MIGRATIONS_DIR):
        if filename.endswith(".py") and filename != "__init__.py":
            file_path = os.path.join(MIGRATIONS_DIR, filename)
            print(f"Checking file: {file_path}")

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # More robustly find the upgrade and downgrade function bodies
            upgrade_match = re.search(
                r"def upgrade\(\) -> None:(.*?)def downgrade\(\) -> None:",
                content,
                re.DOTALL,
            )
            downgrade_match = re.search(
                r"def downgrade\(\) -> None:(.*)", content, re.DOTALL
            )

            if not upgrade_match or not downgrade_match:
                print(
                    f"  WARNING: Could not properly parse upgrade/downgrade "
                    f"functions in {file_path}. Skipping."
                )
                continue

            upgrade_section = upgrade_match.group(1)
            downgrade_section = downgrade_match.group(1)

            # Find all enum types created in the upgrade function
            enum_pattern = re.compile(r"sa\.Enum\(.*?, name='(.*?)'\)")
            created_enums = enum_pattern.findall(upgrade_section)

            if not created_enums:
                continue

            # Check if a corresponding DROP TYPE exists in the downgrade function
            for enum_name in created_enums:
                drop_type_pattern = re.compile(
                    r"DROP TYPE {}".format(re.escape(enum_name)), re.IGNORECASE
                )

                found_drop_in_downgrade = False
                for line in downgrade_section.splitlines():
                    # Ignore commented out lines
                    if line.strip().startswith("#"):
                        continue
                    if drop_type_pattern.search(line):
                        found_drop_in_downgrade = True
                        break

                if not found_drop_in_downgrade:
                    print(
                        f"  ERROR: Enum '{enum_name}' is created in upgrade, "
                        f"but not dropped in downgrade in file {file_path}"
                    )
                    has_errors = True

    if has_errors:
        print("\nMigration check failed. Please fix the issues above.")
        sys.exit(1)
    else:
        print("\nMigration check passed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
