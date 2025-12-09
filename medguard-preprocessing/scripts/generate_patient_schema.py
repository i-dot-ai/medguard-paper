from medguard.data import ModularPatientDataProcessor


def main():
    processor = ModularPatientDataProcessor()

    processor.create_table_views()

    processor.print_database_schema(max_sample_rows=10)


if __name__ == "__main__":
    main()
